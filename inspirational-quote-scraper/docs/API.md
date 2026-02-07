# API Documentation

## QuoteScraper Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize QuoteScraper with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `scrape_quotes() -> Dict[str, int]`

Scrape quotes from all configured sources.

**Returns:**
- Dictionary with scraping statistics:
  - `sources_processed`: Number of sources processed
  - `quotes_scraped`: Number of quotes scraped
  - `quotes_saved`: Number of quotes saved to database
  - `errors`: Number of errors encountered

#### `get_daily_quote(date: Optional[datetime] = None) -> Optional[Dict]`

Get or assign daily quote for a specific date.

**Parameters:**
- `date`: Date to get quote for (default: today)

**Returns:**
- Quote dictionary with keys:
  - `id`: Quote ID
  - `text`: Quote text
  - `author`: Quote author (may be None)
  - `category`: Quote category
  - `source_name`: Source website name
- Returns `None` if no quotes available

#### `display_quote(quote: Dict) -> None`

Display quote in console and send desktop notification.

**Parameters:**
- `quote`: Quote dictionary

## Database Schema

### quotes Table

- `id`: INTEGER PRIMARY KEY
- `text`: TEXT NOT NULL
- `author`: TEXT
- `source_url`: TEXT
- `source_name`: TEXT
- `category`: TEXT
- `scraped_at`: TEXT DEFAULT CURRENT_TIMESTAMP
- `displayed_at`: TEXT
- `display_count`: INTEGER DEFAULT 0

### daily_quotes Table

- `id`: INTEGER PRIMARY KEY
- `quote_id`: INTEGER NOT NULL (Foreign Key to quotes.id)
- `display_date`: TEXT NOT NULL UNIQUE
