"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BufferedReader

from .datatypes import Hash, Integer


@dataclass
class FolderRecord:
    """
    Class for folder records.

    See here for more information:
        https://en.uesp.net/wiki/Skyrim_Mod:Archive_File_Format#Folder_Record
    """

    name_hash: int
    """
    Hash of the folder name (eg: menus\chargen). Must be all lower case,
    and use backslash as directory delimiter(s).
    """

    count: int
    """
    Amount of files in this folder.
    """

    padding: int
    """
    Only present in archive version 105 (Skyrim Special Edition).
    """

    offset: int
    """
    Offset to file records for this folder.
    (Subtract totalFileNameLength to get the actual offset within the file.)
    """

    padding2: int
    """
    Only present in archive version 105 (Skyrim Special Edition).
    """

    @staticmethod
    def parse(stream: BufferedReader) -> FolderRecord:
        """
        Parses a folder record from a stream.

        Args:
            stream (BufferedReader): Stream to parse from.

        Returns:
            FolderRecord: Parsed folder record.
        """

        return FolderRecord(
            name_hash=Hash.parse(stream),
            count=Integer.parse(stream, Integer.IntType.ULong),
            padding=Integer.parse(stream, Integer.IntType.ULong),
            offset=Integer.parse(stream, Integer.IntType.ULong),
            padding2=Integer.parse(stream, Integer.IntType.ULong),
        )

    def dump(self) -> bytes:
        """
        Dumps the folder record to a byte array.

        Returns:
            bytes: Dumped byte array.
        """

        data: bytes = b""

        data += Hash.dump(self.name_hash)
        data += Integer.dump(self.count, Integer.IntType.ULong)
        data += Integer.dump(self.padding, Integer.IntType.ULong)
        data += Integer.dump(self.offset, Integer.IntType.ULong)
        data += Integer.dump(self.padding2, Integer.IntType.ULong)

        return data
