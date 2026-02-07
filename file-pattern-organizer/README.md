# File Pattern Organizer

A command-line tool for organizing files by matching filename patterns using regular expressions. Moves or copies files to folders based on pattern matches, supports multiple patterns, conflict resolution, and comprehensive logging.

## Project Description

File Pattern Organizer solves the problem of automatically organizing files based on their names by using regex pattern matching. It helps users maintain organized file structures by automatically categorizing files into appropriate folders based on patterns in their filenames, such as dates, keywords, or specific naming conventions.

**Target Audience**: Users who need to organize large numbers of files based on naming patterns, such as downloaded files, invoices, receipts, reports, or any files with consistent naming conventions.

## Features

- **Regex Pattern Matching**: Match filenames against multiple regex patterns
- **Flexible Organization**: Move or copy files to folders based on pattern matches
- **Multiple Patterns**: Support for multiple patterns with priority-based matching
- **Conflict Resolution**: Handle file conflicts with skip, overwrite, or rename options
- **Dry Run Mode**: Preview what would happen without actually moving files
- **Recursive Processing**: Process directories and subdirectories
- **Date Subfolders**: Optional date-based subfolder creation
- **Capture Groups**: Use regex capture groups for dynamic folder names
- **Comprehensive Logging**: Detailed logs of all file operations
- **Customizable**: Fully configurable via YAML configuration file

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/file-pattern-organizer
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

### Step 4: Configure Settings

Edit `config.yaml` to customize patterns and options:

```yaml
source_dir: downloads
output_base_dir: organized
patterns:
  - pattern: '(?i)invoice'
    folder: 'invoices'
    description: 'Invoice files'
default_folder: 'misc'
options:
  move_files: true
  dry_run: false
```

## Usage

### Basic Usage

Organize files from the configured source directory:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Specify custom source directory
python src/main.py -s /path/to/files

# Specify custom output directory
python src/main.py -o /path/to/output

# Process directories recursively
python src/main.py -r

# Dry run (preview without moving files)
python src/main.py --dry-run

# Copy files instead of moving
python src/main.py --copy

# Use custom configuration file
python src/main.py -c /path/to/config.yaml
```

### Common Use Cases

**Organize downloaded files**:
```bash
python src/main.py -s ~/Downloads -o ~/Organized
```

**Preview organization (dry run)**:
```bash
python src/main.py --dry-run
```

**Copy files instead of moving**:
```bash
python src/main.py --copy
```

**Recursive organization**:
```bash
python src/main.py -r
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

#### Pattern Configuration

```yaml
patterns:
  - pattern: 'regex_pattern_here'
    folder: 'destination_folder'
    description: 'Description of pattern'
```

Patterns are matched in order, and the first match wins.

#### Common Pattern Examples

**Date patterns**:
```yaml
- pattern: '^\d{4}-\d{2}-\d{2}'  # YYYY-MM-DD format
  folder: 'by_date'
```

**Keyword patterns** (case-insensitive):
```yaml
- pattern: '(?i)invoice'  # Case-insensitive match
  folder: 'invoices'
```

**Multiple keywords**:
```yaml
- pattern: '(?i)(photo|image|img)'  # Match any of these
  folder: 'photos'
```

**Capture groups** (for dynamic folders):
```yaml
- pattern: '^(\d{4})-'  # Capture year
  folder: 'by_year'
  # Use use_capture_groups: true to create year subfolders
```

#### Options

- `move_files`: Move files (true) or copy files (false)
- `dry_run`: Preview mode without actually moving files
- `use_capture_groups`: Use regex capture groups as subfolders
- `preserve_structure`: Preserve directory structure (not yet implemented)
- `create_date_subfolders`: Create YYYY-MM subfolders

#### File Handling

- `on_conflict`: What to do if destination exists
  - `skip`: Skip the file
  - `overwrite`: Overwrite existing file
  - `rename`: Add timestamp to filename
- `max_filename_length`: Maximum filename length (0 = no limit)

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `SOURCE_DIR`: Custom source directory
- `OUTPUT_DIR`: Custom output directory
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Project Structure

```
file-pattern-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Application configuration
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── downloads/               # Source directory (example)
├── organized/               # Output directory (example)
└── logs/
    └── file_organizer.log   # Application logs
```

## Pattern Examples

### Organize by Date

```yaml
patterns:
  - pattern: '^\d{4}-\d{2}-\d{2}'
    folder: 'by_date'
```

Matches files like: `2024-01-15_report.pdf`

### Organize by Keywords

```yaml
patterns:
  - pattern: '(?i)invoice'
    folder: 'invoices'
  - pattern: '(?i)receipt'
    folder: 'receipts'
  - pattern: '(?i)report'
    folder: 'reports'
```

### Organize by File Type Keywords

```yaml
patterns:
  - pattern: '(?i)(photo|image|img|pic)'
    folder: 'photos'
  - pattern: '(?i)(doc|document)'
    folder: 'documents'
```

### Organize by Project Name

```yaml
patterns:
  - pattern: '^project-(\w+)'
    folder: 'projects'
```

With `use_capture_groups: true`, creates subfolders like `projects/project-name/`

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Test Coverage

The test suite covers:
- Pattern matching (various patterns)
- Destination path generation
- File conflict handling
- File organization (move/copy)
- Dry run mode
- Directory organization
- Invalid pattern handling

## Troubleshooting

### Files Not Being Organized

**Check pattern syntax**:
- Verify regex patterns are correct
- Test patterns using online regex testers
- Check logs for pattern compilation errors

**Check file permissions**:
- Ensure read access to source directory
- Ensure write access to output directory
- Check file system permissions

**Use dry run mode**:
```bash
python src/main.py --dry-run
```

### Pattern Not Matching

**Common issues**:
- Case sensitivity: Use `(?i)` prefix for case-insensitive matching
- Anchors: Use `^` for start of string, `$` for end
- Escaping: Escape special regex characters with `\`

**Test your pattern**:
```python
import re
pattern = re.compile('your_pattern_here')
match = pattern.search('test_filename.pdf')
print(match is not None)
```

### File Conflicts

**Options**:
- `skip`: Don't move file if destination exists
- `overwrite`: Replace existing file
- `rename`: Add timestamp to filename

Configure in `config.yaml`:
```yaml
file_handling:
  on_conflict: rename  # or skip, overwrite
```

### Performance Issues

**Large directories**:
- Use recursive mode only when necessary
- Process in batches if needed
- Check disk space availability

**Slow processing**:
- Complex regex patterns may be slower
- Consider simplifying patterns
- Use more specific patterns to reduce matches

## Best Practices

1. **Test with dry run first**: Always use `--dry-run` before actual organization
2. **Backup important files**: Make backups before organizing important files
3. **Start with simple patterns**: Begin with simple patterns and add complexity gradually
4. **Use descriptive folder names**: Make folder names clear and meaningful
5. **Order patterns carefully**: More specific patterns should come first
6. **Log everything**: Check logs regularly for issues
7. **Validate patterns**: Test regex patterns before using them

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guide
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with conventional commit format
7. Push and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

## License

This project is part of the everyday-python-scripts collection. See the main repository for license information.
