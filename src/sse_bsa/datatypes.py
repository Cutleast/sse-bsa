"""
Copyright (c) Cutleast
"""

import os
import struct
from enum import Enum, IntFlag, auto
from typing import Literal, Optional, Self, overload

from .utilities import Stream, get_stream, read_data


class Integer:
    """
    Class for all types of signed and unsigned integers.
    """

    class IntType(Enum):
        UInt8 = (1, False)
        """Unsigned Integer of size 1."""

        UInt16 = (2, False)
        """Unsigned Integer of size 2."""

        UInt32 = (4, False)
        """Unsigned Integer of size 4."""

        UInt64 = (8, False)
        """Unsigned Integer of size 8."""

        UShort = (2, False)
        """Same as UInt16."""

        ULong = (4, False)
        """Same as UInt32."""

        Int8 = (1, True)
        """Signed Integer of Size 1."""

        Int16 = (2, True)
        """Signed Integer of Size 2."""

        Int32 = (4, True)
        """Signed Integer of Size 4."""

        Int64 = (8, True)
        """Signed Integer of Size 8."""

        Short = (2, True)
        """Same as Int16."""

        Long = (4, True)
        """Same as Int32."""

    @staticmethod
    def parse(data: Stream | bytes, type: IntType) -> int:
        """
        Parses an integer of the specified type from the specified data.

        Args:
            data (Stream | bytes): Stream or byte array.
            type (IntType): Integer type.

        Returns:
            int: Parsed integer.
        """

        size: int
        signed: bool
        size, signed = type.value

        return int.from_bytes(
            get_stream(data).read(size), byteorder="little", signed=signed
        )

    @staticmethod
    def dump(value: int, type: IntType) -> bytes:
        """
        Dumps an integer of the specified type to a byte array.

        Args:
            value (int): Integer.
            type (IntType): Integer type.

        Returns:
            bytes: Byte array.
        """

        size: int
        signed: bool
        size, signed = type.value

        return value.to_bytes(size, byteorder="little", signed=signed)


class String:
    """
    Class for all types of chars and strings.
    """

    ENCODING: str = "cp1252"
    """The default encoding used in Bethesda's file formats."""

    class StrType(Enum):
        Char = auto()
        """8-bit character."""

        WChar = auto()
        """16-bit character."""

        String = auto()
        """Not-terminated string."""

        WString = auto()
        """Not-terminated string prefixed by UInt16."""

        BZString = auto()
        """Null-terminated string prefixed by UInt8."""

        BString = auto()
        """Not-terminated string prefixed by UInt8."""

        List = auto()
        """List of strings separated by `\\x00`."""

    @staticmethod
    @overload
    def parse(
        data: Stream | bytes, type: Literal[StrType.Char], size: Literal[1] = 1
    ) -> str: ...

    @staticmethod
    @overload
    def parse(
        data: Stream | bytes, type: Literal[StrType.WChar], size: Literal[1] = 1
    ) -> str: ...

    @staticmethod
    @overload
    def parse(
        data: Stream | bytes, type: Literal[StrType.String], size: int
    ) -> str: ...

    @staticmethod
    @overload
    def parse(
        data: Stream | bytes, type: Literal[StrType.WString], size: None = None
    ) -> str: ...

    @staticmethod
    @overload
    def parse(
        data: Stream | bytes, type: Literal[StrType.BString], size: None = None
    ) -> str: ...

    @staticmethod
    @overload
    def parse(
        data: Stream | bytes, type: Literal[StrType.BZString], size: None = None
    ) -> str: ...

    @staticmethod
    @overload
    def parse(
        data: Stream | bytes, type: Literal[StrType.List], size: int
    ) -> list[str]: ...

    @staticmethod
    def parse(
        data: Stream | bytes, type: StrType, size: Optional[int] = None
    ) -> list[str] | str:
        """
        Parses a string of the specified type from the specified data.

        Args:
            data (Stream | bytes): Stream or byte array.
            type (StrType): String type.
            size (Optional[int], optional): Size of the string(s). Defaults to None.

        Returns:
            list[str] | str: Parsed string(s).
        """

        stream = get_stream(data)

        match type:
            case type.Char:
                text = read_data(stream, 1)

            case type.WChar:
                text = read_data(stream, 2)

            case type.String:
                if size is None:
                    raise ValueError("'size' must not be None when 'type' is 'String'!")

                text = read_data(stream, size)

            case type.WString:
                size = Integer.parse(stream, Integer.IntType.UInt16)
                text = read_data(stream, size)

            case type.BZString | type.BString:
                size = Integer.parse(stream, Integer.IntType.UInt8)
                text = read_data(stream, size).strip(b"\x00")

            case type.List:
                strings: list[str] = []

                if size is None:
                    raise ValueError("'size' must not be None when 'type' is 'List'!")

                while len(strings) < size:
                    string = b""
                    while (char := stream.read(1)) != b"\x00" and char:
                        string += char

                    if string:
                        strings.append(string.decode(String.ENCODING))

                return strings

        return text.decode()

    @staticmethod
    @overload
    def dump(value: list[str], type: Literal[StrType.List]) -> bytes: ...

    @staticmethod
    @overload
    def dump(
        value: str,
        type: Literal[
            StrType.Char,
            StrType.WChar,
            StrType.String,
            StrType.WString,
            StrType.BString,
            StrType.BZString,
        ],
    ) -> bytes: ...

    @staticmethod
    def dump(value: list[str] | str, type: StrType) -> bytes:
        """
        Dumps a string of the specified type to a byte array.

        Args:
            value (list[str] | str): String or list of strings to dump.
            type (StrType): String type.

        Returns:
            bytes: Byte array.
        """

        match type:
            case String.StrType.Char | String.StrType.WChar | String.StrType.String:
                if not isinstance(value, str):
                    raise TypeError("'value' must be a string!")

                return value.encode(String.ENCODING)

            case String.StrType.WString:
                if not isinstance(value, str):
                    raise TypeError("'value' must be a string!")

                text = value.encode(String.ENCODING)
                size = Integer.dump(len(text), Integer.IntType.UInt16)
                return size + text

            case String.StrType.BString:
                if not isinstance(value, str):
                    raise TypeError("'value' must be a string!")

                text = value.encode(String.ENCODING)
                size = Integer.dump(len(text), Integer.IntType.UInt8)
                return size + text

            case String.StrType.BZString:
                if not isinstance(value, str):
                    raise TypeError("'value' must be a string!")

                text = value.encode(String.ENCODING) + b"\x00"
                size = Integer.dump(len(text), Integer.IntType.UInt8)
                return size + text

            case String.StrType.List:
                if not isinstance(value, list):
                    raise TypeError("'value' must be a list!")

                data = b"\x00".join(v.encode(String.ENCODING) for v in value) + b"\x00"

                return data


class Flags(IntFlag):
    """
    Class for all types of flags.
    """

    @classmethod
    def parse(cls, data: Stream | bytes, type: Integer.IntType) -> Self:
        """
        Parses a flag from a stream or byte array.

        Args:
            data (Stream | bytes): Stream or byte array.
            type (Integer.IntType): Integer type.

        Returns:
            Self: Parsed flag.
        """

        value: int = Integer.parse(data, type)
        flag = cls(value)

        return flag

    def dump(self, type: Integer.IntType) -> bytes:
        """
        Dumps a flag to a byte array.

        Args:
            type (Integer.IntType): Integer type.

        Returns:
            bytes: Byte array.
        """

        return Integer.dump(self.value, type)


class Hex:
    """
    Class for all types of hexadecimal strings.
    """

    @staticmethod
    def parse(data: Stream | bytes, size: int) -> str:
        return read_data(data, size).hex()

    @staticmethod
    def dump(value: str, type: Integer.IntType) -> bytes:
        number = int(value, base=16)

        return Integer.dump(number, type)


class Hash:
    """
    Class for all types of hashes.
    """

    @staticmethod
    def parse(data: Stream | bytes) -> int:
        return Integer.parse(data, Integer.IntType.UInt64)

    @staticmethod
    def dump(value: int) -> bytes:
        return Integer.dump(value, Integer.IntType.UInt64)

    @staticmethod
    def calc_hash(filename: str) -> int:
        """
        Returns TES4's two hash values for filename.
        Based on TimeSlips code, fixed for names < 3 characters
        and updated to Python 3.

        This original code is from here:
        https://en.uesp.net/wiki/Oblivion_Mod:Hash_Calculation
        """

        name, ext = os.path.splitext(
            filename.lower()
        )  # --"bob.dds" >> root = "bob", ext = ".dds"

        # Create the hashBytes array equivalent
        hash_bytes = [
            ord(name[-1]) if len(name) > 0 else 0,
            ord(name[-2]) if len(name) >= 3 else 0,
            len(name),
            ord(name[0]) if len(name) > 0 else 0,
        ]

        # Convert the byte array to a single 32-bit integer
        hash1: int = struct.unpack("I", bytes(hash_bytes))[0]

        # Apply extensions-specific bit manipulation
        if ext == ".kf":
            hash1 |= 0x80
        elif ext == ".nif":
            hash1 |= 0x8000
        elif ext == ".dds":
            hash1 |= 0x8080
        elif ext == ".wav":
            hash1 |= 0x80000000

        hash2 = 0
        for i in range(1, len(name) - 2):
            hash2 = hash2 * 0x1003F + ord(name[i])

        hash3 = 0
        for char in ext:
            hash3 = hash3 * 0x1003F + ord(char)

        uint_mask = 0xFFFFFFFF
        combined_hash = ((hash2 + hash3) & uint_mask) << 32 | hash1

        return combined_hash
