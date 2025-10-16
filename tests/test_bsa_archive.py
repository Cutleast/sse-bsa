"""
Copyright (c) Cutleast
"""

import tempfile
from pathlib import Path

import pytest

from src.sse_bsa import BSAArchive, Header


class TestBSAArchive:
    """
    Tests `bsa_archive.BSAArchive`.

    TODO: Add more tests
    """

    def test_create_archive(self) -> None:
        """
        Tests `bsa_archive.BSAArchive.create_archive` with a txt and a png file.
        """

        # given
        input_folder_path: Path = Path("tests/data")
        txt_file_path: Path = (
            input_folder_path / "interface" / "translations" / "test.txt"
        )
        png_file_path: Path = input_folder_path / "textures" / "test" / "test.png"
        bsa_file_path: Path = Path("tests/data/test_out.bsa")
        archive_flags: Header.ArchiveFlags = Header.ArchiveFlags(
            Header.ArchiveFlags.EmbedFileNames
        )

        # when
        assert txt_file_path.is_file()
        assert png_file_path.is_file()
        BSAArchive.create_archive(input_folder_path, bsa_file_path, archive_flags)
        bsa_archive: BSAArchive = BSAArchive(bsa_file_path)

        # then
        assert Path("interface/translations/test.txt") in bsa_archive.files
        assert Path("textures/test/test.png") in bsa_archive.files
        assert (
            bsa_archive.get_file_stream("interface/translations/test.txt").read()
            == txt_file_path.read_bytes()
        )
        assert (
            bsa_archive.get_file_stream("textures/test/test.png").read()
            == png_file_path.read_bytes()
        )
        assert Header.ArchiveFlags.EmbedFileNames in bsa_archive.header.archive_flags
        assert Header.FileFlags.Menus in bsa_archive.header.file_flags
        assert Header.FileFlags.Textures in bsa_archive.header.file_flags

        bsa_file_path.unlink(missing_ok=True)

    TEST_FILES: list[Path | str] = [
        Path("interface") / "translations" / "test.txt",
        Path("INTERFACE") / "translations" / "test.TXT",
        Path("textures") / "test" / "test.png",
        "textures/test/test.png",
        "interface/translations/test.txt",
        "INTERFACE/TRANSLATIONS/TEST.TXT",
        "textures\\test/test.png",
    ]

    @pytest.mark.parametrize("file", TEST_FILES)
    def test_get_file_stream(self, file: Path | str) -> None:
        bsa_archive: BSAArchive = BSAArchive(Path("tests/data/test.bsa"))
        bsa_archive.get_file_stream(file)

    @pytest.mark.parametrize("file", TEST_FILES)
    def test_extract_file(self, file: Path | str) -> None:
        bsa_archive: BSAArchive = BSAArchive(Path("tests/data/test.bsa"))

        with tempfile.TemporaryDirectory() as tmpdir:
            bsa_archive.extract_file(file, Path(tmpdir))
