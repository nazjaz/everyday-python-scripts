# File Access Reporter

A Python automation tool that generates comprehensive reports on file access patterns, modification frequencies, and temporal analysis. This tool scans directories to collect file access and modification statistics, providing insights into file usage patterns over time.

## Project Title and Description

The File Access Reporter scans directories and analyzes file access and modification timestamps to generate detailed reports. It tracks when files were last accessed, how frequently they're modified, and identifies access patterns over time. This helps users understand file usage, identify unused files, and analyze access trends.

This tool solves the problem of understanding file usage patterns in large directory structures, making it easier to identify frequently accessed files, detect unused files, and analyze access trends for storage management and organization.

**Target Audience**: System administrators, storage managers, developers, and anyone managing large file collections who need insights into file access patterns.

## Features

- Comprehensive file access tracking (last accessed time)
- Modification frequency analysis
- Access pattern analysis over time (daily, weekly, monthly, yearly)
- Modification pattern analysis over time
- Frequency distribution by time periods (Today, This Week, This Month, etc.)
- Most and least recently accessed file listings
- Human-readable text reports
- JSON export for programmatic analysis
- Configurable time bucket sizes for pattern analysis
- Skip patterns for excluding system/development directories
- Detailed statistics and summaries

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Read access to directories being scanned

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/file-access-reporter
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python src/main.py --help
```

## Configuration

### Configuration File (config.yaml)

The tool uses a YAML configuration file for settings. The default configuration file is `config.yaml` in the project root.

#### Key Configuration Options

**Scan Settings:**
- `scan.skip_patterns`: List of path patterns to skip during scanning
  - Default includes: .git, __pycache__, .venv, node_modules, etc.

**Report Settings:**
- `report.output_file`: Path for text report output (default: "file_access_report.txt")
- `report.json_output_file`: Path for JSON export (default: "file_access_report.json")
- `report.time_bucket`: Time bucket size for pattern analysis
  - Options: "day", "week", "month", "year" (default: "day")

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
scan:
  skip_patterns:
    - ".git"
    - "backup"
    - "archive"

report:
  output_file: "my_access_report.txt"
  json_output_file: "my_access_report.json"
  time_bucket: "week"

logging:
  level: "INFO"
  file: "logs/app.log"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Generate a file access report for a directory:

```bash
python src/main.py /path/to/directory
```

### Specify Custom Configuration

```bash
python src/main.py /path/to/directory -c custom_config.yaml
```

### Custom Output Path

```bash
python src/main.py /path/to/directory -o custom_report.txt
```

### Generate JSON Export

```bash
python src/main.py /path/to/directory --json
```

### Combined Options

```bash
python src/main.py /path/to/directory -c config.yaml -o report.txt --json
```

### Command-Line Arguments

- `directory`: (Required) Directory path to scan for file access data
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-o, --output`: Custom output path for text report
- `-j, --json`: Also export results to JSON format

### Common Use Cases

**Analyze Downloads Folder:**
```bash
python src/main.py ~/Downloads
```

**Generate Weekly Pattern Analysis:**
1. Update `config.yaml` to set `time_bucket: "week"`
2. Run: `python src/main.py /path/to/directory`

**Export for Further Analysis:**
```bash
python src/main.py /path/to/directory --json
```

**Identify Unused Files:**
1. Run report: `python src/main.py /path/to/directory`
2. Review "LEAST RECENTLY ACCESSED FILES" section
3. Identify files that haven't been accessed in a long time

## Project Structure

```
file-access-reporter/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation
└── logs/
    └── .gitkeep             # Placeholder for logs directory
```

### File Descriptions

- `src/main.py`: Contains the `FileAccessReporter` class and main logic
- `config.yaml`: Configuration file with scan, report, and logging settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `logs/`: Directory for application log files

## Report Contents

The generated report includes:

1. **Summary**: Total files scanned, directories scanned, total size, errors
2. **Access Frequency Distribution**: Files grouped by time since last access
   - Today, This Week, This Month, Last 3 Months, Last 6 Months, Last Year, Over 1 Year
3. **Modification Frequency Distribution**: Files grouped by time since last modification
4. **Access Patterns Over Time**: File access counts by time bucket (last 20 periods)
5. **Modification Patterns Over Time**: File modification counts by time bucket (last 20 periods)
6. **Most Recently Accessed Files**: Top 20 files with most recent access
7. **Least Recently Accessed Files**: Top 20 files with oldest access

## Testing

### Run Tests

```bash
python -m pytest tests/
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage, testing:
- Configuration loading and validation
- File data collection
- Time bucket calculation
- Access frequency categorization
- Report generation
- JSON export
- Error handling

## Troubleshooting

### Common Issues

**Permission Denied Errors:**
- Ensure you have read permissions for the directory being scanned
- Some system directories may require elevated permissions
- The tool will log warnings and continue scanning other files

**Report File Not Generated:**
- Check file permissions in the output directory
- Verify disk space is available
- Review logs for error messages

**No Files Found:**
- Verify the directory path is correct
- Check that skip patterns aren't excluding all files
- Ensure files exist in the directory

**Large Directory Scanning Takes Time:**
- This is expected for large directory trees
- Progress is logged to the console and log file
- Consider scanning subdirectories separately for faster results

### Error Messages

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

**"Configuration file is empty"**: The config.yaml file exists but has no content. Restore from example.

### Best Practices

1. **Start with small directories** to understand report format
2. **Use appropriate time buckets** based on your analysis needs
3. **Review skip patterns** to ensure important files aren't excluded
4. **Export to JSON** for custom analysis or visualization
5. **Regular reports** help track access patterns over time

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guidelines
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Include docstrings for all public functions and classes
- Use meaningful variable names
- Write tests for all new functionality

### Pull Request Process

1. Ensure code follows project standards
2. Update documentation if needed
3. Add/update tests
4. Ensure all tests pass
5. Submit PR with clear description of changes

## License

This project is part of the everyday-python-scripts collection. Please refer to the parent repository for license information.
