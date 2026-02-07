# API Documentation

## FileMetadataExporter Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize FileMetadataExporter with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `extract_metadata(file_path: Path) -> Optional[Dict[str, any]]`

Extract metadata from a file.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- Dictionary with file metadata or None if error
- Metadata includes:
  - `path`: Full file path
  - `name`: File name
  - `directory`: Directory containing file
  - `extension`: File extension
  - `size_bytes`, `size_kb`, `size_mb`: File sizes
  - `created`, `modified`, `accessed`: Timestamps (ISO format)
  - Permission information
  - Checksums (if enabled)

#### `scan_directory(directory: Optional[str] = None) -> List[Dict[str, any]]`

Scan directory and extract metadata from all files.

**Parameters:**
- `directory`: Directory to scan (default: from config)

**Returns:**
- List of file metadata dictionaries

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `NotADirectoryError`: If path is not a directory

#### `export_to_csv(metadata_list: List[Dict[str, any]], output_file: Optional[str] = None) -> str`

Export metadata to CSV file.

**Parameters:**
- `metadata_list`: List of file metadata dictionaries
- `output_file`: Optional path to output CSV file

**Returns:**
- Path to output CSV file

**Raises:**
- `ValueError`: If metadata list is empty
- `IOError`: If CSV file cannot be written

#### `print_summary() -> None`

Print summary to console.

#### `_calculate_checksum(file_path: Path, algorithm: str = "md5") -> Optional[str]`

Calculate file checksum.

**Parameters:**
- `file_path`: Path to file
- `algorithm`: Hash algorithm (md5, sha1, sha256)

**Returns:**
- Checksum string or None if error

#### `_get_file_permissions(file_path: Path) -> Dict[str, any]`

Get file permissions information.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- Dictionary with permission information

## Configuration Structure

```yaml
source:
  directory: "."  # Directory to scan
  recursive: true  # Scan subdirectories

metadata:
  include_owner: false  # Include file owner
  include_group: false  # Include file group
  include_inode: false  # Include inode number
  include_device: false  # Include device number

checksum:
  enabled: true  # Calculate checksums
  algorithms: ["md5", "sha1"]  # Algorithms to use
  chunk_size: 8192  # Chunk size for reading

include:
  extensions: []  # Empty = all extensions
  include_no_extension: true

skip:
  patterns: []  # Patterns to skip
  directories: []  # Directory names to skip
  excluded_paths: []  # Specific paths to exclude

export:
  output_file: "data/file_metadata.csv"
  encoding: "utf-8"
```

## CSV Column Reference

### Standard Columns

- `path`: Full file path
- `name`: File name
- `directory`: Directory path
- `extension`: File extension
- `size_bytes`: Size in bytes
- `size_kb`: Size in kilobytes
- `size_mb`: Size in megabytes
- `created`: Creation timestamp (ISO)
- `modified`: Modification timestamp (ISO)
- `accessed`: Access timestamp (ISO)

### Permission Columns

- `mode_octal`: Permissions in octal
- `mode_readable`: Permissions in readable format
- `is_readable`: File is readable
- `is_writable`: File is writable
- `is_executable`: File is executable
- `owner_read`, `owner_write`, `owner_execute`: Owner permissions
- `group_read`, `group_write`, `group_execute`: Group permissions
- `other_read`, `other_write`, `other_execute`: Other permissions

### Checksum Columns

- `checksum_md5`: MD5 checksum (if enabled)
- `checksum_sha1`: SHA1 checksum (if enabled)
- `checksum_sha256`: SHA256 checksum (if enabled)

### Optional Columns

- `owner`: File owner (if enabled)
- `group`: File group (if enabled)
- `inode`: Inode number (if enabled)
- `device`: Device number (if enabled)

## Statistics

The exporter tracks the following statistics:

- **files_scanned**: Number of files scanned
- **files_processed**: Number of files successfully processed
- **files_skipped**: Number of files skipped
- **errors**: Number of errors encountered

## Error Handling

The exporter handles the following errors:

- **FileNotFoundError**: Directory or file not found
- **PermissionError**: Insufficient permissions
- **NotADirectoryError**: Path is not a directory
- **IOError**: File read/write errors
- **ValueError**: Invalid input or empty metadata

All errors are logged and counted in statistics.
