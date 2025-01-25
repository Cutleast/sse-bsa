"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BufferedReader

from .datatypes import Flags, Integer


@dataclass
class Header:
    """
    Class for archive header.

    See here for more information:
        https://en.uesp.net/wiki/Skyrim_Mod:Archive_File_Format#Header
    """

    class ArchiveFlags(Flags):
        IncludeDirectoryNames = 0x1
        """
        Include Directory Names. (The game may not load a BSA without this bit set.)
        Set in all official BSA files.
        """

        IncludeFileNames = 0x2
        """
        Include File Names. (The game may not load a BSA without this bit set.)
        Set in all official BSA files.
        """

        CompressedArchive = 0x4
        """
        Compressed Archive. This does not mean all files are compressed.
        It means they are compressed by default.
        """

        RetainDirectoryNames = 0x8
        """
        Retain Directory Names. Has no effect on the file structure.
        """

        RetainFileNames = 0x10
        """
        Retain File Names. Has no effect on the file structure.
        """

        RetainFileNameOffsets = 0x20
        """
        Retain File Name Offsets. Has no effect on the file structure.
        """

        Xbox360archive = 0x40
        """
        Xbox360 archive. Hash values and numbers after the header are encoded big-endian.
        """

        RetainStringsDuringStartup = 0x80
        """
        Retain Strings During Startup. Has no effect on the file structure.
        """

        EmbedFileNames = 0x100
        """
        Embed File Names. Indicates the file data blocks begin with a bstring containing
        the full path of the file. For example, in "Skyrim - Textures.bsa" the first data
        block is `$2B textures\\effects\\fxfluidstreamdripatlus.dds`
        ($2B indicating the name is 43 bytes).
        The data block begins immediately after the bstring.
        """

        XMemCodec = 0x200
        """
        XMem Codec. This can only be used with Bit 3 (Compress Archive).
        This is an Xbox 360 only compression algorithm.
        """

    class FileFlags(Flags):
        Meshes = 0x1
        Textures = 0x2
        Menus = 0x4
        Sounds = 0x8
        Voices = 0x10
        Shaders = 0x20
        Trees = 0x40
        Fonts = 0x80
        Miscellaneous = 0x100

    file_id: bytes = b"BSA\x00"
    version: int = 0x69  # Skyrim SE as default version
    offset: int = 0x24  # Header has fix size of 36 bytes
    """
    Offset of beginning of folder records. All headers are the same size,
    therefore this value is 36 (0x24).
    """

    archive_flags: ArchiveFlags = ArchiveFlags(
        ArchiveFlags.IncludeDirectoryNames
        | ArchiveFlags.IncludeFileNames
        | ArchiveFlags.CompressedArchive
        | ArchiveFlags.RetainDirectoryNames
        | ArchiveFlags.RetainFileNames
        | ArchiveFlags.RetainFileNameOffsets
    )
    folder_count: int = 0
    """
    Count of all folders in archive.
    """

    file_count: int = 0
    """
    Count of all files in archive.
    """

    total_folder_name_length: int = 0
    """
    Total length of all folder names, including \0's but not including
    the prefixed length byte.
    """

    total_file_name_length: int = 0
    """
    Total length of all file names, including \0's.
    """

    file_flags: FileFlags = FileFlags(0)
    padding: int = 0

    @staticmethod
    def parse(stream: BufferedReader) -> Header:
        """
        Parses a header from a stream.

        Args:
            stream (BufferedReader): Stream to parse from.

        Raises:
            ValueError: when the archive version is not supported

        Returns:
            Header: Parsed header
        """

        file_id: bytes = stream.read(4)
        version: int = Integer.parse(stream, Integer.IntType.ULong)

        if version != 105:
            raise ValueError("Archive version is not supported!")

        return Header(
            file_id=file_id,
            version=version,
            offset=Integer.parse(stream, Integer.IntType.ULong),
            archive_flags=Header.ArchiveFlags.parse(stream, Integer.IntType.ULong),
            folder_count=Integer.parse(stream, Integer.IntType.ULong),
            file_count=Integer.parse(stream, Integer.IntType.ULong),
            total_folder_name_length=Integer.parse(stream, Integer.IntType.ULong),
            total_file_name_length=Integer.parse(stream, Integer.IntType.ULong),
            file_flags=Header.FileFlags.parse(stream, Integer.IntType.UShort),
            padding=Integer.parse(stream, Integer.IntType.UShort),
        )

    def dump(self) -> bytes:
        """
        Dumps the header to a byte array.

        Returns:
            bytes: Dumped byte array.
        """

        data: bytes = b""

        data += self.file_id
        data += Integer.dump(self.version, Integer.IntType.ULong)
        data += Integer.dump(self.offset, Integer.IntType.ULong)
        data += self.archive_flags.dump(Integer.IntType.ULong)
        data += Integer.dump(self.folder_count, Integer.IntType.ULong)
        data += Integer.dump(self.file_count, Integer.IntType.ULong)
        data += Integer.dump(self.total_folder_name_length, Integer.IntType.ULong)
        data += Integer.dump(self.total_file_name_length, Integer.IntType.ULong)
        data += self.file_flags.dump(Integer.IntType.UShort)
        data += Integer.dump(self.padding, Integer.IntType.UShort)

        return data
