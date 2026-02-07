# Stock Tracker

A GUI application for tracking stock prices from financial websites, displaying them in a dashboard, tracking price changes, and calculating gains. Features real-time price updates, data persistence, and comprehensive logging.

## Project Description

Stock Tracker solves the problem of monitoring multiple stock prices in real-time by providing an intuitive graphical interface to track stocks, view price changes, and calculate gains from initial tracking. It helps users monitor their portfolio or watchlist with automatic updates and visual indicators for price movements.

**Target Audience**: Investors, traders, and financial enthusiasts who want to track stock prices, monitor portfolio performance, and stay updated on market movements with a simple, local application.

## Features

- **GUI Dashboard**: User-friendly graphical interface built with tkinter
- **Real-time Price Updates**: Automatic refresh of stock prices at configurable intervals
- **Multiple Stock Tracking**: Track multiple stocks simultaneously
- **Price Change Tracking**: View current price changes from previous close
- **Gain Calculation**: Calculate absolute and percentage gains from first tracked price
- **Add/Remove Stocks**: Dynamically add or remove stocks from tracking list
- **Data Persistence**: Automatic saving of stock data and tracking history
- **Color Coding**: Visual indicators for positive (green) and negative (red) price changes
- **Company Names**: Display full company names alongside stock symbols
- **Cross-platform**: Works on Windows, macOS, and Linux
- **No API Key Required**: Uses free Yahoo Finance data via yfinance library

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- tkinter (usually included with Python, but may need separate installation on Linux)
- Internet connection for fetching stock data

### Installing tkinter

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install python3-tk
```

**Linux (Fedora)**:
```bash
sudo dnf install python3-tkinter
```

**macOS/Windows**: tkinter is usually included with Python installation

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/stock-tracker
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

Edit `config.yaml` if you want to customize default stocks, refresh rate, or window size:

```yaml
default_stocks:
  - AAPL
  - MSFT
  - GOOGL
refresh_rate: 5000  # milliseconds
window_size: "1000x700"
```

## Usage

### Basic Usage

Launch the stock tracker:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml
```

### Using the Application

1. **Add a Stock**:
   - Enter stock symbol (e.g., "AAPL", "MSFT", "TSLA") in the "Symbol" field
   - Click "Add Stock"
   - The stock will appear in the dashboard

2. **Remove a Stock**:
   - Enter stock symbol in the "Symbol" field
   - Click "Remove Stock"
   - The stock will be removed from tracking

3. **View Dashboard**:
   - The dashboard displays:
     - **Symbol**: Stock ticker symbol
     - **Name**: Company name
     - **Price**: Current stock price
     - **Change**: Price change from previous close (in dollars)
     - **Change %**: Percentage change from previous close
     - **Gain**: Absolute gain from first tracked price
     - **Gain %**: Percentage gain from first tracked price
     - **Last Update**: Timestamp of last price update

4. **Refresh Prices**:
   - Prices automatically refresh at the configured interval (default: 5 seconds)
   - Click "Refresh Now" to manually update prices immediately

5. **Color Coding**:
   - **Green**: Positive price change (≥1%)
   - **Red**: Negative price change (≤-1%)
   - **Gray**: Error fetching data

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

- `data_file`: Path to JSON file storing stock data and tracking history
- `default_stocks`: List of stock symbols to track on startup
- `update_interval`: Update interval in seconds (for reference, not currently used)
- `window_size`: Initial window dimensions (e.g., "1000x700")
- `refresh_rate`: Dashboard refresh rate in milliseconds (default: 5000)
- `thresholds`: Price change thresholds for color coding
- `logging`: Logging configuration (level, file, max_bytes, backup_count, format)

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Project Structure

```
stock-tracker/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Application configuration
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── data/
│   └── stock_data.json     # Stock data and tracking history
└── logs/
    └── stock_tracker.log    # Application logs
```

## Stock Data

The application uses the `yfinance` library to fetch stock data from Yahoo Finance. This provides:

- Real-time stock prices
- Previous close prices
- Daily high/low prices
- Company information

**Note**: Stock prices may have a slight delay (typically 15-20 minutes) as Yahoo Finance provides delayed data for free. For real-time data, consider using paid APIs.

## Understanding the Dashboard

### Price Change
- Shows the difference between current price and previous day's close
- Positive values indicate price increase
- Negative values indicate price decrease

### Gain Calculation
- **Gain**: Absolute dollar amount gained/lost since first tracking
- **Gain %**: Percentage gain/loss since first tracking
- Calculated from the first price recorded when stock was added
- Useful for tracking portfolio performance over time

### Color Indicators
- **Green**: Significant positive change (≥1% by default)
- **Red**: Significant negative change (≤-1% by default)
- **Black**: Normal price movement
- **Gray**: Error fetching data

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Test Coverage

The test suite covers:
- Stock data management (add, update, save, load)
- Stock price fetching (with mocks)
- Company name retrieval
- Data persistence
- Case-insensitive symbol handling

## Troubleshooting

### Application Won't Start

**Error: "tkinter is not available"**
- Install tkinter for your system (see Prerequisites section)
- On Linux, ensure python3-tk package is installed

**Error: "Configuration file not found"**
- Ensure `config.yaml` exists in the project root
- Use `-c` option to specify custom config path

### Data Issues

**Error: "Could not fetch data for [SYMBOL]"**
- Verify stock symbol is correct (e.g., "AAPL" not "apple")
- Check internet connection
- Some symbols may not be available on Yahoo Finance
- Try refreshing after a few seconds

**Prices Not Updating**
- Check internet connection
- Verify refresh rate in config.yaml
- Click "Refresh Now" to manually update
- Check logs for error messages

### Network Issues

**Slow Updates or Timeouts**
- Yahoo Finance may rate-limit requests
- Increase refresh_rate in config.yaml to reduce frequency
- Check firewall/proxy settings
- Verify internet connection stability

## Performance Considerations

- **Refresh Rate**: Lower refresh rates (higher values) reduce API calls and improve performance
- **Multiple Stocks**: Tracking many stocks simultaneously may slow updates
- **Network Speed**: Faster internet connection improves update speed
- **Data Persistence**: Data is saved after each update, which may cause slight delays

## Limitations

- **Delayed Data**: Free Yahoo Finance data has a 15-20 minute delay
- **Rate Limiting**: Too frequent updates may trigger rate limiting
- **Symbol Availability**: Not all stocks are available on Yahoo Finance
- **Market Hours**: Data may be limited outside market hours

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guide
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with conventional commit format
7. Push and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

## License

This project is part of the everyday-python-scripts collection. See the main repository for license information.

## Disclaimer

This application is for informational purposes only. Stock prices and financial data are provided by third-party sources and may not be accurate or up-to-date. Always verify information with official sources before making investment decisions. The authors are not responsible for any financial losses resulting from the use of this software.
