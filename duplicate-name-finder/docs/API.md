# Duplicate Name Finder API Documentation

## DuplicateNameFinder Class

Main class for finding and managing files with duplicate names.

### Constructor

```python
DuplicateNameFinder(config_path: str = "config.yaml") -> None
```

Initialize DuplicateNameFinder with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Default: "config.yaml"

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

**Example:**
```python
finder = DuplicateNameFinder(config_path="config.yaml")
```

### Methods

#### find_duplicate_names

```python
find_duplicate_names(
    directory: Optional[str] = None,
    recursive: bool = True
) -> Dict[str, List[Dict[str, Any]]]
```

Find files with duplicate names in different directories.

**Parameters:**
- `directory` (Optional[str]): Directory to search. Overrides config if provided.
- `recursive` (bool): Whether to search recursively. Default: True

**Returns:**
- `Dict[str, List[Dict[str, Any]]]`: Dictionary mapping filenames to lists of file information. Each file info dict contains:
  - `path` (str): Full path to file
  - `name` (str): Filename
  - `directory` (str): Directory containing file
  - `size` (int): File size in bytes
  - `modified_time` (float): Modification timestamp
  - `modified_datetime` (datetime): Modification datetime object

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `ValueError`: If path is not a directory

**Example:**
```python
duplicates = finder.find_duplicate_names(directory="/path/to/search", recursive=True)
for filename, file_list in duplicates.items():
    print(f"{filename}: found in {len(file_list)} locations")
```

#### rename_with_prefixes

```python
rename_with_prefixes(
    base_directory: Optional[str] = None,
    dry_run: bool = False
) -> int
```

Rename duplicate files with directory prefixes.

**Parameters:**
- `base_directory` (Optional[str]): Base directory for prefix calculation. Overrides config if provided.
- `dry_run` (bool): If True, show what would be renamed without actually renaming. Default: False

**Returns:**
- `int`: Number of files renamed (or would be renamed in dry-run)

**Raises:**
- `ValueError`: If no duplicates found or base directory is invalid
- `FileNotFoundError`: If base directory doesn't exist

**Example:**
```python
# Preview renaming
count = finder.rename_with_prefixes(dry_run=True)
print(f"Would rename {count} files")

# Actually rename
count = finder.rename_with_prefixes()
print(f"Renamed {count} files")
```

#### generate_report

```python
generate_report(output_file: Optional[str] = None) -> str
```

Generate text report of duplicate file names.

**Parameters:**
- `output_file` (Optional[str]): Path to output file. Overrides config if provided.

**Returns:**
- `str`: Report content as string

**Example:**
```python
report = finder.generate_report(output_file="report.txt")
print(report)
```

#### get_statistics

```python
get_statistics() -> Dict[str, Any]
```

Get processing statistics.

**Returns:**
- `Dict[str, Any]`: Dictionary with statistics:
  - `files_scanned` (int): Total files scanned
  - `duplicate_names_found` (int): Number of files with duplicate names
  - `files_renamed` (int): Number of files renamed
  - `errors` (int): Number of errors encountered

**Example:**
```python
stats = finder.get_statistics()
print(f"Scanned {stats['files_scanned']} files")
print(f"Found {stats['duplicate_names_found']} duplicates")
```

### Private Methods

#### _load_config

```python
_load_config(config_path: str) -> dict
```

Load configuration from YAML file.

#### _setup_logging

```python
_setup_logging() -> None
```

Configure logging based on configuration.

#### _is_excluded

```python
_is_excluded(file_path: Path) -> bool
```

Check if file should be excluded from search.

#### _get_directory_prefix

```python
_get_directory_prefix(file_path: Path, base_directory: Path) -> str
```

Get directory prefix for file based on its path.

#### _format_size

```python
_format_size(size_bytes: int) -> str
```

Format file size in human-readable format.

## Attributes

### config

Configuration dictionary loaded from YAML file.

### duplicate_groups

Dictionary mapping filenames to lists of file information for duplicate files.

### stats

Dictionary containing processing statistics:
- `files_scanned`: Total files scanned
- `duplicate_names_found`: Number of files with duplicate names
- `files_renamed`: Number of files renamed
- `errors`: Number of errors encountered

## Usage Examples

### Basic Usage

```python
from src.main import DuplicateNameFinder

# Initialize
finder = DuplicateNameFinder(config_path="config.yaml")

# Find duplicates
duplicates = finder.find_duplicate_names(directory="/path/to/search")

# Generate report
report = finder.generate_report(output_file="report.txt")

# Get statistics
stats = finder.get_statistics()
print(f"Found {len(duplicates)} duplicate names")
```

### Renaming Duplicates

```python
from src.main import DuplicateNameFinder

finder = DuplicateNameFinder()

# Find duplicates
finder.find_duplicate_names(directory="/path/to/search")

# Preview renaming
finder.rename_with_prefixes(dry_run=True)

# Actually rename
finder.rename_with_prefixes()
```

### Custom Configuration

```python
from src.main import DuplicateNameFinder

# Use custom config file
finder = DuplicateNameFinder(config_path="custom_config.yaml")

# Override directory via method
duplicates = finder.find_duplicate_names(directory="/custom/path")
```
