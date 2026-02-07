# API Documentation

## FilenameSanitizer Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize FilenameSanitizer with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `find_problematic_files(directory: Optional[str] = None) -> List[Dict[str, any]]`

Find files with problematic characters.

**Parameters:**
- `directory`: Directory to scan (default: from config)

**Returns:**
- List of file information dictionaries with keys:
  - `path`: Full file path
  - `original_name`: Original filename
  - `sanitized_name`: Sanitized filename
  - `directory`: Directory containing file
  - `issues`: List of detected issues
  - `needs_rename`: True if filename needs renaming

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `NotADirectoryError`: If path is not a directory

#### `rename_file(file_path: Path, new_name: str, dry_run: bool = False) -> bool`

Rename a file.

**Parameters:**
- `file_path`: Path to file to rename
- `new_name`: New filename
- `dry_run`: If True, simulate renaming without actually renaming

**Returns:**
- True if renaming succeeded or was simulated, False otherwise

#### `rename_files(files: List[Dict[str, any]], dry_run: bool = False) -> Dict[str, int]`

Rename multiple files.

**Parameters:**
- `files`: List of file information dictionaries
- `dry_run`: If True, simulate renaming without actually renaming

**Returns:**
- Dictionary with renaming statistics:
  - `files_renamed`: Number of files renamed
  - `files_skipped`: Number of files skipped
  - `errors`: Number of errors encountered

#### `generate_report(files: List[Dict[str, any]], output_file: Optional[str] = None) -> str`

Generate text report of problematic files.

**Parameters:**
- `files`: List of file information dictionaries
- `output_file`: Optional path to save report file

**Returns:**
- Report text string

#### `print_summary() -> None`

Print summary to console.

#### `_has_problematic_characters(filename: str) -> Tuple[bool, List[str]]`

Check if filename has problematic characters.

**Parameters:**
- `filename`: File name to check

**Returns:**
- Tuple of (has_problems, list_of_issues)

**Issues detected:**
- `contains_spaces`: Filename contains spaces
- `contains_<char>`: Filename contains specific problematic character
- `consecutive_special_chars`: Multiple consecutive special characters
- `leading_special_char`: Leading special character
- `trailing_special_char`: Trailing special character
- `reserved_name`: Windows reserved name
- `control_characters`: Control characters present

#### `_sanitize_filename(filename: str) -> str`

Generate filesystem-safe filename.

**Parameters:**
- `filename`: Original filename

**Returns:**
- Sanitized filename

**Sanitization steps:**
1. Replace spaces with configured character
2. Replace problematic characters with configured character
3. Remove consecutive special characters
4. Remove leading/trailing special characters
5. Remove control characters
6. Handle reserved names (prefix with underscore)
7. Limit length if configured

## Configuration Structure

```yaml
scan:
  directory: "."  # Directory to scan
  recursive: true  # Scan subdirectories

sanitization:
  remove_spaces: true  # Remove/replace spaces
  remove_consecutive: true  # Remove consecutive special chars
  remove_leading_trailing: true  # Remove leading/trailing chars
  max_length: null  # Maximum filename length
  problematic_chars: []  # List of problematic characters
  reserved_names: []  # Windows reserved names

replacement:
  space_replacement: "_"  # Character to replace spaces
  char_replacement: "_"  # Character to replace problematic chars
  consecutive_replacement: "_"  # Character for consecutive chars

renaming:
  dry_run: true  # Default to dry-run
  conflicts:
    action: "rename"  # "rename", "skip", or "overwrite"

include:
  extensions: []  # Empty = all extensions
  include_no_extension: true

skip:
  patterns: []  # Patterns to skip
  directories: []  # Directory names to skip
  excluded_paths: []  # Specific paths to exclude
```

## Statistics

The sanitizer tracks the following statistics:

- **files_scanned**: Number of files scanned
- **files_found**: Number of files with problematic names
- **files_renamed**: Number of files renamed
- **files_skipped**: Number of files skipped
- **errors**: Number of errors encountered

## Error Handling

The sanitizer handles the following errors:

- **FileNotFoundError**: Directory or file not found
- **PermissionError**: Insufficient permissions to rename file
- **NotADirectoryError**: Path is not a directory
- **OSError**: General file system errors

All errors are logged and counted in statistics.
