# File Usage Tracker

A Python automation script that tracks file usage frequency by monitoring access times, organizing files by how often they are accessed or modified. Useful for identifying frequently used files, cleaning up unused files, and optimizing file organization based on usage patterns.

## Features

- **Access time tracking**: Monitors and records file access times
- **Usage frequency calculation**: Calculates access and modification frequency over time
- **Frequency-based organization**: Organizes files by usage frequency categories
- **Database storage**: Stores tracking data in SQLite database for historical analysis
- **Multiple organization methods**: Organize by frequency, access count, or modification count
- **Usage reporting**: Generates detailed reports of file usage patterns
- **Recursive scanning**: Optionally scan directories recursively
- **Dry run mode**: Simulate organization without moving files

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd file-usage-tracker
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
database: "./file_usage.db"
tracking_window_days: 30
organize_by: "frequency"
recursive: false
```

## Usage

### Track File Usage

Record current file access times:

```bash
python src/main.py /path/to/files --track
```

### Generate Usage Report

Generate a report of file usage frequency:

```bash
python src/main.py /path/to/files --report
```

### Organize Files by Frequency

Organize files based on usage frequency:

```bash
python src/main.py /path/to/files --organize ./organized --organize-by frequency
```

### Organize by Access Count

Organize files by access frequency only:

```bash
python src/main.py /path/to/files --organize ./organized --organize-by access
```

### Organize by Modification Count

Organize files by modification frequency:

```bash
python src/main.py /path/to/files --organize ./organized --organize-by modification
```

### Dry Run

Preview organization without moving files:

```bash
python src/main.py /path/to/files --organize ./organized --dry-run
```

### Recursive Scanning

Scan directories recursively:

```bash
python src/main.py /path/to/directory --track --recursive
```

### Save Report to File

Save usage report to a file:

```bash
python src/main.py /path/to/files --report --output report.txt
```

### Export to JSON

Export report as JSON:

```bash
python src/main.py /path/to/files --report --json report.json
```

### Use Configuration File

```bash
python src/main.py /path/to/files --config config.yaml --track
```

### Command-Line Arguments

- `paths`: File paths or directory paths to track (required, one or more)
- `--database`: Path to SQLite database file (default: file_usage.db)
- `--track`: Track file access times (record current state)
- `--organize`: Organize files to destination directory
- `--organize-by`: Organization method - frequency, access, or modification (default: frequency)
- `--window-days`: Tracking window in days (default: 30)
- `--recursive`: Recursively scan directories
- `--dry-run`: Simulate organization without moving files
- `--report`: Generate usage frequency report
- `--output`: Output file path for text report
- `--json`: Output JSON file path for report
- `--config`: Path to configuration file (YAML)

## Project Structure

```
file-usage-tracker/
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

- `src/main.py`: Core implementation with FileUsageTracker class and CLI interface
- `config.yaml`: Default configuration file with tracking settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)
- `file_usage.db`: SQLite database file (created automatically)

## Frequency Categories

Files are categorized based on usage frequency:

- **very_frequent**: 50+ accesses/modifications
- **frequent**: 20-49 accesses/modifications
- **moderate**: 5-19 accesses/modifications
- **occasional**: 1-4 accesses/modifications
- **rare**: 0 accesses/modifications

## Organization Methods

### By Frequency

Organizes files by overall usage frequency (access + modification):

```
organized/
├── very_frequent/
│   └── frequently_used_file.txt
├── frequent/
│   └── often_used_file.txt
├── moderate/
│   └── sometimes_used_file.txt
├── occasional/
│   └── rarely_used_file.txt
└── rare/
    └── unused_file.txt
```

### By Access

Organizes files by access frequency only:

```
organized/
├── high_access/
├── medium_access/
└── low_access/
```

### By Modification

Organizes files by modification frequency only:

```
organized/
├── high_modification/
├── medium_modification/
└── low_modification/
```

## Database Schema

The SQLite database stores:

- **file_access_log**: Historical log of file accesses
  - file_path, access_time, modification_time, file_size

- **file_metadata**: Aggregated file usage statistics
  - file_path, first_seen, last_accessed, last_modified
  - access_count, modification_count

## Output Format

### Text Report

```
File Usage Frequency Report
================================================================================

Files analyzed: 25
Tracking window: 30 days

--------------------------------------------------------------------------------

File: /path/to/file1.txt
  Access count: 15
  Modification count: 3
  Frequency category: moderate
  Last accessed: 2024-01-15T14:30:00
  Last modified: 2024-01-10T10:00:00
```

### JSON Report

```json
[
  {
    "path": "/path/to/file1.txt",
    "name": "file1.txt",
    "size": 1234,
    "access_count": 15,
    "modification_count": 3,
    "frequency_category": "moderate",
    "last_accessed": "2024-01-15T14:30:00",
    "last_modified": "2024-01-10T10:00:00"
  }
]
```

## Use Cases

### Identify Frequently Used Files

```bash
python src/main.py /path/to/files --track --report
```

### Organize Files by Usage

```bash
python src/main.py /path/to/files --organize ./organized --organize-by frequency
```

### Find Unused Files

```bash
python src/main.py /path/to/files --report | grep "rare"
```

### Clean Up Old Files

Track files over time, then organize rarely used files:

```bash
python src/main.py /path/to/files --track
# Wait some time, then:
python src/main.py /path/to/files --organize ./archive --organize-by frequency
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
- Database operations
- Access time tracking
- Frequency calculation
- File organization
- Report generation
- Error handling

## Troubleshooting

### Common Issues

**Issue: "No file usage data found"**

Solution: Run `--track` first to record file access times. The script needs historical data to calculate frequency.

**Issue: "Permission denied"**

Solution: Ensure you have read permissions for files you're tracking and write permissions for the database and destination directories.

**Issue: "Database locked"**

Solution: Ensure no other process is using the database file. Close any other instances of the script.

**Issue: "Files not organizing correctly"**

Solution: Verify that:
- You've run `--track` multiple times to build usage history
- The tracking window (`--window-days`) is appropriate
- Files have been accessed/modified within the tracking window

### Error Messages

All errors are logged to both the console and `logs/tracker.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `tracker.log`: Main log file with all operations and errors

## Best Practices

1. **Regular tracking**: Run `--track` regularly to build accurate usage history
2. **Appropriate window**: Set `--window-days` based on your needs (30 days is a good default)
3. **Review before organizing**: Use `--report` to review files before organizing
4. **Use dry run**: Always use `--dry-run` first when organizing files
5. **Backup important files**: Ensure important files are backed up before organization

## Performance Considerations

- Database operations are efficient for typical use cases
- Scanning large directory trees may take time
- Recursive scanning of deeply nested directories may be slow
- Frequency calculation queries are optimized with database indexes

## Limitations

- **Access time precision**: File system access times may have limited precision
- **Time zone**: Uses system time zone for all timestamps
- **Historical data**: Requires multiple tracking runs to build meaningful frequency data
- **File system differences**: Access time behavior may vary by file system

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
