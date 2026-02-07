# Image Scraper

A Python automation script that scrapes public domain images from websites and downloads them to a local directory, organizing by category or date. Useful for collecting public domain images, building image datasets, and archiving web content.

## Features

- **Web scraping**: Extracts image URLs from web pages using HTML parsing
- **Image download**: Downloads images with proper error handling
- **Organization**: Organizes images by date or category
- **Rate limiting**: Configurable delay between requests to be respectful to servers
- **Duplicate detection**: Skips already downloaded images
- **Error handling**: Graceful handling of network errors and invalid files
- **Comprehensive logging**: Detailed logs for all operations
- **Configuration support**: YAML configuration file or command-line arguments

## Important Legal and Ethical Considerations

**Before using this script, please ensure:**

1. **Respect robots.txt**: Check and respect the website's robots.txt file
2. **Terms of Service**: Review and comply with the website's Terms of Service
3. **Copyright**: Only download images that are in the public domain or for which you have permission
4. **Rate Limiting**: Use appropriate rate limits to avoid overloading servers
5. **Attribution**: Respect any attribution requirements for downloaded images
6. **Legal Compliance**: Ensure your use complies with applicable laws and regulations

This script is intended for educational purposes and for scraping public domain or freely available content. Always verify the legal status of images before downloading.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd image-scraper
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
- **requests**: For HTTP requests
- **beautifulsoup4**: For HTML parsing
- **lxml**: XML/HTML parser for BeautifulSoup
- **PyYAML**: For configuration file parsing

## Configuration

### Configuration File (config.yaml)

The script supports configuration via a YAML file:

```yaml
output_directory: "./downloads"
organize_by: "date"  # Options: date, category
max_images: null
rate_limit: 1.0
timeout: 10
urls:
  - "https://example.com/gallery"
```

## Usage

### Basic Usage

Scrape images from a single page:

```bash
python src/main.py https://example.com/gallery --output ./downloads
```

### Multiple URLs

Scrape images from multiple pages:

```bash
python src/main.py https://site1.com/gallery https://site2.com/images --output ./downloads
```

### Organize by Category

Organize downloaded images by category:

```bash
python src/main.py https://example.com/gallery --output ./downloads --organize-by category
```

### Limit Number of Images

Download maximum number of images:

```bash
python src/main.py https://example.com/gallery --output ./downloads --max-images 50
```

### Custom Rate Limiting

Set delay between requests:

```bash
python src/main.py https://example.com/gallery --output ./downloads --rate-limit 2.0
```

### Use Configuration File

```bash
python src/main.py --config config.yaml
```

### Command-Line Arguments

- `urls`: URLs of web pages to scrape (required, one or more)
- `--output`: Output directory for downloaded images (required)
- `--organize-by`: Organization method - date or category (default: date)
- `--max-images`: Maximum number of images to download
- `--rate-limit`: Delay between requests in seconds (default: 1.0)
- `--user-agent`: Custom user agent string
- `--timeout`: Request timeout in seconds (default: 10)
- `--config`: Path to configuration file (YAML)

## Project Structure

```
image-scraper/
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

- `src/main.py`: Core implementation with ImageScraper class and CLI interface
- `config.yaml`: Default configuration file with scraping settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

## Organization Methods

### By Date

Images are organized into folders by download date:

```
downloads/
├── 2024-01-15/
│   ├── image1.jpg
│   └── image2.png
└── 2024-01-16/
    └── image3.jpg
```

### By Category

Images are organized into folders by detected category:

```
downloads/
├── nature/
│   ├── landscape1.jpg
│   └── forest1.png
├── portraits/
│   └── person1.jpg
├── animals/
│   └── cat1.jpg
└── other/
    └── image1.jpg
```

Categories are detected based on URL keywords:
- nature, landscape, outdoor
- portraits, person, people
- animal, pet, wildlife
- food, meal, cooking
- architecture, building, city
- art, painting, drawing
- other (default)

## Supported Image Formats

The script recognizes and downloads:
- JPEG/JPG
- PNG
- GIF
- BMP
- WebP
- SVG
- ICO

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
- URL validation
- Image URL detection
- File organization
- Error handling
- Configuration file loading

## Troubleshooting

### Common Issues

**Issue: "requests and beautifulsoup4 are required"**

Solution: Install required dependencies: `pip install requests beautifulsoup4 lxml`

**Issue: "Connection timeout"**

Solution: Increase timeout value or check network connectivity. Some websites may block automated requests.

**Issue: "No images found"**

Solution: Verify that:
- The URL is accessible
- The page contains image tags
- Images are not loaded dynamically via JavaScript (this script doesn't execute JavaScript)

**Issue: "Permission denied"**

Solution: Ensure you have write permissions for the output directory.

**Issue: "Rate limiting / blocking"**

Solution: Increase the rate limit delay. Some websites may block requests that are too frequent.

### Error Messages

All errors are logged to both the console and `logs/scraper.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `scraper.log`: Main log file with all operations and errors

## Best Practices

1. **Respect rate limits**: Use appropriate delays between requests (1.0+ seconds recommended)
2. **Check robots.txt**: Verify the website allows scraping
3. **Verify copyright**: Only download public domain or permitted images
4. **Use appropriate user agent**: Identify your scraper properly
5. **Handle errors gracefully**: The script includes error handling, but monitor logs
6. **Respect server resources**: Don't overload servers with too many requests

## Limitations

- **JavaScript-rendered content**: The script cannot extract images loaded dynamically via JavaScript
- **Authentication**: The script does not handle login-protected pages
- **CAPTCHA**: The script cannot solve CAPTCHAs
- **Complex sites**: Some websites may require special handling

## Security Considerations

- The script downloads files from external sources - scan downloaded files for malware
- Be cautious when downloading from untrusted sources
- Validate file types and sizes before processing
- Use appropriate rate limiting to avoid being blocked

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

This project is provided as-is for educational and automation purposes. Users are responsible for ensuring their use complies with applicable laws and website terms of service.
