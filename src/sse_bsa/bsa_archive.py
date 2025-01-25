"""
Copyright (c) Cutleast
"""

import os
from io import BytesIO
from pathlib import Path
from typing import Optional

import lz4.frame
from virtual_glob import InMemoryPath, glob

from .datatypes import Hash, Integer, String
from .file_name_block import FileNameBlock
from .file_record import FileRecord
from .file_record_block import FileRecordBlock
from .folder_record import FolderRecord
from .header import Header
from .utilities import create_folder_list


class BSAArchive:
    """
    Represents a BSA archive file for Skyrim Special Edition.
    **Other BSA versions are not supported at the moment!**

    See here for more information about the file specification:
        https://en.uesp.net/wiki/Skyrim_Mod:Archive_File_Format
    """

    __path: Path
    header: Header
    """
    The parsed archive header.
    """

    __folders: list[FolderRecord]
    __file_record_blocks: list[FileRecordBlock]
    __file_name_block: FileNameBlock
    __files: dict[str, FileRecord]

    def __init__(self, archive_path: Path) -> None:
        """
        Initializes a `BSAArchive` instance from a specified path.

        Args:
            archive_path (Path): The path to the archive file.
        """

        self.__path = archive_path

        self.__load()

    def __match_names(self) -> dict[str, FileRecord]:
        result: dict[str, FileRecord] = {}

        index: int = 0
        for file_record_block in self.__file_record_blocks:
            for file_record in file_record_block.file_records:
                file_path: str = file_record_block.name
                file_name: str = self.__file_name_block.file_names[index]
                file: str = str(Path(file_path) / file_name).replace("\\", "/")
                result[file] = file_record
                index += 1

        return result

    def __process_compression_flags(self) -> None:
        for file_record in self.__files.values():
            has_compression_flag: bool = file_record.has_compression_flag()
            compressed_archive: bool = (
                Header.ArchiveFlags.CompressedArchive in self.header.archive_flags
            )

            if has_compression_flag:
                file_record.compressed = not compressed_archive
            else:
                file_record.compressed = compressed_archive

    def __load(self) -> None:
        with self.__path.open("rb") as stream:
            self.header = Header().parse(stream)
            self.__folders = [
                FolderRecord.parse(stream) for i in range(self.header.folder_count)
            ]
            self.__file_record_blocks = [
                FileRecordBlock.parse(stream, self.__folders[i].count)
                for i in range(self.header.folder_count)
            ]
            self.__file_name_block = FileNameBlock.parse(stream, self.header.file_count)

        self.__files = self.__match_names()
        self.__process_compression_flags()

    @property
    def files(self) -> list[str]:
        """
        A list of all files in the archive.
        """

        return list(self.__files.keys())

    def glob(self, pattern: str) -> list[str]:
        """
        Returns a list of file paths that match the specified pattern.

        Args:
            pattern (str): File name pattern.

        Returns:
            list[str]: List of matching filenames
        """

        fs: InMemoryPath = InMemoryPath.from_list(self.files)
        matches: list[str] = [p.path for p in glob(fs, pattern)]

        return matches

    def extract(self, dest_folder: Path) -> None:
        """
        Extracts the archive content to a specified destination folder.

        Args:
            dest_folder (Path): The path to the destination folder.
        """

        for file in self.files:
            self.extract_file(file, dest_folder)

    def extract_file(self, filename: str | Path, dest_folder: Path) -> None:
        """
        Extracts a file from the archive to a specified destination folder.

        Args:
            filename (str | Path): The name of the file to extract.
            dest_folder (Path): The path to the destination folder.

        Raises:
            FileNotFoundError: when the file is not in the archive
            Exception: when the extraction fails
        """

        filename = str(filename).replace("\\", "/")

        if filename not in self.__files:
            raise FileNotFoundError(f"{filename!r} is not in archive!")

        file_record: FileRecord = self.__files[filename]

        # Go to file raw data
        with self.__path.open("rb") as stream:
            stream.seek(file_record.offset)

            file_size: int = file_record.size

            if Header.ArchiveFlags.EmbedFileNames in self.header.archive_flags:
                filename = String.parse(stream, String.StrType.BString)
                # Subtract file name length + Uint8 prefix
                file_size -= len(filename) + 1

            data: bytes
            if file_record.compressed:
                # Parse original file size
                Integer.parse(stream, Integer.IntType.ULong)
                data = stream.read(file_size - 4)
                data = lz4.frame.decompress(data)
            else:
                data = stream.read(file_size)

        destination: Path = dest_folder / filename
        os.makedirs(destination.parent, exist_ok=True)
        with open(destination, "wb") as file:
            file.write(data)

        if not destination.is_file():
            raise Exception(
                f"Failed to extract file '{filename}' from archive '{self.__path}'!"
            )

    def get_file_stream(self, filename: str | Path) -> BytesIO:
        """
        Returns a stream for a file in the archive.

        Args:
            filename (str | Path): The name of the file.

        Raises:
            FileNotFoundError: when the file is not in the archive

        Returns:
            BytesIO: The file stream
        """

        filename = str(filename)

        if filename not in self.__files:
            raise FileNotFoundError("File is not in archive!")

        file_record: FileRecord = self.__files[filename]

        data: bytes
        with self.__path.open("rb") as stream:
            # Go to file raw data
            stream.seek(file_record.offset)

            file_size: int = file_record.size
            if Header.ArchiveFlags.EmbedFileNames in self.header.archive_flags:
                filename = String.parse(stream, String.StrType.BString)
                # Subtract file name length + Uint8 prefix
                file_size -= len(filename) + 1

            if file_record.compressed:
                Integer.parse(stream, Integer.IntType.ULong)  # Parse original size
                data = stream.read(file_size - 4)
                data = lz4.frame.decompress(data)
            else:
                data = stream.read(file_size)

        return BytesIO(data)

    @staticmethod
    def _create_file_flags(folders: list[Path]) -> Header.FileFlags:
        file_flags: Header.FileFlags = Header.FileFlags(0)

        for folder in folders:
            root_folder_name: str = folder.parts[0].lower()
            sub_folder_name: Optional[str] = (
                folder.parts[1].lower() if len(folder.parts) > 1 else None
            )

            match root_folder_name:
                case "meshes":
                    file_flags |= Header.FileFlags.Meshes
                case "textures":
                    file_flags |= Header.FileFlags.Textures
                case "interface":
                    file_flags |= Header.FileFlags.Menus
                case "sounds":
                    file_flags |= Header.FileFlags.Sounds
                    if sub_folder_name == "voice":
                        file_flags |= Header.FileFlags.Voices

                case _:
                    file_flags |= Header.FileFlags.Miscellaneous

        return file_flags

    @staticmethod
    def create_archive(
        input_folder: Path,
        output_file: Path,
        archive_flags: Optional[Header.ArchiveFlags] = None,
        file_flags: Optional[Header.FileFlags] = None,
    ) -> None:
        """
        Creates a new BSA archive and populates it with files from a folder.

        Args:
            input_folder (Path): Path to the folder containing the files.
            output_file (Path): Path to the output archive file.
            archive_flags (Optional[Header.ArchiveFlags], optional):
                Archive flags. Defaults to None.
            file_flags (Optional[Header.FileFlags], optional):
                File flags. Defaults to None.

        Raises:
            FileNotFoundError: when the input folder does not exist
            ValueError:
                when the input folder is empty or doesn't contain any subfolders
                with valid files
        """

        input_folder = input_folder.resolve()
        output_file = output_file.resolve()

        if not input_folder.is_dir():
            raise FileNotFoundError(
                f"{str(input_folder)!r} must be an existing directory!"
            )

        # Get elements and prepare folder and file structure
        files: list[Path] = []
        for element in os.listdir(input_folder):
            if os.path.isdir(input_folder / element):
                files += create_folder_list(input_folder / element)
        file_name_block = FileNameBlock([file.name for file in files])
        folders: dict[Path, list[Path]] = {}
        for file in files:
            folder: Path = file.parent

            if folder in folders:
                folders[folder].append(file)
            else:
                folders[folder] = [file]

        if not folders or not file_name_block.file_names:
            raise ValueError("No elements to pack!")

        # Create header
        header = Header()
        header.file_count = len(files)
        header.folder_count = len(folders)
        header.total_file_name_length = len(file_name_block.dump())
        header.total_folder_name_length = len(
            String.dump([str(folder) for folder in folders], String.StrType.List)
        )
        header.file_flags = BSAArchive._create_file_flags(list(folders.keys()))

        if archive_flags is not None:
            header.archive_flags |= archive_flags
        if file_flags is not None:
            header.file_flags |= file_flags

        if (
            Header.ArchiveFlags.EmbedFileNames in header.archive_flags
            and Header.ArchiveFlags.CompressedArchive in header.archive_flags
        ):
            print(
                "WARNING! Use Embedded File Names and Compresion at the same time at your own risk!"
            )

        # Create record and block structure
        folder_records: list[FolderRecord] = []
        file_record_blocks: list[FileRecordBlock] = []
        file_records: dict[FileRecord, str] = {}
        current_offset: int = 36  # Start with header size
        current_offset += len(folders) * 24  # Add estimated size of all folder records

        for folder, _files in folders.items():
            folder_name = str(folder).replace("/", "\\")

            folder_record = FolderRecord(
                name_hash=Hash.calc_hash(folder_name),
                count=len(_files),
                padding=0,
                offset=current_offset,
                padding2=0,
            )
            folder_records.append(folder_record)

            file_record_block = FileRecordBlock(folder_name)

            for file in _files:
                file_record = FileRecord(
                    name_hash=Hash.calc_hash(file.name.lower()),
                    size=os.path.getsize(input_folder / file),
                )
                file_records[file_record] = str(file).replace("/", "\\")
                file_record_block.file_records.append(file_record)

            # Add name length of file record block (+ Uint8 and null-terminator)
            current_offset += len(file_record_block.name) + 2
            # Add estimated size of all file records from current file record block
            current_offset += len(file_record_block.file_records) * 16

            file_record_blocks.append(file_record_block)

        current_offset += len(file_name_block.dump())  # Add size of file name block

        # Write file
        with output_file.open("wb") as output_stream:
            # Write Placeholder for Record Structure
            output_stream.write(b"\x00" * current_offset)

            for file_record, file_name in file_records.items():
                if Header.ArchiveFlags.EmbedFileNames in header.archive_flags:
                    output_stream.write(String.dump(file_name, String.StrType.BString))
                    file_record.size += len(file_name) + 1

                if Header.ArchiveFlags.CompressedArchive in header.archive_flags:
                    with (input_folder / file_name).open("rb") as input_file:
                        data = input_file.read()

                    compressed_data: bytes = lz4.frame.compress(data)

                    output_stream.write(
                        Integer.dump(file_record.size, Integer.IntType.ULong)
                    )
                    output_stream.write(compressed_data)
                    # Compressed size + ULong prefix
                    file_record.size = len(compressed_data) + 4

                    # Readd file name length after reducing file size to compressed size
                    if Header.ArchiveFlags.EmbedFileNames in header.archive_flags:
                        file_record.size += len(file_name) + 1
                else:
                    with (input_folder / file_name).open("rb") as input_file:
                        while data := input_file.read(1024 * 1024):
                            output_stream.write(data)

            # Calculate file offsets
            for file_record, file_name in file_records.items():
                file_record.offset = current_offset
                current_offset += file_record.size  # Add file size

            output_stream.seek(0)
            output_stream.write(header.dump())
            output_stream.write(
                b"".join(folder_record.dump() for folder_record in folder_records)
            )
            output_stream.write(
                b"".join(
                    file_record_block.dump() for file_record_block in file_record_blocks
                )
            )
            output_stream.write(file_name_block.dump())
