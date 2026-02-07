# Log Compressor

Compress old log files using gzip, keeping original files for a specified retention period and organizing compressed files by date. Efficiently manage disk space while maintaining log file archives.

## Project Description

Log Compressor solves the problem of log files consuming excessive disk space. It automatically compresses old log files using gzip compression, maintains original files for a configurable retention period, and organizes compressed files by date for easy management and retrieval.

**Target Audience**: System administrators, developers, and users who need to manage log file storage efficiently while maintaining archives.

## Features

- **Gzip Compression**: Compress log files using standard gzip format
- **Age-Based Compression**: Only compress files older than specified days
- **Retention Period**: Keep original files for configurable retention period
- **Date-Based Organization**: Organize compressed files by date (year/month structure)
- **Automatic Cleanup**: Remove old compressed files based on retention policy
- **Pattern Matching**: Match log files by configurable patterns (*.log, *.log.*, etc.)
- **Recursive Processing**: Process directories recursively
- **Dry Run Mode**: Preview what would be compressed without actually doing it
- **Comprehensive Logging**: Log all compression operations
- **Space Savings Tracking**: Track disk space saved by compression
- **Detailed Reports**: Generate reports with statistics and file lists

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/log-compressor
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
     - path: "logs"
       enabled: true
       recursive: true
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **targets**: Directories containing log files to process
- **file_patterns**: File patterns to match (*.log, *.log.*, etc.)
- **compression**: Compression settings (min age, compression level, etc.)
- **retention**: Retention periods for original and compressed files
- **organization**: Date-based organization settings
- **safety**: Dry run mode and safety checks

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DRY_RUN`: Enable dry run mode (true/false)
- `TARGET_PATH`: Override target directory path
- `MIN_AGE_DAYS`: Override minimum age in days before compression
- `KEEP_ORIGINAL_DAYS`: Override retention period for original files

### Example Configuration

```yaml
targets:
  - path: "logs"
    enabled: true
    recursive: true

compression:
  min_age_days: 7  # Compress files older than 7 days
  compression_level: 6
  remove_original_after: true

retention:
  keep_original_days: 30  # Keep originals for 30 days
  keep_compressed_days: 365  # Keep compressed for 1 year

organization:
  enabled: true
  organize_by: "date"
  structure: "year/month"  # Organize as YYYY/MM
```

## Usage

### Basic Usage

Compress log files with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Dry run mode (preview without compressing)
python src/main.py -d

# Process specific directory
python src/main.py -p /path/to/logs

# Combine options
python src/main.py -c config.yaml -d -p /path/to/logs
```

### Recommended Workflow

1. **First Run - Dry Run**:
   ```bash
   python src/main.py -d
   ```
   Review what would be compressed

2. **Review Logs**:
   Check `logs/log_compressor.log` and `logs/compression_report.txt`

3. **Actual Compression**:
   ```bash
   python src/main.py
   ```

## Project Structure

```
log-compressor/
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
├── logs/
│   ├── .gitkeep            # Log directory placeholder
│   ├── log_compressor.log  # Application logs
│   └── compression_report.txt  # Compression reports
└── compressed_logs/        # Organized compressed files (created automatically)
```

### File Descriptions

- **src/main.py**: Log file finding, compression, retention management, and organization
- **config.yaml**: YAML configuration file with targets and compression settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/log_compressor.log**: Application log file with rotation
- **logs/compression_report.txt**: Summary reports with statistics
- **compressed_logs/**: Organized compressed log files by date

## How It Works

1. **File Discovery**: Recursively finds log files matching configured patterns
2. **Age Check**: Verifies files are old enough to compress (min_age_days)
3. **Compression**: Compresses files using gzip with configurable compression level
4. **Organization**: Organizes compressed files by date (year/month structure)
5. **Retention**: Keeps original files for retention period, then removes them
6. **Cleanup**: Removes old compressed files exceeding retention period
7. **Logging**: Logs all operations and generates reports

## Date-Based Organization

Compressed files are organized by date for easy management:

- **Structure Options**:
  - `year/month`: `compressed_logs/2024/02/app.log.gz`
  - `year`: `compressed_logs/2024/app.log.gz`
  - `flat`: `compressed_logs/app.log.gz`

- **Date Source**: Uses file modification time (mtime)

## Retention Policy

The retention policy works in two stages:

1. **Original Files**: Kept for `keep_original_days` after compression
2. **Compressed Files**: Kept for `keep_compressed_days` total

Example:
- File compressed on day 7
- Original kept until day 37 (7 + 30 days)
- Compressed kept until day 372 (7 + 365 days)

## Logging

The application logs:

- **All Compressions**: Original and compressed file paths, sizes, space saved
- **Deletions**: Original and compressed file deletions
- **Errors**: Compression failures, permission errors
- **Statistics**: Summary of operations

Log files:
- `logs/log_compressor.log`: Detailed application log
- `logs/compression_report.txt`: Summary report with statistics

## Reports

Reports include:

- **Statistics**: Files scanned, compressed, skipped, failed, deleted
- **Space Saved**: Total disk space saved in MB
- **File List**: Detailed list of compressed files with sizes
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
- File pattern matching
- Age checking
- Compression operations
- Date-based organization
- Error handling

## Troubleshooting

### Common Issues

**Issue**: Permission denied errors

**Solution**: 
- Run with appropriate permissions
- Check file and directory permissions
- Verify write access to output directory

---

**Issue**: Files not being compressed

**Solution**: 
- Check min_age_days setting (files must be older than this)
- Verify file patterns match your log files
- Check skip_recently_modified setting
- Review logs for specific reasons

---

**Issue**: Original files deleted too quickly

**Solution**: 
- Increase keep_original_days in retention settings
- Set remove_original_after to false to keep originals indefinitely

---

**Issue**: Compressed files taking too much space

**Solution**: 
- Adjust compression_level (higher = better compression, slower)
- Reduce keep_compressed_days to delete old compressed files sooner
- Enable auto_cleanup in retention settings

---

**Issue**: Files organized incorrectly

**Solution**: 
- Check organization.structure setting
- Verify file modification times are correct
- Review organization.organize_by setting

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Permission denied"**: Check file and directory permissions
- **"No target directories configured"**: Add target directories to config.yaml

## Best Practices

1. **Always Use Dry Run First**: Preview compressions before actual processing
   ```bash
   python src/main.py -d
   ```

2. **Configure Appropriate Retention**: Balance storage needs with retention requirements
   ```yaml
   retention:
     keep_original_days: 30
     keep_compressed_days: 365
   ```

3. **Review Logs Regularly**: Check logs and reports after running
   - Review `logs/compression_report.txt` for summary
   - Check `logs/log_compressor.log` for details

4. **Set Appropriate Age Threshold**: Don't compress files that are still being written
   ```yaml
   compression:
     min_age_days: 7  # Adjust based on log rotation schedule
   ```

5. **Use Date Organization**: Organize compressed files for easy management
   ```yaml
   organization:
     structure: "year/month"
   ```

6. **Monitor Disk Space**: Regularly check space savings and adjust retention as needed

## Compression Levels

Gzip compression levels (1-9):

- **1-3**: Fast compression, larger files
- **4-6**: Balanced (default: 6)
- **7-9**: Best compression, slower processing

Higher levels provide better compression but take more time.

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
