# Temporary File Cleaner

A Python automation tool that safely cleans up temporary download files, incomplete downloads, and files with temporary extensions. The tool includes comprehensive safety checks to prevent accidental deletion of important files.

## Project Title and Description

The Temporary File Cleaner scans directories to identify and remove temporary files, incomplete downloads, and files with temporary extensions. It uses multiple safety checks including age verification, size limits, protected patterns, and protected directories to ensure only safe-to-delete files are removed.

This tool solves the problem of accumulated temporary files cluttering download directories and storage, while providing safety mechanisms to prevent accidental deletion of important files.

**Target Audience**: System administrators, users managing large download directories, and anyone who needs to clean up temporary files safely.

## Features

- **Multiple detection methods:**
  - Temporary file extensions (.tmp, .download, .part, etc.)
  - Temporary filename patterns
  - Incomplete download detection
- **Safety checks:**
  - Minimum age requirement
  - Maximum size limit
  - Protected pattern matching
  - Protected directory exclusion
  - File lock detection
- **Dry-run mode:** Test cleanup without deleting files
- **Comprehensive reporting:** Detailed reports of files found and deleted
- **Confirmation prompts:** User confirmation before deletion (optional)
- **Space tracking:** Reports total space freed
- **Error handling:** Graceful handling of permission errors and locked files

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Read and write access to directories being cleaned

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/temp-file-cleaner
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

**Cleanup Settings:**
- `cleanup.temp_extensions`: List of temporary file extensions to identify
- `cleanup.temp_filename_patterns`: Filename patterns indicating temporary files
- `cleanup.incomplete_min_age_days`: Minimum age for incomplete downloads
- `cleanup.incomplete_min_size_bytes`: Minimum size for incomplete detection

**Safety Settings:**
- `safety.min_age_days`: Minimum age before file can be deleted
- `safety.max_size_bytes`: Maximum file size to delete (null to disable)
- `safety.protected_patterns`: Patterns that protect files from deletion
- `safety.protected_directories`: Directories to never delete from

**Scan Settings:**
- `scan.skip_patterns`: Path patterns to skip during scanning

**Report Settings:**
- `report.output_file`: Path for cleanup report

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file

### Example Configuration

```yaml
cleanup:
  temp_extensions:
    - ".tmp"
    - ".download"
    - ".part"
  incomplete_min_age_days: 2

safety:
  min_age_days: 1
  max_size_bytes: 1073741824  # 1 GB
  protected_patterns:
    - "important"
    - "backup"

scan:
  skip_patterns:
    - ".git"
    - "backup"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Scan and clean temporary files:

```bash
python src/main.py /path/to/directory
```

### Dry Run Mode

Test cleanup without deleting files:

```bash
python src/main.py /path/to/directory --dry-run
```

### Automatic Deletion

Delete files without confirmation prompt:

```bash
python src/main.py /path/to/directory --auto
```

### Specify Custom Configuration

```bash
python src/main.py /path/to/directory -c custom_config.yaml
```

### Custom Report Output

```bash
python src/main.py /path/to/directory -r custom_report.txt
```

### Combined Options

```bash
python src/main.py /path/to/directory -c config.yaml --dry-run -r report.txt
```

### Command-Line Arguments

- `directory`: (Required) Directory path to scan for temporary files
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Simulate cleanup without deleting files
- `-r, --report`: Custom output path for cleanup report
- `--auto`: Automatically delete files without confirmation

### Common Use Cases

**Clean Downloads Folder:**
```bash
python src/main.py ~/Downloads
```

**Test Before Cleaning:**
1. Run with `--dry-run` first
2. Review report and logs
3. Adjust safety settings if needed
4. Run without `--dry-run` to actually clean

**Automated Cleanup:**
```bash
# Use --auto for automated scripts
python src/main.py ~/Downloads --auto
```

**Clean Specific Directory:**
```bash
python src/main.py /path/to/temp/files --dry-run
```

## Project Structure

```
temp-file-cleaner/
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

- `src/main.py`: Contains the `TemporaryFileCleaner` class and main logic
- `config.yaml`: Configuration file with cleanup, safety, and logging settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `logs/`: Directory for application log files

## Safety Features

### Age Verification

Files must meet minimum age requirement before deletion. This prevents deletion of recently created files that might still be in use.

### Size Limits

Optional maximum size limit prevents deletion of very large files that might be important, even if they have temporary extensions.

### Protected Patterns

Files matching protected patterns (e.g., "important", "backup") are never deleted, regardless of extension or filename.

### Protected Directories

System and important directories are protected. Files in these directories are never deleted.

### File Lock Detection

The tool attempts to detect files that are currently locked (being written to) and skips them to prevent errors.

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
- Temporary file detection
- Incomplete download detection
- Safety check logic
- File deletion operations
- Error handling

## Troubleshooting

### Common Issues

**Files Not Being Deleted:**
- Check safety settings (min_age_days, protected_patterns)
- Verify files match temporary file criteria
- Review logs for specific reasons files were skipped

**Too Many Files Deleted:**
- Increase `min_age_days` in safety settings
- Add more patterns to `protected_patterns`
- Add directories to `protected_directories`
- Use `--dry-run` first to preview

**Permission Errors:**
- Ensure read/write permissions for directory
- Some system files may require elevated permissions
- Tool will log warnings and continue with other files

**Files Still Locked:**
- Wait for downloads to complete
- Close applications using the files
- Re-run cleanup after files are unlocked

### Error Messages

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

**"Configuration file is empty"**: The config.yaml file exists but has no content. Restore from example.

### Best Practices

1. **Always use `--dry-run` first** to see what would be deleted
2. **Review safety settings** before running on important directories
3. **Start with conservative settings** and adjust as needed
4. **Backup important files** before running cleanup
5. **Check logs** to understand why files were or weren't deleted
6. **Use protected patterns** for files you want to keep
7. **Set appropriate age limits** to avoid deleting recent files

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
