# Content Type Organizer API Documentation

## ContentTypeOrganizer Class

Main class for organizing files by content type.

### Methods

#### `__init__(config_path: str = "config.yaml") -> None`

Initialize ContentTypeOrganizer with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Default: "config.yaml"

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

**Example:**
```python
organizer = ContentTypeOrganizer(config_path="config.yaml")
```

#### `scan_directory(directory: str) -> None`

Scan directory and detect file content types.

**Parameters:**
- `directory` (str): Path to directory to scan

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `PermissionError`: If directory is not accessible

**Example:**
```python
organizer.scan_directory("/path/to/directory")
```

#### `organize_files(source_dir: str, dry_run: bool = False) -> None`

Organize files into content-type-based folders.

**Parameters:**
- `source_dir` (str): Source directory containing files
- `dry_run` (bool): If True, simulate organization without moving files. Default: False

**Example:**
```python
# Dry run
organizer.organize_files("/path/to/files", dry_run=True)

# Actual organization
organizer.organize_files("/path/to/files", dry_run=False)
```

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate organization report.

**Parameters:**
- `output_path` (Optional[str]): Optional path to save report file. If None, uses config default.

**Returns:**
- `str`: Report content as string

**Raises:**
- `IOError`: If report file cannot be written
- `PermissionError`: If report directory is not writable

**Example:**
```python
report = organizer.generate_report(output_path="report.txt")
print(report)
```

### Attributes

#### `file_types: Dict[str, Dict[str, Any]]`

Dictionary mapping file paths to file information dictionaries. Populated after `scan_directory()` is called.

**Structure:**
```python
{
    "/path/to/file.pdf": {
        "path": "/path/to/file.pdf",
        "name": "file.pdf",
        "extension": ".pdf",
        "mime_type": "application/pdf",
        "detection_method": "magic_number",
        "extension_mime": "application/pdf",
        "extension_mismatch": False,
        "folder": "Documents",
        "size_bytes": 12345
    }
}
```

#### `stats: Dict[str, int]`

Statistics dictionary containing:
- `files_scanned`: Number of files scanned
- `files_organized`: Number of files organized
- `extension_mismatches`: Number of files with extension mismatches
- `errors`: Number of errors encountered

**Example:**
```python
print(f"Scanned {organizer.stats['files_scanned']} files")
print(f"Found {organizer.stats['extension_mismatches']} mismatches")
```

### Internal Methods

#### `_detect_content_type(file_path: Path) -> Tuple[Optional[str], str]`

Detect file content type using multiple methods.

**Parameters:**
- `file_path` (Path): Path to file

**Returns:**
- `Tuple[Optional[str], str]`: Tuple of (mime_type, detection_method)

**Detection Methods:**
- `"python-magic"`: Detected using python-magic library
- `"magic_number"`: Detected using file magic numbers
- `"extension"`: Detected using file extension (fallback)
- `"unknown"`: Could not be detected

#### `_get_folder_for_mime(mime_type: Optional[str]) -> str`

Get folder name for MIME type.

**Parameters:**
- `mime_type` (Optional[str]): MIME type string

**Returns:**
- `str`: Folder name (e.g., "Images", "Documents", "Unknown")

## Usage Example

```python
from src.main import ContentTypeOrganizer

# Initialize organizer
organizer = ContentTypeOrganizer(config_path="config.yaml")

# Scan directory
organizer.scan_directory("/path/to/files")

# Preview organization (dry run)
organizer.organize_files("/path/to/files", dry_run=True)

# Check statistics
print(f"Scanned: {organizer.stats['files_scanned']}")
print(f"Mismatches: {organizer.stats['extension_mismatches']}")

# View file information
for file_path, file_info in organizer.file_types.items():
    print(f"{file_info['name']}: {file_info['mime_type']} -> {file_info['folder']}")

# Organize files
organizer.organize_files("/path/to/files", dry_run=False)

# Generate report
report = organizer.generate_report(output_path="report.txt")
```
