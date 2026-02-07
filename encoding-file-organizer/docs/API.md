# API Documentation

## EncodingFileOrganizer Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize EncodingFileOrganizer with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `scan_files(directory: Optional[str] = None) -> Dict[str, List[Dict[str, any]]]`

Scan directory and group files by encoding.

**Parameters:**
- `directory`: Directory to scan (default: from config)

**Returns:**
- Dictionary mapping encoding names to lists of file information
- Each file info dictionary contains:
  - `path`: Full file path
  - `name`: File name
  - `encoding`: Detected encoding
  - `confidence`: Detection confidence (0.0-1.0)
  - `size`: File size in bytes
  - `extension`: File extension
  - `relative_path`: Path relative to base directory

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `NotADirectoryError`: If path is not a directory

#### `organize_files(files_by_encoding: Dict[str, List[Dict[str, any]]], dry_run: bool = False) -> Dict[str, int]`

Organize files by moving them to encoding-based folders.

**Parameters:**
- `files_by_encoding`: Dictionary mapping encoding names to file lists
- `dry_run`: If True, simulate organization without actually moving files

**Returns:**
- Dictionary with organization statistics:
  - `files_organized`: Number of files organized
  - `files_skipped`: Number of files skipped
  - `errors`: Number of errors encountered

**Behavior:**
- Creates encoding-based folders (e.g., Encoding_UTF-8, Encoding_LATIN-1)
- Moves files to appropriate encoding folders
- Handles name conflicts based on configuration
- Optionally preserves directory structure

#### `generate_report(files_by_encoding: Dict[str, List[Dict[str, any]]], output_file: Optional[str] = None) -> str`

Generate text report of file organization.

**Parameters:**
- `files_by_encoding`: Dictionary mapping encoding names to file lists
- `output_file`: Optional path to save report file

**Returns:**
- Report text string

#### `print_summary(files_by_encoding: Dict[str, List[Dict[str, any]]]) -> None`

Print summary to console.

**Parameters:**
- `files_by_encoding`: Dictionary mapping encoding names to file lists

#### `_detect_encoding(file_path: Path) -> Tuple[Optional[str], float]`

Detect file encoding.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- Tuple of (encoding, confidence) or (None, 0.0) if detection fails

**Detection methods:**
- Uses chardet library if enabled and available
- Falls back to trying common encodings in order

#### `_is_text_file(file_path: Path) -> bool`

Check if file is likely a text file.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- True if file appears to be text, False otherwise

**Detection methods:**
- Extension check (configurable list)
- Content analysis (null bytes, printable character ratio)

#### `_get_encoding_folder_name(encoding: str) -> str`

Get folder name for an encoding.

**Parameters:**
- `encoding`: Encoding name

**Returns:**
- Folder name for the encoding (e.g., "Encoding_UTF-8")

## Configuration Structure

```yaml
source:
  directory: "."  # Directory to scan
  recursive: true  # Scan subdirectories

text_file:
  extensions: []  # Text file extensions
  check_content: true  # Check file content

encoding_detection:
  use_chardet: false  # Use chardet library
  sample_size: 10000  # Bytes to sample
  encoding_order: []  # Encoding detection order

output:
  directory: "organized"  # Output directory
  preserve_structure: false  # Preserve relative structure

organization:
  dry_run: true  # Default to dry-run
  encoding_naming:
    prefix: "Encoding"  # Folder name prefix
    separator: "_"  # Separator
    normalize_case: true  # Uppercase encoding
  conflicts:
    action: "rename"  # "rename", "skip", or "overwrite"
```

## Statistics

The organizer tracks the following statistics:

- **files_scanned**: Number of files scanned
- **files_processed**: Number of files successfully processed
- **files_organized**: Number of files organized
- **files_skipped**: Number of files skipped
- **errors**: Number of errors encountered
- **encodings_found**: Set of encoding names found

## Error Handling

The organizer handles the following errors:

- **FileNotFoundError**: Directory or file not found
- **PermissionError**: Insufficient permissions
- **NotADirectoryError**: Path is not a directory
- **OSError**: General file system errors
- **UnicodeDecodeError**: Encoding detection errors
- **shutil.Error**: File move/copy errors

All errors are logged and counted in statistics.
