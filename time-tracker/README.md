# Time Tracker

A simple time tracking application with GUI that allows users to log time spent on different tasks and generate daily or weekly reports.

## Features

- **GUI Interface**: User-friendly graphical interface built with tkinter
- **Task Timer**: Start/stop timer for tracking time on tasks
- **Time Logging**: Log time entries with task names and durations
- **Real-time Display**: Live timer display showing elapsed time
- **Time Entries List**: View all logged time entries
- **Daily Reports**: Generate detailed daily time reports
- **Weekly Reports**: Generate weekly time reports with summaries
- **Task Summary**: View total time spent per task
- **Daily Summary**: See total time logged today
- **Data Persistence**: Time entries saved to JSON format
- **Entry Management**: Delete time entries

## Prerequisites

- Python 3.8 or higher
- pip package manager
- tkinter (usually included with Python, but may need separate installation on Linux)

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
cd time-tracker
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

- **app**: Application settings (title, window size)
- **data**: Data storage directory
- **logging**: Logging configuration

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

1. **Start Timer**:
   - Enter task name in the "Task Name" field
   - Click "Start" button
   - Timer begins counting

2. **Stop Timer**:
   - Click "Stop" button to pause timer
   - Timer display freezes at current elapsed time

3. **Log Entry**:
   - With timer running, click "Log Entry"
   - Time entry is saved with task name and duration
   - Timer resets and stops

4. **Clear Timer**:
   - Click "Clear" to reset timer without logging
   - Clears task name field

5. **View Entries**:
   - All logged entries appear in the list
   - Sorted by most recent first
   - Shows date, time, duration, and task name

6. **Generate Reports**:
   - File > Generate Daily Report: Creates report for today
   - File > Generate Weekly Report: Creates report for current week

7. **Delete Entry**:
   - Select entry from list
   - Edit > Delete Selected Entry

## Project Structure

```
time-tracker/
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
│   └── time_entries.json
└── logs/
    └── .gitkeep
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file
- `data/time_entries.json`: Time entries storage (auto-generated)
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory

## GUI Layout

- **Current Task Display**: Shows active task name
- **Timer Display**: Large display showing elapsed time (HH:MM:SS)
- **Task Input**: Text field for entering task name
- **Control Buttons**: Start, Stop, Log Entry, Clear
- **Time Entries List**: Scrollable list of all logged entries
- **Summary**: Total time logged today
- **Status Bar**: Current application status

## Data Storage

Time entries are stored in `data/time_entries.json` with the following structure:

```json
[
  {
    "task": "Project Development",
    "duration_seconds": 3600,
    "date": "2024-02-07",
    "time": "10:30:00",
    "timestamp": "2024-02-07T10:30:00"
  }
]
```

## Reports

### Daily Report

Includes:
- Task summary with total time per task
- Percentage breakdown by task
- Total time for the day
- Detailed entries with timestamps

### Weekly Report

Includes:
- Task summary for the week
- Total time for the week
- Daily breakdown showing time per day
- Percentage breakdown by task

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
pytest tests/test_main.py::test_start_timer
```

## Troubleshooting

### Common Issues

**Application won't start:**
- Verify Python version is 3.8 or higher
- Check that tkinter is installed
- Ensure all dependencies are installed

**Timer not updating:**
- Check that timer is actually started
- Verify system time is correct
- Restart application if timer appears frozen

**Entries not saving:**
- Check write permissions for data directory
- Verify disk space is available
- Check logs for error messages

**Reports not generating:**
- Verify file save dialog permissions
- Check write permissions for save location
- Ensure valid file path is selected

### Error Messages

The tool provides detailed error messages in logs. Check `logs/time_tracker.log` for:
- Application errors
- Data loading/saving issues
- Timer problems

## Use Cases

**Project time tracking:**
- Track time spent on different project tasks
- Generate weekly reports for client billing
- Monitor time distribution across activities

**Personal productivity:**
- Track time spent on hobbies
- Monitor study time
- Analyze time usage patterns

**Work time logging:**
- Log hours worked on different projects
- Generate daily time sheets
- Track billable hours

## Keyboard Shortcuts

- **Enter**: Start timer (when task field is focused)
- **Escape**: Stop timer (if implemented)

## Limitations

- Single active timer at a time
- No task categories or tags
- No export to CSV/Excel (text reports only)
- No time tracking history beyond entries
- No reminders or notifications

## Future Enhancements

Potential improvements:
- Multiple concurrent timers
- Task categories and tags
- Export to CSV/Excel formats
- Time tracking charts and graphs
- Reminders and notifications
- Project/client organization
- Time estimates vs actual
- Dark mode theme
- Keyboard shortcuts

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
