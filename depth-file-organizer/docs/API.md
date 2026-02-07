# API Documentation

## DepthFileOrganizer Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize DepthFileOrganizer with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `scan_files(directory: Optional[str] = None) -> Dict[int, List[Dict[str, any]]]`

Scan directory and group files by depth.

**Parameters:**
- `directory`: Directory to scan (default: from config)

**Returns:**
- Dictionary mapping depth levels to lists of file information
- Each file info dictionary contains:
  - `path`: Full file path
  - `name`: File name
  - `depth`: Depth level
  - `size`: File size in bytes
  - `extension`: File extension
  - `relative_path`: Path relative to base directory

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `NotADirectoryError`: If path is not a directory

#### `organize_files(files_by_depth: Dict[int, List[Dict[str, any]]], dry_run: bool = False) -> Dict[str, int]`

Organize files by moving them to depth-based folders.

**Parameters:**
- `files_by_depth`: Dictionary mapping depth levels to file lists
- `dry_run`: If True, simulate organization without actually moving files

**Returns:**
- Dictionary with organization statistics:
  - `files_organized`: Number of files organized
  - `files_skipped`: Number of files skipped
  - `errors`: Number of errors encountered

**Behavior:**
- Creates depth-based folders (e.g., Depth_0, Depth_1)
- Moves files to appropriate depth folders
- Handles name conflicts based on configuration
- Optionally preserves directory structure

#### `generate_report(files_by_depth: Dict[int, List[Dict[str, any]]], output_file: Optional[str] = None) -> str`

Generate text report of file organization.

**Parameters:**
- `files_by_depth`: Dictionary mapping depth levels to file lists
- `output_file`: Optional path to save report file

**Returns:**
- Report text string

#### `print_summary(files_by_depth: Dict[int, List[Dict[str, any]]]) -> None`

Print summary to console.

**Parameters:**
- `files_by_depth`: Dictionary mapping depth levels to file lists

#### `_calculate_depth(file_path: Path, base_path: Path) -> int`

Calculate depth of file relative to base path.

**Parameters:**
- `file_path`: Path to file
- `base_path`: Base directory path

**Returns:**
- Depth level (0 = base directory, 1 = one level deep, etc.)

#### `_get_depth_folder_name(depth: int) -> str`

Get folder name for a depth level.

**Parameters:**
- `depth`: Depth level

**Returns:**
- Folder name for the depth level (e.g., "Depth_0", "Depth_1")

## Configuration Structure

```yaml
source:
  directory: "."  # Directory to scan
  recursive: true  # Scan subdirectories

output:
  directory: "organized"  # Output directory
  preserve_structure: false  # Preserve relative structure

organization:
  dry_run: true  # Default to dry-run
  depth_naming:
    prefix: "Depth"  # Folder name prefix
    separator: "_"  # Separator between prefix and level
    include_level: true  # Include depth level in name
  conflicts:
    action: "rename"  # "rename", "skip", or "overwrite"

include:
  extensions: []  # Empty = all extensions
  include_no_extension: true

skip:
  patterns: []  # Patterns to skip
  directories: []  # Directory names to skip
  excluded_paths: []  # Specific paths to exclude

report:
  auto_save: true  # Automatically save report
  output_file: "logs/depth_report.txt"
  show_file_list: true  # Include file list
```

## Statistics

The organizer tracks the following statistics:

- **files_scanned**: Number of files scanned
- **files_organized**: Number of files organized
- **files_skipped**: Number of files skipped
- **errors**: Number of errors encountered
- **depths_found**: Set of depth levels found

## Depth Calculation

Depth is calculated as the number of parent directories between the file and the base directory:

- Files directly in base directory: depth 0
- Files one level deep: depth 1
- Files two levels deep: depth 2
- And so on...

## Error Handling

The organizer handles the following errors:

- **FileNotFoundError**: Directory or file not found
- **PermissionError**: Insufficient permissions
- **NotADirectoryError**: Path is not a directory
- **OSError**: General file system errors
- **shutil.Error**: File move/copy errors

All errors are logged and counted in statistics.
