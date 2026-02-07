# Image Resizer

A command-line tool for resizing images to specified dimensions or percentages while maintaining aspect ratios. Supports batch processing, multiple resampling algorithms, format conversion, and web optimization features.

## Project Description

Image Resizer solves the problem of creating web-optimized versions of images by providing an efficient way to resize images while preserving aspect ratios. It helps users batch resize images for web use, create thumbnails, or optimize images for different display sizes without manual editing.

**Target Audience**: Web developers, content creators, and photographers who need to resize images for web optimization, thumbnails, or responsive design requirements.

## Features

- **Flexible Resizing**: Resize by width, height, both dimensions, or percentage
- **Aspect Ratio Preservation**: Automatically maintains original aspect ratios
- **Batch Processing**: Resize multiple images at once
- **Recursive Processing**: Process directories and subdirectories
- **Format Conversion**: Convert to different formats during resize
- **Quality Control**: Adjustable quality settings for JPEG and WEBP
- **Resampling Algorithms**: Choose from LANCZOS, BILINEAR, BICUBIC, or NEAREST
- **Metadata Preservation**: Optionally preserve EXIF metadata
- **Flexible Output**: Save to custom directory or next to source files
- **Comprehensive Logging**: Detailed logs of all resizing operations
- **Cross-platform**: Works on Windows, macOS, and Linux

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/image-resizer
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
resampling: LANCZOS  # Best quality resampling
output_format: null  # null = same as input
jpeg_quality: 90
webp_quality: 90
preserve_metadata: true
```

## Usage

### Basic Usage

Resize a single image by width:

```bash
python src/main.py image.jpg -w 800
```

Resize by height:

```bash
python src/main.py image.jpg -H 600
```

Resize by percentage:

```bash
python src/main.py image.jpg -p 50
```

Resize to specific dimensions:

```bash
python src/main.py image.jpg -s 800x600
```

### Command-Line Options

```bash
# Resize with custom output directory
python src/main.py image.jpg -w 800 -o /path/to/output

# Process directory recursively
python src/main.py /path/to/images -w 1200 -r

# Resize with format conversion
python src/main.py image.png -w 800 --format jpg

# Use different resampling algorithm
python src/main.py image.jpg -w 800 --resampling BILINEAR

# Set custom quality for JPEG
python src/main.py image.png -w 800 --format jpg --quality-jpeg 85

# Disable metadata preservation
python src/main.py image.jpg -w 800 --no-metadata

# Custom suffix for output files
python src/main.py image.jpg -w 800 --suffix _thumb

# Use custom configuration file
python src/main.py image.jpg -w 800 -c /path/to/config.yaml
```

### Common Use Cases

**Create web-optimized images (50% size)**:
```bash
python src/main.py photo.jpg -p 50 --format webp
```

**Batch resize to 1200px width**:
```bash
python src/main.py /path/to/photos -w 1200
```

**Create thumbnails (200px width)**:
```bash
python src/main.py /photos -w 200 --suffix _thumb -o /thumbnails
```

**Resize and convert to JPEG**:
```bash
python src/main.py image.png -s 1920x1080 --format jpg --quality-jpeg 90
```

**Recursive resize with custom output**:
```bash
python src/main.py /images -p 75 -r -o /resized
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for default settings:

- `output_dir`: Default output directory (null = same as input)
- `resampling`: Default resampling algorithm (LANCZOS, BILINEAR, BICUBIC, NEAREST)
- `output_format`: Default output format (null = same as input)
- `jpeg_quality`: Default JPEG quality (1-100)
- `webp_quality`: Default WEBP quality (0-100)
- `preserve_metadata`: Whether to preserve EXIF metadata by default
- `input_formats`: Supported input formats
- `output_formats`: Supported output formats
- `logging`: Logging configuration

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `OUTPUT_DIR`: Custom default output directory
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Resizing Methods

### By Width
Resizes image to specified width, calculating height to maintain aspect ratio:
```bash
python src/main.py image.jpg -w 800
```

### By Height
Resizes image to specified height, calculating width to maintain aspect ratio:
```bash
python src/main.py image.jpg -H 600
```

### By Both Dimensions
Resizes image to fit within specified dimensions while maintaining aspect ratio:
```bash
python src/main.py image.jpg -s 800x600
```

### By Percentage
Resizes image to specified percentage of original size:
```bash
python src/main.py image.jpg -p 50  # 50% of original size
```

## Resampling Algorithms

- **LANCZOS** (default): Highest quality, slower. Best for photos and high-quality images.
- **BILINEAR**: Good quality, faster. Suitable for most use cases.
- **BICUBIC**: Good quality, moderate speed. Alternative to bilinear.
- **NEAREST**: Fastest, lowest quality. Use only for pixel art or when speed is critical.

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

## Project Structure

```
image-resizer/
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
│   └── resized/            # Resized images (if using default output)
└── logs/
    └── image_resizer.log   # Application logs
```

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
- Dimension calculation (width, height, percentage, both dimensions)
- Image resizing with different methods
- Batch processing
- Format conversion
- Output path generation
- File discovery (recursive and non-recursive)
- Quality validation
- RGBA to RGB conversion for JPEG

## Troubleshooting

### Resizing Fails

**Error: "Must specify width, height, size, or percentage"**
- Provide at least one resize parameter: `-w`, `-H`, `-s`, or `-p`

**Error: "Cannot identify image file"**
- Input file may be corrupted or not a valid image
- Check file extension matches actual format
- Try opening the file in an image viewer first

**Error: "Permission denied"**
- Check write permissions on output directory
- Ensure sufficient disk space
- Verify file is not open in another application

### Quality Issues

**Resized images look blurry**
- Use LANCZOS resampling algorithm (default)
- Ensure source image is high quality
- Avoid excessive downscaling (e.g., 10% of original)

**File sizes too large**
- Use lower quality settings for JPEG/WEBP
- Consider using WEBP format for better compression
- Use appropriate dimensions (don't oversize)

### Aspect Ratio Issues

**Images appear stretched**
- The tool automatically maintains aspect ratio
- If both width and height are specified, it uses the limiting dimension
- Check source image aspect ratio matches expectations

## Performance Considerations

- **Batch Processing**: Processes images sequentially to avoid memory issues
- **Large Images**: May take longer to resize; consider resizing in stages
- **Recursive Processing**: Can be slow on large directory trees
- **Resampling Algorithm**: LANCZOS is highest quality but slowest
- **Format Conversion**: Additional processing time for format conversion

## Web Optimization Tips

1. **Use appropriate dimensions**: Resize to actual display size, not larger
2. **Choose right format**: WEBP for modern browsers, JPEG for photos, PNG for transparency
3. **Optimize quality**: Use quality 80-90 for web (good balance of size and quality)
4. **Batch process**: Use recursive mode to process entire directories
5. **Create thumbnails**: Use `-w 200 --suffix _thumb` for thumbnail generation

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
