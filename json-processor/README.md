# JSON Processor

Process JSON files by validating structure, removing null values, and reformatting with consistent indentation and sorted keys. Perfect for cleaning, standardizing, and organizing JSON data files.

## Project Description

JSON Processor solves the problem of inconsistent JSON file formatting and data quality by providing automated processing that validates structure, removes null values, and standardizes formatting. Ideal for data cleaning, API response processing, configuration file management, and maintaining consistent JSON codebases.

**Target Audience**: Developers, data engineers, system administrators, and anyone who works with JSON files and needs consistent formatting and data quality.

## Features

- **JSON Validation**: Validates JSON structure and syntax
- **Null Value Removal**: Recursively removes null values from JSON data
- **Key Sorting**: Alphabetically sorts keys for consistent structure
- **Consistent Formatting**: Reformats JSON with configurable indentation
- **Batch Processing**: Processes multiple JSON files in a directory
- **Recursive Scanning**: Processes files in subdirectories
- **Backup Support**: Optional backup before overwriting files
- **Comprehensive Logging**: Detailed logs of all operations
- **Error Handling**: Gracefully handles invalid JSON and errors
- **Statistics Tracking**: Reports files processed, errors, and validation issues

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read permissions to JSON files being processed
- Write permissions to output directory (if specified)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/json-processor
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

Edit `config.yaml` to set your source directory and processing options:

```yaml
source_directory: ~/Documents/json_files
output_directory: processed_json
processing:
  remove_null: true
  sort_keys: true
  indent: 2
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory containing JSON files to process
- **output_directory**: Directory for processed files (optional, overwrites if not specified)
- **processing**: Processing options
  - **remove_null**: Remove null values from JSON (default: true)
  - **sort_keys**: Sort keys alphabetically (default: true)
  - **indent**: Indentation spaces (default: 2)
  - **ensure_ascii**: Escape non-ASCII characters (default: false)
  - **compact_separators**: Use compact separators (default: false)
- **backup**: Backup configuration
  - **enabled**: Enable backups before overwriting (default: false)
  - **directory**: Backup directory path
- **exclusions**: Configuration for excluding files
  - **directories**: Directories to exclude
  - **patterns**: Patterns to match in filenames
- **operations**: Operation settings
  - **recursive**: Scan subdirectories recursively
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory path
- `OUTPUT_DIRECTORY`: Override output directory path

### Example Configuration

```yaml
source_directory: ~/Documents/json_files
output_directory: processed_json

processing:
  remove_null: true
  sort_keys: true
  indent: 2
  ensure_ascii: false

backup:
  enabled: true
  directory: backups

operations:
  recursive: true
```

## Usage

### Basic Usage

Process JSON files with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Dry run (show what would be done without making changes)
python src/main.py --dry-run
```

### Common Use Cases

1. **Clean and Format JSON Files**:
   ```bash
   python src/main.py
   ```
   Removes null values, sorts keys, and formats with consistent indentation.

2. **Process to Output Directory**:
   - Set `output_directory` in `config.yaml`
   - Original files remain unchanged

3. **Overwrite Files in Place**:
   - Don't set `output_directory` in config
   - Files are overwritten (backup recommended)

4. **Process Specific Directory**:
   - Edit `source_directory` in `config.yaml`
   - Or set environment variable: `export SOURCE_DIRECTORY=/path/to/json`

5. **Enable Backups**:
   - Set `backup.enabled: true` in config
   - Backups created before overwriting files

## Project Structure

```
json-processor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml               # Configuration file
├── .gitignore               # Git ignore rules
├── src/
│   ├── __init__.py          # Package initialization
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation (if applicable)
└── logs/
    └── .gitkeep             # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core JSON processing logic with validation and reformatting
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)
- **processed_json/**: Output directory for processed files (created when script runs)

## Processing Features

### Null Value Removal

Recursively removes null values from JSON structures:

**Before**:
```json
{
  "name": "John",
  "age": null,
  "address": {
    "street": "123 Main St",
    "zip": null
  }
}
```

**After**:
```json
{
  "name": "John",
  "address": {
    "street": "123 Main St"
  }
}
```

### Key Sorting

Alphabetically sorts keys for consistent structure:

**Before**:
```json
{
  "zebra": "last",
  "apple": "first",
  "banana": "middle"
}
```

**After**:
```json
{
  "apple": "first",
  "banana": "middle",
  "zebra": "last"
}
```

### Consistent Formatting

Formats JSON with consistent indentation:

**Before**:
```json
{"name":"John","age":30,"city":"New York"}
```

**After** (indent: 2):
```json
{
  "age": 30,
  "city": "New York",
  "name": "John"
}
```

## JSON Validation

The processor validates JSON files before processing:

- **Syntax Validation**: Ensures valid JSON syntax
- **Structure Validation**: Basic structure validation
- **Error Reporting**: Detailed error messages for invalid files

Invalid JSON files are logged and skipped during processing.

## Performance Considerations

- **Large Files**: Processing time increases with file size
- **Many Files**: Batch processing handles multiple files efficiently
- **Recursive Scanning**: May take longer for deeply nested directories
- **Null Removal**: Recursive processing may be slower for deeply nested structures

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
- JSON validation
- Null value removal
- Key sorting
- File processing operations
- Error handling
- Configuration loading

## Troubleshooting

### Common Issues

**Issue**: `Invalid JSON in file`

**Solution**: The file contains invalid JSON syntax. Check the file manually and fix syntax errors. Common issues include trailing commas, unquoted keys, or invalid characters.

---

**Issue**: `Validation failed`

**Solution**: The JSON structure may be invalid. Review the error message in logs for specific details about what failed validation.

---

**Issue**: `PermissionError` when processing files

**Solution**: Ensure you have read permissions to source files and write permissions to output directory.

---

**Issue**: Files not being processed

**Solution**:
- Check that files have `.json` extension
- Verify file extensions are not excluded in config
- Check exclusions in config
- Review logs for specific error messages

---

**Issue**: Output files not created

**Solution**:
- Check write permissions to output directory
- Verify disk space is available
- Review logs for specific errors
- Ensure at least one file was processed successfully

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Source directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Invalid JSON"**: File contains syntax errors or invalid JSON structure
- **"Validation failed"**: JSON structure doesn't meet validation requirements

## Use Cases

1. **API Response Cleaning**: Clean and format JSON responses from APIs
2. **Configuration Management**: Standardize configuration JSON files
3. **Data Processing**: Prepare JSON data for analysis or import
4. **Code Quality**: Maintain consistent JSON formatting in codebases
5. **Data Migration**: Clean JSON data before migration or transformation

## Tips for Best Results

1. **Backup First**: Enable backups when overwriting files
2. **Test with Small Set**: Process a small subset first to verify settings
3. **Review Logs**: Check logs after processing to identify any issues
4. **Use Output Directory**: Process to separate directory to preserve originals
5. **Validate Before Processing**: Manually validate critical JSON files first
6. **Exclude Patterns**: Configure exclusions to skip test or temporary files

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
