# Temp Cleaner

Clean up temporary files older than a specified number of days from system temp directories. Includes exclusions for active processes, configurable patterns, and comprehensive logging with dry-run mode for safe operation.

## Project Description

Temp Cleaner solves the problem of accumulating temporary files that consume disk space over time. It safely identifies and removes old temporary files while protecting files that are currently in use by active processes. The tool helps maintain system performance and free up disk space without risking data loss or interrupting running applications.

**Target Audience**: System administrators, developers, and users who need to manage disk space by cleaning up old temporary files safely.

## Features

- Automatic detection of system temporary directories (Windows, macOS, Linux)
- Age-based filtering (delete files older than specified days)
- Active process detection to prevent deleting files in use
- Configurable exclusions (directories, patterns, extensions, processes)
- Dry-run mode to preview deletions before executing
- Comprehensive logging with rotation
- Space freed calculation
- Cross-platform support (Windows, macOS, Linux)
- Safe operation with multiple safety checks

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Administrator/root privileges may be required for some system temp directories
- psutil library for process detection

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/temp-cleaner
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

### Step 4: Configure Settings

Edit `config.yaml` to set minimum age and exclusions:

```yaml
min_age_days: 7
exclusions:
  directories:
    - ~/.cache/pip
  patterns:
    - .lock
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **min_age_days**: Minimum age in days for files to be deleted (default: `7`)
- **temp_directories**: List of directories to clean (empty uses system defaults)
- **exclusions**: Configuration for excluding files from deletion
  - **directories**: Directories to exclude
  - **patterns**: Patterns to match in filenames or paths
  - **extensions**: File extensions to exclude
  - **processes**: Process names whose open files should be excluded
- **operations**: Operation settings
  - **dry_run**: Preview mode without deleting files
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `MIN_AGE_DAYS`: Override minimum age in days
- `DRY_RUN`: Enable dry run mode (`true`/`false`)

### System Default Temp Directories

If `temp_directories` is empty, the script automatically detects system temp directories:

- **Windows**: `TEMP`, `TMP`, `LOCALAPPDATA\Temp`
- **macOS**: `/tmp`, `~/Library/Caches`
- **Linux**: `/tmp`, `/var/tmp`, `TMPDIR`

### Example Configuration

```yaml
min_age_days: 14

temp_directories:
  - /tmp
  - ~/Library/Caches

exclusions:
  directories:
    - ~/.cache/pip
    - ~/Library/Caches/com.apple
  patterns:
    - .lock
    - .pid
  extensions:
    - .lock
    - .pid
  processes:
    - python
    - node

operations:
  dry_run: false
```

## Usage

### Basic Usage

Clean temporary files with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Preview changes without deleting files (dry run)
python src/main.py --dry-run

# Set minimum age in days (overrides config)
python src/main.py --min-age 30

# Combine options
python src/main.py --dry-run --min-age 14
```

### Common Use Cases

1. **Preview Cleanup (Recommended First Step)**:
   ```bash
   python src/main.py --dry-run
   ```
   See what would be deleted without actually deleting anything.

2. **Clean Files Older Than 7 Days**:
   ```bash
   python src/main.py
   ```
   Uses default 7-day threshold from config.

3. **Clean Files Older Than 30 Days**:
   ```bash
   python src/main.py --min-age 30
   ```
   More conservative cleanup.

4. **Clean Specific Directories**:
   - Edit `config.yaml` to specify `temp_directories`
   - Run script normally

5. **Exclude Specific Processes**:
   - Add process names to `exclusions.processes` in config
   - Files open by these processes will be skipped

## Project Structure

```
temp-cleaner/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py         # Package initialization
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core cleanup logic, process detection, and file deletion
- **config.yaml**: YAML configuration file with age thresholds and exclusions
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Safety Features

The script includes multiple safety mechanisms:

1. **Active Process Detection**: Files open by any process are never deleted
2. **Age Verification**: Only files older than specified age are considered
3. **Exclusion Patterns**: Configurable patterns to protect specific files
4. **Dry Run Mode**: Preview all operations before executing
5. **Comprehensive Logging**: All operations are logged for review
6. **Error Handling**: Errors are logged but don't stop the cleanup process

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- File age checking
- Active process detection
- Exclusion logic (directories, patterns, extensions, processes)
- File deletion operations
- Dry run mode
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `PermissionError` when accessing temp directories

**Solution**: Run with appropriate permissions. On Linux/Mac, you may need `sudo` for system temp directories. On Windows, run as Administrator.

---

**Issue**: Files that should be deleted are being skipped

**Solution**:
- Check if files are actually older than `min_age_days`
- Verify files aren't in use by processes (check logs)
- Check exclusion patterns in config
- Use `--dry-run` to see why files are being skipped

---

**Issue**: Files in use are being deleted

**Solution**: This should not happen. The script checks active file handles. If it does occur:
- Check that `psutil` is installed correctly
- Verify process detection is working
- Report as a bug with system information

---

**Issue**: Too many files being deleted

**Solution**:
- Increase `min_age_days` to be more conservative
- Add more exclusion patterns
- Use `--dry-run` first to preview
- Review logs to understand what's being deleted

---

**Issue**: Script is slow

**Solution**:
- Process detection can be slow on systems with many processes
- Consider excluding more directories to reduce scanning
- The script is designed to be thorough over fast

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Error accessing directory"**: Permission issue; check directory permissions
- **"Error deleting file"**: File may be locked or permission denied; check logs for details
- **"Error getting active file handles"**: Process detection issue; script will continue but may be less safe

## Security Considerations

- **Run with appropriate permissions**: Some temp directories require elevated privileges
- **Review exclusions carefully**: Ensure important files are excluded
- **Use dry-run first**: Always preview before executing
- **Backup important data**: While temp files should be safe to delete, always backup important data
- **Monitor logs**: Review logs after running to ensure expected behavior

## Legal and Ethical Considerations

- **System files**: The script is designed to only clean user-accessible temp directories
- **Active processes**: Files in use are always protected
- **User responsibility**: Users are responsible for ensuring exclusions are appropriate
- **No warranty**: Use at your own risk; always use dry-run mode first

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov pytest-mock`
5. Create a feature branch: `git checkout -b feature/your-feature`

### Code Style Guidelines

- Follow PEP 8 style guide
- Maximum line length: 88 characters (Black formatter)
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Run tests before committing: `pytest tests/`

### Pull Request Process

1. Ensure all tests pass
2. Update README.md if adding new features
3. Add tests for new functionality
4. Submit pull request with clear description

## License

This project is provided as-is for educational and personal use. Users are responsible for ensuring safe operation and backing up important data.
