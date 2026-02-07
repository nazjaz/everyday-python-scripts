# File Summary Reporter

A Python automation tool for generating comprehensive file summary reports with key statistics, trends, and recommendations for organization and cleanup strategies. This script analyzes file systems, identifies patterns, and provides actionable insights for file management.

## Features

- Comprehensive file statistics collection (counts, sizes, types, ages)
- File type and extension distribution analysis
- Size and age distribution categorization
- Trend analysis and growth indicators
- Identification of largest and oldest files
- Detection of empty files and duplicate patterns
- Organization opportunity identification
- Automated recommendation generation for cleanup, organization, and optimization
- Multiple output formats (text and JSON)
- Configurable filtering and analysis thresholds
- Comprehensive logging with rotation

## Prerequisites

- Python 3.8 or higher
- Read permissions to source directory
- Sufficient disk space for log files

## Installation

1. Clone or navigate to the project directory:
```bash
cd file-summary-reporter
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

4. Copy and configure the environment file (optional):
```bash
cp .env.example .env
# Edit .env with your settings if needed
```

5. Review and customize `config.yaml` with your settings:
   - Set `source_directory` to the directory to analyze
   - Configure filtering options
   - Adjust analysis thresholds

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory to analyze (default: current directory)
- **filtering.exclude_directories**: Directories to exclude from analysis
- **filtering.exclude_files**: File patterns to exclude
- **filtering.exclude_extensions**: File extensions to exclude
- **analysis.top_files_limit**: Maximum files to include in top lists
- **analysis.many_files_threshold**: Threshold for "many files" detection
- **analysis.age_thresholds**: Age categorization thresholds in days
- **analysis.size_thresholds**: Size categorization thresholds in bytes

### Environment Variables

Optional environment variables can override configuration:

- `SOURCE_DIRECTORY`: Override source directory path

## Usage

### Basic Usage

Generate a text report to stdout:
```bash
python src/main.py
```

### Output to File

Save report to a file:
```bash
python src/main.py --output report.txt
```

### JSON Format

Generate report in JSON format:
```bash
python src/main.py --format json --output report.json
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config /path/to/custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-o, --output`: Output file path (default: stdout)
- `-f, --format`: Output format - text or json (default: text)
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
file-summary-reporter/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── .gitkeep             # Documentation directory placeholder
└── logs/
    └── .gitkeep             # Logs directory placeholder
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## How It Works

1. **Statistics Collection**: The script recursively scans the source directory, collecting:
   - Total file and directory counts
   - Total size and size distribution
   - File type and extension distribution
   - Age distribution (based on modification time)
   - Largest and oldest files
   - Empty file detection
   - Directory structure depth analysis

2. **Trend Analysis**: Analyzes collected statistics to identify:
   - File type distribution percentages
   - Size and age trends
   - Growth indicators (total size, average file size)
   - Organization opportunities

3. **Recommendation Generation**: Generates actionable recommendations:
   - **Cleanup**: Actions to remove unnecessary files (empty files, old files)
   - **Organization**: Actions to organize files by type or category
   - **Optimization**: Actions to optimize storage (compress, archive, move large files)
   - Priority levels (low, medium, high) based on impact and effort

4. **Report Generation**: Formats the analysis into readable reports:
   - Text format: Human-readable summary with sections
   - JSON format: Machine-readable structured data

## Report Sections

### Overview
- Total files and directories
- Total size in GB
- Basic statistics

### File Type Distribution
- Count and percentage of each file type category
- Categories: image, document, spreadsheet, video, audio, archive, code, executable, other

### Size Distribution
- Files categorized by size: empty, tiny, small, medium, large, very large

### Age Distribution
- Files categorized by age: recent, active, moderate, old, very old

### Top Files
- Top 10 largest files with sizes
- Top 10 oldest files with ages

### Recommendations
- Cleanup actions with impact and effort ratings
- Organization actions
- Optimization actions
- Priority level

### Organization Opportunities
- Specific opportunities identified from analysis

## Troubleshooting

### Permission Errors

If you encounter permission errors:
- Ensure you have read access to the source directory
- Check file and directory permissions
- Some files may be skipped with warnings in the log

### Large Directory Performance

If analysis is slow for large directories:
- The script processes files efficiently but may take time for very large directories
- Consider analyzing subdirectories separately
- Check log file for progress information

### Missing Files in Report

If files are missing from the report:
- Check that files are not in the exclude lists
- Verify the source directory path is correct
- Check log file for skipped files and reasons

### Configuration Errors

If configuration errors occur:
- Validate YAML syntax in `config.yaml`
- Ensure all required configuration keys are present
- Check that paths are valid and accessible

## Output Formats

### Text Format

Human-readable format with sections and formatted numbers. Suitable for:
- Direct reading
- Printing
- Email reports
- Documentation

### JSON Format

Structured data format suitable for:
- Programmatic processing
- Integration with other tools
- Data analysis
- Automated reporting systems

## Security Considerations

- The script only reads file metadata and does not modify files
- No sensitive file contents are read or logged
- File paths are logged but can be filtered in configuration
- The script respects file permissions and skips inaccessible files

## Performance Considerations

- Processing time increases with the number of files
- Large files are handled efficiently without reading contents
- Statistics are collected in a single pass
- Consider analyzing during off-peak hours for very large directories

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
