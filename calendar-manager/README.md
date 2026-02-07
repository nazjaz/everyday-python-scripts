# Calendar Manager

Manage a local calendar system using iCal files. Add events, view schedules, and receive reminders via desktop notifications. All data is stored locally in standard iCal format.

## Project Description

Calendar Manager solves the problem of managing personal calendars without relying on cloud services or external APIs. It provides a local calendar system using the standard iCal file format, allowing users to add events, view their schedule, and receive desktop notifications for reminders.

**Target Audience**: Users who want a simple, local calendar application with reminder functionality, without cloud dependencies.

## Features

- **iCal File Support**: Store calendar data in standard iCal (.ics) format
- **Event Management**: Add, view, and delete calendar events
- **Schedule Viewing**: View all events in chronological order
- **Desktop Reminders**: Receive desktop notifications before events
- **Configurable Reminders**: Set reminder times (5, 10, 15, 30, 60 minutes before)
- **Event Details**: Store title, description, location, start/end times
- **Automatic Backups**: Calendar file is automatically backed up before modifications
- **No Cloud Required**: All data stored locally
- **Standard Format**: iCal files can be imported into other calendar applications

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- tkinter (usually included with Python, may need separate installation on Linux)

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
cd /path/to/everyday-python-scripts/calendar-manager
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

**Note**: `tkcalendar` is optional. If installation fails, the application will use a text input for dates instead.

### Step 4: Configure Settings (Optional)

1. Copy the example environment file (if needed):
   ```bash
   cp .env.example .env
   ```

2. Edit `config.yaml` to customize:
   - Calendar file location
   - Reminder settings
   - Default event duration
   - Notification settings

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **calendar**: Calendar file path and backup settings
- **reminders**: Reminder check interval and default reminder times
- **notifications**: Desktop notification settings
- **display**: View preferences
- **event_defaults**: Default event duration and reminder time

### Environment Variables

Optional environment variables can override config.yaml settings:

- `CALENDAR_FILE`: Override calendar file path
- `REMINDER_CHECK_INTERVAL`: Override reminder check interval in seconds
- `NOTIFICATIONS_ENABLED`: Enable/disable notifications (true/false)

### Example Configuration

```yaml
calendar:
  file: data/calendar.ics
  backup_enabled: true

reminders:
  enabled: true
  check_interval: 60
  default_reminder_minutes: 15

event_defaults:
  duration_minutes: 60
  reminder_minutes: 15
```

## Usage

### Basic Usage

Launch the calendar application:

```bash
python src/main.py
```

The GUI window will open with:
- **Event List**: Left panel showing all events in chronological order
- **Event Details**: Right panel showing details of selected event
- **Add Event Button**: Create new calendar events
- **Delete Button**: Remove selected events
- **Refresh Button**: Reload calendar from file

### Adding Events

1. Click "Add Event" button
2. Fill in the form:
   - **Title**: Event title (required)
   - **Start Date**: Date picker or YYYY-MM-DD format
   - **Start Time**: Time in HH:MM format
   - **Duration**: Duration in minutes (default: 60)
   - **Location**: Event location (optional)
   - **Description**: Event description (optional)
   - **Reminder**: Minutes before event to remind (default: 15)
3. Click "Save"

### Viewing Events

- Events are displayed in chronological order in the left panel
- Click an event to view details in the right panel
- Events show date, time, and title in the list

### Deleting Events

1. Select an event from the list
2. Click "Delete" button
3. Confirm deletion

### Reminders

- Reminders are automatically checked every minute (configurable)
- Desktop notifications appear at the configured time before events
- Reminders are sent once per event
- Past events do not trigger reminders (configurable)

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml
```

## Project Structure

```
calendar-manager/
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
│   └── calendar.ics        # Calendar file (created automatically)
├── backups/                 # Calendar backups (created automatically)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Calendar management, iCal file handling, event CRUD, reminders, and GUI
- **config.yaml**: YAML configuration file with calendar and reminder settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/calendar.ics**: iCal format calendar file storing all events
- **backups/**: Automatic backups of calendar file before modifications
- **logs/calendar_manager.log**: Application log file with rotation

## iCal File Format

The calendar uses the standard iCal (.ics) format, which means:

- **Compatible**: Can be imported into Google Calendar, Apple Calendar, Outlook, etc.
- **Portable**: Calendar file can be moved between systems
- **Standard**: Follows RFC 5545 iCalendar specification
- **Readable**: Can be opened in text editors to view raw data

### Importing to Other Applications

1. Locate your calendar file: `data/calendar.ics`
2. Import into your calendar application:
   - **Google Calendar**: Settings → Import & Export → Import
   - **Apple Calendar**: File → Import
   - **Outlook**: File → Open & Export → Import/Export

## Reminder System

The reminder system:

1. **Checks Periodically**: Checks for upcoming events every minute (configurable)
2. **Calculates Reminder Time**: Event start time minus reminder minutes
3. **Sends Notification**: Desktop notification when reminder time arrives
4. **One-Time Reminders**: Each event triggers reminder only once
5. **Automatic Cleanup**: Removes old reminders from tracking

### Reminder Configuration

- **Check Interval**: How often to check for reminders (default: 60 seconds)
- **Default Reminder**: Default reminder time for new events (default: 15 minutes)
- **Reminder Options**: Available reminder times (5, 10, 15, 30, 60 minutes)

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
- Calendar file loading and saving
- Event creation and deletion
- Event retrieval by date
- Reminder checking
- iCal file format handling

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named '_tkinter'`

**Solution**: Install tkinter for your system:
- Linux: `sudo apt-get install python3-tk` (Ubuntu/Debian) or `sudo dnf install python3-tkinter` (Fedora)
- macOS/Windows: Usually included, reinstall Python if missing

---

**Issue**: `ModuleNotFoundError: No module named 'tkcalendar'`

**Solution**: 
- Install tkcalendar: `pip install tkcalendar`
- Or use text input for dates (application will work without it)
- Date format: YYYY-MM-DD (e.g., 2024-02-07)

---

**Issue**: Reminders not working

**Solution**: 
- Check that reminders are enabled in config.yaml
- Verify notifications are enabled
- Check that reminder check interval is appropriate
- Ensure events have valid start times
- Check logs for errors

---

**Issue**: Events not saving

**Solution**: 
- Check calendar file path permissions
- Ensure data directory exists and is writable
- Check logs for save errors
- Verify backup directory is writable

---

**Issue**: Calendar file corrupted

**Solution**: 
- Check backups directory for previous versions
- Restore from most recent backup
- Verify iCal file format is valid
- Check logs for parsing errors

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Calendar file not found"**: Calendar file will be created automatically
- **"Invalid input"**: Check date/time format in add event dialog
- **"tkinter not available"**: Install tkinter package for your system

## Backup System

The application automatically creates backups:

- **Before Modifications**: Backup created before saving changes
- **Timestamped**: Each backup has a timestamp in filename
- **Configurable Count**: Keep specified number of backups (default: 5)
- **Automatic Cleanup**: Old backups are automatically removed

Backup location: `backups/calendar_YYYYMMDD_HHMMSS.ics.bak`

## Privacy and Data

- **Local Storage**: All data stored locally in iCal file
- **No Cloud**: No data sent to external services
- **No Tracking**: Application does not track usage
- **Standard Format**: Uses open iCal standard
- **Portable**: Calendar file can be moved/copied freely

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
