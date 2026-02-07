# File Statistics Generator API Documentation

## FileStatisticsGenerator Class

Main class for generating comprehensive file statistics.

### Constructor

```python
FileStatisticsGenerator(config_path: str = "config.yaml") -> None
```

Initialize FileStatisticsGenerator with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Default: "config.yaml"

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

**Example:**
```python
generator = FileStatisticsGenerator(config_path="config.yaml")
```

### Methods

#### scan_files

```python
scan_files(
    directory: Optional[str] = None,
    recursive: bool = True
) -> List[Dict[str, Any]]
```

Scan directory and collect file information.

**Parameters:**
- `directory` (Optional[str]): Directory to scan. Overrides config if provided
- `recursive` (bool): Whether to search recursively. Default: True

**Returns:**
- `List[Dict[str, Any]]`: List of file information dictionaries. Each dict contains:
  - `path` (str): Full path to file
  - `name` (str): Filename
  - `extension` (str): File extension (lowercase)
  - `size` (int): File size in bytes
  - `modified_time` (float): Modification timestamp
  - `modified_datetime` (datetime): Modification datetime object
  - `created_time` (float): Creation timestamp
  - `created_datetime` (datetime): Creation datetime object
  - `directory` (str): Directory containing file

**Raises:**
- `FileNotFoundError`: If directory doesn't exist
- `ValueError`: If path is not a directory

**Example:**
```python
files = generator.scan_files(directory="/path/to/scan", recursive=True)
print(f"Scanned {len(files)} files")
```

#### calculate_statistics

```python
calculate_statistics() -> Dict[str, Any]
```

Calculate comprehensive file statistics.

**Returns:**
- `Dict[str, Any]`: Dictionary containing all calculated statistics:
  - `summary`: Summary statistics (total files, sizes, averages)
  - `extensions`: Extension statistics (most common, counts, sizes)
  - `size_distribution`: Size distribution across ranges
  - `date_trends`: Storage usage trends by date
  - `directory_statistics`: Directory statistics
  - `age_statistics`: File age distribution
  - `scan_timestamp`: Timestamp of scan

**Raises:**
- `ValueError`: If no file data available (must run scan_files first)

**Example:**
```python
statistics = generator.calculate_statistics()
print(f"Total files: {statistics['summary']['total_files']}")
print(f"Total size: {statistics['summary']['total_size_formatted']}")
```

#### generate_report

```python
generate_report(
    output_file: Optional[str] = None,
    format: str = "text"
) -> str
```

Generate text or JSON report of file statistics.

**Parameters:**
- `output_file` (Optional[str]): Path to output file. Overrides config if provided
- `format` (str): Report format ("text" or "json"). Default: "text"

**Returns:**
- `str`: Report content as string

**Raises:**
- `ValueError`: If no statistics available (must run calculate_statistics first)

**Example:**
```python
# Generate text report
report = generator.generate_report(output_file="report.txt", format="text")

# Generate JSON report
json_report = generator.generate_report(output_file="report.json", format="json")
```

#### get_statistics

```python
get_statistics() -> Dict[str, Any]
```

Get calculated statistics.

**Returns:**
- `Dict[str, Any]`: Dictionary with all statistics (copy of internal statistics)

**Example:**
```python
stats = generator.get_statistics()
summary = stats["summary"]
print(f"Total files: {summary['total_files']}")
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

Check if file should be excluded from statistics.

#### _calculate_size_distribution

```python
_calculate_size_distribution(sizes: List[int]) -> List[Dict[str, Any]]
```

Calculate distribution of files by size ranges.

**Parameters:**
- `sizes` (List[int]): List of file sizes in bytes

**Returns:**
- `List[Dict[str, Any]]`: List of size range statistics

#### _calculate_date_trends

```python
_calculate_date_trends() -> Dict[str, Any]
```

Calculate storage usage trends by date.

**Returns:**
- `Dict[str, Any]`: Dictionary with date-based trend statistics

#### _calculate_directory_statistics

```python
_calculate_directory_statistics() -> Dict[str, Any]
```

Calculate statistics by directory.

**Returns:**
- `Dict[str, Any]`: Dictionary with directory statistics

#### _calculate_age_statistics

```python
_calculate_age_statistics() -> Dict[str, Any]
```

Calculate file age statistics.

**Returns:**
- `Dict[str, Any]`: Dictionary with age-based statistics

#### _format_size

```python
_format_size(size_bytes: int) -> str
```

Format file size in human-readable format.

**Parameters:**
- `size_bytes` (int): Size in bytes

**Returns:**
- `str`: Formatted size string (e.g., "1.23 MB")

#### _generate_text_report

```python
_generate_text_report() -> str
```

Generate human-readable text report.

**Returns:**
- `str`: Report content as string

### Attributes

#### config

Configuration dictionary loaded from YAML file.

#### statistics

Dictionary containing all calculated statistics.

#### file_data

List of file information dictionaries collected during scanning.

## Statistics Structure

### Summary Statistics

```python
{
    "total_files": int,
    "total_size": int,
    "total_size_formatted": str,
    "average_size": float,
    "average_size_formatted": str,
    "median_size": int,
    "median_size_formatted": str,
    "min_size": int,
    "min_size_formatted": str,
    "max_size": int,
    "max_size_formatted": str,
}
```

### Extension Statistics

```python
{
    "total_unique": int,
    "most_common": [
        {
            "extension": str,
            "count": int,
            "percentage": float,
            "total_size": int,
            "total_size_formatted": str,
            "average_size": float,
            "average_size_formatted": str,
        },
        ...
    ],
}
```

### Size Distribution

```python
[
    {
        "name": str,
        "min_size": int,
        "max_size": int,
        "min_size_formatted": str,
        "max_size_formatted": str,
        "count": int,
        "percentage": float,
        "total_size": int,
        "total_size_formatted": str,
        "average_size": float,
        "average_size_formatted": str,
    },
    ...
]
```

### Date Trends

```python
{
    "group_by": str,  # "day", "week", "month", or "year"
    "periods": [
        {
            "period": str,
            "count": int,
            "total_size": int,
            "total_size_formatted": str,
        },
        ...
    ],
    "total_periods": int,
}
```

### Directory Statistics

```python
{
    "total_directories": int,
    "top_by_count": [
        {
            "directory": str,
            "count": int,
            "total_size": int,
            "total_size_formatted": str,
        },
        ...
    ],
    "top_by_size": [
        {
            "directory": str,
            "count": int,
            "total_size": int,
            "total_size_formatted": str,
        },
        ...
    ],
}
```

### Age Statistics

```python
{
    "ranges": [
        {
            "name": str,
            "min_days": float,
            "max_days": float,
            "count": int,
            "percentage": float,
            "total_size": int,
            "total_size_formatted": str,
        },
        ...
    ],
    "oldest_file": datetime,
    "newest_file": datetime,
}
```

## Usage Examples

### Basic Usage

```python
from src.main import FileStatisticsGenerator

# Initialize
generator = FileStatisticsGenerator(config_path="config.yaml")

# Scan files
generator.scan_files(directory="/path/to/scan", recursive=True)

# Calculate statistics
statistics = generator.calculate_statistics()

# Access statistics
summary = statistics["summary"]
print(f"Total files: {summary['total_files']}")
print(f"Total size: {summary['total_size_formatted']}")

# Generate report
report = generator.generate_report(output_file="report.txt", format="text")
```

### Accessing Specific Statistics

```python
from src.main import FileStatisticsGenerator

generator = FileStatisticsGenerator()
generator.scan_files("/path/to/scan")
statistics = generator.calculate_statistics()

# Most common extensions
for ext_info in statistics["extensions"]["most_common"]:
    print(f"{ext_info['extension']}: {ext_info['count']} files")

# Size distribution
for size_range in statistics["size_distribution"]:
    print(f"{size_range['name']}: {size_range['count']} files")

# Date trends
for period in statistics["date_trends"]["periods"]:
    print(f"{period['period']}: {period['count']} files")
```

### JSON Export

```python
from src.main import FileStatisticsGenerator
import json

generator = FileStatisticsGenerator()
generator.scan_files("/path/to/scan")
statistics = generator.calculate_statistics()

# Export as JSON
json_report = generator.generate_report(output_file="stats.json", format="json")

# Or manually
with open("stats.json", "w") as f:
    json.dump(statistics, f, indent=2, default=str)
```

### Custom Analysis

```python
from src.main import FileStatisticsGenerator

generator = FileStatisticsGenerator()
generator.scan_files("/path/to/scan")
statistics = generator.calculate_statistics()

# Find largest files by extension
ext_sizes = {}
for ext_info in statistics["extensions"]["most_common"]:
    ext_sizes[ext_info["extension"]] = ext_info["total_size"]

largest_ext = max(ext_sizes, key=ext_sizes.get)
print(f"Largest extension by size: {largest_ext}")

# Analyze trends
trends = statistics["date_trends"]["periods"]
if len(trends) >= 2:
    recent = trends[-1]["total_size"]
    previous = trends[-2]["total_size"]
    change = ((recent - previous) / previous * 100) if previous > 0 else 0
    print(f"Storage change: {change:.1f}%")
```
