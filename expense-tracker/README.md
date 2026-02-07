# Expense Tracker

A GUI application for tracking expenses by category, viewing spending summaries, and exporting expense data to CSV. Built with tkinter for cross-platform compatibility, featuring data persistence, category-based organization, and comprehensive reporting.

## Project Description

Expense Tracker solves the problem of personal finance management by providing an intuitive graphical interface to log expenses, categorize spending, and monitor financial habits over time. It helps users track where their money goes through visual summaries and detailed expense records.

**Target Audience**: Individuals who want to track personal expenses, monitor spending by category, and maintain a simple, local expense log without relying on cloud services or complex financial software.

## Features

- **GUI Interface**: User-friendly graphical interface built with tkinter
- **Expense Logging**: Add expenses with category, amount, description, and date
- **Category Management**: Predefined categories with ability to add custom ones
- **Spending Summary**: View total spending grouped by category
- **Recent Expenses**: Display all expenses in chronological order
- **CSV Export**: Export all expense data to CSV for external analysis
- **Data Persistence**: Automatic saving of expense data to JSON file
- **Date Tracking**: Track expenses by date with automatic today's date
- **Cross-platform**: Works on Windows, macOS, and Linux
- **No Internet Required**: All data stored locally

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- tkinter (usually included with Python, but may need separate installation on Linux)

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
cd /path/to/everyday-python-scripts/expense-tracker
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

Edit `config.yaml` if you want to customize data file location, window size, or categories:

```yaml
data_file: data/expenses.json
window_size: "900x700"
categories:
  - Food
  - Transportation
  - Entertainment
  - Shopping
  - Bills
  - Healthcare
  - Education
  - Other
```

## Usage

### Basic Usage

Launch the expense tracker:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml
```

### Using the Application

1. **Add an Expense**:
   - Select a category from the dropdown (or type a custom category)
   - Enter the amount in dollars
   - Optionally enter a description
   - Optionally change the date (defaults to today)
   - Click "Add Expense"

2. **View Spending Summary**:
   - The "Spending Summary" section automatically displays totals by category
   - Categories are sorted by amount (highest first)
   - Total spending is shown at the bottom

3. **View Recent Expenses**:
   - The "Recent Expenses" section shows all expenses
   - Expenses are sorted by date (most recent first)
   - Displays ID, Date, Category, Amount, and Description

4. **Export to CSV**:
   - Click "Export to CSV" button
   - Choose a location and filename
   - All expenses will be exported with columns: ID, Category, Amount, Description, Date

5. **Refresh Data**:
   - Click "Refresh" button to reload the display
   - Useful if data is modified externally

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

- `data_file`: Path to JSON file storing expense data
- `window_size`: Initial window dimensions (e.g., "900x700")
- `categories`: List of default expense categories
- `logging`: Logging configuration (level, file, max_bytes, backup_count, format)

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `DATA_FILE_PATH`: Custom path to expense data file
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Project Structure

```
expense-tracker/
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
│   └── expenses.json        # Expense data (created at runtime)
└── logs/
    └── expense_tracker.log  # Application logs
```

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
- Expense data management (add, load, save)
- Category-based summaries
- Total spending calculations
- CSV export functionality
- Data persistence and loading

## Troubleshooting

### Application Won't Start

**Error: "tkinter is not available"**
- Install tkinter for your system (see Prerequisites section)
- On Linux, ensure python3-tk package is installed

**Error: "Configuration file not found"**
- Ensure `config.yaml` exists in the project root
- Use `-c` option to specify custom config path

### Data Issues

**Expenses Not Saving**
- Check file permissions on data directory
- Verify disk space is available
- Check logs for error messages

**Data File Corrupted**
- Backup the data file before making changes
- JSON syntax errors will be logged
- Application will start with empty data if file is corrupted

### Export Issues

**CSV Export Fails**
- Check write permissions on target directory
- Ensure sufficient disk space
- Verify file is not open in another application

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
