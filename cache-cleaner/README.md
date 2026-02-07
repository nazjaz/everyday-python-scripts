# Cache Cleaner

A Python command-line tool for cleaning system cache files from common cache directories with age-based filtering and comprehensive size reporting. Safely remove old cache files to free up disk space while maintaining system stability.

## Features

- **Platform-Specific Cache Detection**: Automatically detects and cleans cache directories for macOS, Linux, and Windows
- **Age-Based Filtering**: Filter files by modification date (minimum and maximum age)
- **Size Reporting**: Comprehensive reporting of cache file sizes before and after cleanup
- **Pattern Matching**: Include or exclude files based on regex patterns
- **Dry Run Mode**: Preview files to be deleted without actually deleting them
- **Safety Features**: Confirmation prompts, size limits, and detailed logging
- **Detailed Reports**: Generate comprehensive cleanup reports with directory breakdowns and largest files
- **Recursive Scanning**: Scan directories recursively to find all cache files
- **Configurable**: Highly customizable through YAML configuration file

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Appropriate file system permissions for cache directories

## Installation

### Step 1: Clone or Navigate to Project Directory

```bash
cd everyday-python-scripts/cache-cleaner
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

### Step 4: Configure Environment (Optional)

Copy `.env.example` to `.env` and modify if needed:

```bash
cp .env.example .env
```

Edit `.env` to set logging level or other environment variables.

### Step 5: Review Configuration

Edit `config.yaml` to customize cache directories, filtering options, and safety settings. **Important**: Review the configuration carefully before running to ensure it targets the correct directories.

## Configuration

The `config.yaml` file contains all configuration options:

### Cache Directories

Platform-specific cache directories are configured separately:

```yaml
cache_directories:
  macos:
    - "~/Library/Caches"
    - "~/Library/Logs"
  linux:
    - "~/.cache"
    - "/tmp"
  windows:
    - "%TEMP%"
    - "%LOCALAPPDATA%\\Temp"
```

### File Filtering

```yaml
filtering:
  min_age_days: 7        # Minimum age in days
  max_age_days: 0       # Maximum age (0 = no limit)
  min_file_size: 0      # Minimum file size in bytes
  max_file_size: 0      # Maximum file size in bytes
  include_hidden: true  # Include hidden files
  include_empty: true   # Include zero-byte files
```

### Include/Exclude Patterns

```yaml
include_patterns:
  - ".*\\.cache$"
  - ".*\\.tmp$"
  - ".*\\.log$"

exclude_patterns:
  - "^\\.git"
  - "^\\.svn"

exclude_directories:
  - "^\\.git$"
  - "^node_modules$"
```

### Safety Options

```yaml
safety:
  dry_run: false              # Preview only mode
  require_confirmation: true   # Ask for confirmation
  max_delete_size: 0          # Maximum size to delete (bytes, 0 = no limit)
```

### Reporting Options

```yaml
reporting:
  detailed_report: true
  report_file: "logs/cache_cleanup_report.txt"
  show_directory_breakdown: true
  show_largest_files: true
  largest_files_count: 10
```

## Usage

### Basic Usage

Scan and clean cache files with default settings:

```bash
python src/main.py
```

### Dry Run (Preview Only)

Preview files that would be deleted without actually deleting:

```bash
python src/main.py --dry-run
```

### Skip Confirmation

Run without confirmation prompt (use with caution):

```bash
python src/main.py --no-confirm
```

### Custom Minimum Age

Set minimum file age in days:

```bash
python src/main.py --min-age 30
```

### Limit Total Deletion Size

Set maximum total size to delete in MB:

```bash
python src/main.py --max-size 1000
```

### Custom Configuration File

Use a custom configuration file:

```bash
python src/main.py -c /path/to/custom_config.yaml
```

### Complete Example

```bash
# Preview cleanup of files older than 30 days, max 5GB
python src/main.py --dry-run --min-age 30 --max-size 5242880

# Actually clean with confirmation
python src/main.py --min-age 30 --max-size 5242880
```

## Project Structure

```
cache-cleaner/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/                    # Additional documentation
└── logs/                    # Log files and reports directory
```

## How It Works

1. **Directory Scanning**: Scans configured cache directories for the current platform
2. **File Filtering**: Applies age, size, and pattern filters to identify cache files
3. **Preview**: Shows summary of files to be deleted (if not in dry-run mode)
4. **Confirmation**: Prompts for confirmation (if enabled)
5. **Deletion**: Deletes matching files while logging all operations
6. **Reporting**: Generates detailed report with statistics and breakdowns

## Safety Features

- **Dry Run Mode**: Always test with `--dry-run` first
- **Confirmation Prompts**: Requires user confirmation before deletion (configurable)
- **Size Limits**: Can limit total size of files deleted in one run
- **Detailed Logging**: All operations are logged for audit purposes
- **Pattern Exclusions**: Excludes important directories like `.git`, `node_modules`
- **Permission Handling**: Gracefully handles permission errors

## Reporting

The tool generates detailed reports including:

- Total files found and their total size
- Number of files deleted and failed deletions
- Total disk space freed
- Directory breakdown (top directories by size)
- Largest files found
- All statistics in human-readable format

Reports are saved to `logs/cache_cleanup_report.txt` by default.

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with verbose output:

```bash
pytest tests/ -v
```

Run specific test:

```bash
pytest tests/test_main.py::TestCacheCleaner::test_scan_directory
```

## Troubleshooting

### Error: Permission denied

**Solution:** Run with appropriate permissions. On Linux/macOS, you may need `sudo` for system directories (use with extreme caution):

```bash
sudo python src/main.py --dry-run  # Test first!
```

**Warning:** Be very careful when using `sudo`. Always test with `--dry-run` first.

### Error: Configuration file not found

**Solution:** Ensure `config.yaml` exists in the project root, or specify a custom path:

```bash
python src/main.py -c /path/to/config.yaml
```

### No Files Found

**Possible causes:**
- All files are newer than `min_age_days`
- File patterns don't match your cache files
- Cache directories don't exist on your system
- Files are excluded by exclude patterns

**Solution:** Adjust `min_age_days` or review include/exclude patterns in `config.yaml`.

### Accidentally Deleted Important Files

**Prevention:**
- Always run with `--dry-run` first
- Review the preview carefully
- Adjust exclude patterns to protect important directories
- Use size limits to prevent large deletions

**Recovery:** Check logs for deleted file paths. Some files may be recoverable from system trash/recycle bin.

### Large Number of Files

If scanning takes too long or finds too many files:

- Increase `min_age_days` to target older files only
- Use `max_delete_size` to limit deletion size
- Adjust include patterns to be more specific
- Exclude large directories that aren't needed

### Platform-Specific Issues

**macOS:**
- Some system caches require admin permissions
- Be cautious with `/Library/Caches` and system directories
- User caches in `~/Library/Caches` are generally safe

**Linux:**
- `/tmp` is often cleared on reboot, may not need cleaning
- User cache in `~/.cache` is generally safe
- System caches in `/var/cache` may require root

**Windows:**
- Temp directories are generally safe to clean
- Internet cache may be managed by browsers
- Use Windows Disk Cleanup for system caches

## Best Practices

1. **Always Test First**: Use `--dry-run` to preview deletions
2. **Start Conservative**: Use higher `min_age_days` initially (30+ days)
3. **Review Reports**: Check generated reports to understand what was deleted
4. **Backup Important Data**: Ensure important files are backed up
5. **Monitor Disk Space**: Use size limits to prevent large deletions
6. **Regular Maintenance**: Run periodically (weekly/monthly) with appropriate age filters
7. **Platform Awareness**: Understand platform-specific cache locations

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for all public functions and classes
4. Add unit tests for new features
5. Update README.md for user-facing changes
6. Test on multiple platforms if possible

## License

This project is provided as-is for automation and utility purposes.

## Disclaimer

**Use at your own risk.** This tool deletes files from your system. Always:
- Test with `--dry-run` first
- Review configuration carefully
- Ensure you have backups of important data
- Understand what directories are being targeted

The authors are not responsible for data loss resulting from use of this tool.
