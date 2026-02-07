# Recent Files Finder

A Python automation tool that finds files modified within the last N days, hours, or minutes, useful for tracking recent activity and changes.

## Features

- Find files modified within specified time period (days, hours, or minutes)
- Flexible time units: days, hours, or minutes
- Recursive or non-recursive directory scanning
- File pattern matching (glob patterns)
- Configurable exclusions (patterns, directories, extensions)
- Detailed file information (size, modification time, age)
- Human-readable age display
- Comprehensive text reports
- Simple list output option
- Sorted by modification time (newest first)
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd recent-files-finder
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

- **search**: Search settings (directory, recursive, patterns, exclusions)
- **report**: Report generation settings
- **logging**: Logging configuration

### Environment Variables

You can override configuration using environment variables:

- `SCAN_DIRECTORY`: Directory to search (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Find files modified in last 7 days:**
```bash
python src/main.py --time 7 --unit days
```

**Find files modified in last 24 hours:**
```bash
python src/main.py --time 24 --unit hours
```

**Find files modified in last 30 minutes:**
```bash
python src/main.py --time 30 --unit minutes
```

**Search specific directory:**
```bash
python src/main.py --time 1 --unit days --directory /path/to/search
```

**Match specific file patterns:**
```bash
python src/main.py --time 7 --unit days --pattern "*.log" --pattern "*.txt"
```

**Non-recursive search:**
```bash
python src/main.py --time 1 --unit days --no-recursive
```

**Generate report to file:**
```bash
python src/main.py --time 7 --unit days --output report.txt
```

**Simple list output (paths only):**
```bash
python src/main.py --time 1 --unit days --list-only
```

### Use Cases

**Find recently modified files:**
```bash
python src/main.py -t 1 -u days
```

**Track log file changes:**
```bash
python src/main.py -t 24 -u hours -p "*.log"
```

**Find files modified in last hour:**
```bash
python src/main.py -t 1 -u hours
```

**Monitor project changes:**
```bash
python src/main.py -t 1 -u days -d ./project -p "*.py" -o project_changes.txt
```

## Project Structure

```
recent-files-finder/
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

## Report Contents

The generated report includes:

1. **Summary Statistics**
   - Files scanned
   - Files matched
   - Directories scanned
   - Errors encountered

2. **Recent Files List**
   - Modification date and time
   - File size (human-readable)
   - Age since modification
   - File path
   - Sorted by modification time (newest first)

### Example Report

```
================================================================================
Recent Files Report
================================================================================
Generated: 2024-02-07 10:30:00

Summary Statistics
--------------------------------------------------------------------------------
Files scanned: 1,234
Files matched: 45
Directories scanned: 56
Errors: 0

Recent Files (Newest First)
--------------------------------------------------------------------------------
Modified             Size         Age            File
--------------------------------------------------------------------------------
2024-02-07 10:25:00    2.45 MB    5.0 min       .../project/src/main.py
2024-02-07 10:20:00    1.23 KB    10.0 min      .../project/config.yaml
...
```

## Time Units

The tool supports three time units:

- **days**: Find files modified within last N days
- **hours**: Find files modified within last N hours
- **minutes**: Find files modified within last N minutes

### Examples

- `--time 7 --unit days`: Files modified in last 7 days
- `--time 24 --unit hours`: Files modified in last 24 hours
- `--time 30 --unit minutes`: Files modified in last 30 minutes
- `--time 1 --unit hours`: Files modified in last hour

## File Pattern Matching

Use glob patterns to match specific file types:

- `*.log` - All log files
- `*.txt` - All text files
- `*.py` - All Python files
- `test_*` - Files starting with "test_"
- `*.{log,txt}` - Multiple extensions (may need quoting)

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
pytest tests/test_main.py::test_find_recent_files
```

## Troubleshooting

### Common Issues

**No files found:**
- Verify time period is appropriate
- Check if directory contains recently modified files
- Review exclusion rules in configuration
- Verify file patterns match your files

**Permission errors:**
- Ensure read permissions for search directory
- Some system directories may require elevated privileges
- Check file system permissions

**Large directory scanning:**
- Scanning very large directories may take time
- Consider using exclusions to skip unnecessary directories
- Use non-recursive scan for specific directories
- Check logs for progress information

**Pattern matching issues:**
- Verify glob pattern syntax
- Check if patterns match your file naming conventions
- Test with simple patterns first

### Error Messages

The tool provides detailed error messages in logs. Check `logs/recent_files_finder.log` for:
- Permission errors
- File access issues
- Directory scanning problems
- Pattern matching errors

### Performance Tips

- Use exclusions to skip large unnecessary directories (e.g., `.git`, `node_modules`)
- Scan specific subdirectories instead of entire filesystem
- Use non-recursive scan when searching specific directories
- Consider scanning during off-peak hours for large filesystems
- Use file patterns to limit search scope

## Use Cases

**Track recent changes:**
- Find files modified today: `--time 1 --unit days`
- Find files modified in last hour: `--time 1 --unit hours`
- Find files modified in last 15 minutes: `--time 15 --unit minutes`

**Monitor specific file types:**
- Log files: `--pattern "*.log"`
- Configuration files: `--pattern "*.yaml" --pattern "*.json"`
- Source code: `--pattern "*.py" --pattern "*.js"`

**Track activity in specific directories:**
- Project directory: `--directory ./project`
- Downloads folder: `--directory ~/Downloads`
- System logs: `--directory /var/log`

## Security Considerations

- This tool only reads file metadata, it does not modify files
- Requires read access to directories being searched
- Be cautious when searching system directories (may require sudo)
- Reports may contain sensitive path information
- Review exclusion rules to avoid searching sensitive directories

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
