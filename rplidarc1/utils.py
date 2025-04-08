from enum import Enum

"""
This module provides utility classes for the RPLidar implementation.
"""


class ByteEnum(Enum):
    """
    An extension of the Enum class that provides additional functionality
    for working with byte values.

    This class adds methods to convert enum values to bytes and to perform
    operations like addition and comparison with bytes objects.
    """

    def __bytes__(self) -> bytes:
        """
        Convert the enum value to bytes.

        Returns:
            bytes: The enum value as bytes.
        """
        return self.value

    def __add__(self, other):
        """
        Add this enum value to another value.

        Args:
            other: The value to add. Can be another ByteEnum or a bytes object.

        Returns:
            bytes: The result of the addition.

        Raises:
            NotImplementedError: If the other value is not a ByteEnum or bytes object.
        """
        if isinstance(other, ByteEnum):
            return bytes(self) + other
        elif isinstance(other, bytes):
            return bytes(self) + other
        else:
            return NotImplemented

    def __radd__(self, other):
        """
        Add another value to this enum value (right addition).

        Args:
            other: The value to add. Must be a bytes object.

        Returns:
            bytes: The result of the addition.

        Raises:
            NotImplementedError: If the other value is not a bytes object.
        """
        if isinstance(other, bytes):
            return other + bytes(self)
        else:
            return NotImplemented

    def __eq__(self, other):
        """
        Compare this enum value to another value for equality.

        Args:
            other: The value to compare to. Can be another ByteEnum or any other value.

        Returns:
            bool: True if the values are equal, False otherwise.
        """
        if isinstance(other, type(self)):
            return self is other
        return self.value == other
