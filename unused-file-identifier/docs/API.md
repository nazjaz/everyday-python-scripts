# API Documentation

## UnusedFileIdentifier Class

The main class for identifying unused files in directory structures.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the UnusedFileIdentifier with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.

#### `scan_directory(directory: str) -> None`

Scan a directory for unused files based on the configured threshold.

**Parameters:**
- `directory` (str): Path to directory to scan.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Populates `self.unused_files` with list of unused file information.
- Updates `self.stats` with scanning statistics.

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate a human-readable text report of unused files.

**Parameters:**
- `output_path` (Optional[str]): Path to save report file. If None, uses default from config.

**Returns:**
- `str`: Report content as string.

**Raises:**
- `IOError`: If report file cannot be written.
- `PermissionError`: If output directory is not writable.

#### `export_json(output_path: Optional[str] = None) -> str`

Export unused files data to JSON format.

**Parameters:**
- `output_path` (Optional[str]): Path to save JSON file. If None, uses default from config.

**Returns:**
- `str`: Path to saved JSON file.

**Raises:**
- `IOError`: If JSON file cannot be written.
- `PermissionError`: If output directory is not writable.

### Attributes

#### `unused_files: List[Dict[str, Any]]`

List of dictionaries containing information about unused files. Each dictionary contains:
- `path`: File path as string
- `size_bytes`: File size in bytes
- `last_modified`: ISO format timestamp of last modification
- `last_accessed`: ISO format timestamp of last access
- `days_since_modification`: Number of days since last modification
- `days_since_access`: Number of days since last access

#### `stats: Dict[str, Any]`

Dictionary containing scanning statistics:
- `files_scanned`: Total number of files scanned
- `unused_files_found`: Number of unused files identified
- `directories_scanned`: Number of directories scanned
- `total_size_bytes`: Total size of unused files in bytes
- `errors`: Number of errors encountered during scanning

### Example Usage

```python
from src.main import UnusedFileIdentifier

# Initialize with default config
identifier = UnusedFileIdentifier()

# Scan a directory
identifier.scan_directory("/path/to/directory")

# Generate text report
identifier.generate_report()

# Export to JSON
identifier.export_json()

# Access results
print(f"Found {identifier.stats['unused_files_found']} unused files")
for file_info in identifier.unused_files:
    print(f"{file_info['path']}: {file_info['size_bytes']} bytes")
```
