# Text File Processor

Process text files by removing extra whitespace, normalizing line endings, and standardizing encoding to UTF-8. This tool helps clean and standardize text files for consistent formatting and encoding across your project.

## Project Description

Text File Processor solves the problem of inconsistent text file formatting and encoding by automatically processing text files to remove extra whitespace, normalize line endings (Unix/Windows/Mac), and convert all files to UTF-8 encoding. This ensures consistency across different operating systems and text editors.

**Target Audience**: Developers, content creators, system administrators, and anyone who needs to standardize text file formatting and encoding across multiple files.

## Features

- **Whitespace Removal**: Remove trailing/leading whitespace and normalize multiple spaces
- **Line Ending Normalization**: Convert line endings to Unix (\n), Windows (\r\n), or Mac (\r) format
- **Encoding Standardization**: Convert all files to UTF-8 encoding with automatic detection
- **Recursive Processing**: Process directories and subdirectories recursively
- **Backup Creation**: Automatically create backups before processing
- **Extension Filtering**: Process specific file types or all text files
- **Skip Patterns**: Configure patterns and directories to skip
- **In-Place or Output Directory**: Process files in-place or save to separate directory
- **Detailed Logging**: Comprehensive logging of all operations

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read/write access to files you want to process

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/text-file-processor
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

Edit `config.yaml` to customize processing settings:

```yaml
input:
  directory: "/path/to/text/files"
  recursive: true

processing:
  line_ending: "unix"
  remove_trailing_whitespace: true
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **input**: Directory to process and recursive option
- **output**: In-place processing or output directory settings
- **processing**: Encoding detection, line ending, and whitespace options
- **include**: File extensions to process (empty = common text files)
- **skip**: Patterns and directories to skip
- **backup**: Backup creation settings
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `INPUT_DIRECTORY`: Override input directory
- `OUTPUT_DIRECTORY`: Override output directory
- `BACKUP_ENABLED`: Enable/disable backups ("true" or "false")

### Example Configuration

```yaml
input:
  directory: "/home/user/documents"
  recursive: true

processing:
  line_ending: "unix"
  remove_trailing_whitespace: true
  normalize_spaces: true
  remove_empty_lines: false

include:
  extensions: [".txt", ".md", ".py"]

backup:
  enabled: true
  directory: "backups"
```

## Usage

### Basic Usage

Process all text files in configured directory:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Process specific directory
python src/main.py -d /path/to/directory

# Process single file
python src/main.py -f /path/to/file.txt

# Disable backup creation
python src/main.py --no-backup

# Don't print summary
python src/main.py --no-summary

# Combine options
python src/main.py -d /home/user/docs -f file.txt --no-backup
```

### Common Use Cases

1. **Process Directory Recursively**:
   ```bash
   python src/main.py -d /path/to/directory
   ```

2. **Process Single File**:
   ```bash
   python src/main.py -f document.txt
   ```

3. **Process Without Backup**:
   ```bash
   python src/main.py -d /path/to/directory --no-backup
   ```

4. **Process Specific File Types**:
   - Edit `include.extensions` in `config.yaml`
   - Example: `[".txt", ".md", ".py"]`

5. **Normalize to Windows Line Endings**:
   - Edit `processing.line_ending` in `config.yaml`
   - Set to `"windows"`

## Project Structure

```
text-file-processor/
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
├── backups/                # Backup files (created automatically)
├── processed/              # Processed files (if not in-place)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    └── text_processor.log  # Application logs
```

### File Descriptions

- **src/main.py**: Core text processing, encoding detection, whitespace removal, and line ending normalization
- **config.yaml**: YAML configuration file with processing settings
- **tests/test_main.py**: Unit tests for core functionality
- **backups/**: Directory containing file backups before processing
- **logs/text_processor.log**: Application log file with rotation

## Processing Options

### Whitespace Removal

Configure whitespace processing:

```yaml
processing:
  remove_trailing_whitespace: true   # Remove trailing spaces
  remove_leading_whitespace: false   # Remove leading spaces
  normalize_spaces: true             # Multiple spaces -> single space
  remove_empty_lines: false          # Remove empty lines
  remove_trailing_newlines: false    # Remove trailing newlines
```

### Line Ending Normalization

Normalize line endings to consistent format:

- **unix**: `\n` (Linux, macOS)
- **windows**: `\r\n` (Windows)
- **mac**: `\r` (Old Mac OS)

```yaml
processing:
  line_ending: "unix"  # Options: "unix", "windows", "mac"
```

### Encoding Detection

The processor automatically detects file encoding using this order:

1. UTF-8
2. Latin-1 (ISO-8859-1)
3. CP1252 (Windows-1252)
4. ISO-8859-1

All files are converted to UTF-8 after processing.

## Backup System

Backups are created automatically before processing:

- **Location**: Configured in `backup.directory` (default: "backups")
- **Structure**: Preserves original directory structure
- **Disable**: Use `--no-backup` flag or set `backup.enabled: false`

## Extension Filtering

Filter files by extension:

```yaml
include:
  extensions: [".txt", ".md", ".py"]
```

- Empty list processes common text files (.txt, .md, .py, .js, .html, .css, .json, .xml, .yaml, .yml)
- Specify extensions to process only those file types

## Skip Patterns

Configure patterns and directories to skip:

```yaml
skip:
  patterns:
    - ".git"
    - "__pycache__"
    - "node_modules"
  directories:
    - ".git"
    - "node_modules"
```

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
- Encoding detection and conversion
- Whitespace removal
- Line ending normalization
- File processing
- Backup creation
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Directory not found`

**Solution**: Verify the directory path exists and is accessible. Use absolute paths for best results.

---

**Issue**: `PermissionError` or access denied errors

**Solution**: 
- Ensure you have read/write permissions for files and directories
- Check that backup directory is writable
- Some system files may require elevated permissions

---

**Issue**: Encoding detection fails

**Solution**: 
- Check that file is actually a text file
- Add additional encodings to `encoding_detection_order` in config
- Files with binary content may fail encoding detection

---

**Issue**: Files are corrupted after processing

**Solution**: 
- Check backups in the backup directory
- Verify file is a text file, not binary
- Review processing options in config.yaml
- Check logs for specific errors

---

**Issue**: Too many files being processed

**Solution**: 
- Use `include.extensions` to filter by file type
- Add skip patterns for directories you don't want processed
- Use `recursive: false` to process only top-level directory

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Directory not found"**: Verify input directory path exists
- **"Path is not a directory"**: Ensure the path points to a directory, not a file
- **"Encoding detection failed"**: File may be binary or use unsupported encoding

## Performance Considerations

- **Large Files**: Very large text files may take time to process
- **Many Files**: Processing thousands of files may take significant time
- **Backup Creation**: Backups add processing time but provide safety
- **Recursive Processing**: Deep directory trees take longer to process

## Security Considerations

- **Backups**: Backups preserve original files - ensure backup directory is secure
- **Permissions**: Tool requires read/write access to files
- **Binary Files**: Tool is designed for text files - processing binary files may corrupt them
- **System Files**: Be cautious when processing system directories

## Automation

You can automate the processor using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Process directory daily at 2 AM
0 2 * * * cd /path/to/text-file-processor && /path/to/venv/bin/python src/main.py -d /path/to/documents
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
