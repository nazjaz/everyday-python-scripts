# Crypto Price Tracker

A Python GUI application that scrapes cryptocurrency prices from public APIs and displays them in a simple GUI with price alerts and portfolio tracking.

## Features

- **Real-time Price Updates**: Automatically fetches cryptocurrency prices from CoinGecko API
- **Portfolio Tracking**: Track your cryptocurrency holdings with amounts and current values
- **Price Alerts**: Set alerts for when prices go above or below target prices
- **Simple GUI**: User-friendly interface built with tkinter
- **Auto-refresh**: Configurable automatic price updates
- **Data Persistence**: Saves portfolio and alerts to JSON files
- **Multiple Coins**: Track multiple cryptocurrencies simultaneously
- **Portfolio Value**: Calculate total portfolio value in USD

## Prerequisites

- Python 3.8 or higher
- pip package manager
- tkinter (usually included with Python, but may need separate installation on Linux)
- Internet connection for API access

### Installing tkinter on Linux

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S tk
```

## Installation

1. Clone or navigate to the project directory:
```bash
cd crypto-price-tracker
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

The tool uses a YAML configuration file (`config.yaml`) for settings:

- **api**: API settings (base URL, timeout, optional API key)
- **app**: Application settings (title, window size)
- **update**: Price update settings (interval, default coins)
- **data**: Data storage directory
- **logging**: Logging configuration

### API Information

The application uses CoinGecko API (free tier, no API key required):
- Base URL: `https://api.coingecko.com/api/v3`
- Free tier supports reasonable request rates
- No authentication required for basic price data

### Environment Variables

You can override configuration using environment variables:

- `API_KEY`: API key (optional, not required for CoinGecko free tier)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Running the Application

**Start the application:**
```bash
python src/main.py
```

**With custom configuration:**
```bash
python src/main.py --config custom_config.yaml
```

### Using the Application

1. **Add to Portfolio**:
   - Enter coin ID (e.g., "bitcoin", "ethereum")
   - Enter amount you own
   - Click "Add"

2. **View Prices**:
   - Prices are automatically updated at configured intervals
   - Current prices and portfolio values are displayed
   - Total portfolio value is calculated

3. **Set Price Alerts**:
   - Enter coin ID
   - Enter target price
   - Select condition (Above or Below)
   - Click "Add Alert"
   - Alert will trigger when condition is met

4. **Remove Items**:
   - Select item from list
   - Click "Remove Selected" or "Remove Alert"

5. **Manual Refresh**:
   - Use File > Refresh Prices to update immediately

### Common Coin IDs

- `bitcoin` - Bitcoin (BTC)
- `ethereum` - Ethereum (ETH)
- `litecoin` - Litecoin (LTC)
- `cardano` - Cardano (ADA)
- `polkadot` - Polkadot (DOT)
- `chainlink` - Chainlink (LINK)
- `solana` - Solana (SOL)
- `dogecoin` - Dogecoin (DOGE)

For a complete list, visit [CoinGecko API](https://www.coingecko.com/en/api/documentation)

## Project Structure

```
crypto-price-tracker/
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
│   ├── portfolio.json
│   └── alerts.json
└── logs/
    └── .gitkeep
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file
- `data/portfolio.json`: Portfolio data storage
- `data/alerts.json`: Alerts data storage
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory

## Data Storage

### Portfolio Format

Portfolio is stored in `data/portfolio.json`:
```json
{
  "bitcoin": {
    "amount": 0.5,
    "added_at": "2024-02-07T10:00:00"
  },
  "ethereum": {
    "amount": 2.0,
    "added_at": "2024-02-07T10:05:00"
  }
}
```

### Alerts Format

Alerts are stored in `data/alerts.json`:
```json
[
  {
    "coin_id": "bitcoin",
    "target_price": 50000.0,
    "condition": "above",
    "triggered": false,
    "created_at": "2024-02-07T10:00:00"
  }
]
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
pytest tests/test_main.py::test_fetch_price
```

## Troubleshooting

### Common Issues

**Application won't start:**
- Verify Python version is 3.8 or higher
- Check that tkinter is installed
- Ensure all dependencies are installed

**Prices not updating:**
- Check internet connection
- Verify API endpoint is accessible
- Check logs for API errors
- CoinGecko API may have rate limits

**API errors:**
- CoinGecko free tier has rate limits (10-50 calls/minute)
- Increase update interval if hitting rate limits
- Check API status at CoinGecko website

**Alerts not triggering:**
- Verify alert conditions are set correctly
- Check that prices are updating
- Ensure coin IDs are correct

### Error Messages

The tool provides detailed error messages in logs. Check `logs/crypto_tracker.log` for:
- API connection errors
- Price fetching failures
- Data loading/saving errors

### Rate Limiting

CoinGecko free tier has rate limits:
- **Free tier**: 10-50 calls per minute
- **Default interval**: 60 seconds (1 call per minute)
- Adjust `update.interval_seconds` in config if needed

## API Rate Limits

The application respects API rate limits by default:
- Default update interval: 60 seconds
- Configurable in `config.yaml`
- Manual refresh available without waiting

## Security Considerations

- No API key required for CoinGecko free tier
- Portfolio data stored locally in JSON files
- No sensitive data transmitted (only coin IDs and amounts)
- Review data files before sharing

## Limitations

- Free API tier has rate limits
- Prices update at configured intervals (not real-time)
- Limited to cryptocurrencies available on CoinGecko
- GUI only (no command-line interface)
- Single currency (USD) support

## Future Enhancements

Potential improvements:
- Support for multiple fiat currencies
- Historical price charts
- Price change indicators (24h, 7d, 30d)
- Export portfolio to CSV/Excel
- Multiple portfolios
- Price history tracking
- Desktop notifications for alerts
- Dark mode theme

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.

## Disclaimer

This tool is for informational purposes only. Cryptocurrency investments carry risk. Always do your own research and consult with financial advisors before making investment decisions.
