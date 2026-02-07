# Directory Statistics

A command-line tool for generating comprehensive directory statistics including file counts by type, total sizes, oldest and newest files, and storage breakdown. Supports multiple report formats and customizable file categorization.

## Project Description

Directory Statistics solves the problem of understanding disk usage and file organization by providing detailed analysis of directory contents. It helps users identify storage patterns, find large files, understand file type distribution, and make informed decisions about disk cleanup and organization.

**Target Audience**: System administrators, developers, and users who need to analyze disk usage, understand file distribution, or generate reports on directory contents.

## Features

- **Comprehensive Statistics**: File counts, sizes, and directory counts
- **File Type Analysis**: Count files by extension and category
- **Storage Breakdown**: Percentage breakdown by file category
- **Oldest/Newest Files**: Identify oldest and newest files in directory
- **Largest Files**: Find and list largest files
- **Multiple Report Formats**: Generate reports in JSON, TXT, or CSV format
- **Customizable Categories**: Define file type categories and extensions
- **Flexible Filtering**: Exclude files and directories by patterns or size
- **Recursive Analysis**: Analyze directories recursively or non-recursively
- **Comprehensive Logging**: Detailed logs of all operations

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/directory-statistics
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

Edit `config.yaml` to customize file categories and options:

```yaml
analyze_directories:
  - .
file_type_categories:
  images:
    extensions: [jpg, jpeg, png, gif]
    name: Images
options:
  top_largest_count: 10
  top_oldest_count: 10
  top_newest_count: 10
```

## Usage

### Basic Usage

Analyze configured directory:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Analyze specific directory
python src/main.py -d /path/to/directory

# Non-recursive analysis
python src/main.py --no-recursive

# Specify output file
python src/main.py -o /path/to/report.json

# Specify report format
python src/main.py --format txt

# Use custom configuration file
python src/main.py -c /path/to/config.yaml
```

### Common Use Cases

**Analyze Downloads folder**:
```bash
python src/main.py -d ~/Downloads
```

**Generate text report**:
```bash
python src/main.py --format txt -o stats.txt
```

**Non-recursive analysis**:
```bash
python src/main.py --no-recursive
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

#### File Type Categories

Define categories and their file extensions:

```yaml
file_type_categories:
  images:
    extensions: [jpg, jpeg, png, gif, bmp, svg, webp]
    name: Images
  documents:
    extensions: [pdf, doc, docx, txt, rtf]
    name: Documents
```

#### Exclusion Patterns

```yaml
exclude_patterns:
  - '^\\.'  # Hidden files
  - '\\.tmp$'  # Temporary files
  - '\\.log$'  # Log files
```

#### Options

```yaml
options:
  include_hidden: false  # Include hidden files
  include_empty: true  # Include zero-byte files
  min_file_size: 0  # Minimum file size (bytes)
  max_file_size: 0  # Maximum file size (bytes)
  top_largest_count: 10  # Number of largest files to show
  top_oldest_count: 10  # Number of oldest files to show
  top_newest_count: 10  # Number of newest files to show
```

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Report Formats

### JSON Report

Structured data format with complete statistics:

```json
{
  "directory": "/path/to/directory",
  "analyzed_at": "2024-01-15T10:30:00",
  "total_files": 1234,
  "total_directories": 56,
  "total_size": 1073741824,
  "summary": {
    "total_files": 1234,
    "total_size_mb": 1024.0,
    "total_size_gb": 1.0
  },
  "categories": {...},
  "file_types": {...},
  "top_largest_files": [...],
  "oldest_file": {...},
  "newest_file": {...}
}
```

### Text Report

Human-readable format with formatted output:

```
================================================================================
DIRECTORY STATISTICS REPORT
================================================================================

Directory: /path/to/directory
Analyzed: 2024-01-15T10:30:00
Recursive: true

SUMMARY
--------------------------------------------------------------------------------
Total Files: 1,234
Total Directories: 56
Total Size: 1.00 GB

STORAGE BREAKDOWN BY CATEGORY
--------------------------------------------------------------------------------
Images              234 files      512.00 MB  ( 50.0%)
Documents           456 files      256.00 MB  ( 25.0%)
...

TOP 10 LARGEST FILES
--------------------------------------------------------------------------------
 1.    512.00 MB  /path/to/large_file.zip
 2.    256.00 MB  /path/to/another_file.iso
...
```

### CSV Report

Tabular format suitable for spreadsheet applications:

| Category | Count | Size (bytes) | Percentage |
|----------|-------|--------------|------------|
| Images | 234 | 536870912 | 50.00% |
| Documents | 456 | 268435456 | 25.00% |

## Statistics Provided

### Summary Statistics
- Total number of files
- Total number of directories
- Total size (bytes, MB, GB)

### File Type Statistics
- Count by file extension
- Size by file extension
- Top file types by count

### Category Statistics
- Count by category (Images, Documents, etc.)
- Size by category
- Percentage breakdown

### File Information
- Oldest file (by modification date)
- Newest file (by modification date)
- Largest file (by size)
- Top N largest files
- Top N oldest files
- Top N newest files

## Project Structure

```
directory-statistics/
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
│   └── directory_stats.json  # Generated reports
└── logs/
    └── directory_statistics.log  # Application logs
```

## Customizing File Categories

Edit `config.yaml` to add or modify file categories:

```yaml
file_type_categories:
  my_category:
    extensions: [ext1, ext2, ext3]
    name: My Category Name
```

Files with extensions not in any category are grouped under "other".

## Performance Considerations

- **Large Directories**: Analysis time increases with number of files
- **Recursive Scanning**: Recursive scans take longer but are more thorough
- **File Size Limits**: Setting size limits can speed up analysis
- **Exclusion Patterns**: Excluding common patterns (e.g., `.git`, `node_modules`) speeds up analysis

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
- Directory analysis (recursive and non-recursive)
- File type categorization
- File exclusion (patterns, size, hidden)
- Directory exclusion
- Oldest/newest/largest file detection
- Report generation (JSON, TXT, CSV)
- Size formatting

## Troubleshooting

### Slow Performance

**Large directories**:
- Use size limits to skip very small or very large files
- Exclude common directories (`.git`, `node_modules`, etc.)
- Consider non-recursive scanning if not needed

**Many files**:
- Increase exclusion patterns
- Use file size limits
- Process subdirectories separately

### Memory Issues

**Very large directories**:
- Process directories in batches
- Use size limits to reduce file count
- Exclude unnecessary directories

### Missing Files in Report

**Check exclusions**:
- Verify exclusion patterns aren't too broad
- Check file size limits
- Verify `include_hidden` and `include_empty` settings

### Report Format Issues

**JSON**:
- Valid JSON structure
- All data types serializable

**CSV**:
- Proper CSV encoding (UTF-8)
- Special characters handled correctly

**TXT**:
- UTF-8 encoding
- Proper formatting

## Best Practices

1. **Exclude system directories**: Add common exclusions (`.git`, `node_modules`, `.venv`)
2. **Use appropriate size limits**: Skip very small files if not needed
3. **Customize categories**: Define categories relevant to your use case
4. **Review reports**: Check reports for accuracy before making decisions
5. **Save reports**: Keep reports for comparison over time
6. **Regular analysis**: Run analysis periodically to track changes

## Use Cases

- **Disk Cleanup**: Identify large files and file types taking up space
- **Storage Planning**: Understand storage distribution and plan upgrades
- **File Organization**: Understand file type distribution for organization
- **Audit Reports**: Generate reports for compliance or documentation
- **Performance Analysis**: Identify files affecting system performance

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
