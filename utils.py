from enum import Enum


class ByteEnum(Enum):

    def __bytes__(self) -> bytes:
        return self.value

    def __add__(self, other):
        if isinstance(other, ByteEnum):
            return bytes(self) + other
        elif isinstance(other, bytes):
            return bytes(self) + other
        else:
            return NotImplemented

    def __radd__(self, other):
        if isinstance(other, bytes):
            return other + bytes(self)
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self is other
        return self.value == other
