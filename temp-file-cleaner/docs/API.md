# API Documentation

## TemporaryFileCleaner Class

The main class for cleaning up temporary files with safety checks.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the TemporaryFileCleaner with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.

**Side Effects:**
- Loads configuration
- Sets up logging
- Initializes data structures

#### `scan_directory(directory: str) -> None`

Scan directory for temporary files.

**Parameters:**
- `directory` (str): Path to directory to scan.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Scans directory recursively
- Identifies temporary files
- Populates `temp_files` list
- Updates statistics
- Logs all operations

#### `cleanup_files(dry_run: bool = False) -> None`

Delete temporary files found during scan.

**Parameters:**
- `dry_run` (bool): If True, simulate cleanup without deleting files.

**Side Effects:**
- Deletes files (unless dry_run)
- Updates statistics
- Logs all deletions
- Handles errors gracefully

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate cleanup report.

**Parameters:**
- `output_path` (Optional[str]): Path to save report file. If None, uses default from config.

**Returns:**
- `str`: Report content as string.

**Raises:**
- `IOError`: If report file cannot be written.
- `PermissionError`: If output directory is not writable.

#### `_is_temporary_extension(file_path: Path) -> bool`

Check if file has a temporary extension.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `bool`: True if file has temporary extension, False otherwise.

#### `_is_temporary_filename(file_path: Path) -> bool`

Check if filename indicates temporary file.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `bool`: True if filename indicates temporary file, False otherwise.

#### `_is_incomplete_download(file_path: Path) -> bool`

Check if file appears to be an incomplete download.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `bool`: True if file appears incomplete, False otherwise.

**Criteria:**
- Has temporary extension or filename AND
- (Hasn't been modified in X days OR is very small)

#### `_is_safe_to_delete(file_path: Path, file_info: Dict[str, Any]) -> bool`

Check if file is safe to delete based on safety rules.

**Parameters:**
- `file_path` (Path): Path to file.
- `file_info` (Dict[str, Any]): Dictionary with file information.

**Returns:**
- `bool`: True if safe to delete, False otherwise.

**Safety Checks:**
- Minimum age requirement
- Maximum size limit
- Protected pattern matching
- Protected directory exclusion

#### `_collect_file_info(file_path: Path) -> Optional[Dict[str, Any]]`

Collect information about a file.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Dictionary with file information or None if error.

**File Info Dictionary:**
- `path`: Full file path
- `name`: File name
- `size_bytes`: File size in bytes
- `age_days`: Days since last modification
- `last_modified`: ISO format timestamp
- `is_temp_extension`: Boolean
- `is_temp_filename`: Boolean
- `is_incomplete`: Boolean

#### `_format_size(size_bytes: int) -> str`

Format file size in human-readable format.

**Parameters:**
- `size_bytes` (int): Size in bytes.

**Returns:**
- `str`: Formatted size string (e.g., "1.5 MB").

### Attributes

#### `temp_files: List[Dict[str, Any]]`

List of dictionaries containing information about temporary files found during scan.

#### `stats: Dict[str, Any]`

Dictionary containing operation statistics:
- `files_scanned`: Total number of files scanned
- `temp_files_found`: Number of temporary files found
- `files_deleted`: Number of files successfully deleted
- `space_freed_bytes`: Total bytes freed
- `errors`: Number of errors encountered

#### `config: dict`

Configuration dictionary loaded from YAML file.

### Example Usage

```python
from src.main import TemporaryFileCleaner

# Initialize with default config
cleaner = TemporaryFileCleaner()

# Or with custom config
cleaner = TemporaryFileCleaner(config_path="custom_config.yaml")

# Scan directory
cleaner.scan_directory("/path/to/directory")

# Test cleanup (dry run)
cleaner.cleanup_files(dry_run=True)

# Actually clean files
cleaner.cleanup_files(dry_run=False)

# Generate report
cleaner.generate_report()

# Access results
print(f"Found {cleaner.stats['temp_files_found']} temporary files")
print(f"Freed {cleaner._format_size(cleaner.stats['space_freed_bytes'])}")
```

### Safety Features

The tool implements multiple safety mechanisms:

1. **Age Verification**: Files must meet minimum age before deletion
2. **Size Limits**: Optional maximum size to prevent deletion of large files
3. **Protected Patterns**: Files matching patterns are never deleted
4. **Protected Directories**: System directories are protected
5. **File Lock Detection**: Locked files are skipped

### Temporary File Detection

Files are identified as temporary if they match any of:
- Temporary extensions (.tmp, .download, .part, etc.)
- Temporary filename patterns (temp_, .tmp, etc.)
- Incomplete download criteria (old + small, or old + temp extension)
