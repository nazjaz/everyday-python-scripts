# Depth File Organizer

Organize files by their depth in the directory tree, grouping files from the same nesting level together. This tool helps reorganize files based on how deeply nested they are in the directory structure.

## Project Description

Depth File Organizer solves the problem of organizing files by their depth in the directory tree by calculating how many levels deep each file is and grouping files from the same depth level together. This is useful for analyzing directory structures, reorganizing files, and understanding file distribution across directory levels.

**Target Audience**: System administrators, developers, users managing complex directory structures, and anyone who needs to reorganize files based on their nesting depth.

## Features

- **Depth Calculation**: Automatically calculates file depth in directory tree
- **Depth-Based Grouping**: Groups files from the same depth level together
- **Flexible Organization**: Move files to depth-based folders or generate reports
- **Preserve Structure Option**: Optionally preserve relative directory structure
- **Recursive Scanning**: Scan directories and subdirectories recursively
- **Extension Filtering**: Filter files by extension (optional)
- **Conflict Handling**: Handle file name conflicts with rename, skip, or overwrite
- **Detailed Reports**: Generate comprehensive reports with file distribution
- **Dry-Run Mode**: Simulate organization without actually moving files
- **Comprehensive Logging**: Log all operations for audit and debugging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read access to directories you want to scan
- Write access if organizing files (optional)

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/depth-file-organizer
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

Edit `config.yaml` to customize organization settings:

```yaml
source:
  directory: "/path/to/files"

output:
  directory: "organized"
  preserve_structure: false
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source**: Directory to scan and recursive option
- **output**: Output directory and structure preservation settings
- **organization**: Depth naming, conflict handling, and dry-run settings
- **include**: File extensions to include (empty = all)
- **skip**: Patterns and directories to skip during scanning
- **report**: Report generation settings
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory
- `OUTPUT_DIRECTORY`: Override output directory
- `DRY_RUN`: Enable/disable dry-run mode ("true" or "false")

### Example Configuration

```yaml
source:
  directory: "/home/user/documents"
  recursive: true

output:
  directory: "organized"
  preserve_structure: false

organization:
  dry_run: true
  depth_naming:
    prefix: "Level"
    separator: "-"
    include_level: true
  conflicts:
    action: "rename"
```

## Usage

### Basic Usage

Scan directory and group files by depth (no organization):

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Scan specific directory
python src/main.py -d /path/to/directory

# Organize files by moving them to depth folders
python src/main.py --organize

# Organize in dry-run mode (simulate)
python src/main.py --organize --dry-run

# Generate report
python src/main.py --report report.txt

# Combine options
python src/main.py -d /home/user -o --dry-run --report report.txt
```

### Common Use Cases

1. **Analyze Directory Structure**:
   ```bash
   python src/main.py -d /path/to/directory
   ```

2. **Organize Files by Depth (Dry-Run)**:
   ```bash
   python src/main.py -d /path/to/directory --organize --dry-run
   ```

3. **Actually Organize Files**:
   ```bash
   python src/main.py -d /path/to/directory --organize
   ```

4. **Generate Report Only**:
   ```bash
   python src/main.py -d /path/to/directory --report report.txt --no-summary
   ```

5. **Custom Depth Naming**:
   - Edit `organization.depth_naming` in `config.yaml`
   - Customize prefix, separator, and level inclusion

## Project Structure

```
depth-file-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation
├── data/                   # Data directory
├── organized/              # Organized files (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── depth_organizer.log # Application logs
    └── depth_report.txt    # Generated reports
```

### File Descriptions

- **src/main.py**: Core depth calculation, file scanning, and organization functionality
- **config.yaml**: YAML configuration file with organization settings
- **tests/test_main.py**: Unit tests for core functionality
- **organized/**: Directory containing files organized by depth
- **logs/depth_organizer.log**: Application log file with rotation
- **logs/depth_report.txt**: Generated report files

## Depth Calculation

### How Depth is Calculated

Depth is calculated as the number of parent directories between the file and the base directory:

- **Depth 0**: Files directly in the base directory
- **Depth 1**: Files one level deep (in a subdirectory)
- **Depth 2**: Files two levels deep (in a subdirectory of a subdirectory)
- And so on...

### Example

For base directory `/home/user/documents`:

- `/home/user/documents/file.txt` → Depth 0
- `/home/user/documents/folder/file.txt` → Depth 1
- `/home/user/documents/folder/subfolder/file.txt` → Depth 2

## Organization

### Depth-Based Folders

Files are organized into folders named by their depth level:

- **Default naming**: `Depth_0`, `Depth_1`, `Depth_2`, etc.
- **Customizable**: Configure prefix, separator, and level inclusion

### Organization Options

1. **Flat Organization**: Files moved to depth folders with original names
2. **Preserve Structure**: Maintain relative directory structure within depth folders
3. **Conflict Handling**: Rename, skip, or overwrite on name conflicts

### Output Structure

```
organized/
├── Depth_0/
│   ├── file1.txt
│   └── file2.txt
├── Depth_1/
│   ├── file3.txt
│   └── file4.txt
└── Depth_2/
    └── file5.txt
```

## Report Format

Reports include:

- **Statistics**: Files scanned, organized, skipped, errors, depth levels found
- **Files by Depth**: Detailed breakdown for each depth level:
  - Number of files
  - Total size
  - File list (optional)
  - New paths (if organized)

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Depth calculation
- File scanning
- Organization logic
- Conflict handling
- Report generation
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Directory not found`

**Solution**: Verify the directory path exists and is accessible. Use absolute paths for best results.

---

**Issue**: `PermissionError` when organizing files

**Solution**: 
- Ensure you have write permissions for output directory
- Check source file permissions
- Some files may require elevated permissions

---

**Issue**: Files not being organized correctly

**Solution**: 
- Check depth calculation logic
- Verify base directory is correct
- Review logs for calculation details
- Ensure files are not being skipped by patterns

---

**Issue**: Too many files in one depth level

**Solution**: 
- Use extension filtering to limit file types
- Add skip patterns for unnecessary directories
- Consider preserving structure for better organization

---

**Issue**: Name conflicts during organization

**Solution**: 
- Configure conflict handling in `organization.conflicts.action`
- Options: "rename" (default), "skip", "overwrite"
- Review logs for conflict resolution

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Directory not found"**: Verify source directory path exists
- **"Path is not a directory"**: Ensure the path points to a directory, not a file
- **"Permission denied"**: Check file and directory permissions

## Performance Considerations

- **Large Directories**: Scanning very large directory trees can take time
- **Recursive Scanning**: Disable recursive scanning for faster results on top-level only
- **File Moving**: Moving many files can be slow - use dry-run first
- **Network Drives**: Scanning/moving files on network drives may be slower

## Security Considerations

- **File Permissions**: Tool requires appropriate read/write permissions
- **Backup**: Consider backing up directories before organizing
- **Dry-Run Default**: Tool defaults to dry-run mode for safety
- **Protected Files**: Use skip patterns to exclude important files

## Use Cases

1. **Directory Structure Analysis**: Understand file distribution across depth levels
2. **File Reorganization**: Reorganize files by depth for better structure
3. **Cleanup**: Group scattered files by their nesting level
4. **Migration**: Organize files before moving to new location
5. **Audit**: Generate reports of file distribution

## Automation

You can automate the organizer using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Organize directory weekly (dry-run)
0 2 * * 0 cd /path/to/depth-file-organizer && /path/to/venv/bin/python src/main.py -d /path/to/scan -o --dry-run
```

### Windows (Task Scheduler)

- Create a task to run `python src/main.py -d C:\Users\YourName\Documents -o --dry-run`
- Set working directory to project folder
- Use full path to Python executable

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-mock pytest-cov`
5. Create a feature branch: `git checkout -b feature/your-feature`

### Code Style Guidelines

- Follow PEP 8 style guide
- Maximum line length: 88 characters (Black formatter)
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Run tests before committing: `pytest tests/`

### Pull Request Process

1. Ensure all tests pass
2. Update README.md if adding new features
3. Add tests for new functionality
4. Submit pull request with clear description

## License

This project is provided as-is for educational and personal use.
