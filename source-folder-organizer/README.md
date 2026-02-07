# Source Folder Organizer

A Python automation script that organizes files by their source folder, maintaining a mapping of original locations when moving files to organized structures. Useful for consolidating files from multiple source directories while preserving the relationship between files and their origins.

## Features

- Organize files by source folder: Maintains folder structure based on original source
- Location mapping: Tracks original file locations in JSON format
- Duplicate detection: Identifies duplicate files using SHA256 hashing
- Duplicate handling: Multiple strategies (skip, rename, overwrite)
- Dry run mode: Simulate operations without moving files
- Recursive scanning: Processes all files in source folders and subdirectories
- Comprehensive logging: Detailed logs for all operations
- Configuration support: YAML configuration file or command-line arguments
- Error handling: Graceful handling of permission errors and file conflicts

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd source-folder-organizer
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
source_folders:
  - "./source1"
  - "./source2"
destination: "./organized"
mapping_file: "./location_mapping.json"
handle_duplicates: "skip"  # Options: skip, rename, overwrite
```

### Location Mapping

The script maintains a JSON file that maps organized file locations back to their original locations. This allows you to track where files came from even after organization.

Example mapping structure:
```json
{
  "/organized/source1/file.txt": "/original/path/to/source1/file.txt",
  "/organized/source2/document.pdf": "/original/path/to/source2/document.pdf"
}
```

## Usage

### Basic Usage

Organize files from one source folder:

```bash
python src/main.py \
  --source-folders /path/to/source \
  --destination /path/to/organized
```

### Multiple Source Folders

Organize files from multiple source folders:

```bash
python src/main.py \
  --source-folders /path/to/source1 /path/to/source2 /path/to/source3 \
  --destination /path/to/organized
```

### Dry Run Mode

Simulate organization without moving files:

```bash
python src/main.py \
  --source-folders /path/to/source \
  --destination /path/to/organized \
  --dry-run
```

### Handle Duplicates

Rename duplicate files instead of skipping:

```bash
python src/main.py \
  --source-folders /path/to/source \
  --destination /path/to/organized \
  --handle-duplicates rename
```

### Use Configuration File

```bash
python src/main.py --config config.yaml
```

### Generate Mapping Report

Save a detailed mapping report to a file:

```bash
python src/main.py \
  --source-folders /path/to/source \
  --destination /path/to/organized \
  --report mapping_report.txt
```

### Command-Line Arguments

- `--source-folders`: Source folder paths to organize (space-separated, required)
- `--destination`: Root directory for organized file structure (required)
- `--mapping-file`: Path to JSON file storing location mappings (default: location_mapping.json)
- `--dry-run`: Simulate operations without moving files
- `--handle-duplicates`: How to handle duplicate files - skip, rename, or overwrite (default: skip)
- `--config`: Path to configuration file (YAML)
- `--report`: Output file path for mapping report

### Duplicate Handling Strategies

- **skip**: Skip duplicate files (files with identical content). Original file remains in source.
- **rename**: Rename duplicate files with `_copy1`, `_copy2`, etc. suffixes.
- **overwrite**: Overwrite existing files at destination with source files.

## Project Structure

```
source-folder-organizer/
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

- `src/main.py`: Core implementation with SourceFolderOrganizer class and CLI interface
- `config.yaml`: Default configuration file with source folders and destination settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)
- `location_mapping.json`: JSON file storing original-to-organized location mappings (created automatically)

## How It Works

1. **Scan Source Folders**: Recursively scans all specified source folders for files
2. **Generate Organized Paths**: Creates destination paths based on source folder names, maintaining relative structure
3. **Duplicate Detection**: Calculates SHA256 hash of files to detect duplicates
4. **Handle Duplicates**: Applies selected duplicate handling strategy
5. **Move Files**: Moves files to organized structure (or simulates in dry-run mode)
6. **Update Mapping**: Records original and organized locations in mapping file
7. **Generate Report**: Provides statistics and mapping report

### Example Organization

Given source folders:
```
source1/
  ├── documents/
  │   └── file1.txt
  └── images/
      └── photo.jpg

source2/
  └── data/
      └── report.pdf
```

Organized structure:
```
organized/
  ├── source1/
  │   ├── documents/
  │   │   └── file1.txt
  │   └── images/
  │       └── photo.jpg
  └── source2/
      └── data/
          └── report.pdf
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
- Source folder validation
- File organization functionality
- Duplicate detection and handling
- Location mapping persistence
- Error handling for invalid paths and permissions
- Configuration file loading
- Dry run mode

## Troubleshooting

### Common Issues

**Issue: "Source folder does not exist"**

Solution: Verify the source folder paths exist and are accessible. Use absolute paths or ensure relative paths are correct from the current working directory.

**Issue: "Destination root is not writable"**

Solution: Ensure you have write permissions for the destination directory. On Unix systems, you may need to use `sudo` or adjust directory permissions.

**Issue: "Permission denied" when moving files**

Solution: Ensure you have read permissions for source files and write permissions for the destination directory. Check file ownership and permissions.

**Issue: Files not appearing in organized structure**

Solution: Check the logs for errors. Verify that files were not skipped due to duplicate detection. Use `--dry-run` to preview operations.

**Issue: Mapping file not updating**

Solution: Verify write permissions for the mapping file location. Check logs for errors related to file I/O.

**Issue: "Invalid YAML in config file"**

Solution: Validate your YAML syntax. Ensure proper indentation and that all required fields are present.

### Error Messages

All errors are logged to both the console and `logs/organizer.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `organizer.log`: Main log file with all operations and errors

## Security Considerations

- The script moves files, which is a destructive operation. Always use `--dry-run` first to preview changes.
- The mapping file contains absolute paths, which may include sensitive information. Store it securely.
- File hashing for duplicate detection reads entire file contents. For very large files, this may take time.

## Performance Considerations

- Duplicate detection uses SHA256 hashing, which reads entire files. For large files or many files, this can be time-consuming.
- The script processes files sequentially. For better performance with many files, consider processing in batches.
- Recursive scanning of deeply nested directories may take time.

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
