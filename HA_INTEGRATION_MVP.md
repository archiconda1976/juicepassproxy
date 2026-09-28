# Native Home Assistant integration MVP

This branch begins migration from the standalone JuicePassProxy process to a native Home Assistant custom integration.

## MVP scope

- One JuiceBox with a static IPv4 address.
- Home Assistant listens directly for the legacy JuiceBox UDP protocol (default UDP 8047).
- Routing is by DNS rewrite of the JuiceBox's configured Enel X/eMotorWerks UDP hostname to the Home Assistant host IP.
- Native Home Assistant sensor and number entities; MQTT is not used.
- Legacy protocol parsing and command framing are adapted from JuiceRescue/juicepassproxy.
- Local command responses are sent only after both online and offline current limits are known. The integration does not invent a missing current limit.

## Deferred until after MVP

- Telnet / UDPC rewriting.
- Automatic discovery of the configured upstream hostname/port.
- Multiple JuiceBoxes.
- Transparent forwarding to the legacy Enel X server.
- Encrypted protocol support.
- HACS packaging / Core submission work.

## Test path

1. Copy custom_components/juicebox_local to the HA config directory.
2. Restart Home Assistant.
3. Add JuiceBox Local under Settings -> Devices & services. Enter the charger's static IPv4 address and leave UDP 8047 unless your charger uses another port.
4. In AdGuard Home, rewrite the JuiceBox's configured service hostname to the Home Assistant host IP.
5. Confirm telemetry is arriving before changing current-limit controls.

Firewall policy should allow the JuiceBox to use the DNS resolver containing the rewrite and reach Home Assistant on the configured UDP port.
