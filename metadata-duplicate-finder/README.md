# Metadata Duplicate Finder

A Python automation script that identifies files with duplicate metadata like identical EXIF data, creation dates, or other attributes, grouping related files. Useful for finding duplicate photos, identifying files from the same source, and organizing files by metadata similarity.

## Features

- **EXIF data comparison**: Identifies images with identical EXIF metadata (camera settings, date/time, GPS, etc.)
- **Date matching**: Finds files with identical creation or modification dates
- **File size matching**: Optional file size comparison
- **Filename similarity**: Optional filename pattern matching
- **Similarity mode**: Find files with similar (not identical) metadata
- **Grouping**: Groups files with matching metadata together
- **Comprehensive reporting**: Detailed reports of duplicate groups
- **JSON export**: Export results in JSON format for programmatic processing

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd metadata-duplicate-finder
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

The script requires:
- **Pillow**: For EXIF data extraction from images
- **PyYAML**: For configuration file parsing

## Configuration

### Configuration File (config.yaml)

The script supports configuration via a YAML file:

```yaml
check_exif: true
check_dates: true
check_size: false
check_filename: false
similarity_threshold: 0.8
recursive: false
```

## Usage

### Basic Usage

Find files with duplicate metadata:

```bash
python src/main.py /path/to/files
```

### Recursive Scanning

Scan directories recursively:

```bash
python src/main.py /path/to/directory --recursive
```

### Disable EXIF Checking

Skip EXIF data comparison:

```bash
python src/main.py /path/to/files --no-exif
```

### Check File Sizes

Include file size in comparison:

```bash
python src/main.py /path/to/files --check-size
```

### Similarity Mode

Find files with similar (not identical) metadata:

```bash
python src/main.py /path/to/files --similarity --similarity-threshold 0.8
```

### Save Report to File

Save results to a text file:

```bash
python src/main.py /path/to/files --output report.txt
```

### Export to JSON

Export results to JSON format:

```bash
python src/main.py /path/to/files --json results.json
```

### Use Configuration File

```bash
python src/main.py /path/to/files --config config.yaml
```

### Command-Line Arguments

- `paths`: File paths or directory paths to scan (required, one or more)
- `--recursive`: Recursively scan directories
- `--check-exif`: Check EXIF data for duplicates (default: True)
- `--no-exif`: Disable EXIF checking
- `--check-dates`: Check creation/modification dates (default: True)
- `--check-size`: Check file sizes
- `--check-filename`: Check similar filenames
- `--similarity`: Find similar metadata instead of exact duplicates
- `--similarity-threshold`: Similarity threshold for matching (0.0-1.0, default: 0.8)
- `--output`: Output file path for text report
- `--json`: Output JSON file path for results
- `--config`: Path to configuration file (YAML)

## Project Structure

```
metadata-duplicate-finder/
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

- `src/main.py`: Core implementation with MetadataDuplicateFinder class and CLI interface
- `config.yaml`: Default configuration file with checking settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

## Metadata Comparison

The script compares files based on:

### EXIF Data

For image files (JPEG, PNG, TIFF, etc.), compares:
- Camera make and model
- Date and time taken
- GPS coordinates
- Camera settings (ISO, aperture, shutter speed)
- Other EXIF tags

### File Dates

Compares:
- Creation date
- Modification date

### File Size

Optional comparison of file sizes (useful for finding exact duplicates).

### Filename

Optional comparison of filenames (useful for finding renamed copies).

## Output Format

### Text Report

```
Metadata Duplicate Report
================================================================================

Files processed: 150
Files with EXIF: 120
Duplicate groups: 5
Total duplicates: 12
Errors: 0

--------------------------------------------------------------------------------

Group 1: 3 files with identical metadata

  File: /path/to/image1.jpg
    Size: 1,234,567 bytes
    Created: 2024-01-15T10:30:00
    Modified: 2024-01-15T10:30:00
    EXIF DateTime: 2024:01:15 10:30:00
    EXIF Make: Canon
    EXIF Model: EOS 5D

  File: /path/to/image2.jpg
    ...
```

### JSON Export

```json
{
  "groups": [
    {
      "signature": "exif:...|dates:...",
      "files": [
        {
          "path": "/path/to/file1.jpg",
          "size": 1234567,
          "created": "2024-01-15T10:30:00",
          "modified": "2024-01-15T10:30:00",
          "exif": {
            "DateTime": "2024:01:15 10:30:00",
            "Make": "Canon",
            "Model": "EOS 5D"
          }
        }
      ]
    }
  ]
}
```

## Use Cases

### Finding Duplicate Photos

Find photos taken at the same time with the same camera:

```bash
python src/main.py ~/Pictures --recursive --check-exif --check-dates
```

### Identifying Files from Same Source

Find files with identical creation dates:

```bash
python src/main.py /path/to/files --check-dates --no-exif
```

### Finding Similar Files

Find files with similar metadata:

```bash
python src/main.py /path/to/files --similarity --similarity-threshold 0.7
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
- EXIF data extraction
- Metadata signature creation
- Duplicate detection
- Similarity calculation
- File grouping
- Error handling

## Troubleshooting

### Common Issues

**Issue: "PIL/Pillow not available"**

Solution: Install Pillow: `pip install Pillow`. EXIF checking will be disabled without it.

**Issue: "No duplicates found"**

Solution: Verify that:
- Files have metadata to compare
- Appropriate checking options are enabled
- Files are accessible and readable

**Issue: "Permission denied"**

Solution: Ensure you have read permissions for the files you're trying to scan.

**Issue: "Too many false positives"**

Solution: Adjust checking options. For example, disable file size checking if files are different sizes but have same EXIF data.

**Issue: "Similarity mode not finding matches"**

Solution: Lower the similarity threshold (e.g., `--similarity-threshold 0.6`).

### Error Messages

All errors are logged to both the console and `logs/finder.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `finder.log`: Main log file with all operations and errors

## Performance Considerations

- Processing large numbers of files may take time
- EXIF extraction requires reading image files
- Similarity mode compares all file pairs, which can be slow for many files
- Recursive scanning of large directory trees may take time

## Best Practices

1. **Use specific checking options**: Enable only the metadata types you need to compare
2. **Start with exact duplicates**: Use default settings first, then try similarity mode if needed
3. **Review results carefully**: Some "duplicates" may be legitimate (e.g., edited versions)
4. **Export to JSON**: Use JSON export for programmatic processing or further analysis
5. **Check recursively**: Use `--recursive` to scan entire directory trees

## Limitations

- **EXIF data**: Only available for image files that contain EXIF metadata
- **Date precision**: File system dates may have limited precision
- **Similarity calculation**: Simple set-based similarity; may not catch all variations
- **Large datasets**: Similarity mode can be slow for many files

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
