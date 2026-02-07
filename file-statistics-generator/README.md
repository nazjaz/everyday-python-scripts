# File Statistics Generator

A Python automation tool that generates comprehensive file statistics including total count, average size, most common extensions, and storage usage trends.

## Features

- Total file count and size statistics
- Average, median, min, and max file sizes
- Most common file extensions with counts and sizes
- Size distribution across configurable ranges
- Storage usage trends by date (day, week, month, year)
- Directory statistics (top directories by count and size)
- File age distribution analysis
- Recursive or non-recursive directory scanning
- Configurable exclusions (patterns, directories, extensions)
- Text and JSON report formats
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd file-statistics-generator
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Configuration File

The tool uses a YAML configuration file (`config.yaml`) for settings. Key configuration sections:

- **scan**: Scan settings (directory, recursive, exclusions)
- **statistics**: Statistics calculation settings (top extensions, size ranges, trends)
- **report**: Report generation settings
- **logging**: Logging configuration

### Environment Variables

You can override configuration using environment variables:

- `SCAN_DIRECTORY`: Directory to scan (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Generate statistics for current directory:**
```bash
python src/main.py
```

**Scan specific directory:**
```bash
python src/main.py --directory /path/to/scan
```

**Non-recursive search:**
```bash
python src/main.py --directory /path/to/scan --no-recursive
```

**Generate JSON report:**
```bash
python src/main.py --directory /path/to/scan --format json --output report.json
```

**Generate text report:**
```bash
python src/main.py --directory /path/to/scan --output report.txt
```

### Use Cases

**Analyze downloads folder:**
```bash
python src/main.py -d ~/Downloads -o downloads_stats.txt
```

**Generate JSON for programmatic use:**
```bash
python src/main.py -d /path/to/files --format json -o stats.json
```

**Quick statistics:**
```bash
python src/main.py -d /path/to/files
```

## Project Structure

```
file-statistics-generator/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── API.md
└── logs/
    └── .gitkeep
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory
- `output/`: Generated reports directory

## How It Works

1. **Scan Directory**: Recursively or non-recursively scans directory for files
2. **Collect File Data**: Gathers file information (size, extension, dates, paths)
3. **Calculate Statistics**: Computes various statistics from collected data
4. **Generate Report**: Creates detailed report in text or JSON format

### Statistics Generated

1. **Summary Statistics**
   - Total file count
   - Total size
   - Average, median, min, max sizes

2. **Extension Statistics**
   - Most common extensions
   - Count and percentage for each
   - Total and average size per extension

3. **Size Distribution**
   - Files grouped by size ranges (Tiny, Small, Medium, Large, etc.)
   - Count and percentage in each range
   - Total size per range

4. **Storage Usage Trends**
   - Files grouped by modification date
   - Trends by day, week, month, or year
   - File count and total size per period

5. **Directory Statistics**
   - Top directories by file count
   - Top directories by total size

6. **Age Statistics**
   - Files grouped by age (Very Recent, Recent, This Month, etc.)
   - Count and percentage in each age range
   - Total size per age range

## Report Contents

### Text Report

The text report includes:
- Summary statistics
- Most common extensions with details
- Size distribution across ranges
- Storage usage trends (last 12 periods)
- Top directories by size
- File age distribution

### JSON Report

The JSON report contains all statistics in structured format for programmatic use:
- All summary statistics
- Complete extension data
- Full size distribution
- All trend periods
- Complete directory statistics
- All age statistics

## Configuration Options

### Scan Settings

- `directory`: Directory to scan
- `recursive`: Search subdirectories (default: true)
- `exclude.patterns`: Regex patterns to exclude
- `exclude.directories`: Directory names to exclude
- `exclude.extensions`: File extensions to exclude

### Statistics Settings

- `top_extensions`: Number of top extensions to show (default: 10)
- `top_directories`: Number of top directories to show (default: 10)
- `size_ranges`: Custom size range definitions
- `trends.group_by`: Trend grouping (day, week, month, year)

### Size Ranges

Default size ranges:
- **Tiny**: < 1 KB
- **Small**: < 1 MB
- **Medium**: < 10 MB
- **Large**: < 100 MB
- **Very Large**: < 1 GB
- **Huge**: >= 1 GB

Customize in `config.yaml`:
```yaml
statistics:
  size_ranges:
    - name: "Custom Range"
      max: 5242880  # 5 MB
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_main.py::test_calculate_statistics
```

## Troubleshooting

### Common Issues

**No files found:**
- Verify directory path is correct
- Check exclusion rules aren't too broad
- Ensure directory has read permissions

**Statistics calculation errors:**
- Check file permissions
- Review logs for specific errors
- Verify configuration file is valid YAML

**Memory issues with large directories:**
- Use exclusions to limit scanned files
- Consider non-recursive scanning
- Process subdirectories separately

### Error Messages

The tool provides detailed error messages in logs. Check `logs/statistics.log` for:
- File access errors
- Permission issues
- Configuration problems
- Calculation errors

### Best Practices

1. **Use exclusions**: Configure exclusions to avoid processing system files
2. **Start small**: Test with small directories first
3. **Review reports**: Check generated reports for accuracy
4. **Use JSON format**: For programmatic processing or integration
5. **Monitor logs**: Review logs for warnings or errors

## Security Considerations

- Be cautious when scanning system directories
- Review exclusion rules to avoid processing sensitive files
- Verify file permissions before scanning
- Consider privacy implications of file statistics
- Use exclusions for sensitive directories

## Advanced Usage

### Programmatic Usage

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

### Custom Size Ranges

```yaml
statistics:
  size_ranges:
    - name: "Micro"
      max: 512  # < 512 bytes
    - name: "Small"
      max: 1048576  # < 1 MB
    - name: "Large"
      max: null  # >= 1 MB
```

### Trend Analysis

```yaml
statistics:
  trends:
    group_by: "week"  # Options: day, week, month, year
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
