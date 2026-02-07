# File Activity Organizer

A Python automation tool for organizing files by activity level based on modification and access frequencies. This script tracks file activity, categorizes files as active, archived, or dormant, and organizes them into appropriate directories.

## Features

- Tracks file modification and access times to determine activity levels
- Categorizes files into three activity levels: active, archived, and dormant
- Organizes files into separate directories based on activity category
- Detects duplicate files using MD5 hash comparison
- Configurable activity thresholds for each category
- Preserves directory structure option
- Handles file name conflicts with timestamp-based renaming
- Comprehensive logging with rotation
- Excludes system files and directories from processing
- Dry-run mode to preview changes without making modifications

## Prerequisites

- Python 3.8 or higher
- Write permissions to source and destination directories
- Sufficient disk space for file organization operations

## Installation

1. Clone or navigate to the project directory:
```bash
cd file-activity-organizer
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
   - Set `source_directory` to the directory containing files to organize
   - Configure activity thresholds in the `activity_thresholds` section
   - Set destination directories for each activity category
   - Configure filtering options

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory to scan for files (default: current directory)
- **organization.active_directory**: Directory for active files (default: ./active)
- **organization.archived_directory**: Directory for archived files (default: ./archived)
- **organization.dormant_directory**: Directory for dormant files (default: ./dormant)
- **organization.preserve_structure**: Whether to preserve directory structure (default: false)
- **organization.skip_duplicates**: Skip files if destination exists (default: true)
- **activity_thresholds.active_days**: Days threshold for active files (default: 30)
- **activity_thresholds.archived_days**: Days threshold for archived files (default: 90)
- **activity_thresholds.dormant_days**: Days threshold for dormant files (default: 365)
- **filtering.exclude_directories**: Directories to exclude from scanning
- **filtering.exclude_files**: File patterns to exclude
- **filtering.exclude_extensions**: File extensions to exclude

### Activity Categories

Files are categorized based on the most recent of modification time or access time:

- **Active**: Files modified or accessed within the active threshold (default: 30 days)
- **Archived**: Files modified or accessed within the archived threshold but beyond active (default: 90 days)
- **Dormant**: Files modified or accessed beyond the archived threshold (default: 365+ days)

### Environment Variables

Optional environment variables can override configuration:

- `SOURCE_DIRECTORY`: Override source directory path
- `ACTIVE_DIRECTORY`: Override active directory path
- `ARCHIVED_DIRECTORY`: Override archived directory path
- `DORMANT_DIRECTORY`: Override dormant directory path

## Usage

### Basic Usage

Run the organizer with default configuration:
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

### Skip Duplicate Detection

Skip duplicate file detection for faster processing:
```bash
python src/main.py --no-duplicates
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Perform a dry run without making changes
- `-v, --verbose`: Enable verbose logging
- `--no-duplicates`: Skip duplicate detection

## Project Structure

```
file-activity-organizer/
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

1. **Scanning**: The script recursively scans the source directory for files, excluding system files and directories specified in the configuration.

2. **Activity Tracking**: For each file, it retrieves:
   - Last modification time
   - Last access time
   - File size

3. **Categorization**: Files are categorized based on the most recent activity (modification or access time):
   - Active: Recent activity within the active threshold
   - Archived: Moderate activity within the archived threshold
   - Dormant: Old activity beyond the archived threshold

4. **Duplicate Detection**: Optionally calculates MD5 hashes to identify duplicate files and reports them in the logs.

5. **Organization**: Files are moved to their respective activity category directories:
   - Active files → active_directory
   - Archived files → archived_directory
   - Dormant files → dormant_directory

6. **Conflict Handling**: If a file with the same name exists in the destination, the script either skips it (if configured) or renames it with a timestamp.

7. **Logging**: All operations are logged with timestamps, and a summary is displayed at the end.

## Troubleshooting

### Permission Errors

If you encounter permission errors:
- Ensure you have read access to the source directory
- Ensure you have write access to destination directories
- Check file and directory permissions

### Files Not Being Processed

If files are not being processed:
- Check that files are not in the exclude lists
- Verify the source directory path is correct
- Ensure files are not hidden or system files

### Duplicate Detection Performance

If duplicate detection is slow:
- Use `--no-duplicates` flag to skip duplicate detection
- Consider processing smaller directories at a time
- Duplicate detection processes files in chunks for efficiency

### Organization Directory Issues

If organization fails:
- Verify destination directory paths are writable
- Check available disk space
- Ensure no file conflicts exist (script handles this automatically)

### Configuration Errors

If configuration errors occur:
- Validate YAML syntax in `config.yaml`
- Ensure all required configuration keys are present
- Check that paths are valid and accessible

## Security Considerations

- The script performs file move operations that can reorganize your file system
- Always use `--dry-run` first to preview changes
- Ensure backups are in place before running on important files
- Review excluded directories to prevent accidental processing of system files
- The script does not process files outside the specified source directory
- Duplicate detection reads file contents but does not modify them

## Performance Considerations

- Duplicate detection can be slow for large files or many files
- Processing time increases with the number of files
- File moves are atomic operations where possible
- Consider processing during off-peak hours for large directories

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
