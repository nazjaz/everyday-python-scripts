# Large File Finder

Find files larger than a specified size threshold, generate detailed reports sorted by size, and optionally move them to an archive folder. This tool helps identify and manage large files that may be consuming disk space unnecessarily.

## Project Description

Large File Finder solves the problem of disk space management by automatically identifying files that exceed a configurable size threshold. It provides comprehensive reporting with file sizes sorted in descending order and offers optional archiving functionality to move or copy large files to a designated archive directory.

**Target Audience**: Users who need to identify large files consuming disk space, system administrators managing storage, and developers cleaning up project directories.

## Features

- Scan directories recursively for files exceeding size threshold
- Generate detailed reports sorted by file size (largest first)
- Human-readable file size formatting (B, KB, MB, GB, TB)
- Optional archiving with move or copy operations
- Configurable exclusions for directories and file patterns
- Dry run mode to preview operations without making changes
- Comprehensive logging with rotation
- Handle name conflicts during archiving (skip, rename, overwrite)
- Preserve file timestamps during archive operations
- Support for environment variable overrides

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read permissions to scan directories
- Write permissions to archive directory (if archiving)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/large-file-finder
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

Edit `config.yaml` to set your scan directory, archive directory, and size threshold:

```yaml
scan_directory: ~/Downloads
archive_directory: ~/Archive/LargeFiles
size_threshold_mb: 100
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **scan_directory**: Directory to scan for large files (default: `~/Downloads`)
- **archive_directory**: Directory to archive large files (default: `~/Archive/LargeFiles`)
- **size_threshold_mb**: Size threshold in megabytes (default: `100`)
- **scan_options**: Recursive scanning and symlink following settings
- **exclusions**: Directories and patterns to exclude from scanning
- **archive_options**: Archive method (move/copy), conflict handling, timestamp preservation
- **operations**: Auto-archive, dry run, and directory creation settings
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SCAN_DIRECTORY`: Override scan directory path
- `ARCHIVE_DIRECTORY`: Override archive directory path
- `SIZE_THRESHOLD_MB`: Override size threshold in megabytes
- `DRY_RUN`: Enable dry run mode (`true`/`false`)

### Example Configuration

```yaml
scan_directory: ~/Documents
archive_directory: ~/Archive/LargeFiles
size_threshold_mb: 50

scan_options:
  recursive: true
  follow_symlinks: false

exclusions:
  directories:
    - ~/.Trash
    - node_modules
    - .git
  patterns:
    - .DS_Store

archive_options:
  method: move
  preserve_timestamps: true
  handle_conflicts: rename

operations:
  create_archive_directory: true
  auto_archive: false
  dry_run: false
```

## Usage

### Basic Usage

Find large files and generate a report:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Preview changes without archiving files (dry run)
python src/main.py --dry-run

# Generate report only, do not archive files
python src/main.py --report-only

# Save report to specific file
python src/main.py --output reports/my_report.txt

# Combine options
python src/main.py -c config.yaml --dry-run --output reports/preview.txt
```

### Common Use Cases

1. **Find Large Files in Downloads**:
   ```bash
   python src/main.py
   ```
   This will scan the configured directory, generate a report, and display it.

2. **Preview Archive Operation** (dry run):
   ```bash
   python src/main.py --dry-run
   ```
   Shows what would be archived without actually moving files.

3. **Generate Report Only**:
   ```bash
   python src/main.py --report-only
   ```
   Scans and generates a report without archiving any files.

4. **Find and Archive Large Files**:
   - Set `auto_archive: true` in `config.yaml`, or
   - Use the archive functionality programmatically

5. **Scan Custom Directory**:
   - Edit `config.yaml` to change `scan_directory`
   - Or set environment variable: `export SCAN_DIRECTORY=/path/to/scan`

6. **Custom Size Threshold**:
   - Edit `config.yaml` to change `size_threshold_mb`
   - Or set environment variable: `export SIZE_THRESHOLD_MB=200`

## Project Structure

```
large-file-finder/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore              # Git ignore rules
├── src/
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core file scanning, reporting, and archiving logic
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)
- **reports/**: Directory for report files (created automatically)

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- File size threshold detection
- Directory scanning (recursive and non-recursive)
- Exclusion logic
- Report generation
- File archiving (move and copy)
- Name conflict handling
- Error handling
- Dry run mode

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Scan directory does not exist`

**Solution**: Ensure the scan directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: `PermissionError` when scanning or archiving files

**Solution**: Ensure you have read permissions to scan directories and write permissions to the archive directory. On Linux/Mac, you may need to use `sudo` or adjust directory permissions.

---

**Issue**: Files not being found despite being large

**Solution**: 
- Check that the file size exceeds the threshold (in MB)
- Verify the file is not in an excluded directory
- Ensure recursive scanning is enabled if files are in subdirectories
- Check that you have read permissions to the directory

---

**Issue**: Archive operation fails

**Solution**:
- Verify archive directory exists or `create_archive_directory` is enabled
- Check write permissions to archive directory
- Ensure sufficient disk space in archive location
- Review error messages in logs for specific issues

---

**Issue**: Report file not generated

**Solution**: The report is printed to console by default. To save to file, use `--output` option or configure `report_file` in `config.yaml`. Ensure the reports directory is writable.

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Scan directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Error archiving file"**: Check file permissions, disk space, and archive directory accessibility
- **"Error accessing file"**: File may be locked by another process or permissions may be insufficient

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov`
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

This project is provided as-is for educational and personal use.
