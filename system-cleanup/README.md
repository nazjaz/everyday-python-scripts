# System Cleanup

A Python automation tool for identifying and removing system artifacts, cache files, and temporary system files that are safe to delete. This script helps free up disk space by cleaning up unnecessary system files while maintaining safety checks to prevent deletion of critical files.

## Features

- **Platform Support**: Works on macOS, Windows, and Linux
- **Multiple File Types**:
  - **Cache Files**: Application cache files
  - **Temporary Files**: System temporary files
  - **System Artifacts**: Log files, old backups, crash dumps
- **Safety Checks**:
  - Never deletes critical system files
  - Checks file age before deletion
  - Validates file patterns
  - Protects important directories
- **Dry Run Mode**: Preview what would be deleted without making changes
- **Size Reporting**: Shows how much space would be freed
- **Comprehensive Logging**: Detailed logging of all operations
- **Configurable Limits**: Set maximum size to delete

## Prerequisites

- Python 3.8 or higher
- Administrator/sudo permissions may be required for some system directories
- Sufficient disk space for logging

## Installation

1. Clone or navigate to the project directory:
```bash
cd system-cleanup
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

4. Copy and configure the environment file (optional):
```bash
cp .env.example .env
# Edit .env with your settings if needed
```

5. Review and customize `config.yaml` with your settings:
   - Configure cleanup patterns
   - Adjust safety settings
   - Set minimum age requirements

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **cleanup.cache_patterns**: Patterns to identify cache files
- **cleanup.temp_patterns**: Patterns to identify temporary files
- **cleanup.artifact_patterns**: Patterns to identify system artifacts
- **safety.min_age_days**: Minimum age in days before file can be deleted (0 = no minimum)
- **safety.unsafe_extensions**: File extensions that should never be deleted
- **safety.unsafe_patterns**: Filename patterns that should never be deleted
- **safety.protected_directories**: Directory paths that should never be touched

### Platform-Specific Paths

The script automatically detects your platform and scans appropriate directories:

#### macOS
- Cache: `~/Library/Caches`, `/Library/Caches`
- Temp: `/private/var/folders`, `/private/var/tmp`
- Artifacts: `~/Library/Logs`, `~/.Trash`

#### Windows
- Cache: `%LOCALAPPDATA%\Temp`, `%TEMP%`
- Temp: `%LOCALAPPDATA%\Temp`, `%TEMP%`
- Artifacts: `%LOCALAPPDATA%\Microsoft\Windows\INetCache`, `%LOCALAPPDATA%\Microsoft\Windows\History`

#### Linux
- Cache: `~/.cache`, `/var/cache`
- Temp: `/tmp`, `/var/tmp`
- Artifacts: `/var/log`, `~/.local/share/Trash`

### Environment Variables

Optional environment variables can override configuration:

- `MIN_AGE_DAYS`: Override minimum age in days
- `MAX_SIZE_MB`: Override maximum size to delete in MB

## Usage

### Basic Usage

Run cleanup with default configuration:
```bash
python src/main.py
```

### Dry Run

Preview what would be deleted without making changes:
```bash
python src/main.py --dry-run
```

### Limit Size

Limit total size to delete:
```bash
python src/main.py --max-size 1000  # Limit to 1000 MB
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Perform a dry run without deleting files
- `--max-size`: Maximum total size to delete in MB (default: no limit)
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
system-cleanup/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── .gitkeep             # Documentation directory placeholder
└── logs/
    └── .gitkeep             # Logs directory placeholder
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## How It Works

1. **Platform Detection**: Detects operating system (macOS, Windows, Linux)

2. **Path Discovery**: Identifies platform-specific directories:
   - Cache directories
   - Temporary directories
   - System artifact directories

3. **File Scanning**: Recursively scans directories for:
   - Cache files matching patterns
   - Temporary files matching patterns
   - System artifacts matching patterns

4. **Safety Validation**: For each file found:
   - Checks file extension against unsafe list
   - Checks filename against unsafe patterns
   - Verifies file is not in protected directory
   - Validates minimum age requirement

5. **Deletion**: Safely deletes validated files:
   - Removes files that pass all safety checks
   - Logs all deletion operations
   - Reports size freed

6. **Reporting**: Provides summary of:
   - Files scanned
   - Files found
   - Files deleted
   - Size freed

## Safety Features

### Protected File Types
- Executables (.exe, .dll, .so, .dylib)
- System files (.sys, .drv)
- Application bundles (.app)

### Protected Patterns
- Files containing "system", "kernel", "boot"
- Configuration files
- Settings and preferences

### Protected Directories
- System directories (/System, /usr, /bin, /sbin)
- Windows system directories (System32, SysWOW64)
- Program directories

### Age Requirements
- Optional minimum age before deletion
- Prevents deletion of recently created files

## Example Output

```
============================================================
System Cleanup Summary
============================================================

Cache Files:
  Scanned: 150
  Found: 120
  Deleted: 115
  Failed: 5
  Size freed: 245.67 MB

Temporary Files:
  Scanned: 200
  Found: 180
  Deleted: 175
  Failed: 5
  Size freed: 89.23 MB

System Artifacts:
  Scanned: 50
  Found: 30
  Deleted: 28
  Failed: 2
  Size freed: 12.45 MB

Total Size Freed: 347.35 MB
============================================================
```

## Troubleshooting

### Permission Errors

If you encounter permission errors:
- Run with administrator/sudo privileges for system directories
- Check file and directory permissions
- Some files may require elevated permissions
- Review logs for specific error messages

### No Files Found

If no files are found:
- Verify platform detection is correct
- Check that directories exist and are accessible
- Review configuration patterns
- Ensure minimum age requirement is not too restrictive

### Too Many Files Deleted

If too many files are deleted:
- Increase minimum age requirement
- Add more unsafe patterns
- Add protected directories
- Review logs to identify what was deleted

### Performance Issues

If cleanup is slow:
- Limit scan depth for temp directories
- Use max-size limit to stop early
- Process specific categories separately
- Review logs for performance bottlenecks

## Security Considerations

- **Never deletes critical system files**: Multiple safety checks prevent deletion of important files
- **Dry run by default**: Always test with --dry-run first
- **Comprehensive logging**: All operations are logged for audit
- **Protected directories**: System directories are never touched
- **Pattern validation**: Files matching unsafe patterns are skipped

## Best Practices

1. **Always use dry-run first**: Preview what will be deleted
2. **Start with small limits**: Use --max-size to limit initial cleanup
3. **Review logs**: Check what was deleted after cleanup
4. **Backup important data**: Ensure important files are backed up
5. **Test configuration**: Verify safety settings before full cleanup
6. **Regular cleanup**: Run periodically to maintain system performance

## Limitations

- May require elevated permissions for some directories
- Some files may be locked by running processes
- Platform-specific paths may vary
- Large directory trees may take time to scan

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages
7. Test on multiple platforms

## License

This project is provided as-is for automation purposes.

## Disclaimer

This tool deletes files from your system. Use with caution:
- Always use --dry-run first
- Review what will be deleted
- Ensure important files are backed up
- Test on non-critical systems first
- The authors are not responsible for data loss
