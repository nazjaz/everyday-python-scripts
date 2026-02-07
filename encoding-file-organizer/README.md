# Encoding File Organizer

Organize files by encoding type, detecting text file encodings and grouping files with the same encoding together. This tool helps organize text files based on their character encoding, making it easier to manage files with different encodings.

## Project Description

Encoding File Organizer solves the problem of managing text files with different encodings by automatically detecting file encodings and organizing files into encoding-based folders. This is useful for identifying encoding issues, standardizing file encodings, and organizing files for processing or migration.

**Target Audience**: Developers, system administrators, content managers, and anyone who needs to organize or analyze text files by their encoding type.

## Features

- **Encoding Detection**: Automatically detect text file encodings using multiple methods
- **Encoding-Based Grouping**: Group files with the same encoding together
- **Flexible Detection**: Support for chardet library or fallback detection methods
- **Text File Filtering**: Identify text files by extension or content analysis
- **Recursive Scanning**: Scan directories and subdirectories recursively
- **Organization Options**: Move files to encoding-based folders or generate reports
- **Preserve Structure Option**: Optionally preserve relative directory structure
- **Conflict Handling**: Handle file name conflicts with rename, skip, or overwrite
- **Detailed Reports**: Generate comprehensive reports with encoding statistics
- **Dry-Run Mode**: Simulate organization without actually moving files
- **Comprehensive Logging**: Log all operations for audit and debugging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read access to files you want to scan
- Write access if organizing files (optional)

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/encoding-file-organizer
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

**Optional**: For better encoding detection, install chardet:

```bash
pip install chardet
```

Then enable it in `config.yaml`:
```yaml
encoding_detection:
  use_chardet: true
```

### Step 4: Configure Settings

Edit `config.yaml` to customize organization settings:

```yaml
source:
  directory: "/path/to/text/files"

encoding_detection:
  use_chardet: true
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source**: Directory to scan and recursive option
- **text_file**: Text file extensions and content checking
- **encoding_detection**: Encoding detection method and settings
- **output**: Output directory and structure preservation settings
- **organization**: Encoding naming, conflict handling, and dry-run settings
- **skip**: Patterns and directories to skip during scanning
- **report**: Report generation settings
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory
- `OUTPUT_DIRECTORY`: Override output directory
- `DRY_RUN`: Enable/disable dry-run mode ("true" or "false")

### Example Configuration

```yaml
source:
  directory: "/home/user/documents"
  recursive: true

encoding_detection:
  use_chardet: true
  sample_size: 10000
  encoding_order:
    - "utf-8"
    - "latin-1"
    - "cp1252"

organization:
  dry_run: true
  encoding_naming:
    prefix: "Encoding"
    separator: "_"
    normalize_case: true
```

## Usage

### Basic Usage

Scan directory and group files by encoding (no organization):

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Scan specific directory
python src/main.py -d /path/to/directory

# Organize files by moving them to encoding folders
python src/main.py --organize

# Organize in dry-run mode (simulate)
python src/main.py --organize --dry-run

# Generate report
python src/main.py --report report.txt

# Combine options
python src/main.py -d /home/user -o --dry-run --report report.txt
```

### Common Use Cases

1. **Analyze Encoding Distribution**:
   ```bash
   python src/main.py -d /path/to/directory
   ```

2. **Organize Files by Encoding (Dry-Run)**:
   ```bash
   python src/main.py -d /path/to/directory --organize --dry-run
   ```

3. **Actually Organize Files**:
   ```bash
   python src/main.py -d /path/to/directory --organize
   ```

4. **Generate Report Only**:
   ```bash
   python src/main.py -d /path/to/directory --report report.txt --no-summary
   ```

5. **Custom Encoding Detection**:
   - Enable chardet in `encoding_detection.use_chardet`
   - Adjust `encoding_order` for priority encodings
   - Configure `sample_size` for detection accuracy

## Project Structure

```
encoding-file-organizer/
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
├── organized/              # Organized files (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── encoding_organizer.log  # Application logs
    └── encoding_report.txt     # Generated reports
```

### File Descriptions

- **src/main.py**: Core encoding detection, file scanning, and organization functionality
- **config.yaml**: YAML configuration file with encoding and organization settings
- **tests/test_main.py**: Unit tests for core functionality
- **organized/**: Directory containing files organized by encoding
- **logs/encoding_organizer.log**: Application log file with rotation
- **logs/encoding_report.txt**: Generated report files

## Encoding Detection

### Detection Methods

1. **chardet Library** (if enabled):
   - More accurate detection
   - Provides confidence scores
   - Handles various encodings well
   - Requires chardet package

2. **Fallback Method**:
   - Tries common encodings in order
   - Uses first encoding that successfully decodes file
   - No confidence scores
   - Works without additional dependencies

### Supported Encodings

Common encodings detected:

- **UTF-8**: Most common modern encoding
- **UTF-16**: Unicode 16-bit encoding
- **UTF-32**: Unicode 32-bit encoding
- **Latin-1 (ISO-8859-1)**: Western European
- **CP1252 (Windows-1252)**: Windows Western European
- **ASCII**: Basic ASCII encoding
- **ISO-8859-1**: Latin-1 variant

### Text File Detection

Files are identified as text files by:

1. **Extension Check**: Files with known text extensions
2. **Content Analysis**: Checking for null bytes and printable character ratio
3. **Configurable**: Can disable content checking for extension-only mode

## Organization

### Encoding-Based Folders

Files are organized into folders named by their encoding:

- **Default naming**: `Encoding_UTF-8`, `Encoding_LATIN-1`, etc.
- **Customizable**: Configure prefix, separator, and case normalization

### Organization Options

1. **Flat Organization**: Files moved to encoding folders with original names
2. **Preserve Structure**: Maintain relative directory structure within encoding folders
3. **Conflict Handling**: Rename, skip, or overwrite on name conflicts

### Output Structure

```
organized/
├── Encoding_UTF-8/
│   ├── file1.txt
│   └── file2.txt
├── Encoding_LATIN-1/
│   └── file3.txt
└── Encoding_UNKNOWN/
    └── file4.txt
```

## Report Format

Reports include:

- **Statistics**: Files scanned, processed, organized, skipped, errors, encodings found
- **Files by Encoding**: Detailed breakdown for each encoding:
  - Number of files
  - Total size
  - Average confidence (if using chardet)
  - File list (optional)
  - New paths (if organized)

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
- Encoding detection
- Text file identification
- File scanning
- Organization logic
- Conflict handling
- Report generation
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Directory not found`

**Solution**: Verify the directory path exists and is accessible. Use absolute paths for best results.

---

**Issue**: `PermissionError` when organizing files

**Solution**: 
- Ensure you have write permissions for output directory
- Check source file permissions
- Some files may require elevated permissions

---

**Issue**: Encoding detection fails or is inaccurate

**Solution**: 
- Enable chardet library for better detection: `pip install chardet`
- Set `encoding_detection.use_chardet: true` in config.yaml
- Increase `sample_size` for better accuracy
- Check that file is actually a text file

---

**Issue**: Binary files being processed

**Solution**: 
- Review `text_file.extensions` list
- Enable `text_file.check_content: true` for content-based filtering
- Add skip patterns for binary file directories

---

**Issue**: Too many files in "unknown" encoding

**Solution**: 
- Enable chardet library
- Add more encodings to `encoding_order` list
- Check if files are actually text files
- Review logs for detection errors

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Directory not found"**: Verify source directory path exists
- **"Path is not a directory"**: Ensure the path points to a directory, not a file
- **"Permission denied"**: Check file and directory permissions

## Performance Considerations

- **Large Files**: Encoding detection for very large files can take time
- **Many Files**: Processing thousands of files may take significant time
- **chardet Usage**: Using chardet is more accurate but slower than fallback method
- **Sample Size**: Larger sample sizes improve accuracy but increase processing time
- **Network Drives**: Scanning/moving files on network drives may be slower

## Security Considerations

- **File Permissions**: Tool requires appropriate read/write permissions
- **Backup**: Consider backing up directories before organizing
- **Dry-Run Default**: Tool defaults to dry-run mode for safety
- **Binary Files**: Tool is designed for text files - processing binary files may cause issues

## Use Cases

1. **Encoding Analysis**: Understand encoding distribution in file collections
2. **Encoding Standardization**: Organize files before converting to single encoding
3. **Migration Preparation**: Group files by encoding before migration
4. **Issue Detection**: Identify files with encoding problems
5. **Content Management**: Organize text files for processing pipelines

## Automation

You can automate the organizer using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Organize directory weekly (dry-run)
0 2 * * 0 cd /path/to/encoding-file-organizer && /path/to/venv/bin/python src/main.py -d /path/to/scan -o --dry-run
```

### Windows (Task Scheduler)

- Create a task to run `python src/main.py -d C:\Users\YourName\Documents -o --dry-run`
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
