# API Documentation

## EventCalendarScraper Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize EventCalendarScraper with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `scrape_events() -> Dict[str, int]`

Scrape events from all configured sources.

**Returns:**
- Dictionary with scraping statistics:
  - `sources_processed`: Number of sources processed
  - `events_scraped`: Number of events scraped
  - `events_saved`: Number of events saved to database
  - `errors`: Number of errors encountered

#### `filter_events(start_date: Optional[str] = None, end_date: Optional[str] = None, location: Optional[str] = None, category: Optional[str] = None) -> List[Dict]`

Filter events by date, location, or category.

**Parameters:**
- `start_date`: Filter events starting from this date (ISO format)
- `end_date`: Filter events ending before this date (ISO format)
- `location`: Filter events by location (partial match)
- `category`: Filter events by category

**Returns:**
- List of event dictionaries matching the filters

#### `get_categories() -> List[str]`

Get list of all event categories.

**Returns:**
- List of category names

#### `get_locations() -> List[str]`

Get list of all event locations.

**Returns:**
- List of unique location names

#### `_save_event(event: Dict) -> bool`

Save event to database.

**Parameters:**
- `event`: Event dictionary

**Returns:**
- True if saved successfully, False otherwise (e.g., duplicate)

#### `_parse_date(date_str: str) -> Optional[str]`

Parse date string to ISO format.

**Parameters:**
- `date_str`: Date string in various formats

**Returns:**
- ISO format date string or None if parsing fails

## Database Schema

### events Table

- `id`: INTEGER PRIMARY KEY
- `title`: TEXT NOT NULL
- `description`: TEXT
- `start_date`: TEXT NOT NULL
- `end_date`: TEXT
- `location`: TEXT
- `category`: TEXT
- `source_url`: TEXT
- `source_name`: TEXT
- `event_url`: TEXT
- `price`: TEXT
- `scraped_at`: TEXT DEFAULT CURRENT_TIMESTAMP
- UNIQUE constraint on (title, start_date, location)

### categories Table

- `id`: INTEGER PRIMARY KEY
- `name`: TEXT UNIQUE NOT NULL
- `event_count`: INTEGER DEFAULT 0

## Configuration Structure

```yaml
sources:
  - name: "Source Name"
    url: "https://example.com/events"
    default_category: "general"
    selectors:
      event: ".event-item"
      title: ".event-title"
      description: ".event-description"
      date: ".event-date"
      end_date: ".event-end-date"
      location: ".event-location"
      category: ".event-category"
      url: ".event-link"
      price: ".event-price"

database:
  file: "data/events.db"
  create_tables: true

scraping:
  timeout: 30
  user_agent: "Mozilla/5.0..."
  delay_between_sources: 2

retention:
  auto_cleanup: true
  days_to_keep: 90
```

## Event Dictionary Structure

Events are represented as dictionaries with the following keys:

- `title`: Event title (required)
- `description`: Event description
- `start_date`: Event start date (ISO format)
- `end_date`: Event end date (ISO format, optional)
- `location`: Event location
- `category`: Event category
- `source_url`: Source website URL
- `source_name`: Source website name
- `event_url`: Event detail page URL
- `price`: Event price information

## Date Format Support

The scraper supports multiple date formats:

- `YYYY-MM-DD`
- `YYYY-MM-DD HH:MM:SS`
- `MM/DD/YYYY`
- `DD/MM/YYYY`
- `Month Day, Year` (e.g., "February 15, 2024")
- `Day Month Year` (e.g., "15 February 2024")

All dates are normalized to ISO format for storage and filtering.

## Error Handling

The scraper handles the following errors:

- **FileNotFoundError**: Configuration or directory not found
- **requests.exceptions.RequestException**: Network or HTTP errors
- **sqlite3.Error**: Database errors
- **ValueError**: Date parsing errors

All errors are logged and counted in statistics.
