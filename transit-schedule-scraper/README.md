# Transit Schedule Scraper

Scrape public transportation schedules from transit websites and display next departure times for specified routes and stops. This tool helps you quickly check when the next bus, train, or other transit vehicle will arrive at your stop.

## Project Description

Transit Schedule Scraper solves the problem of accessing real-time or scheduled transit information by automatically scraping departure times from transit agency websites. The tool supports multiple transit systems, stores schedule data in a local database, and provides a clean command-line interface for querying next departures.

**Target Audience**: Commuters, travelers, transit users, and anyone who needs quick access to public transportation schedules without manually visiting multiple websites.

## Features

- **Multi-System Support**: Configure and use multiple transit systems
- **Schedule Scraping**: Automatically scrape departure times from transit websites
- **Next Departure Display**: Show upcoming departures for specified routes and stops
- **Time Parsing**: Intelligently parse various time formats (24-hour, 12-hour, relative times)
- **Delay Information**: Display delay information when available
- **Database Storage**: Store scraped schedules in SQLite database for history
- **Configurable Selectors**: Customize CSS selectors for different transit websites
- **Error Handling**: Robust error handling for network issues and parsing errors
- **Comprehensive Logging**: Log all operations for debugging and audit

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for scraping transit websites

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/transit-schedule-scraper
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

### Step 4: Configure Transit Systems

Edit `config.yaml` to add your transit system configuration:

```yaml
transit_systems:
  your_transit_system:
    base_url: "https://your-transit-agency.com"
    url_template: "{base_url}/schedule?route={route_id}&stop={stop_id}"
    selectors:
      departure_row: "tr.departure"
      time: ".time"
      route: ".route"
      destination: ".destination"
      delay: ".delay"
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **default_transit_system**: Default transit system to use
- **transit_systems**: Configuration for each transit system
  - `base_url`: Base URL of the transit website
  - `url_template`: URL template with placeholders for route_id and stop_id
  - `selectors`: CSS selectors for extracting data from HTML
- **scraping**: Scraping settings (timeout, delay, user agent)
- **database**: SQLite database file path
- **logging**: Logging configuration

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_FILE`: Override database file path
- `REQUEST_TIMEOUT`: Override request timeout in seconds

### Example Configuration

```yaml
transit_systems:
  mta:
    base_url: "https://mta.info"
    url_template: "{base_url}/schedules?route={route_id}&stop={stop_id}"
    selectors:
      departure_row: ".schedule-row"
      time: ".departure-time"
      route: ".route-number"
      destination: ".destination-name"
      delay: ".delay-status"
```

## Usage

### Basic Usage

Get next departures for a route and stop:

```bash
python src/main.py -r "1" -s "12345"
```

### Command-Line Options

```bash
# Basic usage
python src/main.py -r ROUTE_ID -s STOP_ID

# Specify transit system
python src/main.py -r "1" -s "12345" -t "mta"

# Show more departures
python src/main.py -r "1" -s "12345" -n 10

# Use custom configuration
python src/main.py -c /path/to/config.yaml -r "1" -s "12345"

# Show help
python src/main.py --help
```

### Command-Line Arguments

- `-r, --route`: Route identifier (required)
- `-s, --stop`: Stop identifier (required)
- `-t, --transit-system`: Transit system name (optional, uses default from config)
- `-n, --limit`: Number of departures to display (default: 5)
- `-c, --config`: Path to configuration file (default: config.yaml)

### Example Output

```
================================================================================
Next Departures - Route: 1, Stop: 12345
================================================================================
Time                 Route          Destination            Time Until      
--------------------------------------------------------------------------------
2024-12-20 14:30     Route 1        Downtown Station       15 min          
2024-12-20 14:45     Route 1        Downtown Station       30 min          
2024-12-20 15:00     Route 1        Downtown Station       45 min          
================================================================================
```

## Project Structure

```
transit-schedule-scraper/
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
│   └── transit.db          # SQLite database (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    └── transit_scraper.log # Application logs
```

### File Descriptions

- **src/main.py**: Core scraping logic, HTML parsing, and database operations
- **config.yaml**: YAML configuration file with transit system settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/transit.db**: SQLite database storing routes, stops, and departures
- **logs/transit_scraper.log**: Application log file with rotation

## Database Schema

The SQLite database contains three main tables:

### routes
- `id`: Primary key
- `route_id`: Route identifier
- `route_name`: Route name
- `transit_system`: Transit system name
- `created_at`: Creation timestamp

### stops
- `id`: Primary key
- `stop_id`: Stop identifier
- `stop_name`: Stop name
- `transit_system`: Transit system name
- `created_at`: Creation timestamp

### departures
- `id`: Primary key
- `route_id`: Route identifier (foreign key)
- `stop_id`: Stop identifier (foreign key)
- `departure_time`: Departure time (ISO format)
- `scheduled_time`: Original scheduled time string
- `delay_minutes`: Delay in minutes (if available)
- `transit_system`: Transit system name
- `scraped_at`: Scraping timestamp

## How It Works

### Scraping Process

1. **URL Construction**: Builds URL using route_id and stop_id from configuration template
2. **Page Fetching**: Fetches HTML page from transit website with appropriate headers
3. **HTML Parsing**: Uses BeautifulSoup to parse HTML and extract departure information
4. **Data Extraction**: Extracts time, route, destination, and delay using CSS selectors
5. **Time Parsing**: Converts various time formats to datetime objects
6. **Database Storage**: Stores extracted data in SQLite database
7. **Display**: Shows next departures sorted by time

### Time Parsing

The tool supports multiple time formats:
- 24-hour format: "14:30", "14:30:00"
- 12-hour format: "2:30 PM", "2:30PM"
- Relative times: "5 min", "in 10 minutes"
- Handles times in the past (assumes next day)

### Selector Configuration

CSS selectors are configurable per transit system to handle different website structures:
- `departure_row`: Selector for each departure row/item
- `time`: Selector for departure time
- `route`: Selector for route name/number
- `destination`: Selector for destination
- `delay`: Selector for delay/status information

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
- Time parsing
- HTML extraction
- Database operations
- URL construction
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `ConnectionError` or timeout errors

**Solution**: 
- Check internet connection
- Verify transit website URL is correct
- Increase timeout in config.yaml
- Check if website requires authentication or has anti-scraping measures

---

**Issue**: No departures found

**Solution**: 
- Verify route_id and stop_id are correct
- Check CSS selectors match website structure
- Inspect HTML structure of transit website
- Check logs for parsing errors

---

**Issue**: `FileNotFoundError: Configuration file not found`

**Solution**: Ensure `config.yaml` exists or provide correct path with `-c` option.

---

**Issue**: Incorrect time parsing

**Solution**: 
- Check time format on transit website
- Adjust time parsing logic if needed
- Check logs for parsing warnings

---

**Issue**: Website structure changed

**Solution**: 
- Update CSS selectors in config.yaml
- Inspect website HTML to find new selectors
- Test selectors using browser developer tools

### Error Messages

- **"Transit system not configured"**: Transit system name not found in config.yaml
- **"Error fetching URL"**: Network error or invalid URL
- **"Could not parse time string"**: Time format not recognized
- **"No upcoming departures found"**: No departures found for route/stop combination

## Website Compatibility

The scraper is designed to work with transit websites that:
- Display schedules in HTML format
- Have predictable URL patterns
- Use consistent HTML structure for departures

**Note**: Some transit websites may:
- Require JavaScript rendering (not supported)
- Use API endpoints (can be configured if URL is known)
- Have anti-scraping measures
- Require authentication

For websites with APIs, consider configuring the URL template to point directly to API endpoints.

## Customization

### Adding a New Transit System

1. Add configuration to `config.yaml`:

```yaml
transit_systems:
  new_system:
    base_url: "https://new-transit.com"
    url_template: "{base_url}/schedule?r={route_id}&s={stop_id}"
    selectors:
      departure_row: ".departure"
      time: ".time"
      route: ".route"
      destination: ".dest"
      delay: ".delay"
```

2. Test the configuration:

```bash
python src/main.py -r "ROUTE" -s "STOP" -t "new_system"
```

3. Adjust selectors if needed based on website structure

### Modifying Time Parsing

If your transit system uses a unique time format, you may need to modify the `_parse_time_string` method in `src/main.py` to add support for that format.

## Use Cases

1. **Daily Commuting**: Quickly check next bus/train times before leaving
2. **Trip Planning**: Check schedules for multiple routes and stops
3. **Schedule Monitoring**: Track departure times and delays
4. **Automation**: Integrate into scripts or automation tools
5. **Historical Analysis**: Store schedule data for analysis

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

**Important**: Always respect transit website terms of service and robots.txt when scraping. Consider using official APIs when available.
