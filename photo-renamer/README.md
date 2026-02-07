# Photo Renamer

Automatically rename photo files using their EXIF date taken metadata. Formats filenames as `YYYY-MM-DD_HH-MM-SS_original-name` with sequential numbering for photos with the same timestamp.

## Project Description

Photo Renamer solves the problem of organizing photo collections by renaming files based on when they were actually taken (from EXIF data) rather than when they were downloaded or modified. This creates a consistent, chronological naming scheme that makes it easy to find and organize photos.

**Target Audience**: Photographers, users with large photo collections, and anyone who wants to organize photos by their actual capture date.

## Features

- Automatic EXIF date extraction from photo metadata
- Filename format: `YYYY-MM-DD_HH-MM-SS_original-name`
- Sequential numbering for photos with identical timestamps (e.g., `001`, `002`, `003`)
- Support for multiple RAW and JPEG formats
- Fallback to file modification date if EXIF data unavailable
- Dry run mode to preview changes before renaming
- Optional backup creation before renaming
- Preserves original file extensions and timestamps
- Comprehensive logging of all operations

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Photos with EXIF metadata (most digital cameras and smartphones include this)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/photo-renamer
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

2. Edit `config.yaml` to set your source directory:
   ```yaml
   source_directory: ~/Pictures
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory containing photos to rename
- **supported_formats**: List of image file extensions to process
- **naming**: Filename format and date/time format strings
- **exif_date_fields**: Priority order of EXIF date fields to check
- **sequential_numbering**: Settings for handling duplicate timestamps
- **fallback**: Behavior when EXIF date is not available
- **operations**: Dry run, backup, and timestamp preservation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory path
- `DRY_RUN`: Enable dry run mode (`true`/`false`)
- `CREATE_BACKUP`: Enable backup creation (`true`/`false`)

### Example Configuration

```yaml
source_directory: ~/Pictures

naming:
  date_format: "%Y-%m-%d"  # YYYY-MM-DD
  time_format: "%H-%M-%S"  # HH-MM-SS

sequential_numbering:
  enabled: true
  start_number: 1
  padding: 3  # 001, 002, 003

fallback:
  use_file_modification_date: true
  skip_if_no_date: false
  prefix: "NO_DATE_"
```

## Usage

### Basic Usage

Rename photos with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Preview changes without renaming (dry run)
python src/main.py --dry-run

# Combine options
python src/main.py -c config.yaml --dry-run
```

### Common Use Cases

1. **Rename Photos in Directory**:
   ```bash
   python src/main.py
   ```

2. **Preview Renaming** (dry run):
   ```bash
   python src/main.py --dry-run
   ```

3. **Rename with Backup**:
   - Set `operations.create_backup: true` in config.yaml
   - Or set environment variable: `export CREATE_BACKUP=true`

4. **Handle Photos Without EXIF**:
   - Configure fallback behavior in `config.yaml`
   - Options: use file modification date, skip file, or add prefix

5. **Custom Date Format**:
   - Edit `naming.date_format` and `naming.time_format` in config.yaml
   - Use Python datetime format codes

## Project Structure

```
photo-renamer/
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
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core EXIF reading, date parsing, and file renaming logic
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/photo_renamer.log**: Application log file with rotation

## Filename Format

Photos are renamed using the format: `YYYY-MM-DD_HH-MM-SS_original-name.ext`

**Examples**:
- `IMG_1234.jpg` → `2024-02-07_14-30-45_IMG_1234.jpg`
- `DSC_5678.jpg` → `2024-02-07_14-30-45_DSC_5678.jpg`

**With Sequential Numbering** (for same timestamp):
- `photo1.jpg` → `2024-02-07_14-30-45_001_photo1.jpg`
- `photo2.jpg` → `2024-02-07_14-30-45_002_photo2.jpg`
- `photo3.jpg` → `2024-02-07_14-30-45_003_photo3.jpg`

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
- EXIF date parsing
- Filename generation
- Sequential numbering logic
- Date extraction from EXIF
- Fallback date handling
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'PIL'`

**Solution**: Install dependencies: `pip install -r requirements.txt`

---

**Issue**: Photos not being renamed

**Solution**: 
- Verify photos have EXIF data (check with image viewer or EXIF tool)
- Check that file extensions are in `supported_formats` in config.yaml
- Ensure source directory path is correct

---

**Issue**: "No date available" for all photos

**Solution**: 
- Photos may not have EXIF data (common with screenshots or edited images)
- Enable `fallback.use_file_modification_date: true` in config.yaml
- Or check if photos were stripped of EXIF metadata during editing

---

**Issue**: Files with same timestamp not getting sequential numbers

**Solution**: 
- Verify `sequential_numbering.enabled: true` in config.yaml
- Check that padding is set appropriately (e.g., 3 for 001, 002, 003)

---

**Issue**: Permission denied when renaming

**Solution**: 
- Check file permissions in source directory
- Ensure you have write access to the directory
- On Linux/Mac, you may need to adjust directory permissions

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Source directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Error reading EXIF"**: Photo may be corrupted or in unsupported format
- **"Target file already exists"**: Another file with the same name already exists (check for duplicates)

## Supported Formats

The script supports various image formats that can contain EXIF data:

- **JPEG**: `.jpg`, `.jpeg`
- **TIFF**: `.tiff`, `.tif`
- **RAW Formats**: `.nef` (Nikon), `.cr2` (Canon), `.arw` (Sony), `.dng`, `.orf` (Olympus), `.rw2` (Panasonic), `.pef` (Pentax), `.sr2` (Sony), `.raf` (Fuji), `.3fr` (Hasselblad), `.fff` (Hasselblad), `.x3f` (Sigma)

## EXIF Date Field Priority

The script checks EXIF date fields in this order:

1. **DateTimeOriginal**: Date/time when original image was taken (preferred)
2. **DateTimeDigitized**: Date/time when image was digitized
3. **DateTime**: Date/time when image was last modified

If none are found, falls back to file modification date (if enabled).

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
