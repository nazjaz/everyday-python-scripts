# Inspirational Quote Scraper

Scrape public domain quotes from websites, store them in a local database, and display daily inspirational quotes with desktop notifications. This tool helps you stay motivated by automatically collecting and presenting inspirational quotes on a daily basis.

## Project Description

Inspirational Quote Scraper solves the problem of finding and organizing inspirational quotes by automatically scraping public domain quotes from multiple websites, storing them in a local database, and displaying a new quote each day with desktop notifications.

**Target Audience**: Individuals seeking daily motivation, developers building quote-based applications, content creators, and anyone who wants automated access to inspirational quotes.

## Features

- **Web Scraping**: Scrape quotes from multiple public domain quote websites
- **Local Database Storage**: Store quotes in SQLite database for persistence
- **Daily Quote Display**: Automatically select and display a new quote each day
- **Desktop Notifications**: Cross-platform desktop notifications for daily quotes
- **Duplicate Detection**: Automatically skip duplicate quotes
- **Quote Categorization**: Organize quotes by category (inspirational, motivational, etc.)
- **Data Retention**: Automatic cleanup of old entries based on retention policy
- **Configurable Sources**: Define custom quote sources with CSS selectors
- **Rate Limiting**: Built-in delays between scraping requests to respect website policies

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for web scraping
- Desktop environment (for notifications)

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/inspirational-quote-scraper
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

1. Edit `config.yaml` to customize quote sources and settings:
   ```yaml
   sources:
     - name: "Your Quote Source"
       url: "https://example.com/quotes"
       category: "inspirational"
       selectors:
         quote: ".quote-class"
         text: ".quote-text"
         author: ".author-class"
   ```

2. Optionally create `.env` file for environment variables:
   ```bash
   cp .env.example .env
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **sources**: List of quote sources with URLs, categories, and CSS selectors
- **database**: SQLite database file path and table creation settings
- **scraping**: Timeout, user agent, delays, and quote length limits
- **display**: Settings for daily quote selection and rotation
- **notifications**: Desktop notification settings (title, timeout, message length)
- **logging**: Logging level, file path, and rotation settings
- **retention**: Data retention policy for old entries

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_FILE`: Override database file path
- `SCRAPING_TIMEOUT`: Override scraping timeout in seconds

### Example Configuration

```yaml
sources:
  - name: "BrainyQuote"
    url: "https://www.brainyquote.com/topics/inspirational-quotes"
    category: "inspirational"
    selectors:
      quote: ".b-qt"
      text: ".b-qt"
      author: ".bq-aut"

notifications:
  enabled: true
  title: "Daily Inspirational Quote"
  timeout: 10
  max_length: 200

display:
  recent_days_avoid: 30
```

## Usage

### Basic Usage

Scrape quotes and display daily quote:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Scrape quotes only
python src/main.py --scrape

# Display daily quote only
python src/main.py --display

# Display quote for specific date
python src/main.py --display --date 2024-02-07

# Combine options
python src/main.py -c config.yaml --scrape --display
```

### Common Use Cases

1. **Initial Setup - Scrape Quotes**:
   ```bash
   python src/main.py --scrape
   ```

2. **Display Daily Quote**:
   ```bash
   python src/main.py --display
   ```

3. **Scrape and Display**:
   ```bash
   python src/main.py
   ```

4. **Add Custom Quote Sources**:
   - Edit `sources` section in `config.yaml`
   - Add source name, URL, category, and CSS selectors
   - Use browser developer tools to find correct selectors

5. **Customize Notifications**:
   - Edit `notifications` section in `config.yaml`
   - Adjust title, timeout, and message length
   - Disable notifications by setting `enabled: false`

## Project Structure

```
inspirational-quote-scraper/
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
├── data/
│   └── quotes.db           # SQLite database (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    └── quote_scraper.log   # Application logs
```

### File Descriptions

- **src/main.py**: Core quote scraping, database operations, daily quote selection, and notification functionality
- **config.yaml**: YAML configuration file with quote sources and settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/quotes.db**: SQLite database storing all quotes and daily assignments
- **logs/quote_scraper.log**: Application log file with rotation

## Database Schema

The SQLite database contains two main tables:

### quotes
- `id`: Primary key
- `text`: Quote text
- `author`: Quote author (nullable)
- `source_url`: Source website URL
- `source_name`: Source website name
- `category`: Quote category
- `scraped_at`: Timestamp when scraped
- `displayed_at`: Last display timestamp
- `display_count`: Number of times displayed

### daily_quotes
- `id`: Primary key
- `quote_id`: Foreign key to quotes table
- `display_date`: Date when quote was displayed (unique)

## Quote Scraping

Quotes are scraped using CSS selectors configured for each source:

1. **HTML Fetching**: Downloads page content using requests library
2. **HTML Parsing**: Parses HTML using BeautifulSoup
3. **Quote Extraction**: Extracts quotes using configured CSS selectors
4. **Validation**: Validates quote length and format
5. **Storage**: Saves unique quotes to database

### CSS Selector Configuration

Each source requires three selectors:

- `quote`: Selector for the quote container element
- `text`: Selector for the quote text within the container
- `author`: Selector for the author name within the container

Example:
```yaml
selectors:
  quote: ".quote-container"
  text: ".quote-text"
  author: ".author-name"
```

## Daily Quote Selection

The daily quote selection algorithm:

1. **Check Existing**: Checks if a quote is already assigned for today
2. **Avoid Recent**: Selects quotes not displayed in the last N days (configurable)
3. **Random Selection**: Randomly selects from available quotes
4. **Fallback**: If no recent quotes available, selects any random quote
5. **Tracking**: Records daily assignment in database

## Desktop Notifications

Cross-platform desktop notifications are sent using the `plyer` library:

- **Windows**: Uses Windows notification API
- **macOS**: Uses macOS notification center
- **Linux**: Uses D-Bus notifications

Notifications include:
- Title: Configurable (default: "Daily Inspirational Quote")
- Message: Quote text (truncated if too long) and author
- Timeout: Configurable display duration

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
- Quote scraping from HTML
- Database operations
- Daily quote selection
- Duplicate detection
- Notification functionality
- Data cleanup

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'requests'`

**Solution**: Install dependencies: `pip install -r requirements.txt`

---

**Issue**: No quotes being scraped

**Solution**: 
- Verify quote source URLs are correct and accessible
- Check internet connection
- Verify CSS selectors are correct for the source website
- Check logs for parsing errors
- Some websites may block automated scraping

---

**Issue**: Desktop notifications not working

**Solution**: 
- Verify notification permissions are enabled in system settings
- On Linux, ensure D-Bus is running
- On macOS, check notification center settings
- Try disabling and re-enabling notifications in config.yaml

---

**Issue**: CSS selectors not finding quotes

**Solution**: 
- Use browser developer tools to inspect page structure
- Verify selectors match current website structure
- Websites may change their HTML structure over time
- Test selectors manually in browser console

---

**Issue**: Database locked errors

**Solution**: 
- Ensure only one instance of scraper is running
- Check database file permissions
- Close any database viewers that might have the file open

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"No quote sources configured"**: Add at least one quote source to `sources` in config.yaml
- **"Error fetching URL"**: Quote source URL may be invalid or inaccessible
- **"No quotes available"**: Run scraper with `--scrape` first to populate database
- **"Database error"**: Check database file permissions and disk space

## Quote Source Websites

Example public domain quote sources you can configure:

- **BrainyQuote**: `https://www.brainyquote.com/topics/inspirational-quotes`
- **Goodreads**: `https://www.goodreads.com/quotes/tag/inspirational`
- **Wikiquote**: `https://en.wikiquote.org/wiki/Inspirational_quotes`

Note: Always respect website terms of service and robots.txt. Use appropriate delays between requests. Some websites may require authentication or have rate limits.

## Automation

You can automate the scraper using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Scrape quotes daily at 2 AM
0 2 * * * cd /path/to/inspirational-quote-scraper && /path/to/venv/bin/python src/main.py --scrape

# Display daily quote at 9 AM
0 9 * * * cd /path/to/inspirational-quote-scraper && /path/to/venv/bin/python src/main.py --display
```

### Windows (Task Scheduler)

- Create a task to run `python src/main.py --scrape` daily
- Create another task to run `python src/main.py --display` daily
- Set working directory to project folder
- Use full path to Python executable

## Legal and Ethical Considerations

- **Respect robots.txt**: Check and respect robots.txt files on target websites
- **Rate Limiting**: Use appropriate delays between requests to avoid overloading servers
- **Terms of Service**: Review and comply with website terms of service
- **Public Domain**: Focus on public domain quotes to avoid copyright issues
- **Attribution**: Properly attribute quotes to their authors when available

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
