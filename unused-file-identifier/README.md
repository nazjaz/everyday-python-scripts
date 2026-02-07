# Unused File Identifier

A Python automation tool that identifies files that haven't been accessed or modified within a specified time period, generating comprehensive cleanup reports to help manage disk space and organize file systems.

## Project Title and Description

The Unused File Identifier scans directories to find files that have not been accessed or modified beyond a configurable threshold. It generates detailed reports showing file paths, sizes, and last access/modification times, helping users identify files that can be safely archived or deleted to free up disk space.

This tool solves the problem of identifying stale files across large directory structures, making it easier to perform disk cleanup operations and maintain organized file systems.

**Target Audience**: System administrators, developers, and users managing large file collections who need to identify unused files for cleanup.

## Features

- Scans directories recursively to identify unused files
- Configurable time threshold for determining unused status (days, weeks, months, years)
- Checks both file modification time and access time
- Generates human-readable text reports with file details
- Exports results to JSON format for programmatic processing
- Skips common system and development directories (configurable)
- Provides statistics on total files scanned and disk space that could be freed
- Sorts results by file size for easy prioritization
- Comprehensive logging with configurable log levels
- Handles permission errors gracefully

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Read access to directories you want to scan

## Installation

### Step 1: Clone or Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/unused-file-identifier
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
- `scan.unused_threshold`: Time period for considering files unused (default: "90d")
  - Format: number followed by unit (d=days, w=weeks, m=months, y=years)
  - Examples: "30d", "2w", "6m", "1y"
- `scan.skip_patterns`: List of path patterns to skip during scanning
  - Default includes: .git, __pycache__, .venv, node_modules, etc.

**Report Settings:**
- `report.output_file`: Path for text report output (default: "cleanup_report.txt")
- `report.json_output_file`: Path for JSON export (default: "cleanup_report.json")

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
scan:
  unused_threshold: "180d"  # 6 months
  skip_patterns:
    - ".git"
    - "backup"
    - "archive"

report:
  output_file: "my_cleanup_report.txt"
  json_output_file: "my_cleanup_report.json"

logging:
  level: "INFO"
  file: "logs/app.log"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Scan a directory for unused files:

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

- `directory`: (Required) Directory path to scan for unused files
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-o, --output`: Custom output path for text report
- `-j, --json`: Also export results to JSON format

### Common Use Cases

**Find files unused for 6 months:**
1. Update `config.yaml` to set `unused_threshold: "180d"`
2. Run: `python src/main.py /home/user/documents`

**Scan Downloads folder:**
```bash
python src/main.py ~/Downloads
```

**Generate both text and JSON reports:**
```bash
python src/main.py /data/files --json -o cleanup_2024.txt
```

## Project Structure

```
unused-file-identifier/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation (if applicable)
└── logs/
    └── .gitkeep             # Placeholder for logs directory
```

### File Descriptions

- `src/main.py`: Contains the `UnusedFileIdentifier` class and main entry point
- `config.yaml`: Configuration file with scan, report, and logging settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `logs/`: Directory for application log files

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
- Time period parsing
- File scanning logic
- Unused file detection
- Report generation
- JSON export
- Error handling

## Troubleshooting

### Common Issues

**Permission Denied Errors:**
- Ensure you have read permissions for the directory being scanned
- Some system directories may require elevated permissions
- The tool will log warnings and continue scanning other files

**Configuration File Not Found:**
- Ensure `config.yaml` exists in the project root
- Use `-c` flag to specify a custom config path
- Check file permissions

**No Files Found:**
- Verify the directory path is correct
- Check that the unused threshold isn't too short
- Review skip patterns in config - they might be excluding your files

**Large Directory Scanning Takes Time:**
- This is expected for large directory trees
- Progress is logged to the console and log file
- Consider scanning subdirectories separately for faster results

### Error Messages

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

**"Invalid time unit"**: The unused_threshold in config.yaml uses an invalid unit. Use d, w, m, or y.

**"Configuration file is empty"**: The config.yaml file exists but has no content. Restore from example.

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
