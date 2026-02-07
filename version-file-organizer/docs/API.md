# API Documentation

## VersionFileOrganizer Class

The main class for organizing files by format version.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the VersionFileOrganizer with configuration.

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

Scan directory and detect file versions.

**Parameters:**
- `directory` (str): Path to directory to scan.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Scans directory recursively
- Detects versions in filenames
- Groups compatible versions
- Populates `file_versions` and `version_groups`
- Updates statistics
- Logs all operations

#### `organize_files(source_dir: str, dry_run: bool = False) -> None`

Organize files into version-based folder structures.

**Parameters:**
- `source_dir` (str): Source directory containing files.
- `dry_run` (bool): If True, simulate organization without moving files.

**Side Effects:**
- Creates version-based folders
- Moves files to appropriate folders
- Updates statistics
- Logs all operations

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate organization report.

**Parameters:**
- `output_path` (Optional[str]): Path to save report file. If None, uses default from config.

**Returns:**
- `str`: Report content as string.

**Raises:**
- `IOError`: If report file cannot be written.
- `PermissionError`: If output directory is not writable.

#### `_parse_version_from_filename(file_path: Path) -> Optional[str]`

Extract version number from filename.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Version string if found, None otherwise.

**Detection Methods:**
- Uses configured regex patterns
- Falls back to default patterns if none configured
- Supports common formats: v1.2.3, 1.2.3, v1, etc.

#### `_normalize_version(version: str) -> str`

Normalize version string for comparison.

**Parameters:**
- `version` (str): Version string.

**Returns:**
- Normalized version string.

**Normalization:**
- Removes leading/trailing whitespace
- Removes common prefixes (v, V, r, R)
- Extracts numeric version components

#### `_are_versions_compatible(version1: str, version2: str) -> bool`

Check if two versions are compatible based on compatibility rules.

**Parameters:**
- `version1` (str): First version string.
- `version2` (str): Second version string.

**Returns:**
- `bool`: True if versions are compatible, False otherwise.

**Compatibility Modes:**
- `exact`: Only exact matches
- `major`: Same major version
- `minor`: Same major.minor
- `patch`: Same major.minor.patch

#### `_get_version_group_key(version: str) -> str`

Get group key for version based on compatibility mode.

**Parameters:**
- `version` (str): Version string.

**Returns:**
- `str`: Group key string.

#### `_detect_file_version(file_path: Path) -> Optional[str]`

Detect version from filename or metadata.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Version string if found, None otherwise.

**Detection Order:**
1. Filename patterns
2. Metadata (if enabled)

### Attributes

#### `file_versions: Dict[str, Dict[str, Any]]`

Dictionary mapping file paths to version information. Each entry contains:
- `path`: Full file path
- `name`: File name
- `version`: Detected version string
- `normalized_version`: Normalized version string
- `group_key`: Version group key
- `size_bytes`: File size

#### `version_groups: Dict[str, List[str]]`

Dictionary mapping version group keys to lists of file paths in that group.

#### `stats: Dict[str, Any]`

Dictionary containing operation statistics:
- `files_scanned`: Total number of files scanned
- `files_with_versions`: Number of files with detected versions
- `files_organized`: Number of files successfully organized
- `version_groups_created`: Number of version groups created
- `errors`: Number of errors encountered

#### `config: dict`

Configuration dictionary loaded from YAML file.

### Example Usage

```python
from src.main import VersionFileOrganizer

# Initialize with default config
organizer = VersionFileOrganizer()

# Or with custom config
organizer = VersionFileOrganizer(config_path="custom_config.yaml")

# Scan directory
organizer.scan_directory("/path/to/directory")

# Organize files (dry run first)
organizer.organize_files("/path/to/directory", dry_run=True)

# Actually organize files
organizer.organize_files("/path/to/directory", dry_run=False)

# Generate report
organizer.generate_report()

# Access results
print(f"Found {organizer.stats['files_with_versions']} files with versions")
print(f"Created {organizer.stats['version_groups_created']} version groups")
for group_key, files in organizer.version_groups.items():
    print(f"Group {group_key}: {len(files)} files")
```

### Version Detection Patterns

Default patterns support:
- `v1.2.3` - Version with v prefix
- `1.2.3` - Standard semantic versioning
- `v1.2` - Major.minor
- `v1` - Single number
- `file-1.2.3.txt` - With separator
- `file_1.2.3.txt` - With underscore

Custom patterns can be defined in config.yaml using regex with capture groups.

### Compatibility Grouping

Files are grouped based on compatibility mode:
- **Exact**: Only identical versions
- **Major**: Same major version (1.x.x)
- **Minor**: Same major.minor (1.2.x)
- **Patch**: Same major.minor.patch (1.2.3)

Groups are used to create folder structures like:
- `organized/v1/` - Major version grouping
- `organized/v1.2/` - Minor version grouping
- `organized/v1.2.3/` - Exact version grouping
