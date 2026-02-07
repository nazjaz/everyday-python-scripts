# Image Converter

A command-line tool for converting images between formats (JPG, PNG, WEBP, BMP, TIFF) with options to preserve metadata and adjust quality settings. Supports batch processing, recursive directory scanning, and comprehensive logging.

## Project Description

Image Converter solves the problem of converting images between different formats efficiently while maintaining quality and optionally preserving EXIF metadata. It helps users batch convert images for web optimization, format standardization, or compatibility requirements without losing important metadata or image quality.

**Target Audience**: Developers, photographers, and content creators who need to convert images between formats while preserving metadata and controlling quality settings.

## Features

- **Format Conversion**: Convert between JPG, PNG, WEBP, BMP, and TIFF formats
- **Metadata Preservation**: Optionally preserve EXIF metadata during conversion
- **Quality Control**: Adjustable quality settings for JPEG and WEBP formats
- **Batch Processing**: Convert multiple images at once
- **Recursive Processing**: Process directories and subdirectories
- **Flexible Output**: Save to custom directory or next to source files
- **Comprehensive Logging**: Detailed logs of all conversion operations
- **Error Handling**: Graceful handling of unsupported formats and corrupted files
- **Cross-platform**: Works on Windows, macOS, and Linux

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/image-converter
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

### Step 4: Configure Settings (Optional)

Edit `config.yaml` if you want to customize default settings:

```yaml
output_dir: null  # null = save next to source files
quality:
  jpeg: 95
  webp: 90
preserve_metadata: true
```

## Usage

### Basic Usage

Convert a single image:

```bash
python src/main.py image.jpg png
```

Convert all images in a directory:

```bash
python src/main.py /path/to/images png
```

### Command-Line Options

```bash
# Convert with custom output directory
python src/main.py input.jpg png -o /path/to/output

# Process directory recursively
python src/main.py /path/to/images webp -r

# Disable metadata preservation
python src/main.py image.jpg png --no-metadata

# Set custom quality for JPEG
python src/main.py image.png jpg --quality-jpeg 85

# Set custom quality for WEBP
python src/main.py image.jpg webp --quality-webp 95

# Use custom configuration file
python src/main.py image.jpg png -c /path/to/config.yaml
```

### Common Use Cases

**Convert JPG to PNG (preserve quality)**:
```bash
python src/main.py photo.jpg png
```

**Batch convert PNG to WEBP (web optimization)**:
```bash
python src/main.py /path/to/pngs webp --quality-webp 90
```

**Convert with metadata removal**:
```bash
python src/main.py image.jpg png --no-metadata
```

**Recursive conversion with custom output**:
```bash
python src/main.py /photos jpg -r -o /converted
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for default settings:

- `output_dir`: Default output directory (null = same as input)
- `quality`: Default quality settings for JPEG and WEBP
- `preserve_metadata`: Whether to preserve EXIF metadata by default
- `input_formats`: Supported input formats
- `output_formats`: Supported output formats
- `logging`: Logging configuration

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `OUTPUT_DIR`: Custom default output directory
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Project Structure

```
image-converter/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Application configuration
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── data/
│   └── converted/          # Converted images (if using default output)
└── logs/
    └── image_converter.log  # Application logs
```

## Format Support

### Input Formats
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- WEBP (`.webp`)
- BMP (`.bmp`)
- TIFF (`.tiff`, `.tif`)
- GIF (`.gif`)

### Output Formats
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- WEBP (`.webp`)
- BMP (`.bmp`)
- TIFF (`.tiff`)

### Quality Settings

- **JPEG**: Quality range 1-100 (default: 95)
  - Higher values = better quality, larger file size
  - Recommended: 85-95 for photos, 90-100 for high-quality images

- **WEBP**: Quality range 0-100 (default: 90)
  - Higher values = better quality, larger file size
  - Recommended: 80-95 for web use

### Metadata Preservation

EXIF metadata is preserved by default for formats that support it:
- JPEG: Full EXIF support
- TIFF: Full EXIF support
- PNG: Limited metadata support
- WEBP: Limited metadata support

Use `--no-metadata` flag to disable metadata preservation.

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Test Coverage

The test suite covers:
- Image format conversion (PNG to JPG, JPG to PNG, PNG to WEBP)
- Batch processing
- Output path generation
- Quality validation
- File discovery (recursive and non-recursive)
- RGBA to RGB conversion for JPEG
- Error handling for unsupported formats

## Troubleshooting

### Conversion Fails

**Error: "Unsupported output format"**
- Check that the output format is one of: jpg, jpeg, png, webp, bmp, tiff
- Verify the format is listed in `config.yaml` output_formats

**Error: "Cannot identify image file"**
- Input file may be corrupted or not a valid image
- Check file extension matches actual format
- Try opening the file in an image viewer first

**Error: "Permission denied"**
- Check write permissions on output directory
- Ensure sufficient disk space
- Verify file is not open in another application

### Quality Issues

**Converted images look poor quality**
- Increase quality setting (--quality-jpeg or --quality-webp)
- For JPEG, use quality 90-100 for best results
- For WEBP, use quality 85-95 for best results

**File sizes too large**
- Decrease quality setting
- For JPEG, quality 80-90 is usually sufficient
- For WEBP, quality 75-85 is usually sufficient

### Metadata Issues

**Metadata not preserved**
- Some formats (PNG, WEBP) have limited EXIF support
- Use JPEG or TIFF for full metadata preservation
- Check source image actually contains EXIF data

## Performance Considerations

- **Batch Processing**: Processes images sequentially to avoid memory issues
- **Large Images**: May take longer to convert; consider resizing first
- **Recursive Processing**: Can be slow on large directory trees
- **Quality Settings**: Higher quality = slower conversion and larger files

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guide
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with conventional commit format
7. Push and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

## License

This project is part of the everyday-python-scripts collection. See the main repository for license information.
