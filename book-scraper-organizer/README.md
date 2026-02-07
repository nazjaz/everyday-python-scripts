# Book Scraper and Organizer

A Python automation script that scrapes public domain books from online libraries and organizes them by author, genre, or publication date in a local database. Useful for building personal libraries, collecting public domain literature, and organizing digital book collections.

## Features

- **Book scraping**: Extracts book metadata and downloads from public domain libraries
- **Database storage**: Stores book information in SQLite database
- **Organization**: Organizes downloaded books by author, genre, or publication date
- **Metadata extraction**: Extracts title, author, publication date, genre, and other metadata
- **Duplicate detection**: Prevents downloading duplicate books
- **Query functionality**: Query books from database by author, genre, or date
- **Rate limiting**: Configurable delay between requests
- **Error handling**: Graceful handling of network errors and missing data

## Important Legal and Ethical Considerations

**Before using this script, please ensure:**

1. **Respect Terms of Service**: Review and comply with the website's Terms of Service
2. **Public Domain Only**: Only scrape books that are in the public domain
3. **Rate Limiting**: Use appropriate rate limits to avoid overloading servers
4. **Attribution**: Respect any attribution requirements for downloaded books
5. **Legal Compliance**: Ensure your use complies with applicable laws and regulations

This script is intended for educational purposes and for scraping public domain or freely available content. Always verify the legal status of books before downloading.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd book-scraper-organizer
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
database: "./books.db"
output_directory: "./books"
organize_by: "author"  # Options: author, genre, date
rate_limit: 1.0
urls:
  - "https://www.gutenberg.org/ebooks/1"
```

## Usage

### Basic Usage

Scrape books from URLs:

```bash
python src/main.py https://www.gutenberg.org/ebooks/1 --output ./books
```

### Organize by Author

Organize downloaded books by author:

```bash
python src/main.py https://www.gutenberg.org/ebooks/1 \
  --output ./books \
  --organize-by author
```

### Organize by Genre

Organize downloaded books by genre:

```bash
python src/main.py https://www.gutenberg.org/ebooks/1 \
  --output ./books \
  --organize-by genre
```

### Organize by Publication Date

Organize downloaded books by publication date:

```bash
python src/main.py https://www.gutenberg.org/ebooks/1 \
  --output ./books \
  --organize-by date
```

### Query Database

Query books from database:

```bash
python src/main.py --query "Shakespeare" --query-type author --database books.db
```

### Use Configuration File

```bash
python src/main.py --config config.yaml
```

### Command-Line Arguments

- `urls`: URLs of book pages to scrape (required, one or more)
- `--database`: Path to SQLite database file (default: books.db)
- `--output`: Output directory for downloaded books (required)
- `--organize-by`: Organization method - author, genre, or date (default: author)
- `--rate-limit`: Delay between requests in seconds (default: 1.0)
- `--query`: Query books from database (author, genre, or date)
- `--query-type`: Type of query filter (author, genre, or date)
- `--config`: Path to configuration file (YAML)

## Project Structure

```
book-scraper-organizer/
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

- `src/main.py`: Core implementation with BookDatabase and BookScraper classes
- `config.yaml`: Default configuration file with scraping settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)
- `books.db`: SQLite database file (created automatically)

## Organization Methods

### By Author

Books are organized into folders by author name:

```
books/
├── William Shakespeare/
│   ├── Hamlet.txt
│   └── Romeo and Juliet.txt
└── Jane Austen/
    └── Pride and Prejudice.txt
```

### By Genre

Books are organized into folders by genre:

```
books/
├── Fiction/
│   └── The Great Gatsby.txt
└── Poetry/
    └── The Raven.txt
```

### By Publication Date

Books are organized into folders by publication date:

```
books/
├── 1925/
│   └── The Great Gatsby.txt
└── 1845/
    └── The Raven.txt
```

## Database Schema

The SQLite database stores the following information:

- **id**: Unique identifier
- **title**: Book title
- **author**: Author name
- **genre**: Book genre
- **publication_date**: Publication year
- **isbn**: ISBN number (if available)
- **language**: Book language
- **file_path**: Local file path
- **file_url**: Original download URL
- **download_date**: Date when book was downloaded
- **file_size**: File size in bytes
- **description**: Book description (if available)

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
- Database operations
- Metadata extraction
- File organization
- Book downloading
- Error handling

## Troubleshooting

### Common Issues

**Issue: "requests and beautifulsoup4 are required"**

Solution: Install required dependencies: `pip install requests beautifulsoup4 lxml`

**Issue: "Connection timeout"**

Solution: Increase timeout value or check network connectivity. Some websites may block automated requests.

**Issue: "No download link found"**

Solution: The script may not be able to find download links on all websites. Different libraries have different page structures.

**Issue: "Permission denied"**

Solution: Ensure you have write permissions for the output directory and database file location.

**Issue: "Book already exists"**

Solution: The script skips books that already exist in the database. This is expected behavior to prevent duplicates.

### Error Messages

All errors are logged to both the console and `logs/scraper.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `scraper.log`: Main log file with all operations and errors

## Best Practices

1. **Respect rate limits**: Use appropriate delays between requests (1.0+ seconds recommended)
2. **Check Terms of Service**: Verify the website allows scraping
3. **Verify public domain status**: Only download books that are in the public domain
4. **Use appropriate user agent**: Identify your scraper properly
5. **Handle errors gracefully**: Monitor logs for issues
6. **Respect server resources**: Don't overload servers with too many requests

## Limitations

- **Website-specific**: Different libraries have different page structures; may need customization
- **Metadata extraction**: May not extract all metadata fields from all websites
- **Download links**: Some websites may require special handling for download links
- **Authentication**: The script does not handle login-protected pages

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
