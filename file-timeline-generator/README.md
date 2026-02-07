# File Timeline Generator

A Python automation tool for generating file timelines showing when files were created, modified, and accessed. This script is useful for tracking project evolution, understanding file activity patterns, and analyzing development history.

## Features

- **Timeline Collection**: Collects creation, modification, and access times for all files
- **Chronological Timeline**: Generates chronological timeline of all file events
- **Project Evolution Tracking**: Shows how the project evolved over time with file activity
- **Statistics Analysis**: Provides comprehensive statistics about file activity
- **Multiple Output Formats**: Text, JSON, and CSV output formats
- **Event Grouping**: Groups events by date for easy analysis
- **Extension Analysis**: Analyzes file types and their activity patterns
- **Time Span Calculation**: Calculates project time span and activity periods
- **Comprehensive Logging**: Detailed logging with rotation

## Prerequisites

- Python 3.8 or higher
- Read permissions to search directories
- File system that supports timestamps (all modern systems)

## Installation

1. Clone or navigate to the project directory:
```bash
cd file-timeline-generator
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
   - Set search directory
   - Configure output format
   - Adjust filtering options

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **search.directory**: Directory to analyze (default: current directory)
- **output.format**: Output format - text, json, or csv (default: text)
- **filtering.exclude_directories**: Directories to exclude from analysis
- **filtering.exclude_files**: File patterns to exclude
- **filtering.exclude_extensions**: File extensions to exclude

### Environment Variables

Optional environment variables can override configuration:

- `SEARCH_DIRECTORY`: Override search directory path

## Usage

### Basic Usage

Generate timeline with default configuration:
```bash
python src/main.py
```

### Custom Search Directory

Analyze a specific directory:
```bash
python src/main.py --directory /path/to/project
```

### Output to File

Save timeline to a file:
```bash
python src/main.py --output timeline.txt
```

### JSON Format

Generate timeline in JSON format:
```bash
python src/main.py --format json --output timeline.json
```

### CSV Format

Generate timeline in CSV format:
```bash
python src/main.py --format csv --output timeline.csv
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
- `-d, --directory`: Directory to analyze (overrides config)
- `-o, --output`: Output file path (default: stdout)
- `-f, --format`: Output format - text, json, or csv (overrides config)
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
file-timeline-generator/
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

1. **File Discovery**: Recursively scans the search directory for files, excluding system directories and files.

2. **Timeline Collection**: For each file, collects:
   - Creation time (st_ctime)
   - Modification time (st_mtime)
   - Access time (st_atime)
   - File size and extension

3. **Event Creation**: Creates timeline events for each file operation:
   - Created events
   - Modified events
   - Accessed events

4. **Timeline Analysis**: Analyzes collected timelines:
   - Calculates statistics (total files, events, time span)
   - Groups events by date
   - Tracks project evolution over time
   - Analyzes file types and activity patterns

5. **Report Generation**: Generates reports in requested format:
   - **Text**: Human-readable timeline with statistics and chronological events
   - **JSON**: Machine-readable structured data
   - **CSV**: Spreadsheet-compatible format

## Report Sections

### Statistics
- Total files analyzed
- Total events (created, modified, accessed)
- Earliest and latest events
- Time span in days
- Event counts by type
- File counts by extension

### Chronological Timeline
- All events sorted by timestamp
- Grouped by date for readability
- Shows event type, time, and file name

### Project Evolution
- Daily snapshot of project activity
- Shows files created, modified, and accessed per day
- Tracks cumulative total files over time
- Last 30 days by default

## Output Formats

### Text Format

Human-readable format with sections:
- Statistics summary
- Chronological timeline grouped by date
- Project evolution table

### JSON Format

Structured data format suitable for:
- Programmatic processing
- Integration with other tools
- Data visualization
- Automated analysis

### CSV Format

Spreadsheet-compatible format with columns:
- Timestamp
- Event type (created, modified, accessed)
- File path
- File size
- File extension

## Use Cases

### Tracking Project Evolution
Understand how a project has grown and changed over time:
```bash
python src/main.py --directory /path/to/project --output evolution.txt
```

### Analyzing Development Activity
Identify periods of high activity and file modification patterns:
```bash
python src/main.py --format json --output activity.json
```

### File History Analysis
Track when specific files were created, modified, or accessed:
```bash
python src/main.py --directory /path/to/project --format csv --output history.csv
```

### Project Documentation
Generate timeline documentation for project reports:
```bash
python src/main.py --directory /path/to/project --output project_timeline.txt
```

## Troubleshooting

### No Files Found

If no files are found:
- Check that search directory path is correct
- Verify files are not excluded by filters
- Ensure you have read permissions
- Review logs for specific issues

### Missing Timestamps

If timestamps are missing:
- Some file systems may not track all timestamps
- Creation time may not be available on all systems
- Access time may be disabled for performance (Linux)
- Check file system mount options

### Permission Errors

If you encounter permission errors:
- Ensure read access to search directory
- Check file and directory permissions
- Some files may be skipped with warnings
- Review logs for specific error messages

### Large Directory Performance

If analysis is slow:
- Processing time increases with number of files
- Consider analyzing subdirectories separately
- Use filtering to exclude unnecessary files
- Check logs for performance information

### Configuration Errors

If configuration errors occur:
- Validate YAML syntax in `config.yaml`
- Ensure all required configuration keys are present
- Check that paths are valid and accessible

## File System Considerations

### Timestamp Availability

- **Creation Time (st_ctime)**: Available on most systems, but may represent metadata change time on some Linux systems
- **Modification Time (st_mtime)**: Always available and reliable
- **Access Time (st_atime)**: May be disabled on some Linux systems for performance (noatime mount option)

### Performance Impact

- Reading file timestamps is fast
- Large directories may take time to process
- Consider filtering to reduce processing time

## Security Considerations

- The script only reads file metadata, never file contents
- No sensitive file contents are accessed
- File paths are logged but can be filtered
- The script respects file permissions and skips inaccessible files

## Performance Considerations

- Processing time increases with number of files
- Timestamp retrieval is fast but scales with file count
- Consider processing during off-peak hours for very large directories
- Use filtering to reduce the number of files analyzed

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
