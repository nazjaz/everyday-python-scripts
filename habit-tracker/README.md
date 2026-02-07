# Habit Tracker

A GUI application for tracking daily habits, viewing streaks, and generating weekly progress reports. Built with tkinter for cross-platform compatibility, featuring data persistence, streak calculation, and comprehensive reporting.

## Project Description

Habit Tracker solves the problem of maintaining consistency in daily habits by providing an intuitive graphical interface to log habit completion, track streaks, and monitor progress over time. It helps users build and maintain positive habits through visual feedback and progress tracking.

**Target Audience**: Individuals who want to track daily habits, build consistency, and monitor their progress with a simple, local application.

## Features

- **GUI Interface**: User-friendly graphical interface built with tkinter
- **Habit Management**: Add, remove, and manage multiple habits
- **Daily Logging**: Log habit completion for any day
- **Streak Tracking**: Automatic calculation of current streak for each habit
- **Weekly Reports**: View completion statistics for the current week
- **Report Export**: Export weekly reports to text files
- **Data Persistence**: Automatic saving of habit data to JSON file
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
cd /path/to/everyday-python-scripts/habit-tracker
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

Edit `config.yaml` if you want to customize data file location or window size:

```yaml
data_file: data/habits.json
window_size: "800x600"
```

## Usage

### Basic Usage

Launch the habit tracker:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml
```

### Using the Application

1. **Add a Habit**:
   - Enter habit name in "Habit Name" field
   - Optionally enter description
   - Click "Add Habit"

2. **Log Habit Completion**:
   - Select a habit from the list
   - Click "Log Today" to mark it as completed for today
   - Click "Unlog Today" to remove today's log

3. **View Statistics**:
   - Select a habit to view its current streak
   - Streak is displayed automatically when a habit is selected

4. **View Weekly Report**:
   - Select a habit
   - Click "View Weekly Report" to see completion statistics for the current week

5. **Export Report**:
   - Select a habit
   - Click "Export Report" to save a weekly report to a text file

## Project Structure

```
habit-tracker/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py         # Package initialization
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── data/
│   └── habits.json         # Habit data storage (created automatically)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: GUI application, data management, and report generation
- **config.yaml**: YAML configuration file with settings
- **data/habits.json**: JSON file storing all habit data (created automatically)
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Data Storage

Habit data is stored in JSON format in the `data/habits.json` file. The structure is:

```json
{
  "habits": {
    "Exercise": {
      "description": "Daily exercise routine",
      "entries": {
        "2024-01-15": true,
        "2024-01-16": true,
        "2024-01-17": true
      },
      "created": "2024-01-15T10:00:00"
    }
  },
  "last_updated": "2024-01-17T15:30:00"
}
```

## Streak Calculation

Streaks are calculated by counting consecutive days from today backwards. For example:
- If you logged today, yesterday, and the day before: streak = 3
- If you missed yesterday but logged today: streak = 1
- If you haven't logged today: streak = 0

## Weekly Reports

Weekly reports show statistics for the current week (Monday to Sunday):
- Number of days completed
- Total days in week (7)
- Completion percentage
- Current streak
- Week period dates

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Habit data management (add, remove, log)
- Streak calculation
- Weekly statistics
- Data persistence
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'tkinter'`

**Solution**: Install tkinter for your system (see Prerequisites section above).

---

**Issue**: GUI window doesn't appear

**Solution**: 
- Check that Python has tkinter support
- Try running from terminal to see error messages
- Check logs in `logs/habit_tracker.log`

---

**Issue**: Data not saving

**Solution**:
- Check write permissions for `data/` directory
- Verify `data/` directory exists
- Check logs for error messages

---

**Issue**: Streak calculation seems incorrect

**Solution**:
- Streaks are calculated from today backwards
- Missing a day breaks the streak
- Future dates are ignored in streak calculation

### Error Messages

- **"tkinter is not available"**: Install tkinter for your Python distribution
- **"Please select a habit"**: Select a habit from the list before performing actions
- **"Habit already exists"**: Choose a different name for the habit
- **"Failed to export report"**: Check file permissions and disk space

## Tips for Best Results

1. **Be Consistent**: Log habits daily to maintain accurate streaks
2. **Use Descriptions**: Add descriptions to remember what each habit means
3. **Review Weekly**: Use weekly reports to track progress over time
4. **Export Reports**: Save reports periodically to track long-term progress
5. **Backup Data**: Periodically backup `data/habits.json` file

## Future Enhancements

Potential features for future versions:
- Calendar view of habit completion
- Multiple habit categories
- Customizable week start day
- Monthly and yearly reports
- Habit reminders/notifications
- Data visualization charts
- Import/export functionality

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov pytest-mock`
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
