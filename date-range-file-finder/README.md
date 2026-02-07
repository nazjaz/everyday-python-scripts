# Date Range File Finder

A Python automation script that finds files modified within a specific date range. Useful for locating files created or changed during particular time periods, auditing file modifications, and tracking changes in directory structures.

## Features

- Search for files modified within a specified date range
- Support for recursive directory traversal
- Optional file pattern filtering (glob patterns)
- Configurable via command-line arguments or YAML configuration file
- Detailed output with file paths, modification dates, and file sizes
- Export results to a file
- Comprehensive logging for debugging and audit trails

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd date-range-file-finder
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

### Step 4: Set Up Configuration (Optional)

Copy the example configuration file and customize as needed:

```bash
cp config.yaml config.yaml.local
# Edit config.yaml.local with your preferred settings
```

## Configuration

### Configuration File (config.yaml)

The script supports configuration via a YAML file:

```yaml
search_path: "."              # Directory to search
recursive: true               # Search subdirectories
file_pattern: null            # Optional glob pattern (e.g., "*.txt")
```

### Environment Variables

While the script primarily uses command-line arguments and configuration files, you can set default paths via environment variables if needed. See `.env.example` for reference.

## Usage

### Basic Usage

Find all files modified between two dates:

```bash
python src/main.py --start-date "2024-01-01" --end-date "2024-01-31"
```

### Advanced Usage

Search in a specific directory:

```bash
python src/main.py \
  --start-date "2024-01-01" \
  --end-date "2024-01-31" \
  --path "/path/to/search"
```

Search only for Python files:

```bash
python src/main.py \
  --start-date "2024-01-01" \
  --end-date "2024-01-31" \
  --pattern "*.py"
```

Non-recursive search (current directory only):

```bash
python src/main.py \
  --start-date "2024-01-01" \
  --end-date "2024-01-31" \
  --no-recursive
```

Use configuration file:

```bash
python src/main.py \
  --start-date "2024-01-01" \
  --end-date "2024-01-31" \
  --config config.yaml
```

Save results to file:

```bash
python src/main.py \
  --start-date "2024-01-01" \
  --end-date "2024-01-31" \
  --output results.txt
```

### Date Format

Dates can be specified in two formats:
- `YYYY-MM-DD` (e.g., "2024-01-15")
- `YYYY-MM-DD HH:MM:SS` (e.g., "2024-01-15 14:30:00")

### Command-Line Arguments

- `--start-date`: Start date of the range (required)
- `--end-date`: End date of the range (required)
- `--path`: Directory path to search (default: current directory)
- `--no-recursive`: Disable recursive directory search
- `--pattern`: File pattern to match (glob pattern, e.g., "*.txt")
- `--config`: Path to configuration file (YAML)
- `--output`: Output file path to save results

## Project Structure

```
date-range-file-finder/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main script implementation
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation (if applicable)
└── logs/
    └── .gitkeep             # Log directory placeholder
```

### File Descriptions

- `src/main.py`: Core implementation with DateRangeFileFinder class and CLI interface
- `config.yaml`: Default configuration file with search parameters
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

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
- Date range validation
- File finding functionality
- Pattern matching
- Recursive and non-recursive searches
- Error handling for invalid paths and permissions
- Configuration file loading

## Troubleshooting

### Common Issues

**Issue: "Search path does not exist"**

Solution: Verify the path exists and is accessible. Use absolute paths or ensure relative paths are correct from the current working directory.

**Issue: "Permission denied"**

Solution: Ensure you have read permissions for the directory and files you're trying to search. On Unix systems, you may need to use `sudo` or adjust file permissions.

**Issue: "Invalid date format"**

Solution: Use the correct date format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`. Ensure dates are valid (e.g., not February 30th).

**Issue: "No files found"**

Solution: Verify that:
- The date range is correct
- Files actually exist in the specified directory
- The file pattern (if used) matches your files
- You have the correct permissions to read file metadata

**Issue: "Configuration file not found"**

Solution: Ensure the config file path is correct. Use absolute paths or paths relative to the current working directory.

### Error Messages

All errors are logged to both the console and `logs/file_finder.log`. Check the log file for detailed error information and stack traces.

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
