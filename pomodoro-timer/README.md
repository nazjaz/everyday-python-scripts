# Pomodoro Timer

A custom Pomodoro timer application with a graphical user interface, featuring work and break intervals, session tracking, and productivity statistics. Improve your focus and productivity using the Pomodoro Technique.

## Project Description

Pomodoro Timer implements the Pomodoro Technique, a time management method that uses a timer to break work into intervals (typically 25 minutes) separated by short breaks. This application provides a beautiful GUI, tracks your sessions, and generates productivity statistics to help you maintain focus and measure your work patterns.

**Target Audience**: Students, professionals, and anyone who wants to improve focus and productivity using the Pomodoro Technique.

## Features

- **Graphical User Interface**: Clean, modern GUI built with tkinter
- **Work and Break Intervals**: Configurable work (25 min), short break (5 min), and long break (15 min) intervals
- **Session Tracking**: Automatically tracks completed work and break sessions
- **Productivity Statistics**: Daily and total statistics including:
  - Sessions completed
  - Total work time
  - Total break time
  - Daily progress tracking
- **Smart Break Scheduling**: Automatically switches to long break after 4 work sessions
- **Desktop Notifications**: Notifications when timer completes (optional)
- **Sound Alerts**: System beep when timer completes
- **Session Management**: Start, pause, reset, and skip session controls
- **Persistent Storage**: SQLite database stores all session history

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
cd /path/to/everyday-python-scripts/pomodoro-timer
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

2. Edit `config.yaml` to customize timer intervals:
   ```yaml
   intervals:
     work: 1500  # 25 minutes in seconds
     short_break: 300  # 5 minutes
     long_break: 900  # 15 minutes
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **intervals**: Work, short break, and long break durations in seconds
- **database**: SQLite database file path for session storage
- **gui**: Window size, theme colors, and appearance
- **notifications**: Desktop and sound notification settings
- **statistics**: Statistics tracking options

### Environment Variables

Optional environment variables can override config.yaml settings:

- `WORK_INTERVAL`: Override work interval in seconds
- `SHORT_BREAK_INTERVAL`: Override short break interval in seconds
- `LONG_BREAK_INTERVAL`: Override long break interval in seconds

### Example Configuration

```yaml
intervals:
  work: 1500  # 25 minutes
  short_break: 300  # 5 minutes
  long_break: 900  # 15 minutes
  sessions_before_long_break: 4

notifications:
  enabled: true
  sound_on_complete: true
  desktop_notification: true
```

## Usage

### Basic Usage

Launch the timer application:

```bash
python src/main.py
```

The GUI window will open with:
- **Timer Display**: Large countdown timer showing remaining time
- **Mode Indicator**: Current mode (Work Session, Short Break, Long Break)
- **Control Buttons**: Start, Pause, Reset, Skip
- **Statistics Panel**: Daily and total productivity statistics

### Using the Timer

1. **Start Timer**: Click "Start" to begin countdown
2. **Pause Timer**: Click "Pause" to pause/resume (toggles)
3. **Reset Timer**: Click "Reset" to reset current session
4. **Skip Session**: Click "Skip" to move to next interval type

### Timer Flow

1. **Work Session** (25 minutes default)
   - Timer counts down from 25:00
   - When complete, automatically switches to break

2. **Short Break** (5 minutes default)
   - After 1-3 work sessions
   - Timer counts down from 5:00

3. **Long Break** (15 minutes default)
   - After every 4 work sessions
   - Timer counts down from 15:00

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml
```

## Project Structure

```
pomodoro-timer/
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
│   └── pomodoro_sessions.db  # SQLite database (created automatically)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: GUI application, timer logic, session tracking, and statistics
- **config.yaml**: YAML configuration file with intervals and settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/pomodoro_sessions.db**: SQLite database storing all sessions
- **logs/pomodoro_timer.log**: Application log file with rotation

## Database Schema

The SQLite database contains two main tables:

### sessions
- `id`: Primary key (auto-increment)
- `session_type`: Type of session (work, short_break, long_break)
- `duration`: Session duration in seconds
- `completed_at`: Completion timestamp
- `date`: Date of session (YYYY-MM-DD)

### daily_stats
- `id`: Primary key
- `date`: Date (YYYY-MM-DD, unique)
- `sessions_completed`: Number of work sessions completed
- `work_time_seconds`: Total work time in seconds
- `break_time_seconds`: Total break time in seconds

## Statistics

The application tracks and displays:

- **Today's Statistics**:
  - Number of sessions completed today
  - Total work time today (in minutes)

- **Total Statistics**:
  - Total sessions completed (all time)
  - Total work time (all time, in minutes)

Statistics are automatically updated when sessions complete and persist across application restarts.

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
- Timer initialization
- Time formatting
- Mode switching
- Session saving
- Statistics loading
- Database operations

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named '_tkinter'`

**Solution**: Install tkinter for your system:
- Linux: `sudo apt-get install python3-tk` (Ubuntu/Debian) or `sudo dnf install python3-tkinter` (Fedora)
- macOS/Windows: Usually included, reinstall Python if missing

---

**Issue**: GUI window doesn't appear

**Solution**: 
- Check that tkinter is properly installed
- Verify Python version (3.8+)
- Check logs for error messages

---

**Issue**: Notifications not working

**Solution**: 
- Notifications are optional (plyer library)
- Application works without notifications
- Check that plyer is installed: `pip install plyer`
- On Linux, ensure notification daemon is running

---

**Issue**: Timer not counting down

**Solution**: 
- Ensure timer is started (click "Start" button)
- Check that timer is not paused
- Verify configuration intervals are valid numbers

---

**Issue**: Statistics not updating

**Solution**: 
- Statistics update when sessions complete (not when paused/reset)
- Ensure sessions are allowed to complete fully
- Check database file permissions

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Database error"**: Check database file permissions and disk space
- **"tkinter not available"**: Install tkinter package for your system

## Pomodoro Technique

The Pomodoro Technique is a time management method:

1. **Work for 25 minutes** (one Pomodoro)
2. **Take a 5-minute break**
3. **Repeat** for 4 Pomodoros
4. **Take a longer 15-30 minute break**

This application implements this technique with configurable intervals and automatic session tracking.

## Keyboard Shortcuts

Currently, the application uses mouse clicks for all controls. Future versions may include keyboard shortcuts.

## Productivity Tips

- **Focus During Work Sessions**: Avoid distractions during the 25-minute work period
- **Take Real Breaks**: Use break time to rest, not to check social media
- **Track Your Progress**: Review statistics to understand your work patterns
- **Adjust Intervals**: Customize intervals in config.yaml to match your needs
- **Build Consistency**: Use the timer daily to build productive habits

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
