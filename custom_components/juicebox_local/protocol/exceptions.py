"""JuiceBox protocol exceptions."""


class JuiceBoxProtocolError(Exception):
    """Base exception for JuiceBox protocol failures."""


class JuiceBoxInvalidMessageFormat(JuiceBoxProtocolError):
    """Raised when a JuiceBox message cannot be parsed or validated."""
