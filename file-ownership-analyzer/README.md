# File Ownership Analyzer

A Python automation tool that organizes files by owner or group permissions, useful for multi-user systems to identify file ownership patterns and analyze permission distributions.

## Features

- Scan directories and collect file ownership information
- Organize files by owner (user)
- Organize files by group
- Calculate statistics for owners and groups (file count, total size, file types)
- Identify ownership patterns (top owners, top groups, owner/group mismatches)
- Generate detailed text reports
- Query files by specific owner or group
- Recursive or non-recursive directory scanning
- Configurable exclusions (patterns, directories)
- Comprehensive error handling and logging
- Permission details (read, write, execute for owner/group/other)

## Prerequisites

- Python 3.8 or higher
- Unix-like operating system (Linux, macOS) with pwd and grp modules
- Appropriate file system permissions to read target directories

## Installation

1. Clone or navigate to the project directory:
```bash
cd file-ownership-analyzer
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

- **scan**: Directory scanning settings (directory, recursive, exclusions)
- **output**: Output directory for reports
- **report**: Report generation settings
- **logging**: Logging configuration

### Environment Variables

You can override configuration using environment variables:

- `SCAN_DIRECTORY`: Directory to scan (overrides config.yaml)
- `OUTPUT_DIRECTORY`: Output directory for reports (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Scan directory and show summary:**
```bash
python src/main.py --directory /path/to/scan
```

**Scan non-recursively:**
```bash
python src/main.py --directory /path/to/scan --no-recursive
```

**List all owners:**
```bash
python src/main.py --directory /path/to/scan --list-owners
```

**List all groups:**
```bash
python src/main.py --directory /path/to/scan --list-groups
```

**Show files for specific owner:**
```bash
python src/main.py --directory /path/to/scan --owner username
```

**Show files for specific group:**
```bash
python src/main.py --directory /path/to/scan --group groupname
```

**Generate report:**
```bash
python src/main.py --directory /path/to/scan --report ownership_report.txt
```

### Use Cases

**Identify files owned by a specific user:**
```bash
python src/main.py -d /home -o username
```

**Find all files in a specific group:**
```bash
python src/main.py -d /var/www -g www-data
```

**Analyze ownership patterns in a directory:**
```bash
python src/main.py -d /home -r analysis_report.txt
```

**List all owners with file counts:**
```bash
python src/main.py -d /opt --list-owners
```

## Project Structure

```
file-ownership-analyzer/
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

## Output and Reports

### Report Contents

Generated reports include:
- Summary statistics (files scanned, unique owners/groups)
- Top 10 owners by file count
- Top 10 owners by total size
- Top 10 groups by file count
- Top 10 groups by total size
- Files with owner != group (potential issues)

### Statistics Provided

For each owner:
- Total file count
- Total size (bytes and MB)
- Average file size
- File extensions distribution
- Groups distribution

For each group:
- Total file count
- Total size (bytes and MB)
- Average file size
- Owners distribution
- File extensions distribution

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
pytest tests/test_main.py::test_scan_directory
```

## Troubleshooting

### Common Issues

**Permission denied errors:**
- Ensure you have read permissions for the target directory
- Some system directories may require elevated privileges
- Check file system permissions and ownership

**No owners/groups found:**
- Verify the directory exists and is accessible
- Check exclusion rules in configuration
- Ensure files exist in the target directory

**UID/GID not found:**
- System users or groups may have been deleted
- Tool will display UID/GID as numbers if names not found
- This is normal for some system files

**Large directory scanning:**
- Scanning very large directories may take time
- Consider using exclusions to skip unnecessary directories
- Use non-recursive scan for specific directories
- Check logs for progress information

### Error Messages

The tool provides detailed error messages in logs. Check `logs/ownership_analyzer.log` for:
- Permission errors
- File access issues
- Directory scanning problems
- Statistics calculation errors

### Performance Tips

- Use exclusions to skip large unnecessary directories (e.g., `.git`, `node_modules`)
- Scan specific subdirectories instead of entire filesystem
- Use non-recursive scan when searching specific directories
- Consider scanning during off-peak hours for large filesystems

## Security Considerations

- This tool only reads file metadata, it does not modify files
- Requires read access to directories being scanned
- Be cautious when scanning system directories (may require sudo)
- Reports may contain sensitive path information
- Review exclusion rules to avoid scanning sensitive directories

## Platform Compatibility

This tool is designed for Unix-like systems (Linux, macOS) that support:
- `pwd` module for user information
- `grp` module for group information
- `os.stat()` for file metadata

Windows systems are not fully supported due to different permission models.

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
