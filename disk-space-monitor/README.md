# Disk Space Monitor

Monitor disk space usage across all drives and generate desktop alerts when free space falls below configured thresholds. Includes cleanup suggestions to help free up disk space. Cross-platform support for Windows, macOS, and Linux.

## Project Description

Disk Space Monitor solves the problem of running out of disk space unexpectedly by continuously monitoring all drives and alerting users when space is running low. It provides actionable cleanup suggestions including large file locations and system-specific cache directories. Perfect for servers, workstations, and any system where disk space management is critical.

**Target Audience**: System administrators, developers, and users who need proactive disk space monitoring and management.

## Features

- **Multi-Drive Monitoring**: Automatically detects and monitors all drives/partitions
- **Desktop Alerts**: Cross-platform desktop notifications (Windows, macOS, Linux)
- **Configurable Thresholds**: Set warning and critical thresholds (default: 20% and 10%)
- **Cleanup Suggestions**: Identifies large files and suggests system-specific cleanup locations
- **Alert Cooldown**: Prevents notification spam with configurable cooldown period
- **Watch Mode**: Continuous monitoring with periodic checks
- **Large File Detection**: Finds and reports large files consuming disk space
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Comprehensive Logging**: Detailed logs of all monitoring activities

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Desktop notification support (varies by platform)

### Platform-Specific Requirements

**Windows**:
- Windows 10 or later for toast notifications (optional: install `win10toast` for better notifications)

**macOS**:
- No additional requirements (uses built-in `osascript`)

**Linux**:
- `notify-send` command (usually included with desktop environments)
- Install with: `sudo apt-get install libnotify-bin` (Ubuntu/Debian)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/disk-space-monitor
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

**Note**: `win10toast` is optional on Windows. If you prefer native Windows notifications, you can skip this dependency.

### Step 4: Configure Settings (Optional)

Edit `config.yaml` to customize thresholds:

```yaml
thresholds:
  warning: 20.0
  critical: 10.0
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **thresholds**: Disk space alert thresholds
  - **warning**: Percentage threshold for warning alerts (default: 20%)
  - **critical**: Percentage threshold for critical alerts (default: 10%)
- **alert_cooldown_minutes**: Minutes between alerts for same drive (default: 60)
- **large_files**: Settings for large file detection
  - **min_size_mb**: Minimum file size to consider "large" (default: 100 MB)
  - **max_results**: Maximum large files to report (default: 10)
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `WARNING_THRESHOLD`: Override warning threshold percentage
- `CRITICAL_THRESHOLD`: Override critical threshold percentage

### Example Configuration

```yaml
thresholds:
  warning: 25.0
  critical: 15.0

alert_cooldown_minutes: 30

large_files:
  min_size_mb: 50
  max_results: 5
```

## Usage

### Basic Usage

Check disk space once and send alerts if needed:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Run in watch mode (continuous monitoring)
python src/main.py --watch

# Set custom check interval for watch mode (in seconds)
python src/main.py --watch --interval 1800

# Combine options
python src/main.py -c config.yaml --watch --interval 3600
```

### Common Use Cases

1. **One-Time Check**:
   ```bash
   python src/main.py
   ```
   Check all drives once and send alerts if thresholds are exceeded.

2. **Continuous Monitoring**:
   ```bash
   python src/main.py --watch
   ```
   Monitor drives continuously, checking every hour (default).

3. **Custom Check Interval**:
   ```bash
   python src/main.py --watch --interval 1800
   ```
   Check every 30 minutes (1800 seconds).

4. **Server Monitoring**:
   - Run as a background service or cron job
   - Set appropriate thresholds for your needs
   - Review logs regularly

## Project Structure

```
disk-space-monitor/
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
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core monitoring logic, alert generation, and cleanup suggestions
- **config.yaml**: YAML configuration file with thresholds and settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Alert Levels

The monitor uses two alert levels:

- **Warning**: Triggered when free space falls below warning threshold (default: 20%)
- **Critical**: Triggered when free space falls below critical threshold (default: 10%)

Alerts include:
- Current free space percentage
- Free space in human-readable format
- Total disk capacity
- Cleanup suggestions (large files, cache locations)

## Cleanup Suggestions

The monitor provides platform-specific cleanup suggestions:

**Windows**:
- Windows Temp folder
- Recycle Bin
- Browser cache

**macOS**:
- ~/Library/Caches
- ~/.Trash
- Browser cache

**Linux**:
- /tmp directory
- ~/.cache
- Package cache (apt/yum)

Additionally, it identifies large files (configurable minimum size) that may be candidates for deletion or archiving.

## Desktop Notifications

Notifications are sent using platform-native methods:

- **Windows**: Toast notifications (Windows 10+) or PowerShell notifications
- **macOS**: Native macOS notifications via `osascript`
- **Linux**: `notify-send` command (requires desktop environment)

## Watch Mode

Watch mode runs the monitor continuously, checking disk space at regular intervals:

- Default interval: 3600 seconds (1 hour)
- Customizable via `--interval` option
- Stops with Ctrl+C
- Useful for long-running monitoring

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
- Disk usage calculation
- Alert level determination
- Drive detection
- Notification sending
- Cleanup suggestion generation
- Error handling

## Troubleshooting

### Common Issues

**Issue**: Desktop notifications not appearing

**Solution**:
- **Windows**: Ensure Windows 10+ or install `win10toast` package
- **macOS**: Check notification permissions in System Preferences
- **Linux**: Install `libnotify-bin` package and ensure desktop environment is running

---

**Issue**: `PermissionError` when checking drives

**Solution**: Some system drives may require elevated permissions. The script will skip inaccessible drives and log warnings.

---

**Issue**: Too many notifications

**Solution**: 
- Increase `alert_cooldown_minutes` in config
- Adjust thresholds to be less sensitive
- Check that cooldown mechanism is working (review logs)

---

**Issue**: Large file detection is slow

**Solution**:
- Increase `min_size_mb` to scan fewer files
- Reduce `max_results` to limit search
- The scan stops after finding enough large files

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Error getting disk usage"**: Drive may be inaccessible or unmounted
- **"Error sending desktop notification"**: Check platform-specific notification requirements

## Running as a Service

### Linux (systemd)

Create a service file `/etc/systemd/system/disk-monitor.service`:

```ini
[Unit]
Description=Disk Space Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/disk-space-monitor
ExecStart=/path/to/venv/bin/python src/main.py --watch --interval 3600
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable disk-monitor
sudo systemctl start disk-monitor
```

### macOS (launchd)

Create a plist file `~/Library/LaunchAgents/com.diskmonitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.diskmonitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/disk-space-monitor/src/main.py</string>
        <string>--watch</string>
        <string>--interval</string>
        <string>3600</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load with:
```bash
launchctl load ~/Library/LaunchAgents/com.diskmonitor.plist
```

### Windows (Task Scheduler)

Create a scheduled task that runs:
```
python.exe "C:\path\to\disk-space-monitor\src\main.py" --watch --interval 3600
```

Set to run at startup and repeat every hour.

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
