"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BufferedReader
from typing import Optional

from .datatypes import Hash, Integer


@dataclass
class FileRecord:
    """
    Class for file record.

    See here for more information:
        https://en.uesp.net/wiki/Skyrim_Mod:Archive_File_Format#File_Record
    """

    name_hash: int
    """
    Hash of the file name (eg: race_sex_menu.xml). Must be all lower case.
    """

    size: int
    """
    Size of the file data.

    If the 30th bit (0x40000000) is set in the size:
    - If files are default compressed, this file is not compressed.
    - If files are default not compressed, this file is compressed.

    If the file is compressed the file data will have the specification of
    Compressed File block. In addition, the size of compressed data is considered
    to be the ulong "original size" plus the compressed data size (4 + compressed size).
    """

    offset: int = 0
    """
    Offset to raw file data for this folder.
    Note that an "offset" is offset from file byte zero (start), NOT from this location.
    """

    COMPRESSION_FLAG: int = 0x40000000
    compressed: Optional[bool] = None
    """
    Whether the file is compressed.
    """

    def has_compression_flag(self) -> bool:
        """
        Checks if the file has the compression flag set.

        Returns:
            bool: Whether the file has the compression flag set.
        """

        # Mask for the 30th bit (0x40000000)
        mask = 0x40000000

        # Use bitwise AND to check if the 30th bit is set
        is_set = self.size & mask

        return is_set != 0

    @staticmethod
    def apply_compression_flag(size: int) -> int:
        """
        Applies the compression flag to the size.

        Args:
            size (int): Size of the file.

        Returns:
            int: Size with compression flag applied
        """

        # Mask for the 30th bit (0x40000000)
        mask = 0x40000000

        # Use bitwise OR to set the 30th bit
        size |= mask

        return size

    @staticmethod
    def parse(stream: BufferedReader) -> FileRecord:
        """
        Parses a file record from a stream.

        Args:
            stream (BufferedReader): Stream to parse from.

        Returns:
            FileRecord: Parsed file record.
        """

        return FileRecord(
            name_hash=Hash.parse(stream),
            size=Integer.parse(stream, Integer.IntType.ULong),
            offset=Integer.parse(stream, Integer.IntType.ULong),
        )

    def dump(self) -> bytes:
        """
        Dumps the file record to a byte array.

        Returns:
            bytes: Dumped byte array.
        """

        data: bytes = b""

        data += Hash.dump(self.name_hash)
        if self.compressed:
            self.size = self.apply_compression_flag(self.size)
        data += Integer.dump(self.size, Integer.IntType.ULong)
        data += Integer.dump(self.offset, Integer.IntType.ULong)

        return data

    def __hash__(self) -> int:
        return hash((self.name_hash, self.size))
