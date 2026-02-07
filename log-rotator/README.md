# Log Rotator

A Python automation tool that rotates and archives old log files, keeping a specified number of recent logs and compressing older ones with date stamps.

## Features

- Rotate log files based on modification time
- Keep specified number of most recent log files
- Archive older log files to separate directory
- Compress archived logs using gzip
- Add date stamps to archived filenames
- Delete very old archived logs (configurable)
- Support for multiple file patterns
- Dry-run mode to preview operations
- Comprehensive error handling and logging
- Detailed statistics and reporting

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd log-rotator
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Configuration File

The tool uses a YAML configuration file (`config.yaml`) for settings. Key configuration sections:

- **rotation**: Rotation settings (directories, keep count, patterns, compression, date stamps)
- **logging**: Logging configuration

### Environment Variables

You can override configuration using environment variables:

- `LOG_DIRECTORY`: Directory containing log files (overrides config.yaml)
- `ARCHIVE_DIRECTORY`: Directory for archived logs (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Rotate logs with default configuration:**
```bash
python src/main.py
```

**Rotate logs in specific directory:**
```bash
python src/main.py --directory /var/log/app
```

**Specify archive directory:**
```bash
python src/main.py --directory /var/log/app --archive /backup/logs
```

**Keep specific number of recent logs:**
```bash
python src/main.py --directory /var/log/app --keep 10
```

**Match specific file patterns:**
```bash
python src/main.py --directory /var/log/app --pattern "*.log" --pattern "*.txt"
```

**Dry-run to preview operations:**
```bash
python src/main.py --directory /var/log/app --dry-run
```

### Use Cases

**Rotate application logs:**
```bash
python src/main.py -d /var/log/myapp -k 7 -a /backup/logs
```

**Rotate multiple log types:**
```bash
python src/main.py -d /var/log -p "*.log" -p "*.log.*" -k 5
```

**Preview rotation without making changes:**
```bash
python src/main.py -d /var/log/app --dry-run
```

## Project Structure

```
log-rotator/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── API.md
├── logs/
│   └── .gitkeep
└── archive/
    └── (archived logs)
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory
- `archive/`: Default archive directory

## How It Works

1. **Scan for log files**: Finds all files matching specified patterns in the log directory
2. **Sort by modification time**: Orders files from newest to oldest
3. **Keep recent files**: Retains the N most recent log files (configurable)
4. **Archive old files**: Moves older files to archive directory
5. **Add date stamps**: Optionally adds date stamps to archived filenames
6. **Compress archives**: Optionally compresses archived files using gzip
7. **Cleanup old archives**: Optionally deletes archived files older than specified days

### Example Rotation

Before rotation:
```
/var/log/app/
  app.log
  app.log.1
  app.log.2
  app.log.3
  app.log.4
  app.log.5
  app.log.6
  app.log.7
```

After rotation (keep_count=5):
```
/var/log/app/
  app.log
  app.log.1
  app.log.2
  app.log.3
  app.log.4

/backup/logs/
  app.log.5_20240207.gz
  app.log.6_20240207.gz
  app.log.7_20240207.gz
```

## Configuration Options

### Rotation Settings

- `log_directory`: Directory containing log files to rotate
- `archive_directory`: Directory to store archived logs
- `keep_count`: Number of most recent log files to keep (default: 5)
- `patterns`: List of file patterns to match (supports glob patterns)
- `compress`: Whether to compress archived logs (default: true)
- `add_date_stamp`: Whether to add date stamps to archived filenames (default: true)
- `date_format`: Date format for stamps (default: "%Y%m%d")
- `max_age_days`: Delete archived files older than this many days (0 = never delete)

### Date Format Examples

- `%Y%m%d`: 20240207
- `%Y-%m-%d`: 2024-02-07
- `%Y%m%d_%H%M%S`: 20240207_143022

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_main.py::test_rotate_logs
```

## Troubleshooting

### Common Issues

**No log files found:**
- Verify log directory path is correct
- Check file patterns match your log files
- Ensure log directory is readable

**Permission errors:**
- Ensure read permissions for log directory
- Ensure write permissions for archive directory
- Some system log directories may require elevated privileges

**Archive directory errors:**
- Verify archive directory path is writable
- Check available disk space
- Ensure parent directories exist

**Compression errors:**
- Verify sufficient disk space for compressed files
- Check file permissions
- Some files may already be compressed

### Error Messages

The tool provides detailed error messages in logs. Check `logs/log_rotator.log` for:
- File access errors
- Permission issues
- Compression problems
- Archive directory issues

### Best Practices

1. **Test with dry-run first**: Always use `--dry-run` to preview operations
2. **Backup before rotation**: Consider backing up logs before first rotation
3. **Monitor disk space**: Ensure sufficient space for archived logs
4. **Set appropriate keep_count**: Balance between keeping logs and disk usage
5. **Configure max_age_days**: Automatically clean up very old archives
6. **Use date stamps**: Helps identify when logs were archived
7. **Compress archives**: Saves significant disk space

## Automation

### Cron Job Example

Rotate logs daily at 2 AM:
```bash
0 2 * * * /path/to/venv/bin/python /path/to/log-rotator/src/main.py -d /var/log/app
```

### Systemd Timer Example

Create `/etc/systemd/system/log-rotator.service`:
```ini
[Unit]
Description=Log Rotator
After=network.target

[Service]
Type=oneshot
ExecStart=/path/to/venv/bin/python /path/to/log-rotator/src/main.py -d /var/log/app
User=loguser
```

Create `/etc/systemd/system/log-rotator.timer`:
```ini
[Unit]
Description=Daily Log Rotation
Requires=log-rotator.service

[Timer]
OnCalendar=daily
OnCalendar=02:00

[Install]
WantedBy=timers.target
```

## Security Considerations

- Ensure proper file permissions on log and archive directories
- Be cautious when rotating system logs (may require sudo)
- Verify archive directory is not publicly accessible
- Review log retention policies for compliance
- Consider encryption for sensitive archived logs

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
