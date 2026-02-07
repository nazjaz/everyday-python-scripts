# Photo GPS Organizer

Organize photos by GPS location extracted from EXIF data, creating folders named by location or coordinates when available. Perfect for organizing travel photos, location-based photo collections, and creating geographic photo libraries.

## Project Description

Photo GPS Organizer solves the problem of organizing large photo collections by geographic location. By extracting GPS coordinates from EXIF metadata embedded in photos, the script automatically organizes photos into folders named by location (when reverse geocoding is enabled) or by coordinates. Ideal for photographers, travelers, and anyone with location-tagged photos.

**Target Audience**: Photographers, travelers, photo enthusiasts, and anyone who wants to organize photos by geographic location.

## Features

- **EXIF GPS Extraction**: Reads GPS coordinates from photo EXIF data
- **Location-Based Organization**: Creates folders named by location or coordinates
- **Reverse Geocoding**: Optional conversion of coordinates to location names (requires geopy)
- **Multiple Image Formats**: Supports JPEG, PNG, TIFF, HEIC, and more
- **Move or Copy**: Choose to move or copy photos during organization
- **Duplicate Handling**: Skip, rename, or overwrite duplicate files
- **Recursive Scanning**: Processes photos in subdirectories
- **Comprehensive Logging**: Detailed logs of all operations
- **Error Handling**: Gracefully handles photos without GPS data
- **Statistics Tracking**: Reports photos scanned, organized, and errors

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read permissions to photos being processed
- Write permissions to destination directory

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/photo-gps-organizer
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

**Note**: For reverse geocoding (location names), `geopy` is included in requirements.txt. If you only need coordinate-based organization, you can skip installing geopy.

### Step 4: Configure Settings

Edit `config.yaml` to set your source directory and organization preferences:

```yaml
source_directory: ~/Pictures
destination_directory: organized_photos
operation: move  # or "copy"
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory containing photos to organize
- **destination_directory**: Directory where organized photos will be placed
- **image_extensions**: List of image file extensions to process
- **operation**: "move" or "copy" photos
- **duplicate_handling**: How to handle duplicates ("skip", "rename", "overwrite")
- **geocoding**: Reverse geocoding settings (optional)
  - **enabled**: Enable reverse geocoding to get location names
- **folder_naming**: Options for folder naming
  - **coordinate_format**: "decimal" or "dms" (degrees, minutes, seconds)
  - **coordinate_precision**: Decimal places for coordinates
  - **include_coordinates**: Add coordinates to location name folders
- **exclusions**: Configuration for excluding files
  - **directories**: Directories to exclude
  - **patterns**: Patterns to match in filenames
- **operations**: Operation settings
  - **recursive**: Scan subdirectories recursively
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory path
- `DESTINATION_DIRECTORY`: Override destination directory path

### Example Configuration

```yaml
source_directory: ~/Pictures
destination_directory: organized_photos
operation: move
duplicate_handling: rename

geocoding:
  enabled: true  # Requires geopy and internet connection

folder_naming:
  coordinate_format: decimal
  coordinate_precision: 4
  include_coordinates: false

operations:
  recursive: true
```

## Usage

### Basic Usage

Organize photos with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Dry run (copies files instead of moving)
python src/main.py --dry-run
```

### Common Use Cases

1. **Organize Photos by Location**:
   ```bash
   python src/main.py
   ```
   Creates folders based on GPS coordinates or location names.

2. **Copy Instead of Move**:
   - Edit `config.yaml` and set `operation: copy`
   - Or use `--dry-run` flag

3. **Enable Location Names**:
   - Edit `config.yaml` and set `geocoding.enabled: true`
   - Ensure `geopy` is installed: `pip install geopy`
   - Requires internet connection for reverse geocoding

4. **Organize Specific Directory**:
   - Edit `source_directory` in `config.yaml`
   - Or set environment variable: `export SOURCE_DIRECTORY=/path/to/photos`

5. **Handle Duplicates**:
   - Set `duplicate_handling: rename` to automatically rename duplicates
   - Set `duplicate_handling: skip` to skip existing files
   - Set `duplicate_handling: overwrite` to replace existing files

## Project Structure

```
photo-gps-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml               # Configuration file
├── .gitignore               # Git ignore rules
├── src/
│   ├── __init__.py          # Package initialization
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation (if applicable)
└── logs/
    └── .gitkeep             # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core photo organization logic with EXIF GPS extraction
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)
- **organized_photos/**: Destination directory for organized photos (created when script runs)

## Folder Naming

### Coordinate-Based Folders

When reverse geocoding is disabled or fails, folders are named using coordinates:

- **Decimal format** (default): `Lat40.7128_Lon-74.0060`
- **DMS format**: `40d42m46.08sN_74d0m21.6sW`

### Location Name Folders

When reverse geocoding is enabled and successful, folders use location names:

- **City name**: `New_York`
- **With coordinates**: `New_York_Lat40.7128_Lon-74.0060` (if `include_coordinates: true`)

## Reverse Geocoding

Reverse geocoding converts GPS coordinates to human-readable location names using the Nominatim service (OpenStreetMap).

### Requirements

- `geopy` library installed: `pip install geopy`
- Internet connection (for API calls)
- Rate limiting: Nominatim has usage limits (1 request per second recommended)

### Enabling Reverse Geocoding

1. Install geopy: `pip install geopy`
2. Set `geocoding.enabled: true` in `config.yaml`
3. Run the script (requires internet connection)

### Limitations

- Requires internet connection
- May be slow for large photo collections
- Subject to API rate limits
- Location names depend on OpenStreetMap data quality

## Supported Image Formats

The script supports common image formats with EXIF data:

- JPEG (.jpg, .jpeg)
- TIFF (.tiff, .tif)
- PNG (.png) - limited EXIF support
- HEIC/HEIF (.heic, .heif) - if supported by Pillow

## GPS Data Requirements

Photos must contain GPS EXIF data for organization. GPS data is typically added by:

- Cameras with GPS functionality
- Smartphones with location services enabled
- Photo editing software that preserves EXIF data

Photos without GPS data will be logged but not organized.

## Performance Considerations

- **Large Collections**: Processing time increases with number of photos
- **Reverse Geocoding**: Significantly slower due to API calls (1 request/second recommended)
- **File Operations**: Move operations are faster than copy operations
- **Recursive Scanning**: May take longer for deeply nested directories

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- EXIF data extraction
- GPS coordinate conversion
- Folder naming logic
- File organization operations
- Error handling
- Duplicate handling

## Troubleshooting

### Common Issues

**Issue**: `No GPS data in photo`

**Solution**: The photo doesn't contain GPS EXIF data. Ensure your camera or phone has location services enabled when taking photos. Some photo editing software may strip EXIF data.

---

**Issue**: `Error reading EXIF from photo`

**Solution**: The photo may be corrupted or in an unsupported format. Check that the file is a valid image and supported format.

---

**Issue**: Reverse geocoding not working

**Solution**:
- Ensure `geopy` is installed: `pip install geopy`
- Check internet connection
- Verify `geocoding.enabled: true` in config
- Check rate limiting (may need to slow down requests)

---

**Issue**: `PermissionError` when organizing photos

**Solution**: Ensure you have read permissions to source photos and write permissions to destination directory.

---

**Issue**: Photos not being organized

**Solution**:
- Check that photos contain GPS EXIF data
- Verify file extensions are in `image_extensions` list
- Check exclusions in config
- Review logs for specific error messages

---

**Issue**: Folders created but photos not moved

**Solution**:
- Check disk space availability
- Verify write permissions
- Review logs for specific errors
- Check if `operation: copy` is set (photos won't be moved)

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Source directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"No EXIF data"**: Photo doesn't contain EXIF metadata
- **"No GPS data"**: Photo doesn't contain GPS coordinates in EXIF data
- **"Error reading EXIF"**: Photo may be corrupted or unsupported format

## Use Cases

1. **Travel Photo Organization**: Organize vacation photos by location
2. **Photography Portfolio**: Group photos by shooting location
3. **Event Documentation**: Organize event photos by venue location
4. **Location-Based Cataloging**: Create a geographic catalog of photos
5. **Backup Organization**: Organize photo backups by location

## Tips for Best Results

1. **Enable Location Services**: Ensure GPS is enabled when taking photos
2. **Preserve EXIF Data**: Avoid photo editing that strips EXIF data
3. **Use Copy Mode First**: Test with `operation: copy` before moving
4. **Review Logs**: Check logs after processing to identify any issues
5. **Backup First**: Always backup photos before organizing
6. **Test with Small Set**: Process a small subset first to verify settings
7. **Reverse Geocoding**: Use sparingly for large collections due to rate limits

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov pytest-mock`
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
