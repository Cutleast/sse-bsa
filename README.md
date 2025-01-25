# SSE-BSA

This is a Python library to read and write BSA (archive) files for Skyrim Special Edition.

See here for more information about the BSA file specification:
    https://en.uesp.net/wiki/Skyrim_Mod:Archive_File_Format

## Installation 

Run `pip install sse-bsa` to install the library and its dependencies in the current active environment.

## Usage

### Load an archive
```python
>>> archive = BSAArchive(Path("my_archive.bsa"))
```

### Get a list of all files in the archive
```python
>>> archive.files
["interface/translations/test.txt", "textures/test/test.png"]
```

### Search for files that match a specified pattern (glob)
```python
>>> archive.glob("interface/translations/*.txt")
["interface/translations/test.txt"]
```

### Extract a single file from the archive to a specified destination folder
(this maintains its folder structure)
```python
>>> archive.extract_file("interface/translations/test.txt", Path("output"))
```

For eg. the extracted file would be located at `output/interface/translations/test.txt`.

### Extract the entire content of the archive to a specified destination folder
(this also maintains the archive's folder structure)
```python
>>> archive.extract(Path("output"))
```

The entire archive folder structure would be extracted to `output`.

### Get an in-memory stream of a file without extracting it to disk
```python
>>> archive.get_file_stream("interface/translations/test.txt").read()
b'This is a test'
```

### Create a new archive with the content of a specified input folder
```python
>>> BSAArchive.create_archive(Path("input"), Path("new_archive.bsa"))
```

The entire folder structure of `input` gets maintained when packing in the `new_archive.bsa`.
