# Regex File Finder

A Python automation tool that finds files matching regex patterns in filenames or file content, with options to move, copy, or list matching files.

## Features

- Search files by regex pattern in filenames
- Search files by regex pattern in file content
- Search both filename and content simultaneously
- List matching files with detailed information
- Copy matching files to destination directory
- Move matching files to destination directory
- Preserve directory structure option
- Configurable exclusions (patterns, directories, extensions)
- Recursive directory search
- File size limits for content search
- Comprehensive error handling and logging
- Processing statistics and reporting

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd regex-file-finder
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

## Configuration

### Configuration File

The tool uses a YAML configuration file (`config.yaml`) for settings. Key configuration sections:

- **search**: Search settings (directory, case sensitivity, exclusions, file size limits)
- **operations**: Operation settings (output directory, overwrite behavior, structure preservation)
- **logging**: Logging configuration

### Environment Variables

You can override configuration using environment variables:

- `SEARCH_DIRECTORY`: Directory to search (overrides config.yaml)
- `OUTPUT_DIRECTORY`: Output directory for copy/move operations (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**List files matching pattern in filename:**
```bash
python src/main.py --pattern "\.txt$" --action list
```

**List files matching pattern in content:**
```bash
python src/main.py --pattern "TODO|FIXME" --search-in content --action list
```

**Search both filename and content:**
```bash
python src/main.py --pattern "test" --search-in both --action list
```

**Copy matching files:**
```bash
python src/main.py --pattern "\.log$" --action copy --output logs_backup
```

**Move matching files:**
```bash
python src/main.py --pattern "temp_" --action move --output archive
```

**Preserve directory structure:**
```bash
python src/main.py --pattern "\.py$" --action copy --preserve-structure --output backup
```

**Search in specific directory:**
```bash
python src/main.py --pattern "config" --directory /path/to/search --action list
```

**Non-recursive search:**
```bash
python src/main.py --pattern "\.txt$" --no-recursive --action list
```

### Regex Pattern Examples

**Find all Python files:**
```bash
python src/main.py --pattern "\.py$" --action list
```

**Find files containing email addresses:**
```bash
python src/main.py --pattern "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" --search-in content --action list
```

**Find files with dates in filename:**
```bash
python src/main.py --pattern "\d{4}-\d{2}-\d{2}" --action list
```

**Find files containing TODO comments:**
```bash
python src/main.py --pattern "TODO|FIXME|XXX" --search-in content --action list
```

**Find backup files:**
```bash
python src/main.py --pattern "\.(bak|backup|old)$" --action list
```

## Project Structure

```
regex-file-finder/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── API.md
└── logs/
    └── .gitkeep
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory

## Search Options

### Search in Filename

Searches for regex pattern in file names. Can match just the filename or the full path depending on configuration.

### Search in Content

Searches for regex pattern within file content. Features:
- Skips binary files automatically
- Respects file size limits
- Handles encoding issues gracefully
- Reads files in chunks for efficiency

### Search in Both

Searches both filename and content, matching if either matches the pattern.

## Exclusion Rules

Configure exclusions in `config.yaml`:

```yaml
search:
  exclude:
    patterns: ["\\.git", "\\.DS_Store"]  # Regex patterns
    directories: [".git", "node_modules"]  # Directory names
    extensions: [".exe", ".dll", ".so"]  # File extensions
```

## Operations

### List

Lists all matching files with:
- Full path
- File size
- Match type (name, content, or both)

### Copy

Copies matching files to destination directory:
- Preserves file metadata (timestamps, permissions)
- Handles duplicate names automatically
- Option to preserve directory structure
- Option to overwrite existing files

### Move

Moves matching files to destination directory:
- Same features as copy operation
- Removes files from original location after successful move

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_main.py::test_find_files_by_name
```

## Troubleshooting

### Common Issues

**No files found:**
- Verify regex pattern is correct
- Check if search directory exists and is accessible
- Review exclusion rules in configuration
- Check case sensitivity settings

**Permission errors:**
- Ensure read permissions for search directory
- Ensure write permissions for output directory
- Check file ownership and permissions

**Large file handling:**
- Adjust `max_file_size` in configuration for larger files
- Content search skips files larger than the limit
- Consider using filename search for very large files

**Encoding errors:**
- Adjust `encoding` setting in configuration
- Some files may not be readable as text (binary files are skipped)
- Use `errors="ignore"` handling for problematic files

**Regex pattern errors:**
- Verify regex syntax is correct
- Test pattern with a regex tester first
- Escape special characters properly
- Check Python regex documentation

### Error Messages

The tool provides detailed error messages in logs. Check `logs/regex_finder.log` for:
- File access errors
- Regex pattern errors
- Permission issues
- Operation failures

### Performance Tips

- Use filename search when possible (faster than content search)
- Set appropriate file size limits
- Configure exclusions to skip unnecessary directories
- Use non-recursive search when searching specific directories
- Consider file system performance for large directory trees

## Security Considerations

- Be cautious with move operations (files are permanently moved)
- Test with list action before copy/move operations
- Review exclusion rules to avoid processing sensitive files
- Verify destination directory permissions
- Consider backing up before bulk operations

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
