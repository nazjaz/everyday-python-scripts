# File Health Checker

A Python automation tool that performs comprehensive file health checks by verifying file integrity, detecting corruption, and validating file headers and structures. This tool helps identify damaged, corrupted, or invalid files before they cause problems.

## Project Title and Description

The File Health Checker scans directories and performs multiple health checks on files including header validation (magic number verification), structure validation, integrity checks, and corruption detection. It identifies files that may be damaged, incomplete, or corrupted, helping users maintain data integrity.

This tool solves the problem of detecting file corruption and integrity issues before they cause data loss or application errors. It's essential for maintaining reliable file systems and identifying problematic files.

**Target Audience**: System administrators, data managers, backup operators, and anyone who needs to verify file integrity and detect corruption.

## Features

- **File header validation:** Checks magic numbers to verify file types match extensions
- **Structure validation:** Validates file structures for common formats (ZIP, JPEG, PNG, PDF)
- **Corruption detection:** Identifies truncated, damaged, or invalid files
- **Integrity verification:** Optional checksum calculation (MD5, SHA1, SHA256)
- **Comprehensive reporting:** Detailed reports categorizing files by health status
- **Multiple file format support:** Built-in validation for common formats
- **Custom magic numbers:** Configurable file type detection
- **Error handling:** Graceful handling of permission errors and locked files

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Read access to directories being scanned

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/file-health-checker
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

**Health Check Settings:**
- `health_check.calculate_checksum`: Enable checksum calculation (default: false)
- `health_check.checksum_algorithm`: Algorithm to use - "md5", "sha1", or "sha256" (default: "md5")
- `health_check.min_file_size`: Minimum file size in bytes (default: 1)
- `health_check.magic_numbers`: Custom magic numbers for file type detection

**Scan Settings:**
- `scan.skip_patterns`: List of path patterns to skip during scanning

**Report Settings:**
- `report.output_file`: Path for health check report (default: "health_check_report.txt")

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
health_check:
  calculate_checksum: true
  checksum_algorithm: "sha256"
  min_file_size: 100
  magic_numbers:
    ".custom": ["CUSTOM"]

scan:
  skip_patterns:
    - ".git"
    - "backup"

report:
  output_file: "my_health_report.txt"

logging:
  level: "INFO"
  file: "logs/app.log"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Perform health checks on files in a directory:

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

### Combined Options

```bash
python src/main.py /path/to/directory -c config.yaml -o report.txt
```

### Command-Line Arguments

- `directory`: (Required) Directory path to scan for health checks
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-o, --output`: Custom output path for health check report

### Common Use Cases

**Check Downloads Folder:**
```bash
python src/main.py ~/Downloads
```

**Verify Backup Integrity:**
```bash
python src/main.py /backup/directory -o backup_health.txt
```

**Check Media Files:**
```bash
python src/main.py ~/Pictures
```

**Regular Health Checks:**
1. Schedule regular health checks
2. Review reports for corrupted files
3. Replace or repair corrupted files

## Project Structure

```
file-health-checker/
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

- `src/main.py`: Contains the `FileHealthChecker` class and main logic
- `config.yaml`: Configuration file with health check and logging settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `logs/`: Directory for application log files

## Health Check Types

### Header Validation

Checks if file headers (magic numbers) match expected values for the file extension:
- PDF files must start with `%PDF`
- PNG files must start with PNG signature
- JPEG files must start with `\xff\xd8`
- ZIP files must start with `PK`
- And many more...

### Structure Validation

Validates file structure for specific formats:
- **ZIP files:** Checks for end of central directory record
- **JPEG files:** Validates start and end markers
- **PNG files:** Checks signature and IEND chunk
- **PDF files:** Validates header and end marker (%%EOF)

### Integrity Checks

- **Empty file detection:** Identifies zero-byte files
- **Truncation detection:** Detects files that can't be read completely
- **Size validation:** Flags suspiciously small files
- **Checksum calculation:** Optional MD5/SHA1/SHA256 hashing

## File Status Categories

Files are categorized into:
- **Healthy:** No issues detected
- **Suspicious:** One issue detected (may be false positive)
- **Corrupted:** Multiple issues or critical problems
- **Error:** Cannot be checked (permission errors, etc.)

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
- Magic number detection
- File header validation
- Structure validation
- Checksum calculation
- Error handling

## Troubleshooting

### Common Issues

**Too Many False Positives:**
- Adjust `min_file_size` if legitimate small files are flagged
- Review magic number definitions
- Check file format specifications

**Missing File Types:**
- Add custom magic numbers to config
- Some file types may not have standard magic numbers
- Check logs for detection attempts

**Permission Errors:**
- Ensure read permissions for scanned directories
- Some system files may require elevated permissions
- Tool will log warnings and continue with other files

**Checksum Calculation Slow:**
- Disable checksum calculation for large directories
- Use faster algorithms (MD5 vs SHA256)
- Consider running on smaller subsets

### Error Messages

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

**"Configuration file is empty"**: The config.yaml file exists but has no content. Restore from example.

### Best Practices

1. **Regular health checks** to catch corruption early
2. **Review reports carefully** - some issues may be false positives
3. **Backup before repair** if attempting to fix corrupted files
4. **Use checksums** for critical files to verify integrity
5. **Check logs** for detailed information about issues
6. **Start with small directories** to understand tool behavior

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
