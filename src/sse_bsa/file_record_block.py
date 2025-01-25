"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BufferedReader

from .datatypes import String
from .file_record import FileRecord


@dataclass
class FileRecordBlock:
    """
    Class for file record block.

    See here for more information:
        https://en.uesp.net/wiki/Skyrim_Mod:Archive_File_Format#File_Record_blocks
    """

    name: str
    """
    The folder name. Only present if `Header.ArchiveFlags.IncludeDirectoryNames` is set.

    TODO: Although the flag is set in all official BSAs, prevent this from causing an issue if it isn't set
    """

    file_records: list[FileRecord] = field(default_factory=list)
    """
    List of file records in the block.
    """

    @staticmethod
    def parse(stream: BufferedReader, count: int) -> FileRecordBlock:
        """
        Parses a file record block from a stream with a specified number of file records.

        Args:
            stream (BufferedReader): Stream to parse from.
            count (int): Number of file records in the block.

        Returns:
            FileRecordBlock: Parsed file record block.
        """

        return FileRecordBlock(
            name=String.parse(stream, String.StrType.BZString),
            file_records=[FileRecord.parse(stream) for _ in range(count)],
        )

    def dump(self) -> bytes:
        """
        Dumps the file record block to a byte array.

        Returns:
            bytes: Dumped byte array.
        """

        data = b""

        data += String.dump(self.name, String.StrType.BZString)
        data += b"".join(file_record.dump() for file_record in self.file_records)

        return data
