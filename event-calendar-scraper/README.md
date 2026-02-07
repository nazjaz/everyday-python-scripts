# Event Calendar Scraper

Scrape public event listings from websites and create a local event calendar with filtering by date, location, or category. This tool helps you aggregate events from multiple sources into a single, searchable local database.

## Project Description

Event Calendar Scraper solves the problem of tracking events from multiple sources by automatically scraping public event listings from websites, storing them in a local database, and providing filtering capabilities by date, location, or category. This creates a unified event calendar from multiple sources.

**Target Audience**: Event organizers, community managers, users tracking local events, and anyone who needs to aggregate and filter events from multiple websites.

## Features

- **Web Scraping**: Scrape events from multiple websites using configurable CSS selectors
- **Local Database Storage**: Store events in SQLite database for persistence
- **Date Filtering**: Filter events by start date and end date ranges
- **Location Filtering**: Filter events by location (partial match)
- **Category Filtering**: Filter events by category
- **Duplicate Detection**: Automatically skip duplicate events
- **Category Tracking**: Track event counts by category
- **Data Retention**: Automatic cleanup of old events
- **Flexible Date Parsing**: Support for multiple date formats
- **Comprehensive Logging**: Log all operations for audit and debugging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for web scraping

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/event-calendar-scraper
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

Edit `config.yaml` to add your event sources:

```yaml
sources:
  - name: "Your Event Source"
    url: "https://example.com/events"
    default_category: "general"
    selectors:
      event: ".event-item"
      title: ".event-title"
      date: ".event-date"
      location: ".event-location"
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **sources**: List of event sources with URLs and CSS selectors
- **database**: SQLite database file path and table creation settings
- **scraping**: Timeout, user agent, and delay settings
- **retention**: Data retention policy for old events
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_FILE`: Override database file path
- `SCRAPING_TIMEOUT`: Override scraping timeout in seconds

### Example Configuration

```yaml
sources:
  - name: "Local Events"
    url: "https://example.com/events"
    default_category: "local"
    selectors:
      event: ".event"
      title: "h3.event-title"
      date: ".date"
      location: ".venue"
      category: ".category"
      url: "a.event-link"
```

## Usage

### Basic Usage

Scrape events and display calendar:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Scrape events only
python src/main.py --scrape

# Filter events
python src/main.py --filter

# Filter by date range
python src/main.py --filter --start-date 2024-02-01 --end-date 2024-02-28

# Filter by location
python src/main.py --filter --location "New York"

# Filter by category
python src/main.py --filter --category "music"

# Combine filters
python src/main.py --filter --start-date 2024-02-01 --location "New York" --category "music"

# List available categories
python src/main.py --list-categories

# List available locations
python src/main.py --list-locations
```

### Common Use Cases

1. **Scrape Events**:
   ```bash
   python src/main.py --scrape
   ```

2. **View All Events**:
   ```bash
   python src/main.py --filter
   ```

3. **Find Events This Month**:
   ```bash
   python src/main.py --filter --start-date 2024-02-01 --end-date 2024-02-29
   ```

4. **Find Events in Location**:
   ```bash
   python src/main.py --filter --location "San Francisco"
   ```

5. **Find Events by Category**:
   ```bash
   python src/main.py --filter --category "technology"
   ```

6. **Add Custom Event Sources**:
   - Edit `sources` section in `config.yaml`
   - Add source name, URL, and CSS selectors
   - Use browser developer tools to find correct selectors

## Project Structure

```
event-calendar-scraper/
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
│   └── API.md              # API documentation
├── data/
│   └── events.db           # SQLite database (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    └── event_scraper.log   # Application logs
```

### File Descriptions

- **src/main.py**: Core event scraping, database operations, and filtering functionality
- **config.yaml**: YAML configuration file with event sources and settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/events.db**: SQLite database storing all events
- **logs/event_scraper.log**: Application log file with rotation

## Database Schema

The SQLite database contains two main tables:

### events
- `id`: Primary key
- `title`: Event title
- `description`: Event description
- `start_date`: Event start date (ISO format)
- `end_date`: Event end date (ISO format, nullable)
- `location`: Event location
- `category`: Event category
- `source_url`: Source website URL
- `source_name`: Source website name
- `event_url`: Event detail page URL
- `price`: Event price information
- `scraped_at`: Timestamp when scraped

### categories
- `id`: Primary key
- `name`: Category name (unique)
- `event_count`: Number of events in category

## Event Scraping

Events are scraped using CSS selectors configured for each source:

1. **HTML Fetching**: Downloads page content using requests library
2. **HTML Parsing**: Parses HTML using BeautifulSoup
3. **Event Extraction**: Extracts events using configured CSS selectors
4. **Date Parsing**: Parses dates in various formats to ISO format
5. **Storage**: Saves unique events to database

### CSS Selector Configuration

Each source requires selectors for:

- `event`: Selector for the event container element
- `title`: Selector for the event title
- `date`: Selector for the event date
- `location`: Selector for the event location (optional)
- `category`: Selector for the event category (optional)
- `url`: Selector for the event detail link (optional)
- `description`: Selector for the event description (optional)
- `price`: Selector for the event price (optional)
- `end_date`: Selector for the event end date (optional)

## Filtering

### Date Filtering

Filter events by date range:

- `--start-date`: Events starting from this date (YYYY-MM-DD)
- `--end-date`: Events ending before this date (YYYY-MM-DD)

### Location Filtering

Filter events by location (partial match):

- `--location`: Location name or partial match

### Category Filtering

Filter events by category:

- `--category`: Exact category name

### Combined Filtering

All filters can be combined:

```bash
python src/main.py --filter --start-date 2024-02-01 --location "New York" --category "music"
```

## Date Format Support

The scraper supports multiple date formats:

- `YYYY-MM-DD`
- `YYYY-MM-DD HH:MM:SS`
- `MM/DD/YYYY`
- `DD/MM/YYYY`
- `Month Day, Year` (e.g., "February 15, 2024")
- And more

Dates are normalized to ISO format for storage and filtering.

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
- Event scraping from HTML
- Database operations
- Date parsing
- Event filtering
- Duplicate detection
- Data cleanup

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'requests'`

**Solution**: Install dependencies: `pip install -r requirements.txt`

---

**Issue**: No events being scraped

**Solution**: 
- Verify event source URLs are correct and accessible
- Check internet connection
- Verify CSS selectors match current website structure
- Check logs for parsing errors
- Some websites may block automated scraping

---

**Issue**: CSS selectors not finding events

**Solution**: 
- Use browser developer tools to inspect page structure
- Verify selectors match current website structure
- Websites may change their HTML structure over time
- Test selectors manually in browser console

---

**Issue**: Date parsing errors

**Solution**: 
- Check date format in source website
- Add custom date format to parsing logic if needed
- Review logs for date parsing warnings

---

**Issue**: Database locked errors

**Solution**: 
- Ensure only one instance of scraper is running
- Check database file permissions
- Close any database viewers that might have the file open

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"No event sources configured"**: Add at least one event source to `sources` in config.yaml
- **"Error fetching URL"**: Event source URL may be invalid or inaccessible
- **"Database error"**: Check database file permissions and disk space

## Event Source Websites

Example public event sources you can configure:

- **Eventbrite**: Public event listings
- **Meetup**: Local meetup events
- **Facebook Events**: Public Facebook events
- **Local event calendars**: City or venue event calendars

Note: Always respect website terms of service and robots.txt. Use appropriate delays between requests. Some websites may require authentication or have rate limits.

## Legal and Ethical Considerations

- **Respect robots.txt**: Check and respect robots.txt files on target websites
- **Rate Limiting**: Use appropriate delays between requests to avoid overloading servers
- **Terms of Service**: Review and comply with website terms of service
- **Public Events Only**: Focus on publicly available event listings
- **Attribution**: Properly attribute events to their sources

## Automation

You can automate the scraper using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)

```bash
# Scrape events daily at 2 AM
0 2 * * * cd /path/to/event-calendar-scraper && /path/to/venv/bin/python src/main.py --scrape
```

### Windows (Task Scheduler)

- Create a task to run `python src/main.py --scrape` daily
- Set working directory to project folder
- Use full path to Python executable

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
