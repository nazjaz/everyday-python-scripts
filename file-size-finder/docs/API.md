# API Documentation

## FileSizeFinder Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize FileSizeFinder with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `find_files(directory: Optional[str] = None) -> List[Dict]`

Find files matching size criteria.

**Parameters:**
- `directory`: Directory to search (default: from config)

**Returns:**
- List of file dictionaries with keys:
  - `path`: Full file path
  - `size`: File size in bytes
  - `size_formatted`: Human-readable size string
  - `name`: File name
  - `directory`: Directory containing file
  - `extension`: File extension (lowercase)

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `NotADirectoryError`: If path is not a directory

#### `generate_report(files: List[Dict], output_file: Optional[str] = None) -> str`

Generate text report of found files.

**Parameters:**
- `files`: List of file dictionaries
- `output_file`: Optional path to save report file

**Returns:**
- Report text string

#### `print_summary(files: List[Dict]) -> None`

Print summary of found files to console.

**Parameters:**
- `files`: List of file dictionaries

#### `_parse_size(size_str: str) -> int`

Parse size string to bytes.

**Parameters:**
- `size_str`: Size string (e.g., "10MB", "1.5GB", "500KB")

**Returns:**
- Size in bytes

**Raises:**
- `ValueError`: If size string format is invalid

#### `_format_size(size_bytes: int) -> str`

Format bytes to human-readable string.

**Parameters:**
- `size_bytes`: Size in bytes

**Returns:**
- Formatted size string (e.g., "1.5 MB")

#### `_matches_size_criteria(file_size: int) -> bool`

Check if file size matches criteria.

**Parameters:**
- `file_size`: File size in bytes

**Returns:**
- True if file matches size criteria, False otherwise

## Size Format

Size values can be specified as:
- Bytes: `1024` or `1024B`
- Kilobytes: `1KB` or `1.5KB`
- Megabytes: `10MB` or `1.5MB`
- Gigabytes: `1GB` or `2.5GB`
- Terabytes: `1TB`

## Configuration Structure

```yaml
search:
  directory: "."  # Directory to search

size:
  min_bytes: 0  # Minimum size in bytes
  max_bytes: null  # Maximum size in bytes (null = no limit)

skip:
  patterns: []  # Patterns to skip
  directories: []  # Directory names to skip
  excluded_paths: []  # Specific paths to exclude

include:
  extensions: []  # File extensions to include (empty = all)
  include_no_extension: true  # Include files without extensions

report:
  auto_save: true  # Automatically save report
  output_file: "logs/file_size_report.txt"
  sort_by_size: true  # Sort by size (largest first)
```
