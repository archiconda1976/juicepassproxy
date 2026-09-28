"""CRC implementation used by the legacy JuiceBox protocol."""


class JuiceBoxCRC:
    """Calculate the JuiceBox base-35 CRC."""

    ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, payload: str) -> None:
        self.payload = payload

    def integer(self) -> int:
        """Return the integer CRC."""
        h = 0
        for char in self.payload:
            h ^= (h << 5) + (h >> 2) + ord(char)
            h &= 0xFFFF
        return h

    def base35(self) -> str:
        """Return the three-character JuiceBox base-35 CRC."""
        number = self.integer()
        encoded = ""
        while number > 1 or len(encoded) < 3:
            number, index = divmod(number, 35)
            # Preserve the legacy JuiceBox encoding behavior.
            if index == 24:
                index = 35
            encoded += self.ALPHABET[index]
        return encoded
