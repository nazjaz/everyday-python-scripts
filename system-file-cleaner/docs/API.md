# API Documentation

## SystemFileCleaner Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize SystemFileCleaner with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `identify_file(file_path: Path) -> Optional[Dict[str, any]]`

Identify if file is system or hidden file.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- Dictionary with file information or None if not system/hidden
- Dictionary keys:
  - `path`: Full file path
  - `name`: File name
  - `size`: File size in bytes
  - `is_system`: True if system file
  - `is_hidden`: True if hidden file
  - `hidden_reason`: Reason for hidden classification
  - `system_reason`: Reason for system classification

#### `remove_file(file_path: Path, dry_run: bool = False) -> bool`

Remove a file.

**Parameters:**
- `file_path`: Path to file to remove
- `dry_run`: If True, simulate removal without actually deleting

**Returns:**
- True if removal succeeded or was simulated, False otherwise

**Behavior:**
- Protected files are never removed
- Logs removal operations
- Updates statistics

#### `scan_directory(directory: Optional[str] = None, remove_files: bool = False) -> List[Dict[str, any]]`

Scan directory for system and hidden files.

**Parameters:**
- `directory`: Directory to scan (default: from config)
- `remove_files`: If True, remove identified files

**Returns:**
- List of file information dictionaries

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `NotADirectoryError`: If path is not a directory

#### `generate_report(files: List[Dict[str, any]], output_file: Optional[str] = None) -> str`

Generate text report of found files.

**Parameters:**
- `files`: List of file information dictionaries
- `output_file`: Optional path to save report file

**Returns:**
- Report text string

#### `print_summary() -> None`

Print summary to console.

#### `_is_hidden_by_name(file_path: Path) -> bool`

Check if file is hidden by naming convention.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- True if file is hidden by name, False otherwise

#### `_is_hidden_by_attribute(file_path: Path) -> bool`

Check if file is hidden by file attributes.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- True if file is hidden by attribute, False otherwise

**Note:** On Windows, requires win32file module for attribute checking.

#### `_is_system_file(file_path: Path) -> bool`

Check if file is a system file.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- True if file is a system file, False otherwise

#### `_should_skip_path(file_path: Path) -> bool`

Check if path should be skipped.

**Parameters:**
- `file_path`: Path to check

**Returns:**
- True if path should be skipped, False otherwise

#### `_is_protected_file(file_path: Path) -> bool`

Check if file is protected and should not be removed.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- True if file is protected, False otherwise

## Configuration Structure

```yaml
scan:
  directory: "."  # Directory to scan
  recursive: true  # Scan subdirectories

patterns:
  system_name_patterns: []  # System file name patterns
  hidden_name_patterns: []  # Hidden file name patterns
  windows_system: []  # Windows-specific patterns
  windows_hidden: []  # Windows hidden patterns
  windows_system_dirs: []  # Windows system directories
  unix_system: []  # Unix/Linux/macOS patterns
  system_extensions: []  # System file extensions

skip:
  patterns: []  # Patterns to skip
  directories: []  # Directory names to skip
  excluded_paths: []  # Specific paths to exclude

protected:
  patterns: []  # Protected file patterns
  paths: []  # Protected file paths

removal:
  dry_run: true  # Default to dry-run
  require_confirmation: false  # Require confirmation

report:
  auto_save: true  # Automatically save report
  output_file: "logs/system_file_report.txt"
```

## Statistics

The cleaner tracks the following statistics:

- **files_scanned**: Number of files scanned
- **system_files_found**: Number of system files found
- **hidden_files_found**: Number of hidden files found
- **files_removed**: Number of files removed
- **files_skipped**: Number of files skipped (protected)
- **errors**: Number of errors encountered

## Error Handling

The cleaner handles the following errors:

- **FileNotFoundError**: Directory or file not found
- **PermissionError**: Insufficient permissions to remove file
- **NotADirectoryError**: Path is not a directory
- **OSError**: General file system errors

All errors are logged and counted in statistics.
