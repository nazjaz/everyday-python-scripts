# Weather Scraper

Scrape weather information from public weather websites and display current conditions and forecasts in a simple GUI application. No API keys required.

## Project Description

Weather Scraper solves the problem of accessing weather information without requiring API keys or paid services. It scrapes weather data from public weather websites (wttr.in) and displays it in an intuitive GUI with current conditions and forecasts.

**Target Audience**: Users who want a simple, local weather application without API key requirements.

## Features

- **Web Scraping**: Fetches weather data from public weather websites (wttr.in)
- **No API Keys Required**: Uses free public weather services
- **Graphical User Interface**: Clean, simple GUI built with tkinter
- **Current Conditions**: Display current temperature, conditions, humidity, wind, pressure, visibility
- **Weather Forecast**: Show multi-day weather forecasts
- **Auto-Refresh**: Automatically refresh weather data at configurable intervals
- **Multiple Cities**: Enter any city name to get weather information
- **Temperature Units**: Support for Celsius and Fahrenheit
- **Real-time Updates**: Manual refresh button for immediate updates

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- tkinter (usually included with Python, may need separate installation on Linux)
- Internet connection for fetching weather data

### Installing tkinter

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install python3-tk
```

**Linux (Fedora)**:
```bash
sudo dnf install python3-tkinter
```

**macOS/Windows**: Usually included with Python installation

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/weather-scraper
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

### Step 4: Configure Settings (Optional)

1. Copy the example environment file (if needed):
   ```bash
   cp .env.example .env
   ```

2. Edit `config.yaml` to customize:
   - Default city
   - Temperature unit (Celsius/Fahrenheit)
   - Refresh interval
   - Display options

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **location**: Default city and country settings
- **weather_source**: Weather provider and URL settings
- **updates**: Auto-refresh settings
- **display**: What information to display
- **gui**: Window size and theme colors

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DEFAULT_CITY`: Override default city name
- `DEFAULT_COUNTRY`: Override default country code
- `REFRESH_INTERVAL`: Override refresh interval in seconds

### Example Configuration

```yaml
location:
  default_city: "London"
  default_country: "UK"

display:
  temperature_unit: "C"  # or "F"
  forecast_days: 3

updates:
  auto_refresh: true
  refresh_interval: 300  # 5 minutes
```

## Usage

### Basic Usage

Launch the weather application:

```bash
python src/main.py
```

The GUI window will open with:
- **City Input**: Enter a city name and click "Refresh"
- **Current Weather**: Large display of current temperature and conditions
- **Weather Details**: Humidity, wind speed, pressure, visibility
- **Forecast**: Multi-day weather forecast

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Fetch weather for specific city on startup
python src/main.py -l "London"
```

### Using the GUI

1. **Enter City**: Type a city name in the input field
2. **Refresh**: Click "Refresh" button to fetch weather
3. **Auto-Refresh**: Weather automatically refreshes every 5 minutes (configurable)
4. **View Details**: Current conditions and forecast are displayed automatically

## Project Structure

```
weather-scraper/
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
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Weather scraping, data parsing, GUI display, and auto-refresh
- **config.yaml**: YAML configuration file with location and display settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/weather_scraper.log**: Application log file with rotation

## Weather Data Source

The application uses **wttr.in**, a free weather service that provides weather data without requiring API keys. It supports:

- Current weather conditions
- Multi-day forecasts
- Worldwide coverage
- No registration or API keys required

### Supported Information

- **Current Conditions**:
  - Temperature (Celsius/Fahrenheit)
  - Weather condition (Sunny, Cloudy, Rainy, etc.)
  - Feels like temperature
  - Humidity percentage
  - Wind speed and direction
  - Atmospheric pressure
  - Visibility
  - UV index

- **Forecast**:
  - Date
  - Weather condition
  - Maximum temperature
  - Minimum temperature
  - Average temperature

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
- Weather data fetching
- Data parsing
- Configuration loading
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named '_tkinter'`

**Solution**: Install tkinter for your system:
- Linux: `sudo apt-get install python3-tk` (Ubuntu/Debian) or `sudo dnf install python3-tkinter` (Fedora)
- macOS/Windows: Usually included, reinstall Python if missing

---

**Issue**: Weather data not loading

**Solution**: 
- Check internet connection
- Verify city name is correct
- Check logs for error messages
- Ensure wttr.in service is accessible
- Try a different city name

---

**Issue**: `requests.exceptions.ConnectionError`

**Solution**: 
- Check internet connection
- Verify firewall is not blocking requests
- Try again later (service may be temporarily unavailable)

---

**Issue**: GUI window doesn't appear

**Solution**: 
- Check that tkinter is properly installed
- Verify Python version (3.8+)
- Check logs for error messages

---

**Issue**: Wrong city weather displayed

**Solution**: 
- Enter full city name with country if ambiguous (e.g., "London, UK")
- Check city name spelling
- Some cities may need country code for accuracy

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"No weather data available"**: Weather fetch failed, check internet connection and city name
- **"tkinter not available"**: Install tkinter package for your system

## Limitations

- **Service Availability**: Depends on wttr.in service availability
- **Rate Limiting**: May be subject to rate limiting by the weather service
- **City Name Accuracy**: Some city names may need country codes for accuracy
- **No Historical Data**: Only current and forecast data available
- **Internet Required**: Requires active internet connection

## Privacy and Data

- **No Data Storage**: Weather data is not stored locally
- **No Tracking**: Application does not track usage
- **Public Service**: Uses public weather service (wttr.in)
- **No Personal Information**: No personal data is collected or transmitted

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

## Acknowledgments

- Weather data provided by [wttr.in](https://wttr.in) - a free weather service
