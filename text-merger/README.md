# Text Merger

Merge multiple text files into a single file with separators, preserving original filenames as headers and maintaining order. Perfect for combining log files, documentation, or any text-based content into a unified document.

## Project Description

Text Merger solves the problem of combining multiple text files into a single document while maintaining organization and readability. It automatically adds filename headers, inserts separators between files, and preserves the original order. Ideal for consolidating logs, merging documentation, or combining text-based reports.

**Target Audience**: Developers, system administrators, writers, and anyone who needs to combine multiple text files into a single document while maintaining structure and readability.

## Features

- Merge multiple text files into a single output file
- Preserve original filenames as headers
- Configurable separators between files
- Multiple sort options (alphabetical, date, size)
- Recursive directory scanning
- File filtering by extension and patterns
- Custom header format
- Optional header text at beginning of merged file
- Encoding support (UTF-8 and others)
- Dry-run mode to preview operations
- Comprehensive logging and error handling
- Statistics tracking (files merged, lines, errors)

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/text-merger
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

Edit `config.yaml` to set your source directory and output file:

```yaml
source_directory: ~/Documents/TextFiles
output_file: merged_output.txt
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory containing text files to merge
- **output_file**: Path to output merged file
- **text_extensions**: List of file extensions to include (default: .txt, .md, .log)
- **sort_order**: How to sort files (alphabetical, date_modified, date_created, size)
- **header_format**: Format for filename headers (use `{filename}` placeholder)
- **separator**: Separator string between files
- **include_header**: Add header text at beginning of merged file
- **header_text**: Text to add at beginning (if include_header is true)
- **exclusions**: Patterns and extensions to exclude
- **input_encoding**: Encoding for reading files (default: utf-8)
- **output_encoding**: Encoding for writing output (default: utf-8)
- **operations**: Recursive scanning and dry-run settings
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory path
- `OUTPUT_FILE`: Override output file path
- `DRY_RUN`: Enable dry run mode (`true`/`false`)

### Example Configuration

```yaml
source_directory: ~/Documents/Logs
output_file: combined_logs.txt

text_extensions:
  - .txt
  - .log

sort_order: date_modified

header_format: "=== {filename} ==="
separator: "\n" + "=" * 80 + "\n"

include_header: true
header_text: "Combined Log Files\nGenerated: {date}"

exclusions:
  patterns:
    - .tmp
    - .bak
```

## Usage

### Basic Usage

Merge text files with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Preview changes without creating merged file (dry run)
python src/main.py --dry-run

# Specify output file (overrides config)
python src/main.py -o combined.txt

# Combine options
python src/main.py -c config.yaml --dry-run -o output.txt
```

### Common Use Cases

1. **Merge Log Files**:
   ```bash
   python src/main.py
   ```
   Combine multiple log files into a single file for analysis.

2. **Preview Merge (Recommended First Step)**:
   ```bash
   python src/main.py --dry-run
   ```
   See what files would be merged without creating output.

3. **Merge Documentation**:
   - Place markdown files in source directory
   - Configure `text_extensions: [.md]`
   - Run merger to create combined documentation

4. **Combine Text Reports**:
   - Set `sort_order: date_modified` to merge newest first
   - Use custom header format for better organization

5. **Recursive Merge**:
   - Set `recursive: true` to include files from subdirectories
   - Files maintain their relative path in headers

## Project Structure

```
text-merger/
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

- **src/main.py**: Core merging logic, file reading, and output generation
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Output Format

The merged file follows this structure:

```
[Optional Header Text]

=== filename1.txt ===
Content from first file...

================================================================================

=== filename2.txt ===
Content from second file...

================================================================================

=== filename3.txt ===
Content from third file...
```

## Sort Options

Files can be sorted in different ways:

- **alphabetical** (default): Sort by filename alphabetically
- **date_modified**: Sort by last modification time (newest first)
- **date_created**: Sort by creation time (newest first)
- **size**: Sort by file size (largest first)

## File Filtering

The script includes files based on:

1. **Extension**: Only files with extensions in `text_extensions` list
2. **Exclusions**: Files matching excluded patterns or extensions are skipped
3. **File type**: Only regular files (not directories or special files)

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
- File reading and merging
- Header formatting
- Separator insertion
- File filtering and sorting
- Error handling
- Encoding support

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Source directory does not exist`

**Solution**: Ensure the source directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: No files found to merge

**Solution**:
- Check that files have extensions listed in `text_extensions`
- Verify files aren't excluded by patterns
- Check that `recursive` setting matches your directory structure
- Review logs for details

---

**Issue**: Encoding errors when reading files

**Solution**:
- Set `input_encoding` in config to match file encoding
- Script uses error handling to replace problematic characters
- Check logs for specific encoding issues

---

**Issue**: Output file not created

**Solution**:
- Check write permissions to output directory
- Verify disk space is available
- Check logs for specific error messages
- Ensure not in dry-run mode

---

**Issue**: Files merged in wrong order

**Solution**:
- Check `sort_order` setting in config
- Verify file timestamps if using date-based sorting
- Use `alphabetical` for consistent ordering

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Source directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Error reading file"**: File may be corrupted, locked, or have encoding issues
- **"Error writing output file"**: Check permissions and disk space

## Tips for Best Results

1. **Use Dry-Run First**: Always run with `--dry-run` to preview what will be merged
2. **Check File Extensions**: Ensure all text files have extensions listed in config
3. **Review Exclusions**: Configure exclusions to skip unwanted files
4. **Choose Sort Order**: Select appropriate sort order for your use case
5. **Customize Headers**: Adjust header format to match your needs
6. **Check Encoding**: Verify file encodings match input_encoding setting

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
