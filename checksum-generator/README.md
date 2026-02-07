# Checksum Generator

Generate MD5 or SHA256 checksums for all files in a directory and save results to a CSV file with file paths and hash values. Perfect for file integrity verification, duplicate detection, and creating file catalogs.

## Project Description

Checksum Generator solves the problem of verifying file integrity and detecting duplicates by generating cryptographic hashes (MD5 or SHA256) for all files in a directory. Results are saved to a CSV file for easy analysis, comparison, and reference. Ideal for data integrity checks, backup verification, and file cataloging.

**Target Audience**: System administrators, data managers, developers, and anyone who needs to verify file integrity or create file catalogs with checksums.

## Features

- **Multiple Hash Algorithms**: Support for MD5 and SHA256
- **CSV Export**: Saves checksums to CSV with file paths and hash values
- **Recursive Scanning**: Processes files in subdirectories
- **Efficient Processing**: Reads files in chunks for large file support
- **File Filtering**: Exclude directories, patterns, and extensions
- **Minimum File Size**: Skip files below specified size threshold
- **Comprehensive Logging**: Detailed logs of all operations
- **Error Handling**: Gracefully handles inaccessible files
- **Statistics Tracking**: Reports files scanned, checksums generated, errors

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read permissions to files being processed

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/checksum-generator
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

Edit `config.yaml` to set your scan directory and hash algorithm:

```yaml
scan_directory: ~/Documents
hash_algorithm: sha256
output_file: checksums.csv
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **scan_directory**: Directory to scan for files
- **output_file**: Path to output CSV file
- **hash_algorithm**: Hash algorithm to use (md5 or sha256)
- **chunk_size**: Size of chunks for reading files (default: 8192 bytes)
- **min_file_size_bytes**: Minimum file size to process (0 = no minimum)
- **exclusions**: Configuration for excluding files
  - **directories**: Directories to exclude
  - **patterns**: Patterns to match in filenames
  - **extensions**: File extensions to exclude
- **operations**: Operation settings
  - **recursive**: Scan subdirectories recursively
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SCAN_DIRECTORY`: Override scan directory path
- `OUTPUT_FILE`: Override output CSV file path
- `HASH_ALGORITHM`: Override hash algorithm (md5 or sha256)

### Example Configuration

```yaml
scan_directory: ~/Documents
output_file: document_checksums.csv
hash_algorithm: sha256
chunk_size: 8192
min_file_size_bytes: 0

exclusions:
  directories:
    - .git
    - node_modules
  patterns:
    - .DS_Store
  extensions:
    - .tmp

operations:
  recursive: true
```

## Usage

### Basic Usage

Generate checksums with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Specify output file (overrides config)
python src/main.py -o my_checksums.csv

# Use MD5 instead of SHA256
python src/main.py --algorithm md5

# Combine options
python src/main.py -c config.yaml -o output.csv --algorithm sha256
```

### Common Use Cases

1. **Generate SHA256 Checksums**:
   ```bash
   python src/main.py
   ```
   Creates checksums.csv with SHA256 hashes.

2. **Generate MD5 Checksums**:
   ```bash
   python src/main.py --algorithm md5
   ```
   Faster but less secure than SHA256.

3. **Custom Output Location**:
   ```bash
   python src/main.py -o ~/Documents/file_checksums.csv
   ```

4. **Scan Specific Directory**:
   - Edit `scan_directory` in `config.yaml`
   - Or set environment variable: `export SCAN_DIRECTORY=/path/to/scan`

5. **Exclude Large Directories**:
   - Add directories to `exclusions.directories` in config
   - Common exclusions: `.git`, `node_modules`, `venv`

## Project Structure

```
checksum-generator/
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

- **src/main.py**: Core checksum generation logic and CSV export
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)
- **checksums.csv**: Generated CSV file with checksums (created when script runs)

## CSV Output Format

The generated CSV file contains the following columns:

- **file_path**: Relative path from scan directory
- **absolute_path**: Absolute file path
- **checksum**: MD5 or SHA256 hash value
- **algorithm**: Hash algorithm used (MD5 or SHA256)
- **file_size**: File size in bytes

Example CSV row:

```csv
file_path,absolute_path,checksum,algorithm,file_size
document.pdf,/Users/user/Documents/document.pdf,a1b2c3d4e5f6...,SHA256,1048576
```

## Hash Algorithms

### MD5
- **Speed**: Faster
- **Security**: Less secure (collision vulnerabilities)
- **Use Case**: Quick checksums, non-security applications
- **Output**: 32 hexadecimal characters

### SHA256
- **Speed**: Slower but still fast
- **Security**: Cryptographically secure
- **Use Case**: Security-sensitive applications, file integrity verification
- **Output**: 64 hexadecimal characters

## Performance Considerations

- **Large Files**: Files are read in chunks (default: 8KB) for memory efficiency
- **Many Files**: Processing time increases with number of files
- **Algorithm Choice**: MD5 is faster but SHA256 is more secure
- **Exclusions**: Configure exclusions to skip unnecessary files and improve speed

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
- Checksum calculation (MD5 and SHA256)
- File processing and filtering
- CSV export functionality
- Error handling
- Exclusion logic

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Scan directory does not exist`

**Solution**: Ensure the scan directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: Checksum generation is slow

**Solution**:
- Use MD5 for faster processing (less secure)
- Increase `chunk_size` for very large files
- Add more exclusions to skip unnecessary files
- Process smaller directories

---

**Issue**: `PermissionError` when reading files

**Solution**: Ensure you have read permissions to all files being processed. The script will skip inaccessible files and log errors.

---

**Issue**: CSV file not created

**Solution**:
- Check write permissions to output directory
- Verify disk space is available
- Review logs for specific error messages
- Ensure at least one file was processed successfully

---

**Issue**: Out of memory errors

**Solution**:
- Reduce `chunk_size` if set too high
- Process smaller directories
- Add more exclusions to skip large files
- Process files in batches

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Scan directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Unsupported hash algorithm"**: Use "md5" or "sha256" only
- **"Error calculating checksum"**: File may be locked, corrupted, or inaccessible

## Use Cases

1. **File Integrity Verification**: Generate checksums to verify files haven't been modified
2. **Duplicate Detection**: Compare checksums to find duplicate files
3. **Backup Verification**: Verify backup integrity by comparing checksums
4. **File Cataloging**: Create a catalog of files with their checksums
5. **Data Migration**: Verify files after migration

## Tips for Best Results

1. **Choose Appropriate Algorithm**: Use SHA256 for security, MD5 for speed
2. **Configure Exclusions**: Skip unnecessary files to improve performance
3. **Set Minimum File Size**: Skip very small files if not needed
4. **Review Logs**: Check logs after processing to identify any issues
5. **Backup CSV**: Keep CSV files as reference for future comparisons
6. **Process Incrementally**: For very large directories, process in batches

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

This project is provided as-is for educational and personal use.
