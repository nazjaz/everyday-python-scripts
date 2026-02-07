# Download Cleanup Script

A Python automation script that cleans up old download files based on age and type, moving them to archive folders or deleting them after a retention period. Useful for managing download directories, freeing up disk space, and maintaining organized file storage.

## Features

- Age-based cleanup: Removes files older than specified retention period
- Type-based filtering: Process specific file type categories (images, documents, videos, etc.)
- Archive or delete: Choose to archive files or permanently delete them
- Organized archiving: Archives organized by category and year-month
- Pattern exclusion: Exclude files matching specific patterns
- Dry run mode: Simulate operations without moving/deleting files
- Recursive scanning: Processes all files in download folders and subdirectories
- Comprehensive logging: Detailed logs for all operations
- Configuration support: YAML configuration file or command-line arguments
- Error handling: Graceful handling of permission errors and file conflicts

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd download-cleanup
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
download_folders:
  - "~/Downloads"
  - "./downloads"
retention_days: 30
archive_root: "./archived"
action: "archive"  # Options: archive, delete
file_types:
  - images
  - documents
  - videos
  - archives
exclude_patterns:
  - "important"
  - "keep"
```

### File Type Categories

The script recognizes the following file type categories:

- **images**: jpg, jpeg, png, gif, bmp, svg, webp, ico
- **documents**: pdf, doc, docx, xls, xlsx, ppt, pptx, txt, rtf, odt, ods, odp
- **videos**: mp4, avi, mov, wmv, flv, webm, mkv, m4v
- **audio**: mp3, wav, flac, aac, ogg, wma, m4a
- **archives**: zip, rar, 7z, tar, gz, bz2, xz, tar.gz, tar.bz2
- **executables**: exe, msi, dmg, pkg, deb, rpm, app
- **code**: py, js, html, css, java, cpp, c, h, json, xml, yaml, yml
- **other**: Files that don't match any category

## Usage

### Basic Usage

Clean up files older than 30 days in Downloads folder:

```bash
python src/main.py \
  --download-folders ~/Downloads \
  --retention-days 30 \
  --archive-root ~/Archived
```

### Delete Instead of Archive

Permanently delete old files:

```bash
python src/main.py \
  --download-folders ~/Downloads \
  --retention-days 30 \
  --action delete
```

### Filter by File Type

Only clean up images and videos:

```bash
python src/main.py \
  --download-folders ~/Downloads \
  --retention-days 30 \
  --archive-root ~/Archived \
  --file-types images videos
```

### Exclude Patterns

Skip files with "important" or "keep" in filename:

```bash
python src/main.py \
  --download-folders ~/Downloads \
  --retention-days 30 \
  --archive-root ~/Archived \
  --exclude-patterns important keep
```

### Dry Run Mode

Preview what would be cleaned without actually moving/deleting:

```bash
python src/main.py \
  --download-folders ~/Downloads \
  --retention-days 30 \
  --archive-root ~/Archived \
  --dry-run
```

### Use Configuration File

```bash
python src/main.py --config config.yaml
```

### Multiple Download Folders

Clean up multiple download folders:

```bash
python src/main.py \
  --download-folders ~/Downloads ~/Desktop/Downloads ./downloads \
  --retention-days 30 \
  --archive-root ~/Archived
```

### Command-Line Arguments

- `--download-folders`: Download folder paths to clean (space-separated, required)
- `--retention-days`: Number of days to retain files before cleanup (required)
- `--archive-root`: Root directory for archived files (required if action is archive)
- `--action`: Action to take - archive or delete (default: archive)
- `--file-types`: File type categories to process (space-separated, optional)
- `--exclude-patterns`: Filename patterns to exclude (space-separated, optional)
- `--dry-run`: Simulate operations without moving/deleting files
- `--config`: Path to configuration file (YAML)

## Project Structure

```
download-cleanup/
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

- `src/main.py`: Core implementation with DownloadCleanup class and CLI interface
- `config.yaml`: Default configuration file with cleanup settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

## How It Works

1. **Scan Download Folders**: Recursively scans all specified download folders for files
2. **Check File Age**: Compares file modification time against retention period
3. **Apply Filters**: Filters by file type category and exclusion patterns
4. **Archive or Delete**: Moves files to organized archive or deletes them permanently
5. **Organize Archives**: Archives are organized by category and year-month (e.g., `archived/images/2024-01/`)
6. **Log Operations**: Records all operations and statistics

### Archive Structure

When archiving, files are organized as follows:

```
archived/
├── images/
│   ├── 2024-01/
│   │   ├── photo1.jpg
│   │   └── photo2.png
│   └── 2024-02/
│       └── screenshot.png
├── documents/
│   └── 2024-01/
│       └── report.pdf
└── videos/
    └── 2024-01/
        └── video.mp4
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
- File age detection
- File type categorization
- Archive and delete operations
- Pattern exclusion
- Error handling for invalid paths and permissions
- Configuration file loading
- Dry run mode

## Troubleshooting

### Common Issues

**Issue: "Download folder does not exist"**

Solution: Verify the download folder paths exist and are accessible. Use absolute paths or ensure relative paths are correct from the current working directory.

**Issue: "Archive root is not writable"**

Solution: Ensure you have write permissions for the archive directory. On Unix systems, you may need to use `sudo` or adjust directory permissions.

**Issue: "Permission denied" when deleting files**

Solution: Ensure you have write permissions for the files you're trying to delete. Check file ownership and permissions.

**Issue: Files not being cleaned up**

Solution: Check the logs for details. Verify that:
- Files are older than the retention period
- Files match the specified file type categories (if any)
- Files don't match exclusion patterns
- You have the necessary permissions

**Issue: "Invalid YAML in config file"**

Solution: Validate your YAML syntax. Ensure proper indentation and that all required fields are present.

### Error Messages

All errors are logged to both the console and `logs/cleanup.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `cleanup.log`: Main log file with all operations and errors

## Security Considerations

- The script can permanently delete files. Always use `--dry-run` first to preview changes.
- Archive operations move files, which is a destructive operation. Ensure you have backups of important files.
- The script processes files based on modification time, not creation time. Be aware of this distinction.

## Performance Considerations

- Recursive scanning of large download folders may take time.
- The script processes files sequentially. For better performance with many files, consider processing in batches.
- Archive operations create directory structures as needed, which may take time for deeply nested archives.

## Best Practices

1. **Always use dry-run first**: Preview what will be cleaned before actually running cleanup
2. **Set appropriate retention periods**: Consider your workflow and how long you typically need files
3. **Use exclusion patterns**: Protect important files from accidental cleanup
4. **Regular cleanup**: Schedule regular cleanup runs to maintain organized download folders
5. **Monitor logs**: Review logs after cleanup to ensure expected behavior
6. **Backup important files**: Ensure important files are backed up before cleanup

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
