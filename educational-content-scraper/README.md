# Educational Content Scraper

A Python automation tool for scraping public domain educational content from various sources and creating a local learning resource library organized by subject and difficulty level. This script collects educational materials, categorizes them automatically, and organizes them into a structured directory system.

## Features

- Scrapes content from multiple public domain sources (Project Gutenberg, OpenStax, custom sources)
- Automatic subject categorization (Mathematics, Science, Literature, History, Philosophy, etc.)
- Automatic difficulty level detection (Beginner, Intermediate, Advanced)
- Organizes content into library structure: library/subject/difficulty/
- Duplicate detection using content hashing
- Rate limiting and respectful scraping with configurable delays
- Retry logic with exponential backoff for failed requests
- Comprehensive logging with rotation
- Dry-run mode to preview scraping without saving
- Configurable source limits and filtering
- Sanitizes filenames for filesystem compatibility

## Prerequisites

- Python 3.8 or higher
- Internet connection for scraping
- Write permissions for library directory
- Sufficient disk space for downloaded content

## Installation

1. Clone or navigate to the project directory:
```bash
cd educational-content-scraper
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
   - Enable/disable sources
   - Set scraping limits
   - Configure subject keywords
   - Adjust request delays

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **sources.project_gutenberg.enabled**: Enable Project Gutenberg scraping (default: true)
- **sources.project_gutenberg.limit**: Maximum items to scrape (default: 10)
- **sources.openstax.enabled**: Enable OpenStax scraping (default: true)
- **sources.openstax.limit**: Maximum items to scrape (default: 10)
- **sources.custom_sources**: List of custom source configurations
- **organization.library_directory**: Where to save scraped content (default: ./library)
- **organization.subject_keywords**: Keywords for subject categorization
- **scraping.request_delay_seconds**: Delay between requests (default: 2)
- **scraping.max_content_size**: Maximum content size to save (default: 50000)

### Subject Categories

Content is automatically categorized into subjects based on keywords:
- Mathematics
- Science
- Literature
- History
- Philosophy
- Language
- Computer Science
- Art
- General (default)

### Difficulty Levels

Content is automatically assigned difficulty levels:
- **Beginner**: Introduction, basics, getting started, 101, elementary
- **Intermediate**: Default for content without clear indicators
- **Advanced**: Advanced, expert, master, graduate, research, thesis

### Environment Variables

Optional environment variables can override configuration:

- `LIBRARY_DIRECTORY`: Override library directory path

## Usage

### Basic Usage

Scrape content from enabled sources:
```bash
python src/main.py
```

### Dry Run

Preview what would be scraped without saving:
```bash
python src/main.py --dry-run
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config /path/to/custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Perform a dry run without saving content
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
educational-content-scraper/
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
├── logs/
│   └── .gitkeep             # Logs directory placeholder
└── library/                 # Generated library directory (created at runtime)
    └── [subject]/
        └── [difficulty]/
            └── [content files].txt
```

## Library Organization

Content is organized in the following structure:

```
library/
├── mathematics/
│   ├── beginner/
│   │   ├── Introduction_to_Algebra.txt
│   │   └── .hashes.txt
│   ├── intermediate/
│   └── advanced/
├── science/
│   ├── beginner/
│   ├── intermediate/
│   └── advanced/
└── [other subjects]/
```

Each content file includes:
- Title
- Source
- URL
- Subject
- Difficulty
- Scrape timestamp
- Content text

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

1. **Source Configuration**: The script reads configured sources from `config.yaml` and determines which sources to scrape.

2. **Content Scraping**: For each enabled source:
   - Makes HTTP requests with rate limiting
   - Parses HTML content using BeautifulSoup
   - Extracts titles and content text
   - Handles errors with retry logic

3. **Categorization**: For each scraped content:
   - Analyzes title and content for subject keywords
   - Determines difficulty level based on keywords
   - Assigns to appropriate category

4. **Duplicate Detection**: 
   - Calculates MD5 hash of content
   - Checks against existing hashes
   - Skips duplicate content

5. **Organization**: 
   - Creates directory structure: library/subject/difficulty/
   - Sanitizes filenames for filesystem compatibility
   - Saves content with metadata

6. **Logging**: All operations are logged with timestamps and context.

## Troubleshooting

### Network Errors

If you encounter network errors:
- Check your internet connection
- Verify source URLs are accessible
- Increase request delay in configuration
- Some sources may have rate limiting

### Permission Errors

If you encounter permission errors:
- Ensure you have write access to the library directory
- Check file and directory permissions
- Verify sufficient disk space

### Content Not Categorized Correctly

If content is not categorized correctly:
- Review subject keywords in `config.yaml`
- Add custom keywords for your use case
- Check logs for categorization details
- Content may be categorized as "general" if no keywords match

### Scraping Fails

If scraping fails:
- Verify source websites are accessible
- Check that source configurations are correct
- Review logs for specific error messages
- Some sources may have changed their structure
- Try with `--verbose` flag for detailed information

### Duplicate Detection Issues

If duplicates are not detected:
- Hashes are stored per difficulty level
- Same content in different difficulty levels will be saved separately
- Check `.hashes.txt` files in each difficulty directory

## Ethical Considerations

- **Respect robots.txt**: Always check and respect robots.txt files
- **Rate Limiting**: Default delay is 2 seconds between requests
- **Public Domain Only**: Only scrape public domain or openly licensed content
- **Terms of Service**: Review and comply with source website terms of service
- **Attribution**: Content files include source URLs for attribution
- **Fair Use**: Use scraped content in accordance with copyright laws

## Security Considerations

- The script only reads publicly available content
- No authentication or credentials are required for public domain sources
- File paths are sanitized to prevent directory traversal
- Content size is limited to prevent excessive disk usage
- User-Agent header identifies the scraper

## Performance Considerations

- Processing time depends on number of sources and limits
- Rate limiting adds delays between requests
- Large content files may take time to download
- Consider running during off-peak hours for large scraping jobs

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages
7. Respect source website terms of service

## License

This project is provided as-is for automation purposes. Ensure you comply with the terms of service of any sources you scrape.

## Disclaimer

This tool is for educational purposes. Users are responsible for:
- Complying with source website terms of service
- Respecting copyright and licensing
- Using scraped content appropriately
- Following robots.txt and rate limiting guidelines
