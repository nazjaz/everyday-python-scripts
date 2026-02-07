# Modification Pattern Finder

A Python automation script that finds files with specific modification patterns such as files modified at certain times of day or on specific days of the week. Useful for identifying files modified during specific time periods, analyzing file activity patterns, and auditing file modifications.

## Features

- **Time of day filtering**: Find files modified within specific time ranges (e.g., 9 AM to 5 PM)
- **Day of week filtering**: Find files modified on specific days (e.g., Mondays, Fridays)
- **Combined patterns**: Combine time and day filters for precise matching
- **File pattern filtering**: Optionally filter by file extensions or patterns
- **Recursive scanning**: Optionally scan directories recursively
- **Comprehensive reporting**: Detailed reports with file information and modification times
- **Error handling**: Graceful handling of permission errors and file access issues

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd modification-pattern-finder
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
time_start: "09:00"
time_end: "17:00"
days_of_week: ["monday", "tuesday", "wednesday", "thursday", "friday"]
file_patterns: [".py", ".txt"]
recursive: true
```

## Usage

### Basic Usage

Find files in a directory:

```bash
python src/main.py /path/to/directory
```

### Filter by Time of Day

Find files modified between 9 AM and 5 PM:

```bash
python src/main.py /path/to/directory --time-start 09:00 --time-end 17:00
```

### Filter by Day of Week

Find files modified on Mondays:

```bash
python src/main.py /path/to/directory --days monday
```

### Filter by Multiple Days

Find files modified on weekdays:

```bash
python src/main.py /path/to/directory --days monday tuesday wednesday thursday friday
```

### Combine Time and Day Filters

Find files modified on weekdays between 9 AM and 5 PM:

```bash
python src/main.py /path/to/directory \
  --time-start 09:00 \
  --time-end 17:00 \
  --days monday tuesday wednesday thursday friday
```

### Filter by File Type

Find only Python files:

```bash
python src/main.py /path/to/directory --file-patterns .py
```

### Recursive Scanning

Recursively scan directories:

```bash
python src/main.py /path/to/directory --recursive
```

### Save Report to File

Save results to a file:

```bash
python src/main.py /path/to/directory --output report.txt
```

### Use Configuration File

```bash
python src/main.py /path/to/directory --config config.yaml
```

### Command-Line Arguments

- `paths`: File paths or directory paths to scan (required, one or more)
- `--time-start`: Start time of day (HH:MM or HH:MM:SS)
- `--time-end`: End time of day (HH:MM or HH:MM:SS)
- `--days`: Days of week to filter (e.g., monday friday)
- `--file-patterns`: File extensions or patterns to include
- `--recursive`: Recursively scan directories
- `--output`: Output file path for report
- `--config`: Path to configuration file (YAML)

## Project Structure

```
modification-pattern-finder/
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

- `src/main.py`: Core implementation with ModificationPatternFinder class and CLI interface
- `config.yaml`: Default configuration file with filtering settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

## Time Format

Time values can be specified in two formats:
- `HH:MM` (e.g., "09:00", "17:30")
- `HH:MM:SS` (e.g., "09:00:00", "17:30:45")

## Day of Week Format

Days can be specified as:
- Full names: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`
- Abbreviations: `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`

Case-insensitive.

## Output Format

The script provides a formatted report:

```
Modification Pattern Analysis Report
================================================================================

Files scanned: 150
Files matched: 25
Errors: 0

Time filter: from 09:00:00 to 17:00:00

Days of week: Monday, Tuesday, Wednesday, Thursday, Friday

--------------------------------------------------------------------------------

File: /path/to/file1.py
  Name: file1.py
  Size: 1,234 bytes
  Modified: 2024-01-15T14:30:00
  Day: Monday

File: /path/to/file2.txt
  Name: file2.txt
  Size: 5,678 bytes
  Modified: 2024-01-16T10:15:00
  Day: Tuesday
```

## Use Cases

### Find Files Modified During Business Hours

```bash
python src/main.py /path/to/files \
  --time-start 09:00 \
  --time-end 17:00 \
  --days monday tuesday wednesday thursday friday
```

### Find Files Modified on Weekends

```bash
python src/main.py /path/to/files --days saturday sunday
```

### Find Files Modified at Night

```bash
python src/main.py /path/to/files \
  --time-start 22:00 \
  --time-end 06:00
```

### Find Log Files Modified During Specific Hours

```bash
python src/main.py /path/to/logs \
  --time-start 00:00 \
  --time-end 06:00 \
  --file-patterns .log
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
- Time pattern matching
- Day of week filtering
- File pattern filtering
- Time parsing
- Day parsing
- Error handling

## Troubleshooting

### Common Issues

**Issue: "Invalid time format"**

Solution: Use format HH:MM or HH:MM:SS. Examples: "09:00", "17:30:00"

**Issue: "Invalid day of week"**

Solution: Use valid day names: monday, tuesday, wednesday, thursday, friday, saturday, sunday (or abbreviations)

**Issue: "time_start must be before time_end"**

Solution: Ensure start time is before end time. For overnight ranges (e.g., 22:00 to 06:00), the script handles this automatically.

**Issue: "No files found"**

Solution: Verify that:
- Files exist in the specified paths
- Files match the time and day patterns
- Files match the file pattern filters (if specified)
- You have read permissions for the files

**Issue: "Permission denied"**

Solution: Ensure you have read permissions for the files you're trying to scan.

### Error Messages

All errors are logged to both the console and `logs/finder.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `finder.log`: Main log file with all operations and errors

## Performance Considerations

- Scanning large directory trees may take time
- Recursive scanning of deeply nested directories may be slow
- File system metadata access is generally fast
- Pattern matching is efficient for typical use cases

## Best Practices

1. **Use specific time ranges**: Narrow time ranges reduce false positives
2. **Combine filters**: Use time and day filters together for precise matching
3. **Filter by file type**: Use file patterns to focus on relevant file types
4. **Use recursive scanning**: Enable recursive scanning for complete analysis
5. **Review results**: Check the generated reports to verify matches

## Limitations

- **Time zone**: Uses system time zone for file modification times
- **Precision**: File system modification times may have limited precision
- **Overnight ranges**: Time ranges spanning midnight are supported but may need careful specification

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
