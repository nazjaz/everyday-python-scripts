# Priority File Organizer

A Python automation tool that organizes files into priority-based folder structures based on importance tags, file patterns, extensions, keywords, and other criteria defined in configuration. This tool helps maintain organized file systems by automatically categorizing files by their importance level.

## Project Title and Description

The Priority File Organizer scans directories and organizes files into priority-based folder structures. Files are categorized based on configurable criteria including file patterns, extensions, keywords, and size ranges. Each priority level has its own folder, allowing users to quickly identify and access files based on their importance.

This tool solves the problem of maintaining organized file systems by automatically sorting files by priority, making it easier to focus on important files and archive less critical ones.

**Target Audience**: System administrators, project managers, developers, and anyone managing large collections of files who need to organize them by importance.

## Features

- Configurable priority levels with custom criteria
- Multiple matching criteria: file patterns, extensions, keywords, size ranges
- Automatic duplicate detection using content hashing
- Priority-based folder structure creation
- Dry-run mode for safe testing
- Comprehensive logging of all operations
- Detailed organization reports
- Configurable duplicate handling (skip, delete, move)
- Skip patterns for excluding system/development directories
- Filename conflict resolution

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Write access to directories being organized

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/priority-file-organizer
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

### Step 4: Verify Installation

```bash
python src/main.py --help
```

## Configuration

### Configuration File (config.yaml)

The tool uses a YAML configuration file to define priority levels and their criteria. The default configuration file is `config.yaml` in the project root.

#### Priority Level Structure

Each priority level requires:
- `name`: Unique name for the priority level
- `priority`: Numeric value (higher = more important)
- `folder`: Folder name where files will be organized
- `criteria`: Matching criteria (one or more of the following):
  - `patterns`: List of file path patterns (supports wildcards)
  - `extensions`: List of file extensions
  - `keywords`: List of keywords to search in file paths
  - `size_range`: Dictionary with `min` and `max` file sizes in bytes

#### Key Configuration Options

**Organization Settings:**
- `organization.base_folder`: Base folder where organized files are placed (default: "organized")

**Priority Levels:**
- Multiple priority levels sorted by priority value
- Each level can have multiple criteria types
- Files match the first priority level they meet criteria for

**Duplicate Handling:**
- `duplicates.action`: Action for duplicates - "skip", "delete", or "move" (default: "skip")

**Scan Settings:**
- `scan.skip_patterns`: List of path patterns to skip during scanning

**Report Settings:**
- `report.output_file`: Path for organization report (default: "organization_report.txt")

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
organization:
  base_folder: "organized"

priorities:
  - name: "critical"
    priority: 5
    folder: "Critical"
    criteria:
      keywords:
        - "contract"
        - "legal"
      extensions:
        - ".pdf"
        - ".docx"

  - name: "high"
    priority: 4
    folder: "High"
    criteria:
      extensions:
        - ".xlsx"
        - ".pptx"

duplicates:
  action: "skip"

scan:
  skip_patterns:
    - ".git"
    - "__pycache__"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Organize files in a directory:

```bash
python src/main.py /path/to/directory
```

### Dry Run Mode

Test organization without moving files:

```bash
python src/main.py /path/to/directory --dry-run
```

### Specify Custom Configuration

```bash
python src/main.py /path/to/directory -c custom_config.yaml
```

### Custom Report Output

```bash
python src/main.py /path/to/directory -r custom_report.txt
```

### Combined Options

```bash
python src/main.py /path/to/directory -c config.yaml --dry-run -r report.txt
```

### Command-Line Arguments

- `directory`: (Required) Directory path to organize files in
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Simulate organization without moving files
- `-r, --report`: Custom output path for organization report

### Common Use Cases

**Organize Project Files:**
1. Configure priority levels in `config.yaml`
2. Run: `python src/main.py ~/projects`
3. Files are organized into priority-based folders

**Test Before Organizing:**
1. Run with `--dry-run` flag first
2. Review logs to see what would be organized
3. Adjust configuration if needed
4. Run without `--dry-run` to actually organize

**Organize Downloads Folder:**
```bash
python src/main.py ~/Downloads
```

**Organize with Custom Priorities:**
1. Create custom `config.yaml` with your priority definitions
2. Run: `python src/main.py /path/to/files -c custom_config.yaml`

## Project Structure

```
priority-file-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation
└── logs/
    └── .gitkeep             # Placeholder for logs directory
```

### File Descriptions

- `src/main.py`: Contains the `PriorityFileOrganizer` class and main logic
- `config.yaml`: Configuration file with priority levels and settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `organized/`: Directory created at runtime for organized files
- `logs/`: Directory for application log files

## Testing

### Run Tests

```bash
python -m pytest tests/
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage, testing:
- Configuration loading and validation
- Priority level matching logic
- File pattern matching
- Extension matching
- Keyword matching
- Duplicate detection
- File organization operations
- Error handling

## Troubleshooting

### Common Issues

**Files Not Being Organized:**
- Check that priority criteria match your files
- Review logs for detailed matching information
- Ensure files don't match skip patterns
- Verify file permissions

**Permission Errors:**
- Ensure you have read access to source directory
- Ensure you have write access to destination
- Check file ownership and permissions

**Too Many Files Organized:**
- Review priority criteria - they may be too broad
- Adjust patterns, extensions, or keywords
- Use more specific criteria

**Duplicate Detection Not Working:**
- Verify files are actually duplicates (same content)
- Check that duplicate action is configured correctly
- Review logs for duplicate detection messages

### Error Messages

**"No priority levels defined"**: The config.yaml file doesn't have any priority levels. Add at least one priority level.

**"Priority level missing 'name' field"**: A priority level in config.yaml is missing required fields. Check YAML structure.

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

### Best Practices

1. **Always test with `--dry-run` first** to see what will be organized
2. **Backup important files** before running organization
3. **Start with specific criteria** and expand as needed
4. **Review logs** to understand matching behavior
5. **Use skip patterns** to exclude system and development directories
6. **Configure duplicate handling** based on your needs

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guidelines
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Include docstrings for all public functions and classes
- Use meaningful variable names
- Write tests for all new functionality

### Pull Request Process

1. Ensure code follows project standards
2. Update documentation if needed
3. Add/update tests
4. Ensure all tests pass
5. Submit PR with clear description of changes

## License

This project is part of the everyday-python-scripts collection. Please refer to the parent repository for license information.
