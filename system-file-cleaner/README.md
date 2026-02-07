# System File Cleaner

Identify and optionally remove system files and hidden files based on naming patterns and attributes. This tool helps clean up unnecessary system and hidden files from directories while providing safety features to prevent accidental deletion of important files.

## Project Description

System File Cleaner solves the problem of identifying and managing system files and hidden files that accumulate in directories. It can identify these files based on naming patterns (like `.DS_Store`, `Thumbs.db`, files starting with `.`) and file attributes (Windows hidden attribute), with optional removal capabilities and comprehensive safety features.

**Target Audience**: System administrators, developers, users managing disk space, and anyone who needs to identify and clean system/hidden files from directories.

## Features

- **Pattern-Based Identification**: Identify system and hidden files using configurable naming patterns
- **Attribute-Based Detection**: Detect hidden files by file attributes (Windows)
- **Platform-Aware**: Different patterns for Windows, Linux, and macOS
- **Safe Removal**: Dry-run mode and protected file lists prevent accidental deletion
- **Recursive Scanning**: Scan directories and subdirectories recursively
- **Detailed Reports**: Generate comprehensive reports of found files
- **Comprehensive Logging**: Log all operations for audit and debugging
- **Configurable**: YAML-based configuration with extensive customization options

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read access to directories you want to scan
- Write access if removing files (optional)

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/system-file-cleaner
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

Edit `config.yaml` to customize file patterns and settings:

```yaml
patterns:
  system_name_patterns:
    - "thumbs.db"
    - ".ds_store"
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **scan**: Directory to scan and recursive option
- **patterns**: File naming patterns for system and hidden files
- **skip**: Patterns and directories to skip during scanning
- **protected**: Files and paths that should never be removed
- **removal**: Removal settings including dry-run mode
- **report**: Report generation settings
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SCAN_DIRECTORY`: Override scan directory
- `DRY_RUN`: Enable/disable dry-run mode ("true" or "false")

### Example Configuration

```yaml
scan:
  directory: "/home/user/documents"
  recursive: true

patterns:
  system_name_patterns:
    - "thumbs.db"
    - ".ds_store"
  hidden_name_patterns:
    - "~$"
    - ".tmp"

protected:
  patterns:
    - "config.yaml"
    - ".env"
  paths: []

removal:
  dry_run: true
```

## Usage

### Basic Usage

Scan directory for system and hidden files (dry-run by default):

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Scan specific directory
python src/main.py -d /path/to/directory

# Remove identified files (still in dry-run mode)
python src/main.py --remove

# Actually remove files (disable dry-run)
python src/main.py --remove --dry-run=false

# Generate report
python src/main.py -r report.txt

# Combine options
python src/main.py -d /home/user -r --report report.txt
```

### Common Use Cases

1. **Scan Directory (Dry-Run)**:
   ```bash
   python src/main.py -d /path/to/directory
   ```

2. **Scan and Remove (Dry-Run)**:
   ```bash
   python src/main.py -d /path/to/directory --remove
   ```

3. **Actually Remove Files**:
   ```bash
   python src/main.py -d /path/to/directory --remove --dry-run=false
   ```

4. **Generate Report Only**:
   ```bash
   python src/main.py -d /path/to/directory --report report.txt --no-summary
   ```

5. **Custom Patterns**:
   - Edit `patterns` section in `config.yaml`
   - Add custom system or hidden file patterns

## Project Structure

```
system-file-cleaner/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation
├── data/                   # Data directory
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── system_file_cleaner.log  # Application logs
    └── system_file_report.txt    # Generated reports
```

### File Descriptions

- **src/main.py**: Core file identification, pattern matching, and removal functionality
- **config.yaml**: YAML configuration file with patterns and settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/system_file_cleaner.log**: Application log file with rotation
- **logs/system_file_report.txt**: Generated report files

## File Identification

### System Files

System files are identified by:

1. **Name Patterns**: Files matching configured system file name patterns
2. **Extension Patterns**: Files with system file extensions
3. **Platform-Specific Patterns**: Windows, Linux, or macOS-specific patterns
4. **Directory Patterns**: Files in system directories (Windows)

### Hidden Files

Hidden files are identified by:

1. **Name Patterns**: Files starting with `.` (Unix/Linux/macOS) or matching hidden patterns
2. **File Attributes**: Files with hidden attribute set (Windows)
3. **Custom Patterns**: Additional hidden file name patterns

### Common System Files

Examples of files typically identified:

- **Windows**: `Thumbs.db`, `desktop.ini`, `~$*.doc`
- **macOS**: `.DS_Store`, `.localized`, `.Trashes`
- **Linux**: `.directory`, `.fuse_hidden*`
- **Cross-platform**: Files starting with `.`, temporary files

## Safety Features

### Protected Files

Files matching protected patterns or paths are never removed:

```yaml
protected:
  patterns:
    - "config.yaml"
    - ".env"
  paths:
    - "/important/path"
```

### Dry-Run Mode

By default, the tool runs in dry-run mode, simulating removal without actually deleting files. Use `--dry-run=false` to actually remove files.

### Skip Patterns

Configure patterns and directories to skip:

```yaml
skip:
  patterns:
    - ".git"
    - "__pycache__"
  directories:
    - ".git"
    - "node_modules"
```

## Report Format

Reports include:

- **Statistics**: Files scanned, found, removed, skipped, errors
- **System Files**: List of identified system files with details
- **Hidden Files**: List of identified hidden files with details
- **Removal Status**: Whether each file was removed or skipped

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- File identification logic
- Pattern matching
- Hidden file detection
- System file detection
- Removal functionality
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Directory not found`

**Solution**: Verify the directory path exists and is accessible. Use absolute paths for best results.

---

**Issue**: `PermissionError` when removing files

**Solution**: 
- Ensure you have write permissions for files
- Some system files may require elevated permissions
- Check logs for specific permission errors

---

**Issue**: Files not being identified

**Solution**: 
- Check that file patterns in config.yaml match your files
- Verify file naming conventions (case sensitivity)
- Check skip patterns aren't excluding desired files
- Review logs for identification details

---

**Issue**: Important files being identified for removal

**Solution**: 
- Add files to `protected.patterns` in config.yaml
- Add paths to `protected.paths` in config.yaml
- Review identified files before removing
- Always use dry-run mode first

---

**Issue**: Too many files being identified

**Solution**: 
- Refine patterns in config.yaml to be more specific
- Add more skip patterns
- Use protected patterns to exclude important files
- Review and adjust pattern matching logic

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Directory not found"**: Verify scan directory path exists
- **"Path is not a directory"**: Ensure the path points to a directory, not a file
- **"Permission denied"**: Check file permissions and access rights

## Security Considerations

- **Protected Files**: Always configure protected patterns for important files
- **Dry-Run Default**: Tool defaults to dry-run mode for safety
- **Backup**: Consider backing up directories before removing files
- **System Files**: Be cautious when removing system files - some may be needed
- **Permissions**: Tool requires appropriate file permissions

## Performance Considerations

- **Large Directories**: Scanning very large directory trees can take time
- **Recursive Scanning**: Disable recursive scanning for faster results on top-level only
- **Skip Patterns**: Use skip patterns to exclude unnecessary directories
- **Network Drives**: Scanning network drives may be slower than local drives

## Platform-Specific Notes

### Windows

- Uses file attributes to detect hidden files (requires win32file if available)
- Identifies Windows-specific system files (Thumbs.db, desktop.ini)
- Checks for system directories

### Linux/macOS

- Detects hidden files by name (starting with `.`)
- Identifies Unix-specific system files (.DS_Store, .localized)
- Uses name-based detection for hidden files

## Automation

You can automate the cleaner using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Scan directory weekly (dry-run)
0 2 * * 0 cd /path/to/system-file-cleaner && /path/to/venv/bin/python src/main.py -d /path/to/scan
```

### Windows (Task Scheduler)

- Create a task to run `python src/main.py -d C:\Users\YourName\Documents`
- Set working directory to project folder
- Use full path to Python executable

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-mock pytest-cov`
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
