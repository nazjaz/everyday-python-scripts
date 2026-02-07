# File Size Finder

Find files within specified size ranges, useful for identifying unusually large or small files that may need attention. This tool helps you discover files that match your size criteria across directories, making it easy to locate files that are too large, too small, or within a specific size range.

## Project Description

File Size Finder solves the problem of locating files based on size criteria by recursively scanning directories and identifying files that match specified size ranges. This is particularly useful for disk space management, finding unusually large files that may be consuming excessive storage, or identifying suspiciously small files that might be corrupted or incomplete.

**Target Audience**: System administrators, developers, users managing disk space, and anyone who needs to identify files based on size criteria.

## Features

- **Recursive Directory Scanning**: Scan directories and subdirectories recursively
- **Flexible Size Criteria**: Specify minimum and maximum file sizes
- **Human-Readable Size Format**: Support for bytes, KB, MB, GB, TB units
- **Extension Filtering**: Filter files by extension (optional)
- **Skip Patterns**: Configure patterns and directories to skip (e.g., .git, node_modules)
- **Detailed Reports**: Generate comprehensive text reports with file details
- **Statistics Summary**: View summary statistics including total size and file count
- **Error Handling**: Gracefully handle permission errors and inaccessible files
- **Configurable**: YAML-based configuration with command-line overrides

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read access to directories you want to scan

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/file-size-finder
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

Edit `config.yaml` to customize search settings:

```yaml
search:
  directory: "/path/to/search"

size:
  min_bytes: 10485760  # 10MB
  max_bytes: 1073741824  # 1GB
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **search**: Directory to search and search options
- **size**: Minimum and maximum file size criteria (in bytes)
- **skip**: Patterns, directories, and paths to skip during search
- **include**: File extensions to include (empty = all)
- **report**: Report generation settings
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SEARCH_DIRECTORY`: Override search directory
- `MIN_SIZE`: Override minimum size (e.g., "10MB", "1GB")
- `MAX_SIZE`: Override maximum size (e.g., "100MB", "5GB")

### Example Configuration

```yaml
search:
  directory: "/home/user/documents"

size:
  min_bytes: 10485760  # 10MB minimum
  max_bytes: null  # No maximum

skip:
  patterns:
    - ".git"
    - "node_modules"
  directories:
    - ".git"

include:
  extensions: [".pdf", ".doc", ".docx"]
  include_no_extension: false

report:
  auto_save: true
  output_file: "logs/file_size_report.txt"
```

## Usage

### Basic Usage

Find files matching size criteria:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Search specific directory
python src/main.py -d /path/to/directory

# Set minimum size
python src/main.py --min-size 10MB

# Set maximum size
python src/main.py --max-size 1GB

# Set both min and max size
python src/main.py --min-size 1MB --max-size 100MB

# Save report to file
python src/main.py -r report.txt

# Don't print summary
python src/main.py --no-summary

# Combine options
python src/main.py -d /home/user -m 10MB -M 1GB -r report.txt
```

### Common Use Cases

1. **Find Large Files (over 100MB)**:
   ```bash
   python src/main.py --min-size 100MB
   ```

2. **Find Small Files (under 1KB)**:
   ```bash
   python src/main.py --max-size 1KB
   ```

3. **Find Files in Size Range**:
   ```bash
   python src/main.py --min-size 1MB --max-size 10MB
   ```

4. **Find Large Files in Specific Directory**:
   ```bash
   python src/main.py -d /home/user/downloads --min-size 50MB
   ```

5. **Generate Report Only**:
   ```bash
   python src/main.py --no-summary -r report.txt
   ```

## Project Structure

```
file-size-finder/
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
    ├── file_size_finder.log # Application logs
    └── file_size_report.txt # Generated reports
```

### File Descriptions

- **src/main.py**: Core file finding, size parsing, filtering, and report generation
- **config.yaml**: YAML configuration file with search and size criteria
- **tests/test_main.py**: Unit tests for core functionality
- **logs/file_size_finder.log**: Application log file with rotation
- **logs/file_size_report.txt**: Generated report files

## Size Format

Size values can be specified in multiple formats:

- **Bytes**: `1048576` or `1048576B`
- **Kilobytes**: `1024KB` or `1KB`
- **Megabytes**: `10MB` or `1.5MB`
- **Gigabytes**: `1GB` or `2.5GB`
- **Terabytes**: `1TB`

Examples:
- `10MB` = 10,485,760 bytes
- `1.5GB` = 1,610,612,736 bytes
- `500KB` = 512,000 bytes

## Skip Patterns

Configure patterns and directories to skip during search:

```yaml
skip:
  patterns:
    - ".git"
    - "__pycache__"
    - "node_modules"
  directories:
    - ".git"
    - "venv"
  excluded_paths:
    - "/specific/path/to/exclude"
```

Patterns are matched anywhere in the path, while directories are matched as directory names.

## Extension Filtering

Filter files by extension:

```yaml
include:
  extensions: [".pdf", ".doc", ".jpg", ".png"]
  include_no_extension: true
```

- Empty `extensions` list means all extensions are included
- `include_no_extension` controls whether files without extensions are included

## Report Format

Reports include:

- **Search Criteria**: Minimum and maximum size settings
- **Statistics**: Files found, total size, directories scanned, errors
- **File List**: Detailed list of matching files with:
  - File name
  - Full path
  - Size (formatted)
  - File extension

Files are sorted by size (largest first) by default.

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
- Size parsing and formatting
- File matching logic
- Skip pattern matching
- Extension filtering
- Report generation
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Directory not found`

**Solution**: Verify the directory path exists and is accessible. Use absolute paths for best results.

---

**Issue**: `PermissionError` or access denied errors

**Solution**: 
- Ensure you have read permissions for the directory
- Some system directories may require elevated permissions
- Check logs for specific files causing permission errors

---

**Issue**: `ValueError: Invalid size format`

**Solution**: 
- Use valid size format: number followed by unit (B, KB, MB, GB, TB)
- Examples: "10MB", "1.5GB", "500KB"
- Case insensitive

---

**Issue**: No files found when files should match

**Solution**: 
- Check size criteria (min/max) are correct
- Verify extension filters aren't excluding desired files
- Check skip patterns aren't excluding the directory
- Verify directory path is correct

---

**Issue**: Search is too slow

**Solution**: 
- Add more skip patterns to exclude unnecessary directories
- Use extension filtering to limit file types
- Search smaller directory trees
- Consider running during off-peak hours

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Directory not found"**: Verify search directory path exists
- **"Invalid size format"**: Use format like "10MB" or "1.5GB"
- **"Path is not a directory"**: Ensure the path points to a directory, not a file

## Performance Considerations

- **Large Directories**: Scanning very large directory trees can take time
- **Skip Patterns**: Use skip patterns to exclude unnecessary directories (e.g., node_modules, .git)
- **Extension Filtering**: Filter by extension to reduce files checked
- **Network Drives**: Scanning network drives may be slower than local drives

## Security Considerations

- **Permissions**: The tool requires read access to directories and files
- **Sensitive Data**: Reports may contain file paths - review before sharing
- **System Directories**: Be cautious when scanning system directories
- **Large Scans**: Scanning entire filesystems may take significant time

## Automation

You can automate the file finder using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Find large files daily at 2 AM
0 2 * * * cd /path/to/file-size-finder && /path/to/venv/bin/python src/main.py -d /home/user --min-size 100MB -r logs/daily_report.txt
```

### Windows (Task Scheduler)

- Create a task to run `python src/main.py -d C:\Users\YourName --min-size 100MB -r logs\report.txt`
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
