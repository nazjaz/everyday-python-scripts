# Content Type Organizer

A Python script that identifies files by content type using MIME type detection and magic numbers, organizing files by actual content rather than file extensions. This tool helps organize files even when extensions are missing, incorrect, or misleading.

## Features

- **Content-Based Detection**: Uses magic numbers (file signatures) and MIME type detection to identify file types by actual content
- **Multiple Detection Methods**: Supports python-magic library, magic number detection, and extension-based fallback
- **Extension Mismatch Detection**: Identifies files where extensions don't match actual content
- **Intelligent Organization**: Organizes files into folders based on detected content type (Images, Videos, Documents, Music, Archives, etc.)
- **Comprehensive Reporting**: Generates detailed reports showing file distribution, detection methods, and extension mismatches
- **Dry Run Mode**: Test organization without actually moving files
- **Configurable**: Customizable MIME mappings, magic numbers, and folder structures via YAML configuration
- **Safe Operation**: Handles filename conflicts and provides detailed logging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Optional Dependencies

- **python-magic**: For enhanced MIME type detection (recommended)
  - On macOS: `brew install libmagic`
  - On Linux: `sudo apt-get install libmagic1` (Debian/Ubuntu) or `sudo yum install file-devel` (RHEL/CentOS)
  - On Windows: Install from [python-magic-bin](https://github.com/pidydx/libmagicwin64)

The script will work without python-magic using fallback detection methods, but accuracy is improved with it installed.

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd content-type-organizer
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install python-magic** (optional but recommended):
   ```bash
   pip install python-magic
   ```
   
   Note: You may also need to install system libraries (see Prerequisites).

## Configuration

The script uses `config.yaml` for configuration. Key settings include:

### Organization Settings

- `base_folder`: Base directory where organized files will be placed (default: "organized")
- `unknown_folder`: Folder name for files with unknown content type (default: "Unknown")
- `mime_mappings`: Custom mappings from MIME types to folder names

### Content Detection

- `magic_numbers`: Custom magic number definitions for file type detection

### Scanning

- `skip_patterns`: Patterns to skip during scanning (e.g., ".git", "__pycache__")

### Example Configuration

```yaml
organization:
  base_folder: "organized"
  unknown_folder: "Unknown"
  mime_mappings:
    "application/x-custom": "CustomFiles"

content_detection:
  magic_numbers:
    "application/x-custom": ["CUSTOM"]

scan:
  skip_patterns:
    - ".git"
    - "__pycache__"
    - ".venv"
```

## Usage

### Basic Usage

Scan and organize files in a directory:

```bash
python src/main.py /path/to/directory
```

### Command-Line Options

- `directory`: Directory to scan and organize (required)
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Simulate organization without moving files
- `-r, --report`: Output path for organization report (overrides config)

### Examples

**Dry run to preview organization**:
```bash
python src/main.py /path/to/files -d
```

**Organize files with custom config**:
```bash
python src/main.py /path/to/files -c custom_config.yaml
```

**Generate report to specific location**:
```bash
python src/main.py /path/to/files -r /path/to/report.txt
```

**Full example with all options**:
```bash
python src/main.py ~/Downloads -d -c config.yaml -r report.txt
```

## Project Structure

```
content-type-organizer/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── config.yaml            # Configuration file
├── .gitignore            # Git ignore patterns
├── src/
│   └── main.py           # Main application
├── tests/
│   └── test_main.py      # Unit tests
├── docs/
│   └── API.md            # API documentation
└── logs/
    └── .gitkeep          # Placeholder for logs
```

## How It Works

1. **Scanning**: Recursively scans the specified directory for files
2. **Detection**: For each file, attempts multiple detection methods:
   - **python-magic** (if available): Uses libmagic for accurate MIME detection
   - **Magic Numbers**: Checks file signatures (first bytes) against known patterns
   - **Extension Fallback**: Uses file extension as last resort
3. **Analysis**: Compares detected content type with file extension to identify mismatches
4. **Organization**: Moves files to folders based on detected content type:
   - Images → Images/
   - Videos → Videos/
   - Documents → Documents/
   - Music → Music/
   - Archives → Archives/
   - Unknown → Unknown/
5. **Reporting**: Generates a comprehensive report with statistics and findings

## Supported File Types

The script recognizes many common file types including:

- **Images**: JPEG, PNG, GIF, BMP, WebP, SVG
- **Documents**: PDF, Word, Excel, PowerPoint, Text, HTML, XML, JSON
- **Videos**: MP4, AVI, QuickTime, Matroska, WebM
- **Audio**: MP3, WAV, FLAC, OGG
- **Archives**: ZIP, RAR, 7Z, TAR, GZIP
- **Executables**: Windows executables (PE format)

Custom file types can be added via configuration.

## Testing

Run the test suite using pytest:

```bash
pytest tests/test_main.py -v
```

For coverage report:

```bash
pytest tests/test_main.py --cov=src --cov-report=html
```

## Troubleshooting

### "python-magic not available" Warning

This is normal if python-magic is not installed. The script will use fallback detection methods. For better accuracy, install python-magic and system libraries (see Prerequisites).

### Permission Errors

Ensure you have read access to source files and write access to the destination directory. The script will log permission errors and continue processing other files.

### Files Not Detected Correctly

1. Check if the file type is supported (see Supported File Types)
2. Add custom magic numbers in `config.yaml` for unsupported types
3. Install python-magic for improved detection accuracy

### Large Directory Scanning

For very large directories, scanning may take time. The script logs progress and provides statistics upon completion. Consider using dry-run mode first to preview operations.

### Extension Mismatches

The script will report files where extensions don't match content. Review the report to identify files that may need manual attention.

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for all public functions and classes
4. Add unit tests for new features
5. Update documentation as needed

## License

This project is provided as-is for educational and personal use.
