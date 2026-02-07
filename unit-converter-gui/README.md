# Unit Converter GUI

A Python GUI application that converts between different units of length, weight, temperature, and currency. Built with tkinter for a simple, cross-platform interface.

## Features

- Length conversion: Convert between meters, kilometers, centimeters, millimeters, miles, yards, feet, and inches
- Weight conversion: Convert between kilograms, grams, pounds, ounces, tons, and stone
- Temperature conversion: Convert between Celsius, Fahrenheit, and Kelvin
- Currency conversion: Convert between multiple currencies with configurable exchange rates
- Real-time conversion: Results update automatically as you type
- User-friendly interface: Simple, intuitive GUI with dropdown menus
- Configurable currency rates: Update exchange rates via JSON file or configuration

## Prerequisites

- Python 3.8 or higher
- tkinter (usually included with Python, may require separate installation on Linux)
- pip (Python package installer)

### Installing tkinter

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install python3-tkinter
```

**macOS:** tkinter is included with Python

**Windows:** tkinter is included with Python

## Installation

### Step 1: Navigate to Project Directory

```bash
cd unit-converter-gui
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

### Step 4: Verify tkinter Installation

```bash
python3 -c "import tkinter; print('tkinter is available')"
```

## Configuration

### Configuration File (config.yaml)

The script supports configuration via a YAML file:

```yaml
currency_rates_file: "./currency_rates.json"
```

### Currency Rates File (currency_rates.json)

Currency exchange rates are stored in JSON format. Rates are relative to USD (1.0):

```json
{
  "USD": 1.0,
  "EUR": 0.85,
  "GBP": 0.73,
  "JPY": 110.0
}
```

To update exchange rates, edit the `currency_rates.json` file or use an API to fetch current rates.

## Usage

### Basic Usage

Launch the GUI application:

```bash
python src/main.py
```

### With Configuration File

```bash
python src/main.py --config config.yaml
```

### With Custom Currency Rates

```bash
python src/main.py --currency-rates ./custom_rates.json
```

### Command-Line Arguments

- `--config`: Path to configuration file (YAML)
- `--currency-rates`: Path to currency rates JSON file

## Using the Application

1. **Select Category**: Choose from Length, Weight, Temperature, or Currency
2. **Select From Unit**: Choose the source unit from the dropdown
3. **Enter Value**: Type the value to convert
4. **Select To Unit**: Choose the target unit from the dropdown
5. **View Result**: The converted value appears automatically in the Result field
6. **Clear**: Click the Clear button to reset all fields

### Conversion Examples

- **Length**: Convert 100 meters to feet
- **Weight**: Convert 5 pounds to kilograms
- **Temperature**: Convert 32 Fahrenheit to Celsius
- **Currency**: Convert 100 USD to EUR

## Project Structure

```
unit-converter-gui/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file template
├── currency_rates.json      # Currency exchange rates
├── .gitignore               # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py              # Main script implementation
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation (if applicable)
└── logs/
    └── .gitkeep             # Log directory placeholder
```

### File Descriptions

- `src/main.py`: Core implementation with UnitConverter class and GUI interface
- `config.yaml`: Configuration file with currency rates settings
- `currency_rates.json`: JSON file storing currency exchange rates
- `tests/test_main.py`: Unit tests for conversion functions
- `logs/`: Directory for log files (created automatically)

## Supported Units

### Length
- Meter (m)
- Kilometer (km)
- Centimeter (cm)
- Millimeter (mm)
- Mile (mi)
- Yard (yd)
- Foot (ft)
- Inch (in)

### Weight
- Kilogram (kg)
- Gram (g)
- Pound (lb)
- Ounce (oz)
- Ton (t)
- Stone (st)

### Temperature
- Celsius (°C)
- Fahrenheit (°F)
- Kelvin (K)

### Currency
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- JPY (Japanese Yen)
- CAD (Canadian Dollar)
- AUD (Australian Dollar)
- CHF (Swiss Franc)
- CNY (Chinese Yuan)
- And more (configurable via currency_rates.json)

## Testing

### Run Tests

```bash
pytest tests/
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage and includes:
- Length conversion accuracy
- Weight conversion accuracy
- Temperature conversion accuracy
- Currency conversion accuracy
- Error handling for invalid units
- Configuration file loading
- Currency rates loading

## Troubleshooting

### Common Issues

**Issue: "tkinter is not available"**

Solution: Install tkinter for your Python installation. See Prerequisites section for installation instructions.

**Issue: "No module named 'tkinter'"**

Solution: On Linux, install python3-tk package. On other systems, ensure Python was installed with tkinter support.

**Issue: GUI window does not appear**

Solution: Check that you're running the script in an environment that supports GUI applications. Some headless servers may not support GUI applications.

**Issue: Currency conversion seems incorrect**

Solution: Update the currency rates in `currency_rates.json` with current exchange rates. Rates are relative to USD (1.0).

**Issue: "Invalid JSON in rates file"**

Solution: Validate your JSON syntax. Ensure proper formatting and that all rates are numeric values.

### Error Messages

All errors are logged to both the console and `logs/converter.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `converter.log`: Main log file with all operations and errors

## Updating Currency Rates

### Manual Update

Edit `currency_rates.json` with current exchange rates:

```json
{
  "USD": 1.0,
  "EUR": 0.92,
  "GBP": 0.79
}
```

### Using an API (Future Enhancement)

You can extend the application to fetch rates from an API:

```python
import requests

def fetch_currency_rates():
    response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
    return response.json()["rates"]
```

## Performance Considerations

- The GUI application is lightweight and responsive
- Conversions are performed in real-time as you type
- Currency rates are loaded once at startup
- No network requests are made during normal operation

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes following the code style guidelines
4. Write or update tests
5. Ensure all tests pass: `pytest tests/`
6. Commit your changes with conventional commit messages
7. Push to your branch and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable and function names
- Keep functions focused on a single responsibility

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Follow conventional commit message format
4. Request review from maintainers

## License

This project is provided as-is for educational and automation purposes.
