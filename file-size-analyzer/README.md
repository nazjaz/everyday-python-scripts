# File Size Analyzer

A Python automation tool that generates detailed file size reports showing largest files, size distribution by type, and recommendations for cleanup.

## Features

- Scan directories and collect file size information
- Identify largest files with detailed paths
- Calculate size distribution by file type/extension
- Generate cleanup recommendations based on:
  - Large files (configurable threshold)
  - Old files (configurable age threshold)
  - Extension-specific rules
  - Many files of same type
- Comprehensive text reports
- Recursive or non-recursive directory scanning
- Configurable exclusions (patterns, directories, extensions)
- Human-readable file size formatting
- Detailed statistics and analysis

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd file-size-analyzer
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

- **analysis**: Analysis settings (scan directory, recursive, exclusions)
- **cleanup**: Cleanup recommendation rules and thresholds
- **report**: Report generation settings
- **logging**: Logging configuration

### Environment Variables

You can override configuration using environment variables:

- `SCAN_DIRECTORY`: Directory to analyze (overrides config.yaml)
- `OUTPUT_DIRECTORY`: Output directory for reports (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Analyze directory with default configuration:**
```bash
python src/main.py
```

**Analyze specific directory:**
```bash
python src/main.py --directory /path/to/analyze
```

**Non-recursive scan:**
```bash
python src/main.py --directory /path/to/analyze --no-recursive
```

**Generate report to file:**
```bash
python src/main.py --directory /path/to/analyze --output report.txt
```

**Show top N largest files:**
```bash
python src/main.py --directory /path/to/analyze --largest 20
```

### Use Cases

**Analyze home directory:**
```bash
python src/main.py -d ~ -o ~/file_analysis.txt
```

**Analyze downloads folder:**
```bash
python src/main.py -d ~/Downloads
```

**Analyze project directory:**
```bash
python src/main.py -d ./project --output project_analysis.txt
```

## Project Structure

```
file-size-analyzer/
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
└── output/
    └── (generated reports)
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory
- `output/`: Generated reports directory

## Report Contents

The generated report includes:

1. **Summary Statistics**
   - Total files scanned
   - Total size
   - Directories scanned
   - Errors encountered

2. **Largest Files (Top 20)**
   - List of largest files with sizes and paths
   - Sorted by file size (largest first)

3. **Size Distribution by File Type**
   - Breakdown by file extension
   - File count per type
   - Total size per type
   - Percentage of total size
   - Average file size per type
   - Top 30 file types displayed

4. **Cleanup Recommendations**
   - Prioritized recommendations (high, medium, low)
   - Large files recommendation
   - Old files recommendation
   - Extension-specific recommendations
   - Many files of same type recommendation
   - Specific suggestions for each recommendation

## Cleanup Recommendations

The tool generates recommendations based on:

- **Large Files**: Files exceeding configurable size threshold (default: 100MB)
- **Old Files**: Files older than configurable age (default: 365 days)
- **Extension Rules**: Custom rules for specific file types (logs, temp files, etc.)
- **Many Files**: Extensions with many files (default: 100+ files)

### Example Recommendations

- **High Priority**: Temporary files, large log files
- **Medium Priority**: Old backup files, large archives
- **Low Priority**: Cache files, many files of same type

## Configuration Options

### Analysis Settings

- `scan_directory`: Directory to analyze
- `recursive`: Scan subdirectories (default: true)
- `exclude.patterns`: Regex patterns to exclude
- `exclude.directories`: Directory names to exclude
- `exclude.extensions`: File extensions to exclude

### Cleanup Settings

- `large_file_threshold_mb`: Threshold for large files (MB)
- `old_file_threshold_days`: Age threshold for old files (days)
- `duplicate_extension_threshold`: Threshold for many files of same type
- `extension_recommendations`: Custom rules per extension

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
pytest tests/test_main.py::test_scan_directory
```

## Troubleshooting

### Common Issues

**Permission errors:**
- Ensure read permissions for scan directory
- Some system directories may require elevated privileges
- Check file system permissions

**Large directory scanning:**
- Scanning very large directories may take time
- Consider using exclusions to skip unnecessary directories
- Use non-recursive scan for specific directories
- Check logs for progress information

**Memory issues:**
- Very large directory trees may consume significant memory
- Consider scanning subdirectories separately
- Review exclusion rules to reduce file count

**Report generation errors:**
- Verify write permissions for output directory
- Check available disk space
- Review logs for specific error messages

### Error Messages

The tool provides detailed error messages in logs. Check `logs/file_analyzer.log` for:
- Permission errors
- File access issues
- Directory scanning problems
- Report generation errors

### Performance Tips

- Use exclusions to skip large unnecessary directories (e.g., `.git`, `node_modules`)
- Scan specific subdirectories instead of entire filesystem
- Use non-recursive scan when searching specific directories
- Consider scanning during off-peak hours for large filesystems

## Security Considerations

- This tool only reads file metadata, it does not modify files
- Requires read access to directories being analyzed
- Be cautious when analyzing system directories (may require sudo)
- Reports may contain sensitive path information
- Review exclusion rules to avoid analyzing sensitive directories

## Example Output

```
================================================================================
File Size Analysis Report
================================================================================
Generated: 2024-02-07 10:30:00

Summary Statistics
--------------------------------------------------------------------------------
Total files scanned: 15,234
Total size: 45.67 GB
Directories scanned: 1,234
Errors encountered: 0

Largest Files (Top 20)
--------------------------------------------------------------------------------
 1.     2.45 GB  large_video.mp4  /path/to/large_video.mp4
 2.     1.23 GB  archive.zip      /path/to/archive.zip
 ...

Size Distribution by File Type
--------------------------------------------------------------------------------
Extension              Count    Total Size    % of Total    Avg Size
--------------------------------------------------------------------------------
.mp4                   234      12.45 GB       27.25%       54.49 MB
.zip                    45       8.23 GB       18.01%      187.11 MB
...

Cleanup Recommendations
--------------------------------------------------------------------------------

1. [HIGH] Found 15 file(s) larger than 100.00 MB
   Size: 5.67 GB
   Files: 15
   Suggestion: Review large files and consider archiving or moving to external storage
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
