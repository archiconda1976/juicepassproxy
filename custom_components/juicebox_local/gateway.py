"""Async UDP gateway for JuiceBox Local."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
import logging

from .models import JuiceBoxState
from .protocol import (
    JuiceBoxCommand,
    JuiceBoxDebugMessage,
    JuiceBoxEncryptedMessage,
    JuiceBoxInvalidMessageFormat,
    JuiceBoxStatusMessage,
    juicebox_message_from_bytes,
)

_LOGGER = logging.getLogger(__name__)
StateCallback = Callable[[JuiceBoxState], None]


class _Protocol(asyncio.DatagramProtocol):
    def __init__(self, gateway: "JuiceBoxGateway") -> None:
        self.gateway = gateway

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.gateway.datagram_received(data, addr)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.warning("JuiceBox UDP transport error: %s", exc)


class JuiceBoxGateway:
    """Own one local UDP listener and the state of one JuiceBox."""

    def __init__(self, host: str, listen_port: int, on_state: StateCallback) -> None:
        self.host = host
        self.listen_port = listen_port
        self.on_state = on_state
        self.state = JuiceBoxState()
        self._transport: asyncio.DatagramTransport | None = None
        self._juicebox_addr: tuple[str, int] | None = None
        self._last_status: JuiceBoxStatusMessage | None = None
        self._last_command: JuiceBoxCommand | None = None

    async def async_start(self) -> None:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _Protocol(self), local_addr=("0.0.0.0", self.listen_port)
        )
        self._transport = transport
        _LOGGER.info("Listening for JuiceBox %s on UDP %s", self.host, self.listen_port)

    async def async_stop(self) -> None:
        if self._transport:
            self._transport.close()
            self._transport = None

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if addr[0] != self.host:
            _LOGGER.debug("Ignoring JuiceBox UDP packet from unexpected host %s", addr[0])
            return

        try:
            message = juicebox_message_from_bytes(data)
        except JuiceBoxInvalidMessageFormat as err:
            _LOGGER.warning("Invalid JuiceBox datagram from %s: %s", addr[0], err)
            return

        self._juicebox_addr = addr
        self.state.last_seen = datetime.now(UTC)

        if isinstance(message, JuiceBoxEncryptedMessage):
            self.state.update_from_message({
                "serial": message.serial,
                "protocol_version": message.version,
                "debug_message": "Encrypted JuiceBox protocol is not supported",
            })
            self.on_state(self.state)
            return

        if isinstance(message, JuiceBoxDebugMessage):
            self.state.update_from_message(message.to_simple_format())
            self.on_state(self.state)
            return

        self._last_status = message
        self.state.update_from_message(message.to_simple_format())
        if self.state.desired_online_current is None and self.state.current_max_online is not None:
            self.state.desired_online_current = int(self.state.current_max_online)
        if self.state.desired_offline_current is None and self.state.current_max_offline is not None:
            self.state.desired_offline_current = int(self.state.current_max_offline)
        self.on_state(self.state)
        self._send_current_limits()

    def set_online_current(self, value: int) -> None:
        self._validate_current(value)
        self.state.desired_online_current = value
        self.on_state(self.state)
        self._send_current_limits()

    def set_offline_current(self, value: int) -> None:
        self._validate_current(value)
        self.state.desired_offline_current = value
        self.on_state(self.state)
        self._send_current_limits()

    def _validate_current(self, value: int) -> None:
        if value < 0:
            raise ValueError("Current limit cannot be negative")
        if self.state.current_rating is not None and value > self.state.current_rating:
            raise ValueError("Current limit exceeds charger rating")

    def _send_current_limits(self) -> None:
        if (
            self._transport is None
            or self._juicebox_addr is None
            or self._last_status is None
            or self.state.desired_online_current is None
            or self.state.desired_offline_current is None
        ):
            return
        command = JuiceBoxCommand(
            previous=self._last_command,
            new_version=self._last_status.get_value("v") == "09u",
        )
        command.instant_amperage = self.state.desired_online_current
        command.offline_amperage = self.state.desired_offline_current
        self._transport.sendto(command.build().encode(), self._juicebox_addr)
        self._last_command = command
