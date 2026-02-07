# File Permission Organizer

A command-line tool for organizing files based on their permission settings. Groups executable files, read-only files, and files with specific permission patterns into categorized folders. Useful for organizing system files, scripts, and managing file permissions.

## Project Description

File Permission Organizer solves the problem of organizing files based on their permission settings by automatically categorizing files into folders based on whether they are executable, read-only, or match specific permission patterns. It helps users organize system files, scripts, and manage files with different permission requirements.

**Target Audience**: System administrators, developers, and users who need to organize files based on permission settings, separate executables from regular files, or manage files with specific permission requirements.

## Features

- **Executable File Detection**: Identify and group files with execute permissions
- **Read-Only File Detection**: Identify and group read-only files
- **Permission Pattern Matching**: Group files by specific octal permission patterns (e.g., 755, 644)
- **Flexible Organization**: Move or copy files to permission-based folders
- **Conflict Resolution**: Handle file conflicts with skip, overwrite, or rename options
- **Dry Run Mode**: Preview what would happen without actually moving files
- **Recursive Processing**: Process directories and subdirectories
- **Comprehensive Logging**: Detailed logs of all file operations
- **Customizable**: Fully configurable via YAML configuration file

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/file-permission-organizer
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

Edit `config.yaml` to customize permission folders and options:

```yaml
source_dir: downloads
output_base_dir: organized
permission_folders:
  executable:
    folder: "executables"
    check_owner: true
permission_patterns:
  - pattern: "755"
    folder: "permissions_755"
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

#### Permission Folders

Define folders for specific permission types:

```yaml
permission_folders:
  executable:
    folder: "executables"
    check_owner: true  # Check owner execute permission
    check_group: false
    check_other: false
  
  read_only:
    folder: "read_only"
    check_owner: true
    check_group: true
    check_other: true
```

#### Permission Patterns

Define folders for specific octal permission patterns:

```yaml
permission_patterns:
  - pattern: "755"  # rwxr-xr-x
    folder: "permissions_755"
  - pattern: "644"  # rw-r--r--
    folder: "permissions_644"
```

#### Options

```yaml
options:
  move_files: true  # Move (true) or copy (false)
  dry_run: false  # Preview mode
  create_permission_subfolders: false  # Create subfolders by octal
```

#### File Handling

```yaml
file_handling:
  on_conflict: rename  # skip, overwrite, or rename
  max_filename_length: 255
```

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `SOURCE_DIR`: Custom source directory
- `OUTPUT_DIR`: Custom output directory
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Permission Patterns

### Common Permission Patterns

- **755** (rwxr-xr-x): Owner: read/write/execute, Group: read/execute, Other: read/execute
- **644** (rw-r--r--): Owner: read/write, Group: read, Other: read
- **777** (rwxrwxrwx): All permissions for all users
- **600** (rw-------): Owner: read/write, Group: none, Other: none
- **700** (rwx------): Owner: read/write/execute, Group: none, Other: none

### Permission Checking

The tool checks permissions in this order:
1. Permission pattern matches (most specific)
2. Executable files
3. Read-only files
4. Write-only files
5. Default folder (if no match)

## Project Structure

```
file-permission-organizer/
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
    └── file_permission_organizer.log  # Application logs
```

## How It Works

1. **File Discovery**: Scans specified directories for files
2. **Permission Reading**: Reads file permissions using `stat` module
3. **Permission Analysis**: Checks if file matches permission patterns or categories
4. **Folder Assignment**: Assigns file to appropriate folder based on permissions
5. **File Organization**: Moves or copies files to assigned folders
6. **Conflict Handling**: Resolves conflicts based on configuration

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
- Permission reading and analysis
- Executable file detection
- Read-only file detection
- Permission pattern matching
- File organization
- Conflict handling
- Dry run mode
- Directory exclusion

## Troubleshooting

### Files Not Being Organized

**Check permissions**:
- Verify files have readable permissions
- Check source directory permissions
- Ensure output directory is writable

**Check configuration**:
- Verify permission patterns are correct
- Check folder mappings in config
- Review exclusion patterns

**Use dry run mode**:
```bash
python src/main.py --dry-run
```

### Permission Detection Issues

**Files not detected as executable**:
- Verify file actually has execute permission
- Check `check_owner`, `check_group`, `check_other` settings
- Use `stat` command to verify permissions manually

**Pattern not matching**:
- Verify octal permission value
- Check pattern format (should be string like "755")
- Ensure pattern is in permission_patterns list

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

## Best Practices

1. **Test with dry run first**: Always use `--dry-run` before actual organization
2. **Backup important files**: Make backups before organizing important files
3. **Understand permissions**: Know what permissions mean before organizing
4. **Use specific patterns**: More specific patterns should come first in config
5. **Review exclusions**: Ensure exclusion patterns don't exclude needed files
6. **Check logs**: Review logs regularly for issues

## Security Considerations

- **Permission Changes**: Tool reads but does not modify file permissions
- **File Access**: Requires read access to source files and write access to output directory
- **Executable Files**: Be careful when organizing executable files
- **System Files**: Avoid organizing system directories without understanding implications

## Platform Differences

- **Unix/Linux/macOS**: Full permission support (read, write, execute)
- **Windows**: Limited permission support (mainly read-only detection)
- **Cross-platform**: Tool handles platform differences automatically

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
