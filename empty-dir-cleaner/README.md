# Empty Directory Cleaner

Find and remove empty directories recursively with options to preserve specific directory patterns and comprehensive logging of all deletions. Clean up your filesystem by removing unnecessary empty directories.

## Project Description

Empty Directory Cleaner solves the problem of accumulated empty directories in filesystems. It recursively scans directories, identifies empty folders, and removes them while preserving important directories based on configurable patterns. All operations are logged for audit and safety.

**Target Audience**: System administrators, developers, and users who need to clean up empty directories while protecting important system and project directories.

## Features

- **Recursive Scanning**: Recursively finds all empty directories in target paths
- **Pattern Preservation**: Preserve specific directory patterns (e.g., .git, node_modules)
- **Comprehensive Logging**: Logs all deletions and preserved directories
- **Dry Run Mode**: Preview what would be deleted without actually deleting
- **Bottom-Up Deletion**: Deletes deepest directories first to handle nested empty dirs
- **Parent Cleanup**: Automatically cleans parent directories that become empty
- **Configurable Depth**: Limit search depth for performance
- **Batch Processing**: Process directories in batches with progress reporting
- **Detailed Reports**: Generate summary reports with statistics and deleted paths
- **Safety Features**: Multiple safety checks and confirmation options

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/empty-dir-cleaner
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

1. Copy the example environment file (if needed):
   ```bash
   cp .env.example .env
   ```

2. **IMPORTANT**: Edit `config.yaml` to set target directories:
   ```yaml
   targets:
     - path: "/path/to/clean"
       enabled: true
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **targets**: List of directories to clean
- **preserve_patterns**: Directory patterns to never delete
- **safety**: Dry run mode, confirmation, depth limits
- **deletion**: Recursive deletion and parent cleanup settings
- **logging**: Logging configuration
- **reporting**: Report generation settings

### Preserve Patterns

Configure directories to preserve:

```yaml
preserve_patterns:
  enabled: true
  patterns:
    - ".git"
    - "__pycache__"
    - "node_modules"
  match_type: "name"  # name, path, or regex
```

**Match Types**:
- **name**: Match directory name exactly
- **path**: Match if pattern appears anywhere in path
- **regex**: Use regular expression matching

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DRY_RUN`: Enable dry run mode (true/false)
- `TARGET_PATH`: Override target directory path
- `PRESERVE_PATTERNS_ENABLED`: Enable/disable pattern preservation (true/false)

### Example Configuration

```yaml
targets:
  - path: "/home/user/projects"
    enabled: true

preserve_patterns:
  enabled: true
  patterns:
    - ".git"
    - "__pycache__"
    - "node_modules"

safety:
  dry_run: false
  max_depth: null  # Unlimited
```

## Usage

### Basic Usage

Clean empty directories with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Dry run mode (preview without deleting)
python src/main.py -d

# Clean specific directory
python src/main.py -p /path/to/clean

# Combine options
python src/main.py -c config.yaml -d -p /path/to/clean
```

### Recommended Workflow

1. **First Run - Dry Run**:
   ```bash
   python src/main.py -d
   ```
   Review what would be deleted

2. **Review Logs**:
   Check `logs/empty_dir_cleaner.log` and `logs/cleanup_report.txt`

3. **Actual Cleanup**:
   ```bash
   python src/main.py
   ```

## Project Structure

```
empty-dir-cleaner/
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
│   └── API.md              # API documentation (if applicable)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── empty_dir_cleaner.log  # Application logs
    └── cleanup_report.txt     # Cleanup reports
```

### File Descriptions

- **src/main.py**: Empty directory detection, pattern matching, deletion, and logging
- **config.yaml**: YAML configuration file with targets and preserve patterns
- **tests/test_main.py**: Unit tests for core functionality
- **logs/empty_dir_cleaner.log**: Application log file with rotation
- **logs/cleanup_report.txt**: Summary reports with statistics and deleted paths

## How It Works

1. **Scanning**: Recursively scans target directories for empty directories
2. **Pattern Matching**: Checks each empty directory against preserve patterns
3. **Deletion**: Deletes empty directories (deepest first for nested structures)
4. **Parent Cleanup**: Checks if parent directories became empty and cleans them
5. **Logging**: Logs all operations and generates reports

## Safety Features

- **Dry Run Mode**: Preview deletions without actually deleting
- **Pattern Preservation**: Protect important directories automatically
- **Permission Handling**: Gracefully handles permission errors
- **Error Recovery**: Continues processing even if individual deletions fail
- **Comprehensive Logging**: Full audit trail of all operations

## Logging

The application logs:

- **All Deletions**: Path of every deleted directory
- **Preserved Directories**: Directories that were preserved (if enabled)
- **Errors**: Permission errors, deletion failures
- **Statistics**: Summary of operations

Log files:
- `logs/empty_dir_cleaner.log`: Detailed application log
- `logs/cleanup_report.txt`: Summary report with statistics

## Reports

Reports include:

- **Statistics**: Directories scanned, found, preserved, deleted, failed
- **Deleted Paths**: Complete list of deleted directory paths
- **Preserved Paths**: List of preserved directories (if enabled)
- **Mode**: Indicates if dry run mode was used

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
- Empty directory detection
- Pattern preservation
- Directory deletion
- Error handling

## Troubleshooting

### Common Issues

**Issue**: Permission denied errors

**Solution**: 
- Run with appropriate permissions (sudo on Linux/macOS)
- Check directory permissions
- Verify you have write access to target directories

---

**Issue**: Important directories being deleted

**Solution**: 
- Add directory names to preserve_patterns in config.yaml
- Use dry run mode first to preview deletions
- Check preserve_patterns.match_type setting

---

**Issue**: Too many directories being preserved

**Solution**: 
- Review preserve_patterns.patterns list
- Adjust match_type (name vs path vs regex)
- Disable preserve_patterns if not needed

---

**Issue**: Process is slow

**Solution**: 
- Set max_depth to limit recursion depth
- Increase batch_size for faster progress reporting
- Disable log_preserved if not needed

---

**Issue**: Parent directories not being cleaned

**Solution**: 
- Ensure remove_parent_if_empty is set to true
- Check that parent directories are actually empty after child deletion
- Verify parent directories are not in preserve patterns

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Permission denied"**: Check directory permissions and run with appropriate access
- **"No target directories configured"**: Add target directories to config.yaml

## Best Practices

1. **Always Use Dry Run First**: Preview deletions before actual cleanup
   ```bash
   python src/main.py -d
   ```

2. **Configure Preserve Patterns**: Protect important directories
   ```yaml
   preserve_patterns:
     patterns:
       - ".git"
       - "node_modules"
   ```

3. **Review Logs**: Check logs and reports after running
   - Review `logs/cleanup_report.txt` for summary
   - Check `logs/empty_dir_cleaner.log` for details

4. **Start Small**: Test on a small directory first
   ```bash
   python src/main.py -p /path/to/test/directory
   ```

5. **Backup Important Data**: Ensure important data is backed up

6. **Use Max Depth**: Limit recursion depth for large directory trees
   ```yaml
   safety:
     max_depth: 5
   ```

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

## Disclaimer

**Use with caution**: This tool permanently deletes directories. Always:
- Use dry run mode first
- Review logs and reports
- Ensure important directories are in preserve patterns
- Have backups of important data
