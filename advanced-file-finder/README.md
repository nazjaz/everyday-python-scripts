# Advanced File Finder

A Python automation tool for finding files matching complex pattern combinations. This script supports multiple search criteria including file size, date ranges, file types, filename patterns, and content patterns, with flexible logical operators for combining criteria.

## Features

- **Size Patterns**: Find files by size (min, max, ranges)
- **Date Patterns**: Search by modification, creation, or access dates
- **Type Patterns**: Match by file extensions or type categories
- **Filename Patterns**: Use glob patterns, regex, or contains matching
- **Content Patterns**: Search for text or regex patterns within file contents
- **Logical Operators**: Combine patterns with AND or OR logic
- **Multiple Output Formats**: Text, JSON, or CSV output
- **Recursive Search**: Search directories recursively with exclusion support
- **Comprehensive Logging**: Detailed logging with rotation
- **Performance Optimized**: Skips large files for content search

## Prerequisites

- Python 3.8 or higher
- Read permissions to search directories
- Sufficient memory for content pattern searches

## Installation

1. Clone or navigate to the project directory:
```bash
cd advanced-file-finder
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure the environment file (optional):
```bash
cp .env.example .env
# Edit .env with your settings if needed
```

5. Review and customize `config.yaml` with your search patterns:
   - Configure size, date, type, filename, and content patterns
   - Set logical operator (AND or OR)
   - Configure output format

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

#### Search Configuration
- **search.directory**: Directory to search (default: current directory)
- **search.exclude_directories**: Directories to exclude (glob patterns)

#### Pattern Configuration
- **patterns.logic_operator**: How to combine patterns - "AND" or "OR" (default: AND)
- **patterns.size**: Size criteria (min_bytes, max_bytes, ranges)
- **patterns.date**: Date criteria (modified, created, accessed)
- **patterns.type**: File type criteria (extensions, exclude_extensions, categories)
- **patterns.filename**: Filename criteria (glob, regex, contains)
- **patterns.content**: Content criteria (text, regex, max_file_size_bytes)

#### Output Configuration
- **output.format**: Output format - text, json, or csv (default: text)

### Pattern Examples

#### Find Large Files Modified Recently
```yaml
patterns:
  size:
    min_bytes: 10485760  # 10 MB
  date:
    modified:
      days_ago: 7  # Modified in last 7 days
```

#### Find Text Files Containing Specific Content
```yaml
patterns:
  type:
    extensions: [".txt", ".md"]
  content:
    text: ["TODO", "FIXME"]
```

#### Find Images Modified Before Date
```yaml
patterns:
  type:
    categories: ["image"]
  date:
    modified:
      before: "2024-01-01"
```

#### Find Files with Regex Pattern in Name
```yaml
patterns:
  filename:
    regex: ["^backup_.*\\.zip$"]
```

### Environment Variables

Optional environment variables can override configuration:

- `SEARCH_DIRECTORY`: Override search directory path

## Usage

### Basic Usage

Search with default configuration:
```bash
python src/main.py
```

### Custom Search Directory

Search in a specific directory:
```bash
python src/main.py --directory /path/to/search
```

### Output to File

Save results to a file:
```bash
python src/main.py --output results.txt
```

### JSON Output

Generate results in JSON format:
```bash
python src/main.py --format json --output results.json
```

### CSV Output

Generate results in CSV format:
```bash
python src/main.py --format csv --output results.csv
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --directory`: Directory to search (overrides config)
- `-o, --output`: Output file path (default: stdout)
- `-f, --format`: Output format - text, json, or csv (overrides config)
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
advanced-file-finder/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── .gitkeep             # Documentation directory placeholder
└── logs/
    └── .gitkeep             # Logs directory placeholder
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## How It Works

1. **Configuration Loading**: The script loads patterns from `config.yaml` or command-line arguments.

2. **Pattern Matching**: For each file in the search directory:
   - Checks size criteria (min, max, ranges)
   - Checks date criteria (modified, created, accessed)
   - Checks type criteria (extensions, categories)
   - Checks filename criteria (glob, regex, contains)
   - Checks content criteria (text, regex) for readable files

3. **Logical Combination**: Applies logic operator (AND or OR) to combine pattern results.

4. **Result Collection**: Collects matching files with metadata (path, size, modified date, extension).

5. **Output Formatting**: Formats results in requested format (text, JSON, or CSV).

6. **Logging**: All operations are logged with timestamps and context.

## Pattern Types

### Size Patterns
- **min_bytes**: Minimum file size
- **max_bytes**: Maximum file size
- **ranges**: List of size ranges (files must match at least one)

### Date Patterns
- **modified**: Modification date criteria
  - **after**: Files modified after date
  - **before**: Files modified before date
  - **days_ago**: Files modified within N days
- **created**: Creation date criteria (same options)
- **accessed**: Access date criteria (same options)

Date formats:
- ISO format: "2024-01-01"
- Relative: "30 days ago", "2 weeks ago", "1 month ago"

### Type Patterns
- **extensions**: List of file extensions to match
- **exclude_extensions**: List of extensions to exclude
- **categories**: File type categories (image, document, video, audio, code, archive)

### Filename Patterns
- **glob**: Glob patterns (e.g., "*.txt", "file_*")
- **regex**: Regular expression patterns
- **contains**: Substring matches (case-insensitive)

### Content Patterns
- **text**: List of text strings to search for (case-insensitive)
- **regex**: Regular expression patterns to search for
- **max_file_size_bytes**: Maximum file size to search content (default: 10 MB)

## Troubleshooting

### No Results Found

If no results are found:
- Check that patterns are not too restrictive
- Verify search directory path is correct
- Try using OR logic operator instead of AND
- Check logs for excluded directories or files

### Content Search Performance

If content search is slow:
- Reduce max_file_size_bytes to skip large files
- Use more specific filename or type patterns to reduce files checked
- Consider using text patterns instead of regex for better performance

### Permission Errors

If you encounter permission errors:
- Ensure you have read access to search directory
- Check file and directory permissions
- Some files may be skipped with warnings in the log

### Regex Pattern Errors

If regex patterns fail:
- Validate regex syntax
- Escape special characters properly
- Test patterns in a regex tester first
- Check logs for specific error messages

### Configuration Errors

If configuration errors occur:
- Validate YAML syntax in `config.yaml`
- Ensure all required configuration keys are present
- Check that paths are valid and accessible
- Review pattern format examples

## Use Cases

### Find Large Old Files
```yaml
patterns:
  size:
    min_bytes: 104857600  # 100 MB
  date:
    modified:
      days_ago: 365  # Older than 1 year
```

### Find Code Files with TODOs
```yaml
patterns:
  type:
    categories: ["code"]
  content:
    text: ["TODO", "FIXME"]
```

### Find Backup Files
```yaml
patterns:
  filename:
    contains: ["backup"]
    regex: [".*\\.bak$", ".*\\.backup$"]
  logic_operator: "OR"
```

### Find Recent Images
```yaml
patterns:
  type:
    categories: ["image"]
  date:
    modified:
      days_ago: 7
```

## Security Considerations

- Content search reads file contents - ensure you have permission
- Large files are skipped for content search to prevent memory issues
- Regex patterns can be computationally expensive - use carefully
- The script only reads files, never modifies them

## Performance Considerations

- Content pattern matching is slower than other patterns
- Large directories may take time to process
- Consider using more specific patterns to reduce search space
- Content search is limited to files under max_file_size_bytes

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
