# Project Cleanup

A Python automation tool for cleaning up old project folders based on inactivity. This script scans a directory for project folders, identifies inactive projects, and either archives or removes them according to configurable thresholds.

## Features

- Scans directories for project folders using configurable indicators
- Detects project inactivity based on last modification time
- Archives inactive projects to a designated archive directory
- Optionally removes projects that have been inactive for extended periods
- Configurable inactivity thresholds for archiving and removal
- Dry-run mode to preview changes without making modifications
- Comprehensive logging with rotation
- Excludes system directories and files from modification time checks
- Handles errors gracefully with detailed error reporting

## Prerequisites

- Python 3.8 or higher
- Write permissions to source and archive directories
- Sufficient disk space for archiving operations

## Installation

1. Clone or navigate to the project directory:
```bash
cd project-cleanup
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

5. Review and customize `config.yaml` with your settings:
   - Set `source_directory` to the directory containing projects to scan
   - - Set `archive_directory` to where archived projects should be stored
   - Configure inactivity thresholds in the `actions` section

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory to scan for projects (default: current directory)
- **archive_directory**: Where to store archived projects (default: ./archive)
- **actions.archive_after_days**: Days of inactivity before archiving (default: 90)
- **actions.remove_after_days**: Days of inactivity before removal (default: 365)
- **actions.enable_removal**: Whether to enable permanent removal (default: false)
- **filtering.exclude_directories**: Directories to exclude from scanning
- **filtering.exclude_files**: File patterns to exclude from modification checks
- **filtering.project_indicators**: Files that identify a directory as a project

### Environment Variables

Optional environment variables can override configuration:

- `SOURCE_DIRECTORY`: Override source directory path
- `ARCHIVE_DIRECTORY`: Override archive directory path

## Usage

### Basic Usage

Run the cleanup script with default configuration:
```bash
python src/main.py
```

### Dry Run

Preview what would be done without making changes:
```bash
python src/main.py --dry-run
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config /path/to/custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Perform a dry run without making changes
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
project-cleanup/
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
│   └── API.md               # API documentation (if applicable)
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

1. **Scanning**: The script scans the source directory for folders that appear to be projects based on configurable indicators (e.g., README.md, requirements.txt).

2. **Inactivity Detection**: For each project, it checks the last modification time by examining all files in the project directory (excluding system files and directories).

3. **Action Decision**: Projects are categorized based on inactivity:
   - Active: Modified within the archive threshold - skipped
   - Archive candidate: Inactive for archive threshold but less than removal threshold - archived
   - Removal candidate: Inactive for removal threshold - removed (if enabled)

4. **Processing**: Projects are either:
   - Archived: Moved to the archive directory with a timestamp suffix
   - Removed: Permanently deleted from the filesystem
   - Skipped: Left unchanged if still active

5. **Logging**: All operations are logged with timestamps, and a summary is displayed at the end.

## Troubleshooting

### Permission Errors

If you encounter permission errors:
- Ensure you have read access to the source directory
- Ensure you have write access to the archive directory
- Check file and directory permissions

### Projects Not Detected

If projects are not being detected:
- Verify the project has at least one indicator file listed in `config.yaml`
- Check that the project directory is not in the exclude list
- Ensure the source directory path is correct

### Archive Directory Issues

If archiving fails:
- Verify the archive directory path is writable
- Check available disk space
- Ensure no file conflicts exist (e.g., duplicate project names)

### Configuration Errors

If configuration errors occur:
- Validate YAML syntax in `config.yaml`
- Ensure all required configuration keys are present
- Check that paths are valid and accessible

## Security Considerations

- The script performs destructive operations (archiving and removal)
- Always use `--dry-run` first to preview changes
- Ensure backups are in place before enabling removal
- Review excluded directories to prevent accidental processing of system files
- The script does not process files outside the specified source directory

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
