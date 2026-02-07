# File Metadata Exporter

Generate a detailed file list with metadata including size, dates, permissions, and checksums exported to CSV format. This tool helps catalog files, track changes, verify integrity, and analyze file distributions.

## Project Description

File Metadata Exporter solves the problem of cataloging and documenting file collections by automatically scanning directories, extracting comprehensive metadata from each file, and exporting the information to a structured CSV format. This is useful for file audits, integrity verification, backup documentation, and file management.

**Target Audience**: System administrators, developers, archivists, data managers, and anyone who needs to catalog and document file collections with detailed metadata.

## Features

- **Comprehensive Metadata**: Extract size, dates (created, modified, accessed), permissions, and checksums
- **Multiple Checksum Algorithms**: Support for MD5, SHA1, and SHA256 checksums
- **CSV Export**: Export all metadata to CSV format for easy analysis
- **Recursive Scanning**: Scan directories and subdirectories recursively
- **Extension Filtering**: Filter files by extension (optional)
- **Permission Details**: Detailed file permission information (readable, writable, executable)
- **Platform Support**: Works on Windows, Linux, and macOS
- **Large File Support**: Efficiently handles large files with chunked reading
- **Error Handling**: Graceful handling of permission errors and inaccessible files
- **Comprehensive Logging**: Log all operations for audit and debugging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read access to files you want to scan

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/file-metadata-exporter
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

Edit `config.yaml` to customize metadata extraction and export settings:

```yaml
source:
  directory: "/path/to/files"

checksum:
  enabled: true
  algorithms: ["md5", "sha1"]
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source**: Directory to scan and recursive option
- **metadata**: Additional metadata to include (owner, group, inode, device)
- **checksum**: Checksum calculation settings (algorithms, chunk size)
- **include**: File extensions to include (empty = all)
- **skip**: Patterns and directories to skip during scanning
- **export**: CSV export settings (output file, encoding)
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory
- `OUTPUT_FILE`: Override output CSV file path

### Example Configuration

```yaml
source:
  directory: "/home/user/documents"
  recursive: true

metadata:
  include_owner: true
  include_group: true

checksum:
  enabled: true
  algorithms: ["md5", "sha1", "sha256"]
  chunk_size: 8192

export:
  output_file: "data/file_metadata.csv"
```

## Usage

### Basic Usage

Scan directory and export metadata to CSV:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Scan specific directory
python src/main.py -d /path/to/directory

# Specify output CSV file
python src/main.py -o /path/to/output.csv

# Combine options
python src/main.py -d /home/user -o metadata.csv

# Don't print summary
python src/main.py --no-summary
```

### Common Use Cases

1. **Catalog Directory**:
   ```bash
   python src/main.py -d /path/to/directory
   ```

2. **Export with Custom Output**:
   ```bash
   python src/main.py -d /path/to/directory -o my_metadata.csv
   ```

3. **Generate Checksums Only**:
   - Edit `checksum.algorithms` in `config.yaml`
   - Run: `python src/main.py -d /path/to/directory`

4. **Filter by Extension**:
   - Edit `include.extensions` in `config.yaml`
   - Example: `[".txt", ".pdf", ".jpg"]`

5. **Include Owner/Group** (Unix/Linux/macOS):
   - Set `metadata.include_owner: true` in `config.yaml`
   - Set `metadata.include_group: true` in `config.yaml`

## Project Structure

```
file-metadata-exporter/
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
├── data/
│   └── file_metadata.csv   # Generated CSV file
└── logs/
    ├── .gitkeep            # Log directory placeholder
    └── metadata_exporter.log  # Application logs
```

### File Descriptions

- **src/main.py**: Core metadata extraction, checksum calculation, and CSV export
- **config.yaml**: YAML configuration file with extraction and export settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/file_metadata.csv**: Generated CSV file with file metadata
- **logs/metadata_exporter.log**: Application log file with rotation

## CSV Output Format

The CSV file includes the following columns (depending on configuration):

### Standard Columns

- **path**: Full file path
- **name**: File name
- **directory**: Directory containing file
- **extension**: File extension
- **size_bytes**: File size in bytes
- **size_kb**: File size in kilobytes
- **size_mb**: File size in megabytes
- **created**: Creation timestamp (ISO format)
- **modified**: Modification timestamp (ISO format)
- **accessed**: Access timestamp (ISO format)

### Permission Columns

- **mode_octal**: File permissions in octal format
- **mode_readable**: File permissions in readable format (e.g., -rw-r--r--)
- **is_readable**: File is readable
- **is_writable**: File is writable
- **is_executable**: File is executable
- **owner_read**, **owner_write**, **owner_execute**: Owner permissions (Unix/Linux/macOS)
- **group_read**, **group_write**, **group_execute**: Group permissions (Unix/Linux/macOS)
- **other_read**, **other_write**, **other_execute**: Other permissions (Unix/Linux/macOS)

### Checksum Columns

- **checksum_md5**: MD5 checksum (if enabled)
- **checksum_sha1**: SHA1 checksum (if enabled)
- **checksum_sha256**: SHA256 checksum (if enabled)

### Optional Columns

- **owner**: File owner (if enabled, Unix/Linux/macOS)
- **group**: File group (if enabled, Unix/Linux/macOS)
- **inode**: Inode number (if enabled)
- **device**: Device number (if enabled)

## Checksum Calculation

### Supported Algorithms

- **MD5**: Fast, widely used, 128-bit hash
- **SHA1**: Secure, 160-bit hash
- **SHA256**: More secure, 256-bit hash

### Performance

- Files are read in chunks to handle large files efficiently
- Chunk size is configurable (default: 8192 bytes)
- Multiple algorithms can be calculated simultaneously

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
- Metadata extraction
- Checksum calculation
- Permission extraction
- CSV export
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Directory not found`

**Solution**: Verify the directory path exists and is accessible. Use absolute paths for best results.

---

**Issue**: `PermissionError` when accessing files

**Solution**: 
- Ensure you have read permissions for files
- Some system files may require elevated permissions
- Check logs for specific permission errors

---

**Issue**: Checksum calculation is slow

**Solution**: 
- Reduce number of algorithms in `checksum.algorithms`
- Increase `checksum.chunk_size` for faster processing
- Use only MD5 for faster checksums

---

**Issue**: CSV file is too large

**Solution**: 
- Use extension filtering to limit file types
- Add skip patterns for unnecessary directories
- Process directories separately

---

**Issue**: Missing owner/group information

**Solution**: 
- Owner/group information is only available on Unix/Linux/macOS
- Enable `metadata.include_owner` and `metadata.include_group` in config.yaml
- Requires appropriate file permissions

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Directory not found"**: Verify source directory path exists
- **"Path is not a directory"**: Ensure the path points to a directory, not a file
- **"No metadata to export"**: No files found matching criteria

## Performance Considerations

- **Large Files**: Checksum calculation for very large files can take time
- **Many Files**: Processing thousands of files may take significant time
- **Multiple Algorithms**: Calculating multiple checksums increases processing time
- **Network Drives**: Scanning files on network drives may be slower

## Security Considerations

- **File Permissions**: Tool requires read access to files
- **CSV Content**: CSV files may contain sensitive file paths - review before sharing
- **Checksums**: Use checksums to verify file integrity and detect changes
- **Large Datasets**: CSV files for large directories can be very large

## Use Cases

1. **File Cataloging**: Create comprehensive catalogs of file collections
2. **Integrity Verification**: Use checksums to verify file integrity over time
3. **Backup Documentation**: Document files before backup or migration
4. **Change Detection**: Compare CSV exports to detect file changes
5. **Audit**: Generate file inventories for compliance and auditing
6. **Analysis**: Analyze file distributions, sizes, and types using spreadsheet tools

## CSV Analysis

The generated CSV file can be opened in:

- **Excel**: Microsoft Excel
- **Google Sheets**: Google Sheets
- **LibreOffice Calc**: LibreOffice Calc
- **Python pandas**: For programmatic analysis
- **Any CSV viewer**: Standard CSV format

### Example Analysis

```python
import pandas as pd

# Load CSV
df = pd.read_csv('data/file_metadata.csv')

# Analyze file sizes
print(df['size_mb'].describe())

# Group by extension
print(df.groupby('extension')['size_bytes'].sum())

# Find largest files
print(df.nlargest(10, 'size_bytes')[['path', 'size_mb']])
```

## Automation

You can automate the exporter using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Export metadata daily at 2 AM
0 2 * * * cd /path/to/file-metadata-exporter && /path/to/venv/bin/python src/main.py -d /path/to/scan
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
