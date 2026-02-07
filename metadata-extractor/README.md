# Metadata Extractor

A Python automation script that extracts and reports file metadata including EXIF data for images, ID3 tags for audio files, and document properties for office files. Useful for cataloging files, analyzing media properties, and extracting embedded information.

## Features

- **Image EXIF extraction**: Extracts EXIF data, GPS information, and image properties from JPEG, PNG, TIFF, and other image formats
- **Audio ID3 tags**: Extracts ID3 tags, duration, bitrate, and audio properties from MP3, FLAC, OGG, and other audio formats
- **Office document properties**: Extracts metadata from DOCX and XLSX files including author, creation date, and document properties
- **Multiple output formats**: Supports JSON and human-readable text reports
- **Recursive scanning**: Optionally scan directories recursively
- **Comprehensive logging**: Detailed logs for all operations
- **Error handling**: Graceful handling of corrupted or unsupported files

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd metadata-extractor
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

The script requires the following libraries:
- **Pillow**: For image EXIF data extraction
- **mutagen**: For audio ID3 tag extraction
- **python-docx**: For DOCX document properties
- **openpyxl**: For XLSX spreadsheet properties
- **PyYAML**: For configuration file parsing

## Configuration

### Configuration File (config.yaml)

The script supports configuration via a YAML file:

```yaml
recursive: false
file_types: null  # Options: images, audio, office
output_format: "both"  # Options: json, text, both
```

## Usage

### Basic Usage

Extract metadata from a single file:

```bash
python src/main.py image.jpg
```

### Multiple Files

Extract metadata from multiple files:

```bash
python src/main.py image1.jpg image2.png audio.mp3 document.docx
```

### Directory Scanning

Extract metadata from all files in a directory:

```bash
python src/main.py /path/to/directory
```

### Recursive Scanning

Recursively scan directories:

```bash
python src/main.py /path/to/directory --recursive
```

### Output to JSON

Save metadata to JSON file:

```bash
python src/main.py image.jpg --output metadata.json
```

### Output to Text Report

Save human-readable report:

```bash
python src/main.py image.jpg --report report.txt
```

### Both Output Formats

Save both JSON and text reports:

```bash
python src/main.py image.jpg --output metadata.json --report report.txt
```

### Use Configuration File

```bash
python src/main.py /path/to/files --config config.yaml
```

### Command-Line Arguments

- `paths`: File paths or directory paths to process (required, one or more)
- `--recursive`: Recursively scan directories
- `--output`: Output file path for JSON report
- `--report`: Output file path for text report
- `--config`: Path to configuration file (YAML)

## Supported File Types

### Images
- JPEG/JPG
- PNG
- TIFF/TIF
- BMP
- GIF
- WebP

**Extracted metadata:**
- Image dimensions (width x height)
- File format and color mode
- EXIF data (camera settings, date/time, GPS coordinates)
- Image information (compression, quality settings)

### Audio Files
- MP3
- FLAC
- OGG
- M4A
- AAC
- WMA

**Extracted metadata:**
- ID3 tags (title, artist, album, genre, year)
- Duration
- Bitrate
- Sample rate
- Channels

### Office Documents
- DOCX (Microsoft Word)
- XLSX (Microsoft Excel)

**Extracted metadata:**
- Document properties (title, author, subject, keywords)
- Creation and modification dates
- Revision information
- Document statistics (paragraph count, sheet count)

## Project Structure

```
metadata-extractor/
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

- `src/main.py`: Core implementation with MetadataExtractor class and CLI interface
- `config.yaml`: Default configuration file with processing settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

## Output Formats

### JSON Format

Structured JSON output suitable for programmatic processing:

```json
{
  "file_path": "/path/to/image.jpg",
  "file_type": "image",
  "file_size": 123456,
  "format": "JPEG",
  "size": {
    "width": 1920,
    "height": 1080
  },
  "exif": {
    "DateTime": "2024:01:15 14:30:00",
    "Make": "Canon",
    "Model": "EOS 5D"
  }
}
```

### Text Report Format

Human-readable text report with formatted output:

```
Metadata Extraction Report
================================================================================

Total files processed: 5
Images: 3
Audio: 1
Office files: 1
Errors: 0

--------------------------------------------------------------------------------

File: /path/to/image.jpg
Type: image
Size: 123,456 bytes
Dimensions: 1920x1080
EXIF Data:
  DateTime: 2024:01:15 14:30:00
  Make: Canon
  Model: EOS 5D
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
- Image EXIF extraction
- Audio ID3 tag extraction
- Office document property extraction
- Error handling for unsupported files
- Configuration file loading
- Output formatting

## Troubleshooting

### Common Issues

**Issue: "PIL/Pillow not available"**

Solution: Install Pillow: `pip install Pillow`

**Issue: "mutagen not available"**

Solution: Install mutagen: `pip install mutagen`

**Issue: "python-docx not available"**

Solution: Install python-docx: `pip install python-docx`

**Issue: "openpyxl not available"**

Solution: Install openpyxl: `pip install openpyxl`

**Issue: "No metadata extracted"**

Solution: Verify that:
- Files are of supported types
- Files are not corrupted
- Required libraries are installed
- Files have embedded metadata (some files may not have metadata)

**Issue: "Permission denied"**

Solution: Ensure you have read permissions for the files you're trying to process.

### Error Messages

All errors are logged to both the console and `logs/extractor.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `extractor.log`: Main log file with all operations and errors

## Examples

### Extract EXIF from Photos

```bash
python src/main.py ~/Pictures --recursive --output photos_metadata.json
```

### Extract ID3 Tags from Music

```bash
python src/main.py ~/Music --recursive --output music_metadata.json
```

### Extract Document Properties

```bash
python src/main.py ~/Documents/*.docx --output documents_metadata.json
```

### Generate Comprehensive Report

```bash
python src/main.py ~/Media --recursive \
  --output metadata.json \
  --report report.txt
```

## Performance Considerations

- Processing large numbers of files may take time
- Image EXIF extraction requires reading file headers
- Audio ID3 extraction is generally fast
- Office document extraction may be slower for large files
- Recursive scanning of large directory trees may take time

## Security Considerations

- The script only reads files and does not modify them
- EXIF data may contain sensitive location information (GPS coordinates)
- Document properties may contain author names and other metadata
- Be cautious when sharing extracted metadata files

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
