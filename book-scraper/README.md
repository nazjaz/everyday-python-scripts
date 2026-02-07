# Book Scraper

A Python automation tool that scrapes book information from library websites and maintains a personal reading list with progress tracking and notes functionality.

## Features

- Scrape book information from library websites (title, author, ISBN, pages, description, etc.)
- Maintain a personal reading list stored in JSON format
- Track reading progress (pages read, percentage complete)
- Manage reading status (to_read, reading, completed, abandoned)
- Add and manage notes for each book
- Filter and sort reading list by various criteria
- Comprehensive error handling and logging
- Configurable CSS selectors for different website structures
- Respectful web scraping with configurable delays

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection for web scraping

## Installation

1. Clone or navigate to the project directory:
```bash
cd book-scraper
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

## Configuration

### Configuration File

The tool uses a YAML configuration file (`config.yaml`) for settings. Key configuration sections:

- **data**: Data storage directory
- **scraping**: Web scraping settings (timeout, delay, headers, CSS selectors)
- **reading_list**: Reading list management settings
- **progress**: Progress tracking settings
- **logging**: Logging configuration

### CSS Selectors

The tool uses CSS selectors to extract book information from web pages. You may need to adjust these selectors based on the target website structure. The default selectors are generic and should work with many library websites, but for best results, inspect the target website and update the selectors in `config.yaml`.

Example selector configuration:
```yaml
selectors:
  title: "h1.book-title"
  author: ".book-author"
  isbn: ".isbn-number"
```

### Environment Variables

You can override configuration using environment variables:

- `DATA_DIRECTORY`: Directory for storing reading list data

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Scrape book information:**
```bash
python src/main.py --scrape "https://example-library.com/book/123"
```

**Scrape and add to reading list:**
```bash
python src/main.py --scrape "https://example-library.com/book/123" --add
```

**List all books in reading list:**
```bash
python src/main.py --list
```

**List books by status:**
```bash
python src/main.py --list --status reading
```

**Update reading progress:**
```bash
python src/main.py --update-progress BOOK_ID 150
```

**Add note to a book:**
```bash
python src/main.py --note BOOK_ID "Great character development in chapter 5"
```

**Delete a book:**
```bash
python src/main.py --delete BOOK_ID
```

### Reading Status

Books can have the following statuses:
- `to_read`: Book is in the list but not started
- `reading`: Currently reading the book
- `completed`: Finished reading the book
- `abandoned`: Stopped reading the book

### Progress Tracking

Progress can be updated in two ways:
1. **By pages read**: Specify the number of pages read
2. **By percentage**: Specify the percentage complete (0-100)

The tool automatically:
- Calculates percentage from pages read (if total pages known)
- Calculates pages read from percentage (if total pages known)
- Updates status based on progress (0% = to_read, 1-99% = reading, 100% = completed)

### Notes

Notes are timestamped and appended to existing notes. Each note entry includes the date and time when it was added.

## Project Structure

```
book-scraper/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── API.md
├── data/
│   └── reading_list.json
└── logs/
    └── .gitkeep
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file
- `data/reading_list.json`: Reading list data storage
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory

## Data Format

The reading list is stored as JSON with the following structure:

```json
{
  "book_id": {
    "title": "Book Title",
    "author": "Author Name",
    "isbn": "1234567890",
    "pages": 300,
    "status": "reading",
    "progress": {
      "pages_read": 150,
      "percentage": 50.0,
      "started_date": "2024-01-15T10:30:00",
      "completed_date": null
    },
    "notes": "2024-01-20 14:30: Interesting plot twist",
    "added_at": "2024-01-10T09:00:00",
    "updated_at": "2024-01-20T14:30:00"
  }
}
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_main.py::test_scrape_book
```

## Troubleshooting

### Common Issues

**Scraping fails or returns incomplete data:**
- Check if the website structure matches the CSS selectors in `config.yaml`
- Inspect the target webpage and update selectors accordingly
- Some websites may block automated requests (check User-Agent header)
- Verify the URL is accessible and the book page exists

**Reading list file errors:**
- Ensure the data directory is writable
- Check file permissions
- Verify JSON file is not corrupted (check logs for errors)

**Progress tracking issues:**
- Ensure book has page count set for automatic percentage calculation
- Verify book_id is correct (use --list to see all book IDs)
- Check that pages_read doesn't exceed total pages

**Network/timeout errors:**
- Increase timeout in `config.yaml` (scraping.timeout)
- Check internet connection
- Some websites may rate-limit requests (increase scraping.delay)

### Error Messages

The tool provides detailed error messages in logs. Check `logs/book_scraper.log` for:
- Scraping failures
- File access errors
- Data validation issues
- Network problems

### Website-Specific Configuration

Different library websites have different HTML structures. To configure for a specific website:

1. Open the book page in a web browser
2. Inspect the HTML structure (right-click > Inspect)
3. Identify CSS selectors for book information
4. Update `config.yaml` with the appropriate selectors

Example for a specific website:
```yaml
scraping:
  selectors:
    title: ".book-detail-title"
    author: ".book-detail-author-name"
    isbn: ".book-meta-isbn"
    pages: ".book-meta-pages"
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## Legal and Ethical Considerations

- Always respect website terms of service
- Use appropriate delays between requests
- Do not overload servers with excessive requests
- Some websites may require authentication or have API access
- Consider using official APIs when available instead of scraping
- Be aware of copyright and fair use policies

## License

This project is part of the everyday-python-scripts collection.
