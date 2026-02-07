# Usage Frequency Organizer

A Python automation tool for organizing files by usage frequency. This script analyzes file access times and organizes files into categories based on how frequently they are accessed: frequently accessed files, occasionally used files, rarely accessed files, and archived files.

## Features

- **Usage Frequency Analysis**: Analyzes file access times to determine usage frequency
- **Four-Tier Organization**: Categorizes files into:
  - **Frequent**: Files accessed within 7 days (configurable)
  - **Occasional**: Files accessed within 30 days (configurable)
  - **Rare**: Files accessed within 90 days (configurable)
  - **Archive**: Files accessed beyond 90 days (configurable)
- **Access Time Tracking**: Uses file system access times (st_atime) for analysis
- **Modification Time Fallback**: Uses modification time if access time is unavailable
- **Duplicate Detection**: Uses content hashing to detect and skip duplicate files
- **Structure Preservation**: Optional preservation of directory structure
- **Comprehensive Logging**: Detailed logging with rotation
- **Configurable Thresholds**: Customize frequency thresholds for your needs

## Prerequisites

- Python 3.8 or higher
- Write permissions to source and destination directories
- Sufficient disk space for file organization
- File system that supports access time tracking (most modern systems)

## Installation

1. Clone or navigate to the project directory:
```bash
cd usage-frequency-organizer
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
   - Set frequency thresholds (days)
   - Configure source and destination directories
   - Adjust filtering options

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory to organize (default: current directory)
- **frequency_thresholds.frequent_days**: Days threshold for frequent files (default: 7)
- **frequency_thresholds.occasional_days**: Days threshold for occasional files (default: 30)
- **frequency_thresholds.rare_days**: Days threshold for rare files (default: 90)
- **organization.frequent_directory**: Directory for frequent files (default: ./frequent)
- **organization.occasional_directory**: Directory for occasional files (default: ./occasional)
- **organization.rare_directory**: Directory for rare files (default: ./rare)
- **organization.archive_directory**: Directory for archived files (default: ./archive)
- **organization.preserve_structure**: Preserve directory structure (default: false)
- **organization.check_duplicates**: Enable duplicate detection (default: true)

### Usage Categories

Files are categorized based on days since last access:

- **Frequent**: 0-7 days (default) - Files you use regularly
- **Occasional**: 8-30 days (default) - Files used occasionally
- **Rare**: 31-90 days (default) - Files rarely accessed
- **Archive**: 90+ days (default) - Long-unused files for archiving

### Environment Variables

Optional environment variables can override configuration:

- `SOURCE_DIRECTORY`: Override source directory path
- `FREQUENT_DIRECTORY`: Override frequent directory path
- `OCCASIONAL_DIRECTORY`: Override occasional directory path
- `RARE_DIRECTORY`: Override rare directory path
- `ARCHIVE_DIRECTORY`: Override archive directory path

## Usage

### Basic Usage

Organize files with default configuration:
```bash
python src/main.py
```

### Dry Run

Preview what would be organized without making changes:
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
usage-frequency-organizer/
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

1. **File Discovery**: Recursively scans the source directory for files, excluding system directories and files.

2. **Access Time Analysis**: For each file:
   - Retrieves access time (st_atime) from file system
   - Falls back to modification time if access time is unavailable
   - Calculates days since last access

3. **Frequency Calculation**: Determines usage category based on thresholds:
   - Compares days since access to configured thresholds
   - Assigns frequency score (0.0 to 1.0)
   - Categorizes into frequent, occasional, rare, or archive

4. **Organization**: Moves files to appropriate category directories:
   - Frequent files → frequent_directory
   - Occasional files → occasional_directory
   - Rare files → rare_directory
   - Archive files → archive_directory

5. **Duplicate Detection**: Uses content hashing to prevent duplicate files from being organized multiple times.

6. **Logging**: All operations are logged with timestamps and context.

## Example Scenarios

### Scenario 1: Recently Accessed File
- **File**: `report.pdf` (accessed 2 days ago)
- **Category**: Frequent
- **Destination**: `./frequent/report.pdf`

### Scenario 2: Occasionally Used File
- **File**: `presentation.pptx` (accessed 15 days ago)
- **Category**: Occasional
- **Destination**: `./occasional/presentation.pptx`

### Scenario 3: Rarely Accessed File
- **File**: `old_document.doc` (accessed 60 days ago)
- **Category**: Rare
- **Destination**: `./rare/old_document.doc`

### Scenario 4: Archived File
- **File**: `backup_2020.zip` (accessed 200 days ago)
- **Category**: Archive
- **Destination**: `./archive/backup_2020.zip`

## Troubleshooting

### Files Not Being Organized

If files are not being organized:
- Check that files have valid access times
- Verify source directory path is correct
- Ensure files are not excluded by filters
- Review logs for specific error messages

### Incorrect Categorization

If files are categorized incorrectly:
- Verify access times are being tracked by your file system
- Some file systems may not update access times (e.g., some Linux configurations)
- Check that modification time fallback is enabled
- Review frequency thresholds in configuration

### Access Time Not Available

If access times are not available:
- The script uses modification time as fallback
- Some file systems disable access time tracking for performance
- Check file system mount options (noatime flag)
- Consider using modification time as primary metric

### Permission Errors

If you encounter permission errors:
- Ensure read access to source directory
- Ensure write access to destination directories
- Check file and directory permissions
- Some files may be skipped with warnings

### Duplicate Detection Issues

If duplicates are not detected:
- Ensure check_duplicates is enabled in config
- Hashes are stored per category directory
- Same content in different categories will be saved separately

## File System Considerations

### Access Time Tracking

- **macOS**: Access times are tracked by default
- **Linux**: May require `relatime` or `strictatime` mount options
- **Windows**: Access times are tracked by default
- Some file systems disable access time tracking for performance

### Performance Impact

- Access time tracking can have performance implications
- Some systems disable it by default
- The script falls back to modification time if access time is unavailable

## Security Considerations

- The script performs file move operations
- Always use `--dry-run` first to preview changes
- Ensure backups are in place before organizing important files
- Duplicate detection reads file contents but does not modify them
- The script does not process files outside the specified source directory

## Performance Considerations

- Processing time increases with number of files
- Duplicate detection can be slow for large files
- Consider processing during off-peak hours for large directories
- Access time retrieval is fast but may be limited by file system performance

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
