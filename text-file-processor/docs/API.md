# API Documentation

## TextFileProcessor Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize TextFileProcessor with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `process_file(file_path: Path) -> bool`

Process a single text file.

**Parameters:**
- `file_path`: Path to file to process

**Returns:**
- True if processing succeeded, False otherwise

**Processing steps:**
1. Detect file encoding
2. Read and decode file content
3. Remove extra whitespace
4. Normalize line endings
5. Encode to UTF-8
6. Create backup (if enabled)
7. Write processed content

#### `process_directory(directory: Optional[str] = None) -> Dict[str, int]`

Process all text files in a directory.

**Parameters:**
- `directory`: Directory to process (default: from config)

**Returns:**
- Dictionary with processing statistics:
  - `files_processed`: Number of files successfully processed
  - `files_skipped`: Number of files skipped
  - `files_failed`: Number of files that failed processing
  - `bytes_processed`: Total bytes processed
  - `bytes_saved`: Total bytes saved (original - processed)

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `NotADirectoryError`: If path is not a directory

#### `print_summary() -> None`

Print processing summary to console.

#### `_detect_encoding(file_path: Path) -> Tuple[str, bytes]`

Detect file encoding and read content.

**Parameters:**
- `file_path`: Path to file

**Returns:**
- Tuple of (encoding, file_content_bytes)

**Raises:**
- `UnicodeDecodeError`: If encoding cannot be determined

#### `_normalize_line_endings(text: str) -> str`

Normalize line endings to specified format.

**Parameters:**
- `text`: Text content

**Returns:**
- Text with normalized line endings

**Line ending formats:**
- `"unix"`: `\n` (Linux, macOS)
- `"windows"`: `\r\n` (Windows)
- `"mac"`: `\r` (Old Mac OS)

#### `_remove_extra_whitespace(text: str) -> str`

Remove extra whitespace from text.

**Parameters:**
- `text`: Text content

**Returns:**
- Text with extra whitespace removed

**Whitespace options:**
- Remove trailing whitespace from lines
- Remove leading whitespace from lines
- Normalize multiple spaces to single space
- Remove empty lines
- Remove trailing newlines at end of file

## Configuration Structure

```yaml
input:
  directory: "."  # Directory to process
  recursive: true  # Process subdirectories

output:
  in_place: true  # Overwrite original files
  directory: "processed"  # Output directory (if not in-place)

processing:
  encoding_detection_order: ["utf-8", "latin-1", "cp1252"]
  line_ending: "unix"  # "unix", "windows", or "mac"
  remove_trailing_whitespace: true
  remove_leading_whitespace: false
  normalize_spaces: true
  remove_empty_lines: false
  remove_trailing_newlines: false

include:
  extensions: []  # Empty = common text files

skip:
  patterns: []  # Patterns to skip
  directories: []  # Directory names to skip

backup:
  enabled: true  # Create backups
  directory: "backups"  # Backup location
```

## Statistics

The processor tracks the following statistics:

- **files_processed**: Number of files successfully processed
- **files_skipped**: Number of files skipped (not matching criteria)
- **files_failed**: Number of files that failed processing
- **bytes_processed**: Total bytes in original files
- **bytes_saved**: Total bytes saved (original - processed size)
