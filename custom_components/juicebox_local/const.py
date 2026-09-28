"""Constants for the JuiceBox Local integration."""

from homeassistant.const import Platform

DOMAIN = "juicebox_local"

CONF_LISTEN_PORT = "listen_port"
DEFAULT_LISTEN_PORT = 8047
DEFAULT_NAME = "JuiceBox"

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR, Platform.NUMBER)

# JuiceBox normally reports much more frequently than this while online.
AVAILABILITY_TIMEOUT_SECONDS = 180
