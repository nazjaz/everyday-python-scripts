# Filename Sanitizer

Find files with special characters, spaces, or problematic characters in names and optionally rename them to filesystem-safe names. This tool helps ensure file compatibility across different operating systems and prevents issues with special characters.

## Project Description

Filename Sanitizer solves the problem of files with problematic characters in their names by identifying files with spaces, special characters, or other filesystem-unsafe elements, and optionally renaming them to safe alternatives. This ensures compatibility across Windows, Linux, and macOS filesystems.

**Target Audience**: System administrators, developers, users managing file collections, and anyone who needs to ensure filesystem compatibility and prevent issues with special characters in filenames.

## Features

- **Problematic Character Detection**: Identify files with spaces, special characters, or problematic names
- **Filesystem-Safe Renaming**: Generate and apply filesystem-safe filenames
- **Multiple Issue Detection**: Detect spaces, special chars, consecutive chars, reserved names, control characters
- **Configurable Rules**: Customize which characters are problematic and how to replace them
- **Dry-Run Mode**: Simulate renaming without actually renaming files
- **Conflict Handling**: Handle name conflicts with rename, skip, or overwrite options
- **Recursive Scanning**: Scan directories and subdirectories recursively
- **Extension Filtering**: Filter files by extension (optional)
- **Detailed Reports**: Generate comprehensive reports of problematic files
- **Comprehensive Logging**: Log all operations for audit and debugging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read/write access to files you want to scan and rename

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/filename-sanitizer
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

Edit `config.yaml` to customize sanitization rules:

```yaml
sanitization:
  remove_spaces: true
  problematic_chars: ["<", ">", ":", "/", "\\"]
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **scan**: Directory to scan and recursive option
- **sanitization**: Rules for detecting problematic characters
- **replacement**: Characters to use for replacements
- **renaming**: Renaming settings including dry-run and conflict handling
- **include**: File extensions to include (empty = all)
- **skip**: Patterns and directories to skip during scanning
- **report**: Report generation settings
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SCAN_DIRECTORY`: Override scan directory
- `DRY_RUN`: Enable/disable dry-run mode ("true" or "false")

### Example Configuration

```yaml
sanitization:
  remove_spaces: true
  remove_consecutive: true
  problematic_chars: ["<", ">", ":", "/", "\\", "|", "?"]

replacement:
  space_replacement: "_"
  char_replacement: "_"

renaming:
  dry_run: true
  conflicts:
    action: "rename"
```

## Usage

### Basic Usage

Find files with problematic names (dry-run by default):

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Scan specific directory
python src/main.py -d /path/to/directory

# Rename problematic files (still in dry-run mode)
python src/main.py --rename

# Actually rename files (disable dry-run)
python src/main.py --rename --dry-run=false

# Generate report
python src/main.py --report report.txt

# Combine options
python src/main.py -d /home/user -r --report report.txt
```

### Common Use Cases

1. **Find Problematic Files**:
   ```bash
   python src/main.py -d /path/to/directory
   ```

2. **Preview Renames (Dry-Run)**:
   ```bash
   python src/main.py -d /path/to/directory --rename
   ```

3. **Actually Rename Files**:
   ```bash
   python src/main.py -d /path/to/directory --rename --dry-run=false
   ```

4. **Generate Report Only**:
   ```bash
   python src/main.py -d /path/to/directory --report report.txt --no-summary
   ```

5. **Custom Sanitization Rules**:
   - Edit `sanitization` section in `config.yaml`
   - Add or remove problematic characters
   - Configure replacement characters

## Project Structure

```
filename-sanitizer/
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
    ├── filename_sanitizer.log  # Application logs
    └── sanitizer_report.txt    # Generated reports
```

### File Descriptions

- **src/main.py**: Core file detection, character analysis, and renaming functionality
- **config.yaml**: YAML configuration file with sanitization rules
- **tests/test_main.py**: Unit tests for core functionality
- **logs/filename_sanitizer.log**: Application log file with rotation
- **logs/sanitizer_report.txt**: Generated report files

## Problematic Characters

### Common Problematic Characters

The tool detects and handles:

- **Spaces**: Can cause issues in command-line and scripts
- **Special Characters**: `< > : " / \ | ? * [ ] { } ( ) & % $ # @ ! ~ ` ^ = + ; ,`
- **Reserved Names**: Windows reserved names (CON, PRN, AUX, COM1-9, LPT1-9)
- **Control Characters**: Non-printable control characters
- **Consecutive Special Characters**: Multiple special characters in a row
- **Leading/Trailing Special Characters**: Special chars at start or end of filename

### Filesystem Compatibility

Different filesystems have different restrictions:

- **Windows**: Cannot use `< > : " / \ | ? *` and reserved names
- **Linux/macOS**: Generally more permissive but spaces and special chars can cause issues
- **Cross-platform**: Using safe characters ensures compatibility

## Sanitization Rules

### Character Replacement

- **Spaces**: Replaced with configurable character (default: `_`)
- **Special Characters**: Replaced with configurable character (default: `_`)
- **Consecutive Special Characters**: Replaced with single character
- **Leading/Trailing Special Characters**: Removed

### Reserved Names

Windows reserved names are prefixed with underscore:
- `CON` → `_CON`
- `PRN` → `_PRN`
- `COM1` → `_COM1`

### Examples

- `My File (2024).txt` → `My_File_2024.txt`
- `Report: Q1/2024.pdf` → `Report_Q1_2024.pdf`
- `File<>Name|Test.doc` → `File_Name_Test.doc`
- `CON.txt` → `_CON.txt`

## Conflict Handling

When a sanitized name already exists:

- **rename**: Generate unique name by appending counter (default)
- **skip**: Skip renaming the file
- **overwrite**: Overwrite existing file (use with caution)

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
- Problematic character detection
- Filename sanitization
- File renaming
- Conflict handling
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Directory not found`

**Solution**: Verify the directory path exists and is accessible. Use absolute paths for best results.

---

**Issue**: `PermissionError` when renaming files

**Solution**: 
- Ensure you have write permissions for files
- Some system files may require elevated permissions
- Check logs for specific permission errors

---

**Issue**: Files not being detected as problematic

**Solution**: 
- Check that problematic characters are listed in `sanitization.problematic_chars`
- Verify file names actually contain problematic characters
- Review logs for detection details

---

**Issue**: Renamed files have unexpected names

**Solution**: 
- Review sanitization rules in `config.yaml`
- Check replacement character settings
- Test with dry-run mode first
- Review logs for renaming operations

---

**Issue**: Too many files being renamed

**Solution**: 
- Use extension filtering to limit file types
- Add skip patterns for directories you don't want processed
- Review files before renaming (use dry-run mode)

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Directory not found"**: Verify scan directory path exists
- **"Path is not a directory"**: Ensure the path points to a directory, not a file
- **"Permission denied"**: Check file permissions and access rights

## Performance Considerations

- **Large Directories**: Scanning very large directory trees can take time
- **Recursive Scanning**: Disable recursive scanning for faster results on top-level only
- **File Renaming**: Renaming many files can be slow - use dry-run first
- **Network Drives**: Scanning/renaming files on network drives may be slower

## Security Considerations

- **Backup**: Consider backing up directories before renaming files
- **Dry-Run Default**: Tool defaults to dry-run mode for safety
- **Permissions**: Tool requires read/write access to files
- **System Files**: Be cautious when renaming system or application files

## Use Cases

1. **Cross-Platform Compatibility**: Ensure files work on Windows, Linux, and macOS
2. **Script Compatibility**: Prepare files for use in shell scripts
3. **Web Upload**: Sanitize filenames before uploading to web servers
4. **Archive Preparation**: Clean filenames before archiving
5. **Migration**: Prepare files for migration between systems

## Automation

You can automate the sanitizer using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Scan directory weekly (dry-run)
0 2 * * 0 cd /path/to/filename-sanitizer && /path/to/venv/bin/python src/main.py -d /path/to/scan
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
