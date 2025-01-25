"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BufferedReader

from .datatypes import String


@dataclass
class FileNameBlock:
    """
    Class for file name block.

    See here for more information:
        https://en.uesp.net/wiki/Skyrim_Mod:Archive_File_Format#File_Name_block
    """

    file_names: list[str]
    """
    List of file names in the block.
    """

    @staticmethod
    def parse(stream: BufferedReader, count: int) -> FileNameBlock:
        """
        Parses a file name block from a stream with a specified number of file names.

        Args:
            stream (BufferedReader): Stream to parse from.
            count (int): Number of file names in the block.

        Returns:
            FileNameBlock: Parsed file name block.
        """

        filename_block = FileNameBlock(String.parse(stream, String.StrType.List, count))

        return filename_block

    def dump(self) -> bytes:
        """
        Dumps the file name block to a byte array.

        Returns:
            bytes: Dumped byte array.
        """

        data: bytes = String.dump(self.file_names, String.StrType.List)

        return data
