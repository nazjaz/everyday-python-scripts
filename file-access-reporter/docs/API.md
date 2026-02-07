# API Documentation

## FileAccessReporter Class

The main class for generating file access and modification reports.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the FileAccessReporter with configuration.

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

Scan directory and collect file access and modification data.

**Parameters:**
- `directory` (str): Path to directory to scan.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Scans directory recursively
- Collects file access and modification timestamps
- Builds access and modification pattern dictionaries
- Updates statistics
- Logs all operations

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate comprehensive file access report.

**Parameters:**
- `output_path` (Optional[str]): Path to save report file. If None, uses default from config.

**Returns:**
- `str`: Report content as string.

**Raises:**
- `IOError`: If report file cannot be written.
- `PermissionError`: If output directory is not writable.

**Report Contents:**
- Summary statistics
- Access frequency distribution
- Modification frequency distribution
- Access patterns over time
- Modification patterns over time
- Most recently accessed files
- Least recently accessed files

#### `export_json(output_path: Optional[str] = None) -> str`

Export file access data to JSON format.

**Parameters:**
- `output_path` (Optional[str]): Path to save JSON file. If None, uses default from config.

**Returns:**
- `str`: Path to saved JSON file.

**Raises:**
- `IOError`: If JSON file cannot be written.
- `PermissionError`: If output directory is not writable.

#### `_collect_file_data(file_path: Path) -> Optional[Dict[str, Any]]`

Collect access and modification data for a file.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Dictionary with file data or None if error.

**File Data Dictionary:**
- `path`: Full file path
- `name`: File name
- `extension`: File extension
- `size_bytes`: File size in bytes
- `last_accessed`: ISO format timestamp of last access
- `last_modified`: ISO format timestamp of last modification
- `created`: ISO format timestamp of creation
- `days_since_access`: Days since last access
- `days_since_modification`: Days since last modification
- `access_bucket`: Time bucket string for access
- `modification_bucket`: Time bucket string for modification

#### `_get_time_bucket(timestamp: datetime, bucket_size: str) -> str`

Get time bucket string for grouping.

**Parameters:**
- `timestamp` (datetime): Datetime object.
- `bucket_size` (str): Bucket size ('day', 'week', 'month', 'year').

**Returns:**
- `str`: Time bucket string.

#### `_calculate_days_since(timestamp: datetime) -> int`

Calculate days since timestamp.

**Parameters:**
- `timestamp` (datetime): Datetime object.

**Returns:**
- `int`: Number of days since timestamp.

#### `_get_access_frequency_category(days: int) -> str`

Categorize access frequency based on days since access.

**Parameters:**
- `days` (int): Days since last access.

**Returns:**
- `str`: Frequency category string.

**Categories:**
- "Today" (0 days)
- "This Week" (1-7 days)
- "This Month" (8-30 days)
- "Last 3 Months" (31-90 days)
- "Last 6 Months" (91-180 days)
- "Last Year" (181-365 days)
- "Over 1 Year" (>365 days)

#### `_format_size(size_bytes: int) -> str`

Format file size in human-readable format.

**Parameters:**
- `size_bytes` (int): Size in bytes.

**Returns:**
- `str`: Formatted size string (e.g., "1.5 MB").

### Attributes

#### `file_data: List[Dict[str, Any]]`

List of dictionaries containing file access and modification data for each scanned file.

#### `access_patterns: Dict[str, int]`

Dictionary mapping time bucket strings to file access counts.

#### `modification_patterns: Dict[str, int]`

Dictionary mapping time bucket strings to file modification counts.

#### `stats: Dict[str, Any]`

Dictionary containing scanning statistics:
- `files_scanned`: Total number of files scanned
- `directories_scanned`: Number of directories scanned
- `errors`: Number of errors encountered

#### `config: dict`

Configuration dictionary loaded from YAML file.

### Example Usage

```python
from src.main import FileAccessReporter

# Initialize with default config
reporter = FileAccessReporter()

# Or with custom config
reporter = FileAccessReporter(config_path="custom_config.yaml")

# Scan directory
reporter.scan_directory("/path/to/directory")

# Generate text report
reporter.generate_report()

# Export to JSON
reporter.export_json()

# Access data
print(f"Scanned {reporter.stats['files_scanned']} files")
print(f"Access patterns: {reporter.access_patterns}")
```

### JSON Export Format

The JSON export contains:

```json
{
  "generated": "2024-02-07T12:00:00",
  "stats": {
    "files_scanned": 100,
    "directories_scanned": 10,
    "errors": 0
  },
  "access_patterns": {
    "2024-02-07": 5,
    "2024-02-06": 10
  },
  "modification_patterns": {
    "2024-02-07": 3,
    "2024-02-06": 8
  },
  "files": [
    {
      "path": "/path/to/file.txt",
      "name": "file.txt",
      "extension": ".txt",
      "size_bytes": 1024,
      "last_accessed": "2024-02-07T10:00:00",
      "last_modified": "2024-02-06T15:00:00",
      "created": "2024-01-01T00:00:00",
      "days_since_access": 0,
      "days_since_modification": 1,
      "access_bucket": "2024-02-07",
      "modification_bucket": "2024-02-06"
    }
  ]
}
```
