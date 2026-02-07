# Duplicate Name Finder

A Python automation tool that finds files with duplicate names in different directories, generates detailed reports, and optionally renames them with directory prefixes.

## Features

- Find files with duplicate names across different directories
- Generate detailed reports showing all duplicate files
- Optionally rename duplicate files with directory prefixes
- Recursive or non-recursive directory scanning
- Configurable exclusions (patterns, directories, extensions)
- Dry-run mode to preview renaming operations
- Comprehensive error handling and logging
- File size and modification time information
- Statistics tracking

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd duplicate-name-finder
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

- **search**: Search settings (directory, recursive, exclusions)
- **renaming**: Renaming settings (prefix separator, skip options)
- **report**: Report generation settings
- **logging**: Logging configuration

### Environment Variables

You can override configuration using environment variables:

- `SCAN_DIRECTORY`: Directory to search (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Find duplicate file names:**
```bash
python src/main.py
```

**Search specific directory:**
```bash
python src/main.py --directory /path/to/search
```

**Non-recursive search:**
```bash
python src/main.py --directory /path/to/search --no-recursive
```

**Generate report to file:**
```bash
python src/main.py --directory /path/to/search --output report.txt
```

**Preview renaming (dry-run):**
```bash
python src/main.py --directory /path/to/search --dry-run
```

**Rename duplicate files with directory prefixes:**
```bash
python src/main.py --directory /path/to/search --rename
```

### Use Cases

**Find duplicate names in project:**
```bash
python src/main.py -d ./project -o duplicates.txt
```

**Preview renaming before applying:**
```bash
python src/main.py -d ./project --dry-run
```

**Rename duplicates automatically:**
```bash
python src/main.py -d ./project --rename
```

## Project Structure

```
duplicate-name-finder/
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
- `output/`: Generated reports directory

## How It Works

1. **Scan Directory**: Finds all files in specified directory
2. **Group by Name**: Groups files by filename
3. **Identify Duplicates**: Finds files with same name in different directories
4. **Generate Report**: Creates detailed report of all duplicates
5. **Optional Renaming**: Renames files with directory prefixes if requested

### Renaming Strategy

When renaming duplicate files, the tool:
- Calculates directory prefix based on file's location relative to base directory
- Adds prefix to filename: `{directory_prefix}_{original_filename}`
- Skips files if target name already exists (configurable)
- Optionally skips files in base directory

### Example Renaming

**Before:**
```
project/
  src/
    utils.py
  tests/
    utils.py
  docs/
    utils.py
```

**After (with prefixes):**
```
project/
  src/
    src_utils.py
  tests/
    tests_utils.py
  docs/
    docs_utils.py
```

## Report Contents

The generated report includes:

1. **Summary Statistics**
   - Files scanned
   - Duplicate names found
   - Files with duplicate names
   - Files renamed (if applicable)
   - Errors encountered

2. **Duplicate File Names**
   - For each duplicate name:
     - Filename
     - Number of locations
     - Full paths to each duplicate
     - File size and modification time

## Configuration Options

### Search Settings

- `directory`: Directory to search
- `recursive`: Search subdirectories (default: true)
- `exclude.patterns`: Regex patterns to exclude
- `exclude.directories`: Directory names to exclude
- `exclude.extensions`: File extensions to exclude

### Renaming Settings

- `prefix_separator`: Separator between prefix and filename (default: "_")
- `skip_if_exists`: Skip if target name exists (default: true)
- `skip_base_directory`: Skip files in base directory (default: true)

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
pytest tests/test_main.py::test_find_duplicate_names
```

## Troubleshooting

### Common Issues

**No duplicates found:**
- Verify directory contains files with duplicate names
- Check exclusion rules aren't too broad
- Ensure files are in different directories (not just same directory)

**Renaming errors:**
- Check file permissions
- Verify target names don't already exist
- Ensure sufficient disk space
- Review logs for specific error messages

**Permission errors:**
- Ensure read permissions for search directory
- Ensure write permissions for renaming
- Some system directories may require elevated privileges

### Error Messages

The tool provides detailed error messages in logs. Check `logs/duplicate_finder.log` for:
- File access errors
- Permission issues
- Renaming problems
- Directory scanning errors

### Best Practices

1. **Test with dry-run first**: Always use `--dry-run` to preview renaming
2. **Backup before renaming**: Consider backing up files before bulk renaming
3. **Review exclusions**: Configure exclusions to avoid processing system files
4. **Check report**: Review report before renaming to understand impact
5. **Use version control**: If working with code, ensure files are committed first

## Security Considerations

- Be cautious when renaming files in system directories
- Review exclusion rules to avoid processing sensitive files
- Verify file permissions before renaming
- Consider backing up before bulk operations
- Test with dry-run mode first

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
