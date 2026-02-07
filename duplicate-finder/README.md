# Duplicate File Finder

A command-line tool for finding duplicate files by comparing file hashes. Groups duplicate files, calculates space wasted, and generates reports with recommendations for which files to keep or delete.

## Project Description

Duplicate File Finder solves the problem of identifying duplicate files in your file system by using cryptographic hashes to compare file contents. It helps users free up disk space by identifying duplicate files and providing intelligent recommendations on which files to keep based on various criteria such as file age, path length, and directory priority.

**Target Audience**: Users who need to clean up duplicate files, free disk space, or organize their file systems by identifying and removing redundant files.

## Features

- **Hash-based Detection**: Uses MD5, SHA1, or SHA256 hashes to identify identical files
- **Efficient Scanning**: Processes large files in chunks to minimize memory usage
- **Flexible Filtering**: Exclude files and directories by patterns or size limits
- **Intelligent Recommendations**: Suggests which files to keep based on age, path, or directory priority
- **Multiple Report Formats**: Generate reports in JSON, TXT, or CSV format
- **Space Calculation**: Calculates total space wasted by duplicates
- **Recursive Scanning**: Scan directories and subdirectories
- **Comprehensive Logging**: Detailed logs of all operations
- **Configurable**: Fully customizable via YAML configuration file

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/duplicate-finder
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

Edit `config.yaml` to customize scan directories and options:

```yaml
scan_directories:
  - downloads
  - documents
hash_algorithm: md5
min_file_size: 0
max_file_size: 0
```

## Usage

### Basic Usage

Find duplicates in configured directories:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Scan specific directories
python src/main.py -d /path/to/dir1 /path/to/dir2

# Non-recursive scan
python src/main.py --no-recursive

# Specify output file
python src/main.py -o /path/to/report.json

# Specify report format
python src/main.py --format txt

# Use SHA256 hash algorithm
python src/main.py --hash sha256

# Use custom configuration file
python src/main.py -c /path/to/config.yaml
```

### Common Use Cases

**Find duplicates in Downloads folder**:
```bash
python src/main.py -d ~/Downloads
```

**Generate text report**:
```bash
python src/main.py --format txt -o duplicates.txt
```

**Scan with SHA256 (more secure, slower)**:
```bash
python src/main.py --hash sha256
```

**Non-recursive scan**:
```bash
python src/main.py --no-recursive
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

#### Scan Directories

```yaml
scan_directories:
  - downloads
  - documents
  - photos
```

#### Hash Algorithm

- `md5`: Fast, suitable for most use cases (default)
- `sha1`: More secure, slightly slower
- `sha256`: Most secure, slowest

#### File Size Limits

```yaml
min_file_size: 1024  # Skip files smaller than 1KB
max_file_size: 104857600  # Skip files larger than 100MB
```

#### Exclusion Patterns

```yaml
exclude_patterns:
  - '^\\.'  # Hidden files
  - '\\.tmp$'  # Temporary files
  - '\\.log$'  # Log files
```

#### Recommendations

```yaml
recommendations:
  keep_oldest: true  # Keep oldest file in duplicate group
  keep_shortest_path: false  # Keep file with shortest path
  keep_directories:  # Priority directories (files here kept first)
    - documents
    - important
```

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Report Formats

### JSON Report

Structured data format, suitable for programmatic processing:

```json
{
  "generated_at": "2024-01-15T10:30:00",
  "total_duplicate_groups": 5,
  "total_duplicate_files": 12,
  "total_space_wasted": 52428800,
  "duplicates": {...},
  "recommendations": {...}
}
```

### Text Report

Human-readable format with detailed information:

```
================================================================================
DUPLICATE FILE REPORT
================================================================================

Generated: 2024-01-15T10:30:00
Total duplicate groups: 5
Total duplicate files: 12
Total space wasted: 50.00 MB

Group 1 (Hash: a1b2c3d4e5f6g7h8...)
  File size: 1024.00 KB
  Duplicates: 3
  Space wasted: 2.00 MB

  KEEP:
    /path/to/file1.txt
    Modified: 2024-01-10T08:00:00

  DELETE:
    /path/to/file2.txt
    Modified: 2024-01-12T09:00:00
    ...
```

### CSV Report

Tabular format suitable for spreadsheet applications:

| Hash | Action | Path | Size (bytes) | Modified | Group Size | Space Wasted (bytes) |
|------|--------|------|--------------|----------|------------|----------------------|
| a1b2... | KEEP | /path/to/file1.txt | 1048576 | 2024-01-10T08:00:00 | 3 | 2097152 |
| a1b2... | DELETE | /path/to/file2.txt | 1048576 | 2024-01-12T09:00:00 | 3 | 2097152 |

## Project Structure

```
duplicate-finder/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Application configuration
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── data/
│   └── duplicate_report.json  # Generated reports
└── logs/
    └── duplicate_finder.log  # Application logs
```

## How It Works

1. **File Discovery**: Scans specified directories for files (recursively or not)
2. **Filtering**: Excludes files matching patterns or outside size limits
3. **Hash Calculation**: Calculates hash for each file using chosen algorithm
4. **Grouping**: Groups files with identical hashes (duplicates)
5. **Recommendations**: Generates recommendations on which files to keep
6. **Reporting**: Generates report in chosen format

## Recommendation Logic

The tool uses the following priority order to recommend which file to keep:

1. **Directory Priority**: Files in `keep_directories` are preferred
2. **File Age**: If `keep_oldest: true`, older files are preferred
3. **Path Length**: If `keep_shortest_path: true`, shorter paths are preferred

All other files in the duplicate group are recommended for deletion.

## Performance Considerations

- **Hash Algorithm**: MD5 is fastest, SHA256 is slowest but most secure
- **File Size**: Large files take longer to hash
- **Chunk Size**: Larger chunks use more memory but may be faster
- **Directory Size**: More files = longer scan time
- **Recursive Scanning**: Recursive scans take longer but are more thorough

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Test Coverage

The test suite covers:
- Hash calculation (MD5, SHA256)
- File exclusion (patterns, size)
- Directory exclusion
- Duplicate detection
- Recommendation generation
- Report generation (JSON, TXT, CSV)
- Recursive and non-recursive scanning

## Troubleshooting

### Slow Performance

**Large directories**:
- Use size limits to skip very small or very large files
- Consider scanning in batches
- Use MD5 instead of SHA256 for faster hashing

**Many files**:
- Exclude unnecessary directories (e.g., `.git`, `node_modules`)
- Use exclusion patterns to skip temporary files
- Consider non-recursive scanning if duplicates are in root only

### Memory Issues

**Large files**:
- Increase `chunk_size` in config (default: 8192)
- Use size limits to skip very large files
- Process directories separately

### No Duplicates Found

**Check configuration**:
- Verify directories exist and contain files
- Check exclusion patterns aren't too broad
- Verify size limits aren't excluding all files

**Verify files**:
- Ensure files actually have identical content
- Check file permissions (need read access)

### Report Issues

**Report not generated**:
- Check write permissions on output directory
- Verify disk space available
- Check logs for errors

**Report format issues**:
- JSON: Valid JSON structure
- CSV: Proper CSV encoding
- TXT: UTF-8 encoding

## Best Practices

1. **Start with dry run**: Review recommendations before deleting
2. **Backup important files**: Always backup before bulk deletion
3. **Use appropriate hash**: MD5 for speed, SHA256 for security
4. **Exclude system directories**: Add common exclusions (`.git`, `node_modules`, etc.)
5. **Set size limits**: Skip very small files (e.g., < 1KB) to save time
6. **Review recommendations**: Check recommendations make sense before acting
7. **Keep reports**: Save reports for reference and audit

## Security Considerations

- **Hash Collisions**: MD5 and SHA1 have known collision vulnerabilities, but collisions are extremely rare for file content
- **File Access**: Tool only reads files, never modifies them
- **Permissions**: Requires read access to scanned directories
- **Report Data**: Reports contain file paths - keep secure if sensitive

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guide
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with conventional commit format
7. Push and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

## License

This project is part of the everyday-python-scripts collection. See the main repository for license information.
