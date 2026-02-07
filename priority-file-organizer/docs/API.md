# API Documentation

## PriorityFileOrganizer Class

The main class for organizing files by priority levels.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the PriorityFileOrganizer with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.
- `ValueError`: If priority levels are invalid or missing.

**Side Effects:**
- Loads configuration
- Sets up logging
- Loads and validates priority levels

#### `organize_directory(source_dir: str, dry_run: bool = False) -> None`

Organize files in directory by priority levels.

**Parameters:**
- `source_dir` (str): Path to directory to organize.
- `dry_run` (bool): If True, simulate organization without moving files.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Scans directory recursively
- Determines priority for each file
- Moves files to priority-based folders (unless dry_run)
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

#### `_determine_priority(file_path: Path) -> Optional[Dict[str, Any]]`

Determine priority level for a file based on criteria.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Priority level dictionary or None if no match.

**Matching Criteria (checked in order):**
1. File patterns (wildcard matching)
2. File extensions
3. Keywords in path/name
4. File size range

#### `_matches_extension(file_path: Path, extensions: List[str]) -> bool`

Check if file has matching extension.

**Parameters:**
- `file_path` (Path): Path to check.
- `extensions` (List[str]): List of extensions (with or without dot).

**Returns:**
- `bool`: True if extension matches, False otherwise.

#### `_matches_keywords(file_path: Path, keywords: List[str]) -> bool`

Check if file path contains any keywords.

**Parameters:**
- `file_path` (Path): Path to check.
- `keywords` (List[str]): List of keywords to search for.

**Returns:**
- `bool`: True if any keyword is found, False otherwise.

#### `_matches_pattern(file_path: Path, pattern: str) -> bool`

Check if file path matches pattern (supports wildcards).

**Parameters:**
- `file_path` (Path): Path to check.
- `pattern` (str): Pattern to match (supports wildcards).

**Returns:**
- `bool`: True if pattern matches, False otherwise.

#### `_is_duplicate(file_path: Path) -> Tuple[bool, Optional[str]]`

Check if file is a duplicate based on content hash.

**Parameters:**
- `file_path` (Path): Path to file to check.

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_duplicate, duplicate_path).

#### `_calculate_file_hash(file_path: Path) -> str`

Calculate MD5 hash of file content.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `str`: MD5 hash string.

**Raises:**
- `IOError`: If file cannot be read.

### Attributes

#### `priority_levels: List[Dict[str, Any]]`

List of priority level dictionaries sorted by priority (highest first). Each dictionary contains:
- `name`: Priority level name
- `priority`: Numeric priority value
- `folder`: Destination folder name
- `criteria`: Matching criteria dictionary

#### `stats: Dict[str, Any]`

Dictionary containing organization statistics:
- `files_scanned`: Total number of files scanned
- `files_organized`: Number of files successfully organized
- `duplicates_found`: Number of duplicate files found
- `errors`: Number of errors encountered
- `priority_distribution`: Dictionary mapping priority names to file counts

#### `config: dict`

Configuration dictionary loaded from YAML file.

#### `file_hashes: Dict[str, str]`

Dictionary mapping file paths to their content hashes (used for duplicate detection).

### Example Usage

```python
from src.main import PriorityFileOrganizer

# Initialize with default config
organizer = PriorityFileOrganizer()

# Or with custom config
organizer = PriorityFileOrganizer(config_path="custom_config.yaml")

# Test organization (dry run)
organizer.organize_directory("/path/to/files", dry_run=True)

# Actually organize files
organizer.organize_directory("/path/to/files", dry_run=False)

# Generate report
organizer.generate_report()

# Access statistics
print(f"Organized {organizer.stats['files_organized']} files")
print(f"Found {organizer.stats['duplicates_found']} duplicates")
```

### Priority Level Configuration

Priority levels are defined in the configuration file with the following structure:

```yaml
priorities:
  - name: "high"
    priority: 4
    folder: "High"
    criteria:
      patterns: ["*important*"]
      extensions: [".pdf", ".doc"]
      keywords: ["contract", "legal"]
      size_range:
        min: 0
        max: 10485760
```

### Duplicate Handling

Duplicates are detected using MD5 content hashing. The action taken is configured in `config.yaml`:

- `skip`: Skip duplicate files (default)
- `delete`: Delete duplicate files
- `move`: Move duplicates to a separate location
