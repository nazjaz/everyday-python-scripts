# Purpose-Based File Organizer API Documentation

## PurposeBasedOrganizer Class

Main class for organizing files by inferred purpose tags.

### Methods

#### `__init__(config_path: str = "config.yaml") -> None`

Initialize PurposeBasedOrganizer with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Default: "config.yaml"

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

**Example:**
```python
organizer = PurposeBasedOrganizer(config_path="config.yaml")
```

#### `scan_directory(directory: str) -> None`

Scan directory and infer file purposes.

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

Organize files into purpose-based folder hierarchies.

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

#### `file_purposes: Dict[str, Dict[str, Any]]`

Dictionary mapping file paths to file purpose information. Populated after `scan_directory()` is called.

**Structure:**
```python
{
    "/path/to/file.pdf": {
        "path": "/path/to/file.pdf",
        "name": "file.pdf",
        "extension": ".pdf",
        "primary_purpose": "Financial",
        "all_purposes": ["Financial", "Work"],
        "folder": "organized/Financial",
        "filename_scores": {"Financial": 3, "Work": 1},
        "location_scores": {"Temporary": 2},
        "content_scores": {"Financial": 2},
        "is_duplicate": False,
        "file_hash": "abc123...",
        "size_bytes": 12345
    }
}
```

#### `stats: Dict[str, int]`

Statistics dictionary containing:
- `files_scanned`: Number of files scanned
- `files_organized`: Number of files organized
- `duplicates_found`: Number of duplicate files found
- `errors`: Number of errors encountered

**Example:**
```python
print(f"Scanned {organizer.stats['files_scanned']} files")
print(f"Found {organizer.stats['duplicates_found']} duplicates")
```

### Internal Methods

#### `_infer_purpose_from_filename(filename: str) -> Dict[str, int]`

Infer purpose tags from filename.

**Parameters:**
- `filename` (str): Name of the file

**Returns:**
- `Dict[str, int]`: Dictionary mapping purpose names to confidence scores

#### `_infer_purpose_from_location(file_path: Path) -> Dict[str, int]`

Infer purpose tags from file location.

**Parameters:**
- `file_path` (Path): Path to file

**Returns:**
- `Dict[str, int]`: Dictionary mapping purpose names to confidence scores

#### `_infer_purpose_from_content(file_path: Path) -> Dict[str, int]`

Infer purpose tags from file content (for text files).

**Parameters:**
- `file_path` (Path): Path to file

**Returns:**
- `Dict[str, int]`: Dictionary mapping purpose names to confidence scores

#### `_determine_primary_purpose(filename_scores: Dict[str, int], location_scores: Dict[str, int], content_scores: Dict[str, int]) -> Tuple[Optional[str], List[str]]`

Determine primary purpose from all scores.

**Parameters:**
- `filename_scores`: Purpose scores from filename analysis
- `location_scores`: Purpose scores from location analysis
- `content_scores`: Purpose scores from content analysis

**Returns:**
- `Tuple[Optional[str], List[str]]`: Tuple of (primary_purpose, all_purposes)

#### `_build_folder_hierarchy(primary_purpose: Optional[str], all_purposes: List[str]) -> Path`

Build folder hierarchy path based on purposes.

**Parameters:**
- `primary_purpose`: Primary purpose tag
- `all_purposes`: All detected purpose tags

**Returns:**
- `Path`: Path object representing folder hierarchy

#### `_calculate_file_hash(file_path: Path) -> str`

Calculate MD5 hash of file for duplicate detection.

**Parameters:**
- `file_path` (Path): Path to file

**Returns:**
- `str`: MD5 hash as hexadecimal string

## Usage Example

```python
from src.main import PurposeBasedOrganizer

# Initialize organizer
organizer = PurposeBasedOrganizer(config_path="config.yaml")

# Scan directory
organizer.scan_directory("/path/to/files")

# Preview organization (dry run)
organizer.organize_files("/path/to/files", dry_run=True)

# Check statistics
print(f"Scanned: {organizer.stats['files_scanned']}")
print(f"Duplicates: {organizer.stats['duplicates_found']}")

# View file purposes
for file_path, file_info in organizer.file_purposes.items():
    print(f"{file_info['name']}: {file_info['primary_purpose']} -> {file_info['folder']}")

# Organize files
organizer.organize_files("/path/to/files", dry_run=False)

# Generate report
report = organizer.generate_report(output_path="report.txt")
```
