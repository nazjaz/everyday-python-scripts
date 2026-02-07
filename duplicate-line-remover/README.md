# Duplicate Line Remover

Remove duplicate lines from text files while preserving line order, with options to ignore case and whitespace differences. Clean up text files by removing redundant lines efficiently.

## Project Description

Duplicate Line Remover solves the problem of duplicate lines in text files. It removes duplicate lines while preserving the original order of unique lines, with flexible options to handle case and whitespace differences. Useful for cleaning log files, data files, and any text files with duplicate entries.

**Target Audience**: Developers, data analysts, system administrators, and anyone who needs to clean duplicate lines from text files.

## Features

- **Preserve Line Order**: Maintains original order of unique lines
- **Case-Insensitive Option**: Ignore case differences when comparing lines
- **Whitespace Options**: Ignore whitespace differences (leading/trailing, multiple spaces)
- **Empty Line Handling**: Configurable handling of empty/blank lines
- **Line Trimming**: Optional trimming of leading/trailing whitespace
- **Whitespace Normalization**: Normalize multiple spaces to single space
- **Backup Creation**: Automatically backup original files before processing
- **Batch Processing**: Process multiple files in a directory
- **Comprehensive Logging**: Log all operations and statistics
- **Detailed Reports**: Generate reports with processing statistics

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/duplicate-line-remover
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

### Step 4: Configure Settings (Optional)

1. Copy the example environment file (if needed):
   ```bash
   cp .env.example .env
   ```

2. Edit `config.yaml` to customize processing options:
   ```yaml
   processing:
     ignore_case: false
     ignore_whitespace: false
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **processing**: Duplicate detection options (case, whitespace, etc.)
- **file_handling**: File encoding, backup, and output settings
- **output**: Output file naming and creation
- **batch**: Batch processing settings for directories
- **logging**: Logging configuration
- **reporting**: Report generation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `INPUT_FILE`: Override input file path
- `OUTPUT_FILE`: Override output file path
- `IGNORE_CASE`: Enable case-insensitive comparison (true/false)
- `IGNORE_WHITESPACE`: Enable whitespace-ignoring comparison (true/false)

### Example Configuration

```yaml
processing:
  ignore_case: true  # Treat "Hello" and "HELLO" as duplicates
  ignore_whitespace: false
  preserve_empty_lines: true
  trim_lines: false

file_handling:
  backup_original: true
  overwrite_original: false
```

## Usage

### Basic Usage

Remove duplicates from a single file:

```bash
python src/main.py -i input.txt
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml -i input.txt

# Ignore case differences
python src/main.py -i input.txt --ignore-case

# Ignore whitespace differences
python src/main.py -i input.txt --ignore-whitespace

# Custom output file
python src/main.py -i input.txt -o output.txt

# Process all files in directory
python src/main.py -d /path/to/directory

# Combine options
python src/main.py -i input.txt --ignore-case --ignore-whitespace
```

### Common Use Cases

1. **Basic Duplicate Removal**:
   ```bash
   python src/main.py -i file.txt
   ```

2. **Case-Insensitive Removal**:
   ```bash
   python src/main.py -i file.txt --ignore-case
   ```
   Removes duplicates like "Hello" and "HELLO"

3. **Whitespace-Ignoring Removal**:
   ```bash
   python src/main.py -i file.txt --ignore-whitespace
   ```
   Removes duplicates like "Hello World" and "Hello  World"

4. **Process Directory**:
   ```bash
   python src/main.py -d /path/to/logs
   ```
   Processes all matching files in directory

## Project Structure

```
duplicate-line-remover/
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
│   └── API.md              # API documentation (if applicable)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── duplicate_remover.log  # Application logs
    └── deduplication_report.txt  # Processing reports
```

### File Descriptions

- **src/main.py**: Duplicate detection, line normalization, file processing, and reporting
- **config.yaml**: YAML configuration file with processing options
- **tests/test_main.py**: Unit tests for core functionality
- **logs/duplicate_remover.log**: Application log file with rotation
- **logs/deduplication_report.txt**: Summary reports with statistics

## Processing Options

### Ignore Case

When enabled, treats lines as duplicates regardless of case:
- "Hello" and "HELLO" → duplicates
- "Test" and "test" → duplicates

### Ignore Whitespace

When enabled, ignores whitespace differences:
- "Hello World" and "Hello  World" → duplicates
- "  Test  " and "Test" → duplicates (if trim_lines also enabled)

### Preserve Empty Lines

Controls handling of empty/blank lines:
- `true`: Keep first empty line, remove duplicates
- `false`: Remove all empty lines

### Trim Lines

Trims leading/trailing whitespace before comparison:
- "  Hello  " → "Hello" for comparison

### Normalize Whitespace

Normalizes multiple spaces to single space:
- "Hello    World" → "Hello World" for comparison

## How It Works

1. **Read File**: Reads input file line by line
2. **Normalize**: Normalizes each line based on configuration options
3. **Track Seen**: Maintains set of seen normalized lines
4. **Preserve Order**: Keeps first occurrence of each unique line
5. **Write Output**: Writes deduplicated lines to output file
6. **Create Backup**: Backs up original file (if configured)

## Examples

### Example 1: Basic Deduplication

**Input** (`input.txt`):
```
apple
banana
apple
cherry
banana
```

**Output** (`input.txt.deduplicated`):
```
apple
banana
cherry
```

### Example 2: Case-Insensitive

**Input**:
```
Hello
HELLO
hello
World
```

**With `--ignore-case`**:
```
Hello
World
```

### Example 3: Whitespace-Ignoring

**Input**:
```
Hello World
Hello  World
HelloWorld
```

**With `--ignore-whitespace`**:
```
Hello World
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
- Line normalization
- Duplicate detection
- Case-insensitive comparison
- Whitespace-ignoring comparison
- File processing
- Order preservation

## Troubleshooting

### Common Issues

**Issue**: Duplicates not being removed

**Solution**: 
- Check if lines are actually identical (including whitespace)
- Enable `ignore_case` or `ignore_whitespace` if needed
- Verify file encoding is correct
- Check logs for processing details

---

**Issue**: Too many lines removed

**Solution**: 
- Disable `ignore_case` if case differences matter
- Disable `ignore_whitespace` if whitespace differences matter
- Check `trim_lines` and `normalize_whitespace` settings
- Review normalization logic in logs

---

**Issue**: Empty lines all removed

**Solution**: 
- Set `preserve_empty_lines: true` in config
- Empty lines will be preserved (first occurrence kept)

---

**Issue**: Encoding errors

**Solution**: 
- Check file encoding matches `input_encoding` in config
- Try different encoding (utf-8, latin-1, etc.)
- Check file for binary content

---

**Issue**: Output file not created

**Solution**: 
- Verify `create_output_file: true` in config
- Check output directory permissions
- Review logs for errors

### Error Messages

- **"Input file not found"**: Verify input file path is correct
- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path
- **"Encoding error"**: File encoding doesn't match configured encoding

## Best Practices

1. **Backup First**: Always backup important files before processing
   - Backups are created automatically by default
   - Check backup files before deleting originals

2. **Test Options**: Test with different options to find best settings
   ```bash
   # Test with case-insensitive
   python src/main.py -i test.txt --ignore-case
   
   # Test with whitespace-ignoring
   python src/main.py -i test.txt --ignore-whitespace
   ```

3. **Review Output**: Always review output file before using
   - Check that important lines weren't removed
   - Verify line order is correct

4. **Start Small**: Test on small files first
   - Verify behavior matches expectations
   - Check statistics in reports

5. **Use Appropriate Options**: Choose options based on your needs
   - Use `ignore_case` for case-insensitive data
   - Use `ignore_whitespace` for data with inconsistent spacing

## Performance Considerations

- **Large Files**: Processing is line-by-line, memory efficient
- **Many Files**: Batch processing handles multiple files efficiently
- **Encoding**: UTF-8 is fastest, other encodings may be slower
- **Options**: More normalization options may slow processing slightly

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
