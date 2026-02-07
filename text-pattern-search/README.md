# Text Pattern Search

A Python automation script that searches file contents for specific text patterns, listing all files containing the search terms with line numbers and context. Useful for finding code references, searching documentation, and locating specific content across multiple files.

## Features

- **Text pattern search**: Search for literal text or regular expressions
- **Line numbers**: Shows exact line numbers where matches are found
- **Context display**: Shows surrounding lines for better understanding
- **Multiple file types**: Supports common text file formats
- **Recursive scanning**: Optionally search subdirectories recursively
- **File filtering**: Include or exclude specific file patterns
- **Case sensitivity**: Optional case-sensitive or case-insensitive search
- **Binary file detection**: Automatically skips binary files
- **Comprehensive logging**: Detailed logs for all operations

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd text-pattern-search
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

## Configuration

### Configuration File (config.yaml)

The script supports configuration via a YAML file:

```yaml
use_regex: false
case_sensitive: true
context_lines: 2
file_patterns: null
exclude_patterns:
  - "__pycache__"
  - ".git"
recursive: false
```

## Usage

### Basic Usage

Search for literal text in files:

```bash
python src/main.py "search term" file1.txt file2.txt
```

### Search in Directory

Search all files in a directory:

```bash
python src/main.py "function_name" /path/to/directory
```

### Recursive Search

Recursively search subdirectories:

```bash
python src/main.py "pattern" /path/to/directory --recursive
```

### Regular Expression Search

Search using regular expressions:

```bash
python src/main.py "def\s+\w+\(" /path/to/code --regex
```

### Case-Insensitive Search

Perform case-insensitive search:

```bash
python src/main.py "ERROR" /path/to/logs --case-insensitive
```

### Custom Context Lines

Show more context around matches:

```bash
python src/main.py "pattern" file.txt --context 5
```

### Filter by File Type

Search only specific file types:

```bash
python src/main.py "import" /path/to/code --file-patterns .py .js
```

### Exclude Patterns

Exclude files matching patterns:

```bash
python src/main.py "pattern" /path/to/project --exclude __pycache__ .git
```

### Save Results to File

Save search results to a file:

```bash
python src/main.py "pattern" /path/to/files --output results.txt
```

### Use Configuration File

```bash
python src/main.py "pattern" /path/to/files --config config.yaml
```

### Command-Line Arguments

- `pattern`: Text pattern to search for (required)
- `paths`: File paths or directory paths to search (required, one or more)
- `--regex`: Treat pattern as regular expression
- `--case-insensitive`: Perform case-insensitive search
- `--context`: Number of context lines to show (default: 2)
- `--file-patterns`: File extensions or patterns to include
- `--exclude`: File patterns to exclude
- `--recursive`: Recursively search subdirectories
- `--output`: Output file path for search results
- `--config`: Path to configuration file (YAML)

## Supported File Types

The script automatically recognizes and searches common text file formats:

- **Code files**: .py, .js, .html, .css, .java, .cpp, .c, .h, .go, .rs, .php, .rb, .ts, .tsx, .jsx, .vue, .swift, .kt, .scala, .clj, .lua
- **Data files**: .json, .xml, .yaml, .yml, .csv, .sql
- **Documentation**: .md, .txt, .log
- **Configuration**: .conf, .config, .ini, .cfg, .properties
- **Scripts**: .sh, .bat, .vim
- **And more**: Custom file patterns can be specified

Binary files are automatically detected and skipped.

## Project Structure

```
text-pattern-search/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file template
├── .gitignore               # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py              # Main script implementation
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation (if applicable)
└── logs/
    └── .gitkeep             # Log directory placeholder
```

### File Descriptions

- `src/main.py`: Core implementation with TextPatternSearch class and CLI interface
- `config.yaml`: Default configuration file with search settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

## Output Format

The script provides formatted output showing:

```
Search Results for Pattern: search_term
================================================================================

Files searched: 10
Files matched: 3
Total matches: 5
Errors: 0

--------------------------------------------------------------------------------

File: /path/to/file.py
Matches: 2

  Line 15:
    def search_function():
    Context:
      def helper():
        return True
      def search_function():
        return results

  Line 42:
    result = search_function()
    Context:
      if condition:
        result = search_function()
        return result

--------------------------------------------------------------------------------
```

## Examples

### Find Function Definitions

```bash
python src/main.py "def main" /path/to/code --recursive
```

### Search for Error Messages

```bash
python src/main.py "ERROR" /path/to/logs --case-insensitive --recursive
```

### Find TODO Comments

```bash
python src/main.py "TODO|FIXME|XXX" /path/to/code --regex --recursive
```

### Search Configuration Values

```bash
python src/main.py "database_url" /path/to/config --file-patterns .yaml .yml .conf
```

### Find Import Statements

```bash
python src/main.py "^import\s+\w+" /path/to/code --regex --recursive
```

## Testing

### Run Tests

```bash
pytest tests/
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage and includes:
- Text pattern matching
- Regular expression support
- Case sensitivity handling
- Context line extraction
- File filtering
- Binary file detection
- Error handling

## Troubleshooting

### Common Issues

**Issue: "No matches found"**

Solution: Verify that:
- The pattern is correct (check spelling and case sensitivity)
- Files contain the search pattern
- File types are supported
- Files are not excluded by exclude patterns

**Issue: "Invalid regex pattern"**

Solution: Validate your regular expression syntax. Test patterns using online regex testers before using them.

**Issue: "Permission denied"**

Solution: Ensure you have read permissions for the files you're trying to search.

**Issue: "File encoding error"**

Solution: The script uses UTF-8 encoding with error handling. If issues persist, check file encoding.

**Issue: Too many results**

Solution: Use more specific patterns, filter by file type, or exclude certain directories.

### Error Messages

All errors are logged to both the console and `logs/search.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `search.log`: Main log file with all operations and errors

## Performance Considerations

- Searching large files may take time
- Recursive scanning of large directory trees may be slow
- Regular expressions can be slower than literal text search
- Binary file detection adds minimal overhead

## Best Practices

1. **Use specific patterns**: More specific patterns yield better results
2. **Filter file types**: Limit search to relevant file types for faster results
3. **Exclude unnecessary directories**: Exclude build directories, node_modules, etc.
4. **Use regex wisely**: Regular expressions are powerful but can be slower
5. **Review context**: Adjust context lines based on your needs

## Security Considerations

- The script only reads files and does not modify them
- Be cautious when searching in directories with sensitive files
- Search patterns may be logged; avoid including sensitive information in patterns
- Results files may contain file contents; handle them securely

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes following the code style guidelines
4. Write or update tests
5. Ensure all tests pass: `pytest tests/`
6. Commit your changes with conventional commit messages
7. Push to your branch and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable and function names
- Keep functions focused on a single responsibility

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Follow conventional commit message format
4. Request review from maintainers

## License

This project is provided as-is for educational and automation purposes.
