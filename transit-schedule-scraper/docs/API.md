# API Documentation

## TransitScheduleScraper Class

Main class for scraping transit schedules from websites.

### Methods

#### `__init__(config_path: str = "config.yaml") -> None`

Initialize TransitScheduleScraper with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

---

#### `scrape_departures(route_id: str, stop_id: str, transit_system: Optional[str] = None) -> List[Dict[str, any]]`

Scrape departure times for a route and stop.

**Parameters:**
- `route_id`: Route identifier
- `stop_id`: Stop identifier
- `transit_system`: Transit system name (uses default if not provided)

**Returns:**
List of departure dictionaries with keys:
- `route_id`: Route identifier
- `stop_id`: Stop identifier
- `departure_time`: Departure time (ISO format)
- `scheduled_time`: Original scheduled time string
- `route_name`: Route name
- `destination`: Destination
- `delay`: Delay information
- `transit_system`: Transit system name

---

#### `get_next_departures(route_id: str, stop_id: str, limit: int = 5) -> List[Dict[str, any]]`

Get next departure times for a route and stop.

**Parameters:**
- `route_id`: Route identifier
- `stop_id`: Stop identifier
- `limit`: Maximum number of departures to return

**Returns:**
List of departure dictionaries sorted by time, with additional keys:
- `departure_datetime`: Datetime object
- `time_until`: Formatted time until departure
- `route_name`: Route name from database
- `stop_name`: Stop name from database

---

#### `display_departures(route_id: str, stop_id: str, limit: int = 5) -> None`

Display next departures for a route and stop.

**Parameters:**
- `route_id`: Route identifier
- `stop_id`: Stop identifier
- `limit`: Maximum number of departures to display

Prints formatted table of next departures to console.

---

#### `_parse_time_string(time_str: str) -> Optional[datetime]`

Parse time string to datetime object (internal method).

**Parameters:**
- `time_str`: Time string in various formats

**Returns:**
Datetime object or None if parsing failed

Supports formats:
- 24-hour: "14:30", "14:30:00"
- 12-hour: "2:30 PM", "2:30PM"
- Relative: "5 min", "in 10 minutes"

---

#### `_format_time_until(departure_time: datetime) -> str`

Format time until departure (internal method).

**Parameters:**
- `departure_time`: Departure datetime

**Returns:**
Formatted time string (e.g., "15 min", "1h 30m", "Now", "Departed")

---

#### `_fetch_page(url: str) -> Optional[BeautifulSoup]`

Fetch and parse a web page (internal method).

**Parameters:**
- `url`: URL to fetch

**Returns:**
BeautifulSoup object or None if fetch failed

---

#### `_extract_departure_times(soup: BeautifulSoup, selectors: Dict[str, str]) -> List[Dict[str, any]]`

Extract departure times from parsed HTML (internal method).

**Parameters:**
- `soup`: BeautifulSoup object
- `selectors`: Dictionary of CSS selectors

**Returns:**
List of departure dictionaries

---

#### `_save_departure(departure: Dict[str, any]) -> bool`

Save departure to database (internal method).

**Parameters:**
- `departure`: Departure dictionary

**Returns:**
True if saved successfully, False otherwise
