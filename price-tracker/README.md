# Price Tracker

Scrape product prices from e-commerce websites and save price history to a local database, tracking price changes over time. Monitor price drops, increases, and trends for products you care about.

## Project Description

Price Tracker solves the problem of monitoring product prices across e-commerce websites. It automatically scrapes product prices, stores them in a local database, and tracks price changes over time, helping you identify the best time to buy and track price trends.

**Target Audience**: Consumers, deal hunters, and anyone who wants to track product prices and identify price drops or trends.

## Features

- **Web Scraping**: Scrape product prices from e-commerce websites
- **Price History**: Store price history in SQLite database
- **Price Change Tracking**: Automatically detect and log price changes
- **Multiple Products**: Track multiple products simultaneously
- **Flexible Selectors**: Configure CSS selectors for different websites
- **Price Parsing**: Intelligent price extraction from various formats
- **Automatic Cleanup**: Remove old price history based on retention policy
- **Detailed Reports**: Generate reports with price history and changes
- **No API Keys Required**: Uses web scraping (no API keys needed)
- **Error Handling**: Robust error handling with retry logic

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for scraping prices

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/price-tracker
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

### Step 4: Configure Products

**IMPORTANT**: Edit `config.yaml` to add products you want to track:

```yaml
products:
  - name: "Product Name"
    url: "https://example.com/product"
    website: "example"
    enabled: true
    price_selector: ".price"  # CSS selector for price
    title_selector: "h1"  # CSS selector for title
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **products**: List of products to track with URLs and selectors
- **website_selectors**: Default CSS selectors for different websites
- **scraping**: Scraping settings (interval, timeout, retry logic)
- **price_tracking**: Price change detection settings
- **retention**: Data retention policy
- **reporting**: Report generation settings

### Adding Products

To track a product, add it to the `products` list:

```yaml
products:
  - name: "iPhone 15"
    url: "https://example.com/iphone-15"
    website: "example"
    enabled: true
    price_selector: ".product-price"
    title_selector: "h1.product-title"
```

### Finding CSS Selectors

To find the correct CSS selector for a price:

1. Open the product page in a web browser
2. Right-click on the price and select "Inspect"
3. Note the HTML element and its class/id
4. Use that as the `price_selector` in config

Example: If price is in `<span class="price">$99.99</span>`, use `.price` as selector.

### Website-Specific Selectors

Configure default selectors for different websites:

```yaml
website_selectors:
  amazon:
    price_selector: "#priceblock_ourprice, .a-price-whole"
    title_selector: "#productTitle"
    currency_symbol: "$"
```

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_FILE`: Override database file path
- `SCRAPING_INTERVAL`: Override scraping interval in seconds
- `NOTIFICATIONS_ENABLED`: Enable/disable notifications (true/false)

## Usage

### Basic Usage

Check prices for all configured products:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Run once and exit (don't loop)
python src/main.py -o
```

### Automated Monitoring

Set up a cron job or scheduled task to run periodically:

**Linux/macOS (cron)**:
```bash
# Check prices every hour
0 * * * * cd /path/to/price-tracker && /path/to/venv/bin/python src/main.py
```

**Windows (Task Scheduler)**:
- Create a task to run `python src/main.py` on a schedule
- Set working directory to project folder

## Project Structure

```
price-tracker/
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
│   └── price_history.db    # SQLite database (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── price_tracker.log   # Application logs
    └── price_tracking_report.txt  # Price tracking reports
```

### File Descriptions

- **src/main.py**: Web scraping, price extraction, database operations, and price change tracking
- **config.yaml**: YAML configuration file with products and website selectors
- **tests/test_main.py**: Unit tests for core functionality
- **data/price_history.db**: SQLite database storing all price history
- **logs/price_tracker.log**: Application log file with rotation
- **logs/price_tracking_report.txt**: Summary reports with price history

## Database Schema

The SQLite database contains three main tables:

### products
- `id`: Primary key
- `name`: Product name
- `url`: Product URL (unique)
- `website`: Website identifier
- `enabled`: Whether product is enabled
- `created_at`: Creation timestamp

### price_history
- `id`: Primary key
- `product_id`: Foreign key to products
- `price`: Price value
- `currency`: Currency symbol
- `title`: Product title at time of check
- `checked_at`: Timestamp when price was checked

### price_changes
- `id`: Primary key
- `product_id`: Foreign key to products
- `old_price`: Previous price
- `new_price`: New price
- `change_percent`: Percentage change
- `changed_at`: Timestamp when change was detected

## Price Change Detection

The tracker automatically detects price changes:

- **All Changes**: Tracks all price changes by default
- **Change Percentage**: Calculates percentage change
- **Change History**: Stores all price changes in database
- **Reports**: Includes price changes in reports

## Reports

Reports include:

- **Statistics**: Products checked, prices updated, price changes
- **Recent Price Changes**: Last 20 price changes with details
- **Current Prices**: Current price for each tracked product

Reports are generated automatically and saved to `logs/price_tracking_report.txt`.

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
- Price parsing
- Database operations
- Price change detection
- Web scraping (mocked)

## Troubleshooting

### Common Issues

**Issue**: Price not being extracted

**Solution**: 
- Check CSS selector is correct for the website
- Verify website structure hasn't changed
- Try different selectors (comma-separated for multiple options)
- Check logs for extraction errors
- Inspect HTML structure of product page

---

**Issue**: `requests.exceptions.ConnectionError`

**Solution**: 
- Check internet connection
- Verify website URL is correct and accessible
- Some websites may block automated requests
- Try increasing timeout in config
- Check if website requires authentication

---

**Issue**: Website blocking requests

**Solution**: 
- Update user agent in config
- Add delays between requests
- Some websites may require cookies or headers
- Consider using a proxy (advanced)

---

**Issue**: Wrong price extracted

**Solution**: 
- Verify CSS selector targets correct element
- Check if website has multiple price elements
- Use more specific selector
- Test selector in browser developer tools

---

**Issue**: Database errors

**Solution**: 
- Check database file permissions
- Ensure data directory exists and is writable
- Verify database isn't locked by another process
- Check disk space

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Could not extract price"**: CSS selector may be incorrect, check website structure
- **"Failed to fetch"**: Network error or website blocking, check connection and URL

## Best Practices

1. **Test Selectors First**: Use browser developer tools to verify CSS selectors work
2. **Start with One Product**: Test with one product before adding more
3. **Monitor Logs**: Check logs regularly to ensure scraping is working
4. **Respect Rate Limits**: Don't scrape too frequently (use appropriate intervals)
5. **Update Selectors**: Websites may change structure, update selectors as needed
6. **Backup Database**: Regularly backup price history database

## Legal and Ethical Considerations

- **Respect robots.txt**: Check website's robots.txt file
- **Rate Limiting**: Don't scrape too frequently
- **Terms of Service**: Review website's terms of service
- **Personal Use**: Intended for personal use only
- **No Commercial Use**: Don't use for commercial price monitoring services

## Limitations

- **Website Changes**: Websites may change HTML structure, requiring selector updates
- **Anti-Scraping**: Some websites may block automated requests
- **JavaScript**: Cannot scrape prices loaded via JavaScript (requires Selenium)
- **Rate Limiting**: May be subject to rate limiting by websites
- **Accuracy**: Price extraction depends on correct CSS selectors

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

## Disclaimer

This tool is for personal use only. Always respect website terms of service and robots.txt files. Some websites may prohibit automated scraping. Use responsibly and ethically.
