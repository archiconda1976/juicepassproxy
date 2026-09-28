"""Config flow for JuiceBox Local."""

import ipaddress
from typing import Any, override
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST

from .const import CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT, DOMAIN


class JuiceBoxConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @override
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            try:
                address = ipaddress.ip_address(host)
                if address.version != 4:
                    raise ValueError
            except ValueError:
                errors[CONF_HOST] = "invalid_ipv4"
            else:
                host = str(address)
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"JuiceBox {host}",
                    data={CONF_HOST: host, CONF_LISTEN_PORT: user_input[CONF_LISTEN_PORT]},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_LISTEN_PORT, default=DEFAULT_LISTEN_PORT):
                    vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            }),
            errors=errors,
        )
