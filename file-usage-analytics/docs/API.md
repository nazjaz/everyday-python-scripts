# API Documentation

## FileUsageAnalytics Class

The main class for analyzing file usage patterns and generating visualizations.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the FileUsageAnalytics with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.
- `ValueError`: If configuration file is empty.

**Side Effects:**
- Loads configuration
- Sets up logging
- Initializes analytics data structures

#### `analyze_directory(source_dir: str) -> None`

Analyze file usage patterns in directory.

**Parameters:**
- `source_dir` (str): Path to directory to analyze.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Scans directory recursively
- Collects file metadata
- Analyzes access patterns, modification trends, and storage growth
- Updates statistics
- Logs all operations

**Analytics Data Collected:**
- File metadata (path, size, timestamps, extension)
- Access patterns by hour
- Modification trends by date
- Storage growth by creation date
- Extension distribution
- Size distribution

#### `generate_visualizations(output_dir: Optional[str] = None) -> Dict[str, Path]`

Generate all visualization charts.

**Parameters:**
- `output_dir` (Optional[str]): Optional directory to save charts. If None, uses default from config.

**Returns:**
- `Dict[str, Path]`: Dictionary mapping chart names to output file paths.

**Raises:**
- `ValueError`: If no analytics data is available (must run `analyze_directory()` first).

**Generated Charts:**
- `access_patterns`: Bar chart showing file accesses by hour of day
- `modification_trends`: Line chart showing file modifications over time
- `storage_growth`: Dual chart showing daily and cumulative storage growth
- `extension_distribution`: Horizontal bar chart of top 15 file extensions
- `size_distribution`: Bar chart showing file size distribution in MB buckets

**Side Effects:**
- Creates output directory if it doesn't exist
- Generates PNG image files for each chart
- Logs chart generation

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate analytics report.

**Parameters:**
- `output_path` (Optional[str]): Optional path to save report file. If None, uses default from config.

**Returns:**
- `str`: Report content as string.

**Raises:**
- `ValueError`: If no analytics data is available (must run `analyze_directory()` first).
- `IOError`: If report file cannot be written.
- `PermissionError`: If output directory is not writable.

**Report Sections:**
- Summary statistics (files analyzed, storage totals, averages)
- Access patterns (peak hours, hourly breakdown)
- Modification trends (recent modification dates)
- Storage growth (total growth, recent additions)
- Extension distribution (top file types)

**Side Effects:**
- Creates output directory if it doesn't exist
- Writes report to file
- Logs report generation

#### `_collect_file_metadata(file_path: Path) -> Optional[Dict[str, Any]]`

Collect metadata for a single file.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `Optional[Dict[str, Any]]`: Dictionary with file metadata or None if error.

**Metadata Fields:**
- `path`: Full file path as string
- `size`: File size in bytes
- `modified`: Modification timestamp as datetime
- `accessed`: Access timestamp as datetime
- `created`: Creation timestamp as datetime
- `extension`: File extension (lowercase, with dot)

**Raises:**
- Logs errors but returns None instead of raising exceptions

#### `_should_skip_path(path: Path) -> bool`

Check if a path should be skipped during scanning.

**Parameters:**
- `path` (Path): Path to check.

**Returns:**
- `bool`: True if path should be skipped, False otherwise.

**Skip Logic:**
- Checks if any skip pattern from config is contained in path string
- Used to exclude system directories, build artifacts, etc.

### Attributes

#### `analytics_data: Dict[str, Any]`

Dictionary containing collected analytics data:
- `files`: List of file metadata dictionaries
- `access_patterns`: Dictionary mapping hour (0-23) to access count
- `modification_trends`: Dictionary mapping date to modification count
- `storage_growth`: Dictionary mapping date to bytes added
- `extension_distribution`: Dictionary mapping extension to file count
- `size_distribution`: Dictionary mapping size bucket (MB) to file count

#### `stats: Dict[str, Any]`

Dictionary containing analysis statistics:
- `files_analyzed`: Total number of files analyzed
- `directories_scanned`: Number of directories scanned
- `errors`: Number of errors encountered

#### `config: dict`

Configuration dictionary loaded from YAML file.

### Example Usage

```python
from src.main import FileUsageAnalytics

# Initialize with default config
analytics = FileUsageAnalytics()

# Or with custom config
analytics = FileUsageAnalytics(config_path="custom_config.yaml")

# Analyze directory
analytics.analyze_directory("/path/to/directory")

# Generate visualizations
charts = analytics.generate_visualizations()
print(f"Generated {len(charts)} charts")

# Generate report
report = analytics.generate_report()
print(report)

# Access statistics
print(f"Analyzed {analytics.stats['files_analyzed']} files")
print(f"Scanned {analytics.stats['directories_scanned']} directories")

# Access analytics data
access_patterns = analytics.analytics_data["access_patterns"]
peak_hour = max(access_patterns.items(), key=lambda x: x[1])
print(f"Peak access hour: {peak_hour[0]}:00")
```

### Visualization Details

#### Access Patterns Chart

Bar chart showing file access frequency by hour of day (0-23). Helps identify peak usage times.

#### Modification Trends Chart

Line chart showing number of file modifications over time. Helps track activity patterns.

#### Storage Growth Chart

Dual-panel chart:
- Top panel: Daily storage additions (bar chart)
- Bottom panel: Cumulative storage growth (line chart)

Helps visualize storage growth patterns and trends.

#### Extension Distribution Chart

Horizontal bar chart showing top 15 file extensions by count. Helps understand file type distribution.

#### Size Distribution Chart

Bar chart showing file count by size ranges (10 MB buckets). Helps understand file size patterns.

### Configuration Structure

Priority levels are defined in the configuration file with the following structure:

```yaml
scan:
  skip_patterns:
    - ".git"
    - "__pycache__"

visualizations:
  output_dir: "analytics_charts"

report:
  output_file: "analytics_report.txt"

logging:
  level: "INFO"
  file: "logs/app.log"
```

### Error Handling

The class handles errors gracefully:
- File access errors are logged but don't stop analysis
- Missing files are skipped
- Permission errors are logged and re-raised
- Invalid configuration raises exceptions during initialization
