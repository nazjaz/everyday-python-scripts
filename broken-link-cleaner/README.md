# Broken Link Cleaner

Find and remove broken symbolic links, logging all removed links with their original target paths for reference. Helps clean up filesystem clutter caused by broken symlinks and maintains a detailed log of all removals.

## Project Description

Broken Link Cleaner solves the problem of broken symbolic links cluttering the filesystem. When files or directories that symlinks point to are moved or deleted, the symlinks become broken. This tool automatically finds these broken links, removes them, and logs their original target paths for reference. Perfect for system maintenance and filesystem cleanup.

**Target Audience**: System administrators, developers, and users who need to maintain clean filesystems by removing broken symbolic links.

## Features

- **Broken Link Detection**: Identifies symbolic links pointing to non-existent targets
- **Recursive Scanning**: Scans directories and subdirectories for broken links
- **Removal Logging**: Logs all removed links with their target paths
- **Exclusion Patterns**: Skip specific directories or patterns
- **Dry-Run Mode**: Preview removals without actually deleting links
- **Comprehensive Logging**: Detailed logs of all operations
- **Error Handling**: Gracefully handles permission errors and inaccessible paths
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read permissions to scan directories
- Write permissions to remove symbolic links

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/broken-link-cleaner
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

Edit `config.yaml` to set your scan directory:

```yaml
scan_directory: ~/Documents
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **scan_directory**: Directory to scan for broken symbolic links
- **removal_log_file**: Path to save log of removed links
- **exclusions**: Configuration for excluding paths
  - **directories**: Directories to exclude from scanning
  - **patterns**: Patterns to match in link names or paths
- **operations**: Operation settings
  - **recursive**: Scan subdirectories recursively
  - **dry_run**: Preview mode without removing links
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SCAN_DIRECTORY`: Override scan directory path
- `DRY_RUN`: Enable dry run mode (`true`/`false`)

### Example Configuration

```yaml
scan_directory: ~/Documents

exclusions:
  directories:
    - ~/.git
    - node_modules
    - venv
  patterns:
    - .git

operations:
  recursive: true
  dry_run: false
```

## Usage

### Basic Usage

Find and remove broken symbolic links:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Preview changes without removing links (dry run)
python src/main.py --dry-run

# Specify custom removal log file
python src/main.py -o removed_links.txt

# Combine options
python src/main.py --dry-run -o preview_log.txt
```

### Common Use Cases

1. **Preview Cleanup (Recommended First Step)**:
   ```bash
   python src/main.py --dry-run
   ```
   See what broken links would be removed without actually removing them.

2. **Clean Broken Links**:
   ```bash
   python src/main.py
   ```
   Finds and removes all broken symbolic links in scan directory.

3. **Scan Specific Directory**:
   - Edit `scan_directory` in `config.yaml`
   - Or set environment variable: `export SCAN_DIRECTORY=/path/to/scan`

4. **Save Removal Log**:
   ```bash
   python src/main.py -o my_removal_log.txt
   ```
   Saves log of removed links to custom file.

## Project Structure

```
broken-link-cleaner/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py         # Package initialization
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core detection logic, symlink removal, and logging
- **config.yaml**: YAML configuration file with scan settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)
- **logs/removed_links.txt**: Log of removed links with target paths

## Removal Log Format

The removal log file contains:

```
Broken Symbolic Links Removed
================================================================================

Link: /path/to/broken_link
Target: /path/to/nonexistent/target
--------------------------------------------------------------------------------

Link: /path/to/another_broken_link
Target: /path/to/another/nonexistent/target
--------------------------------------------------------------------------------
```

## How Broken Links Are Detected

A symbolic link is considered broken if:

1. The path is a symbolic link (checked with `is_symlink()`)
2. The target path does not exist (resolved relative to link's parent directory)
3. The link passes exclusion filters

The script handles both absolute and relative symlink targets correctly.

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Broken symlink detection
- Symlink target resolution
- Removal operations
- Exclusion logic
- Error handling
- Log file generation

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Scan directory does not exist`

**Solution**: Ensure the scan directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: `PermissionError` when removing links

**Solution**: Ensure you have write permissions to remove symbolic links. On Linux/Mac, you may need to use `sudo` or adjust permissions.

---

**Issue**: Links not being detected as broken

**Solution**:
- Verify links are actually broken (target doesn't exist)
- Check that links are symbolic links, not regular files
- Review logs for specific detection issues
- Ensure links aren't excluded by patterns

---

**Issue**: Too many links being removed

**Solution**:
- Use `--dry-run` first to preview
- Add more exclusion patterns in config
- Review removal log to understand what's being removed

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Scan directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Error removing symlink"**: Check file permissions and ensure link is not in use
- **"Error scanning directory"**: Directory may have permission restrictions (logged but script continues)

## Safety Features

The script includes safety mechanisms:

1. **Dry-Run Mode**: Preview all operations before executing
2. **Detailed Logging**: All removals are logged with target paths
3. **Exclusion Patterns**: Skip important directories (e.g., .git, node_modules)
4. **Error Handling**: Errors are logged but don't stop the cleanup process
5. **Removal Log**: Complete record of all removed links for reference

## Tips for Best Results

1. **Always Use Dry-Run First**: Preview removals before executing
2. **Review Removal Log**: Check the log file to see what was removed
3. **Configure Exclusions**: Add important directories to exclusions
4. **Backup Important Data**: While symlinks are safe to remove, ensure important data is backed up
5. **Check Logs**: Review logs after running to ensure expected behavior

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov pytest-mock`
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
