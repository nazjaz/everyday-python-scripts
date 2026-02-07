# Historical Events Database

A Python automation tool for scraping public domain historical data and creating a local searchable database of historical events. This script allows you to search historical events by date, location, or topic, making it useful for research, education, and project documentation.

## Features

- **Web Scraping**: Scrapes historical data from public domain sources (Wikipedia, custom sources)
- **SQLite Database**: Stores events in a local SQLite database for fast searching
- **Multiple Search Options**:
  - Search by date (year, month, day, or date range)
  - Search by location
  - Search by topic/keyword
- **Data Extraction**: Automatically extracts dates, locations, and topics from scraped content
- **Database Indexing**: Indexed database for fast queries
- **Statistics**: Provides database statistics (total events, year range, etc.)
- **Rate Limiting**: Respectful scraping with configurable delays
- **Retry Logic**: Handles network errors with exponential backoff
- **Comprehensive Logging**: Detailed logging with rotation

## Prerequisites

- Python 3.8 or higher
- Internet connection for scraping
- Write permissions for database directory
- Sufficient disk space for database

## Installation

1. Clone or navigate to the project directory:
```bash
cd historical-events-database
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
   - Configure database path
   - Adjust request delays

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **database.path**: Path to SQLite database file (default: ./historical_events.db)
- **sources.wikipedia.enabled**: Enable Wikipedia scraping (default: true)
- **sources.wikipedia.limit**: Maximum events to scrape (default: 50)
- **sources.custom_sources**: List of custom source configurations
- **scraping.request_delay_seconds**: Delay between requests (default: 2)
- **scraping.max_retries**: Maximum retry attempts (default: 3)

### Environment Variables

Optional environment variables can override configuration:

- `DATABASE_PATH`: Override database file path

## Usage

### Scrape Historical Data

Scrape and populate the database:
```bash
python src/main.py --scrape
```

Dry run to preview what would be scraped:
```bash
python src/main.py --scrape --dry-run
```

### Search by Date

Search events by year:
```bash
python src/main.py --search-date 1776
```

Search events by year and month:
```bash
python src/main.py --search-date 1776-07
```

Search events by full date:
```bash
python src/main.py --search-date 1776-07-04
```

Search events by date range:
```bash
python src/main.py --date-range 1776-01-01 1776-12-31
```

### Search by Location

Search events by location:
```bash
python src/main.py --search-location "France"
```

### Search by Topic

Search events by topic:
```bash
python src/main.py --search-topic "war"
```

### Show Database Statistics

View database statistics:
```bash
python src/main.py --stats
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `--scrape`: Scrape historical data and populate database
- `--dry-run`: Perform a dry run without storing data
- `--search-date`: Search by date (YYYY-MM-DD, YYYY-MM, or YYYY)
- `--search-location`: Search by location
- `--search-topic`: Search by topic/keyword
- `--date-range`: Search by date range (START END)
- `--stats`: Show database statistics
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
historical-events-database/
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
└── historical_events.db      # Generated database file
```

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

1. **Data Scraping**: 
   - Scrapes historical events from configured sources (Wikipedia, custom sources)
   - Extracts dates, descriptions, locations, and topics
   - Handles various date formats and parsing

2. **Data Storage**:
   - Stores events in SQLite database
   - Creates indexes for fast searching
   - Tracks source URLs and metadata

3. **Search Functionality**:
   - **By Date**: Search by year, month, day, or date range
   - **By Location**: Search for events in specific locations
   - **By Topic**: Search for events by topic/keyword

4. **Database Schema**:
   - Events table with date, description, location, topic, source
   - Indexed fields for fast queries
   - Timestamps for tracking

## Database Schema

The database contains a single `events` table with the following fields:
- `id`: Primary key
- `date`: Event date (YYYY-MM-DD format)
- `year`, `month`, `day`: Separate date components
- `description`: Event description
- `location`: Event location (extracted from description)
- `topic`: Event topic/keyword (extracted from description)
- `source`: Data source (e.g., "wikipedia")
- `url`: Source URL
- `created_at`: Timestamp when event was added to database

## Example Usage

### Scraping Historical Data
```bash
# Scrape from Wikipedia
python src/main.py --scrape

# Preview what would be scraped
python src/main.py --scrape --dry-run
```

### Searching Events
```bash
# Find events in 1776
python src/main.py --search-date 1776

# Find events on July 4, 1776
python src/main.py --search-date 1776-07-04

# Find events in France
python src/main.py --search-location "France"

# Find events about wars
python src/main.py --search-topic "war"

# Find events in a date range
python src/main.py --date-range 1776-01-01 1783-12-31
```

### Viewing Statistics
```bash
python src/main.py --stats
```

## Troubleshooting

### Scraping Fails

If scraping fails:
- Check your internet connection
- Verify source URLs are accessible
- Some sources may have changed their structure
- Increase request delay in configuration
- Review logs for specific error messages

### No Results Found

If searches return no results:
- Ensure database has been populated (run --scrape first)
- Check search terms match database content
- Try broader search terms
- Review database statistics with --stats

### Database Errors

If database errors occur:
- Ensure write permissions for database directory
- Check disk space availability
- Verify database file is not corrupted
- Review logs for specific error messages

### Permission Errors

If you encounter permission errors:
- Ensure write access to database directory
- Check file and directory permissions
- Verify sufficient disk space

## Ethical Considerations

- **Respect robots.txt**: Always check and respect robots.txt files
- **Rate Limiting**: Default delay is 2 seconds between requests
- **Public Domain Only**: Only scrape public domain or openly licensed content
- **Terms of Service**: Review and comply with source website terms of service
- **Attribution**: Database includes source URLs for attribution

## Security Considerations

- Database is stored locally and contains only scraped public data
- No authentication or credentials required for public domain sources
- File paths are sanitized
- SQL injection protection through parameterized queries

## Performance Considerations

- Database queries are indexed for fast searching
- Scraping time depends on number of sources and limits
- Rate limiting adds delays between requests
- Consider running scraping during off-peak hours

## Limitations

- Wikipedia structure may change, requiring parser updates
- Date parsing may not handle all date formats
- Location and topic extraction are simplified and may miss some cases
- Custom sources require specific configuration per source

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
- Using scraped data appropriately
- Following robots.txt and rate limiting guidelines
