# Version File Organizer

A Python automation tool that organizes files by format version, detecting version numbers in filenames or metadata and grouping compatible versions together. This helps manage multiple versions of files and organize them into version-based folder structures.

## Project Title and Description

The Version File Organizer scans directories to detect version numbers in filenames using pattern matching, normalizes versions, and groups compatible versions together. Files are then organized into version-based folder structures, making it easier to manage multiple versions of documents, software, or any versioned files.

This tool solves the problem of managing files with version numbers by automatically detecting versions, identifying compatible version groups, and organizing them into structured folders.

**Target Audience**: Developers, document managers, system administrators, and anyone managing multiple versions of files who need organized version-based file structures.

## Features

- **Version detection:**
  - Extracts version numbers from filenames using configurable patterns
  - Supports common version formats (v1.2.3, 1.2.3, v1, etc.)
  - Placeholder for metadata extraction (future enhancement)
- **Version normalization:** Standardizes version strings for comparison
- **Compatibility grouping:** Groups compatible versions based on:
  - Exact version matching
  - Major version grouping (1.x.x)
  - Minor version grouping (1.2.x)
  - Patch version grouping (1.2.3)
- **Version-based organization:** Creates folder structures based on version groups
- **Configurable patterns:** Custom regex patterns for version detection
- **Dry-run mode:** Test organization without moving files
- **Comprehensive reporting:** Detailed reports with version groups and file listings

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Read and write access to directories being organized

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/version-file-organizer
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

### Step 4: Verify Installation

```bash
python src/main.py --help
```

## Configuration

### Configuration File (config.yaml)

The tool uses a YAML configuration file for settings. The default configuration file is `config.yaml` in the project root.

#### Key Configuration Options

**Organization Settings:**
- `organization.base_folder`: Base folder where organized files are placed (default: "organized")
- `organization.group_by_exact_version`: If true, group by exact version instead of compatibility group

**Version Detection Settings:**
- `version.filename_patterns`: List of regex patterns to extract version from filename
- `version.use_metadata`: Enable metadata extraction (placeholder for future)

**Compatibility Settings:**
- `version.compatibility.mode`: Compatibility grouping mode
  - `"exact"`: Only exact version matches
  - `"major"`: Group by major version (1.x.x) - default
  - `"minor"`: Group by major.minor (1.2.x)
  - `"patch"`: Group by major.minor.patch (1.2.3)

**Scan Settings:**
- `scan.skip_patterns`: List of path patterns to skip

**Report Settings:**
- `report.output_file`: Path for organization report

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file

### Example Configuration

```yaml
organization:
  base_folder: "organized"
  group_by_exact_version: false

version:
  filename_patterns:
    - "v(\\d+\\.\\d+\\.\\d+)"
    - "version(\\d+)"
  compatibility:
    mode: "minor"

scan:
  skip_patterns:
    - ".git"
    - "backup"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Organize files by version:

```bash
python src/main.py /path/to/directory
```

### Dry Run Mode

Test organization without moving files:

```bash
python src/main.py /path/to/directory --dry-run
```

### Specify Custom Configuration

```bash
python src/main.py /path/to/directory -c custom_config.yaml
```

### Custom Report Output

```bash
python src/main.py /path/to/directory -r custom_report.txt
```

### Combined Options

```bash
python src/main.py /path/to/directory -c config.yaml --dry-run -r report.txt
```

### Command-Line Arguments

- `directory`: (Required) Directory path to scan and organize
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Simulate organization without moving files
- `-r, --report`: Custom output path for organization report

### Common Use Cases

**Organize Software Versions:**
1. Files like `app_v1.0.0.exe`, `app_v1.0.1.exe`, `app_v2.0.0.exe`
2. Will be grouped by major version (v1, v2)
3. Organized into `organized/v1/` and `organized/v2/`

**Organize Document Versions:**
1. Files like `document_v1.pdf`, `document_v2.pdf`, `document_v1.1.pdf`
2. Grouped by compatibility mode
3. Organized into version-based folders

**Exact Version Grouping:**
1. Set `group_by_exact_version: true` in config
2. Each exact version gets its own folder
3. Useful when you need to separate all versions

## Project Structure

```
version-file-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation
└── logs/
    └── .gitkeep             # Placeholder for logs directory
```

### File Descriptions

- `src/main.py`: Contains the `VersionFileOrganizer` class and main logic
- `config.yaml`: Configuration file with version detection and organization settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `organized/`: Directory created at runtime for organized files
- `logs/`: Directory for application log files

## Version Detection

### Supported Formats

The tool detects versions in various formats:
- `v1.2.3` - Version with 'v' prefix
- `1.2.3` - Standard semantic versioning
- `v1.2` - Major.minor version
- `v1` - Single version number
- `file-1.2.3.txt` - Version with separator
- `file_1.2.3.txt` - Version with underscore

### Custom Patterns

You can define custom regex patterns in `config.yaml`:
```yaml
version:
  filename_patterns:
    - "version(\\d+\\.\\d+)"  # Matches "version1.2"
    - "rev(\\d+)"  # Matches "rev5"
```

## Compatibility Modes

### Exact Mode
Groups only files with identical version numbers.
- `v1.2.3` and `v1.2.3` → Same group
- `v1.2.3` and `v1.2.4` → Different groups

### Major Mode (Default)
Groups files by major version number.
- `v1.2.3`, `v1.3.0`, `v1.0.0` → Same group (v1)
- `v2.0.0` → Different group (v2)

### Minor Mode
Groups files by major.minor version.
- `v1.2.3`, `v1.2.4` → Same group (v1.2)
- `v1.3.0` → Different group (v1.3)

### Patch Mode
Groups files by major.minor.patch version.
- `v1.2.3` and `v1.2.3` → Same group
- `v1.2.4` → Different group

## Testing

### Run Tests

```bash
python -m pytest tests/
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage, testing:
- Configuration loading and validation
- Version detection from filenames
- Version normalization
- Compatibility checking
- Version grouping
- File organization
- Error handling

## Troubleshooting

### Common Issues

**No Versions Detected:**
- Check that filenames contain version numbers
- Review default patterns or add custom patterns
- Check logs for version detection attempts
- Verify file naming conventions match patterns

**Too Many/Few Groups:**
- Adjust compatibility mode (major/minor/patch/exact)
- Use `group_by_exact_version` for more granular grouping
- Review version normalization results

**Files Not Organized:**
- Verify files have detectable versions
- Check that files are in the source directory
- Review logs for organization errors
- Ensure write permissions in destination

**Permission Errors:**
- Ensure read access to source directory
- Ensure write access to destination
- Check file ownership and permissions

### Error Messages

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

**"Configuration file is empty"**: The config.yaml file exists but has no content. Restore from example.

### Best Practices

1. **Start with dry-run** to see what would be organized
2. **Review version patterns** to match your file naming conventions
3. **Choose appropriate compatibility mode** based on your needs
4. **Test with small directories** first
5. **Check logs** to understand version detection
6. **Backup important files** before organizing

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guidelines
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Include docstrings for all public functions and classes
- Use meaningful variable names
- Write tests for all new functionality

### Pull Request Process

1. Ensure code follows project standards
2. Update documentation if needed
3. Add/update tests
4. Ensure all tests pass
5. Submit PR with clear description of changes

## License

This project is part of the everyday-python-scripts collection. Please refer to the parent repository for license information.
