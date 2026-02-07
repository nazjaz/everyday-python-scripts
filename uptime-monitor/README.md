# Uptime Monitor

Monitor system uptime and log system boot times, shutdown events, and session durations to a local database. This tool helps track system usage patterns, identify boot/shutdown events, and analyze session durations.

## Project Description

Uptime Monitor solves the problem of tracking system uptime and boot/shutdown events by automatically detecting system boot times, monitoring uptime, detecting shutdown events on next boot, and storing all information in a local SQLite database. This provides a historical record of system usage and helps identify patterns.

**Target Audience**: System administrators, developers, users tracking system usage, and anyone who needs to monitor and log system boot/shutdown events.

## Features

- **Boot Time Detection**: Automatically detect and log system boot times
- **Uptime Monitoring**: Track current system uptime
- **Shutdown Event Detection**: Detect and log shutdown events on next boot
- **Session Duration Tracking**: Calculate and store session durations
- **Cross-Platform Support**: Works on Windows, Linux, and macOS
- **Continuous Monitoring**: Optional continuous monitoring mode
- **Historical Data**: Store boot and shutdown history in database
- **Statistics**: Generate statistics on boot events and session durations
- **Automatic Cleanup**: Clean up old uptime snapshots based on retention policy
- **Comprehensive Logging**: Log all operations for audit and debugging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- System access to query boot time and uptime information

**Optional**: For better cross-platform support, install psutil:
```bash
pip install psutil
```

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/uptime-monitor
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

### Step 4: Configure Settings

Edit `config.yaml` to customize monitoring settings:

```yaml
monitoring:
  interval: 300  # Check every 5 minutes
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **database**: SQLite database file path and table creation settings
- **monitoring**: Monitoring interval and snapshot logging settings
- **retention**: Data retention policy for old entries
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_FILE`: Override database file path
- `MONITORING_INTERVAL`: Override monitoring interval in seconds

### Example Configuration

```yaml
database:
  file: "data/uptime.db"
  create_tables: true

monitoring:
  interval: 300  # 5 minutes
  log_snapshots: true

retention:
  auto_cleanup: true
  days_to_keep: 90
```

## Usage

### Basic Usage

Check and log current system state:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Check and log current state
python src/main.py --check

# Monitor continuously
python src/main.py --monitor

# Show boot history
python src/main.py --boot-history 10

# Show shutdown history
python src/main.py --shutdown-history 10

# Show statistics
python src/main.py --stats

# Combine options
python src/main.py --check --stats
```

### Common Use Cases

1. **Check Current Uptime**:
   ```bash
   python src/main.py --check
   ```

2. **Monitor Continuously**:
   ```bash
   python src/main.py --monitor
   ```

3. **View Boot History**:
   ```bash
   python src/main.py --boot-history 20
   ```

4. **View Shutdown History**:
   ```bash
   python src/main.py --shutdown-history 20
   ```

5. **View Statistics**:
   ```bash
   python src/main.py --stats
   ```

## Project Structure

```
uptime-monitor/
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
│   └── API.md              # API documentation
├── data/
│   └── uptime.db           # SQLite database (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    └── uptime_monitor.log  # Application logs
```

### File Descriptions

- **src/main.py**: Core uptime monitoring, boot/shutdown detection, and database operations
- **config.yaml**: YAML configuration file with monitoring settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/uptime.db**: SQLite database storing boot events, shutdown events, and snapshots
- **logs/uptime_monitor.log**: Application log file with rotation

## Database Schema

The SQLite database contains three main tables:

### boot_events
- `id`: Primary key
- `boot_time`: Boot time (ISO format)
- `detected_at`: When boot event was detected
- `uptime_seconds`: Uptime at detection (seconds)
- `system_info`: System information string

### shutdown_events
- `id`: Primary key
- `session_start_time`: Boot time that started the session
- `shutdown_time`: When system was shut down/rebooted
- `session_duration_seconds`: Duration of the session
- `detected_at`: When shutdown event was detected

### uptime_snapshots
- `id`: Primary key
- `timestamp`: Snapshot timestamp (ISO format)
- `uptime_seconds`: Uptime at snapshot (seconds)
- `boot_time`: Boot time (ISO format)
- `system_info`: System information string

## How It Works

### Boot Time Detection

The tool detects boot time using platform-specific methods:

- **Windows**: Uses `wmic os get lastbootuptime`
- **macOS**: Uses `sysctl kern.boottime`
- **Linux**: Reads `/proc/uptime` and calculates boot time
- **Fallback**: Uses psutil library if available

### Shutdown Detection

Shutdown events are detected by comparing:
1. Last logged boot time in database
2. Current system boot time

If current boot time is newer than last logged boot time, a shutdown/reboot occurred.

### Session Duration

Session duration is calculated as the time between:
- Session start (boot time)
- Session end (next boot time / shutdown time)

## Platform Support

### Windows

- Uses WMI (Windows Management Instrumentation) to get boot time
- Requires `wmic` command (available on Windows XP+)

### Linux

- Reads `/proc/uptime` for uptime information
- Calculates boot time from current time minus uptime

### macOS

- Uses `sysctl kern.boottime` to get boot time
- Provides accurate boot time information

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
- Boot time detection
- Uptime calculation
- Database operations
- Shutdown detection
- Statistics generation
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Configuration file not found`

**Solution**: Ensure `config.yaml` exists or provide correct path with `-c` option.

---

**Issue**: Cannot detect boot time

**Solution**: 
- On Windows, ensure `wmic` command is available
- On Linux, ensure `/proc/uptime` is readable
- On macOS, ensure `sysctl` command is available
- Install psutil for better cross-platform support: `pip install psutil`

---

**Issue**: Permission denied errors

**Solution**: 
- Ensure you have read access to system information
- Some operations may require appropriate permissions
- Check logs for specific permission errors

---

**Issue**: Shutdown events not detected

**Solution**: 
- Shutdown events are detected on next boot
- Ensure tool runs after system boot to detect previous shutdown
- Check that boot events are being logged correctly

---

**Issue**: Database locked errors

**Solution**: 
- Ensure only one instance of monitor is running
- Check database file permissions
- Close any database viewers that might have the file open

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Cannot determine boot time"**: System-specific method failed, try installing psutil
- **"Database error"**: Check database file permissions and disk space

## Automation

You can automate the monitor using system services:

### Linux (systemd)

Create `/etc/systemd/system/uptime-monitor.service`:

```ini
[Unit]
Description=Uptime Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/uptime-monitor
ExecStart=/path/to/venv/bin/python src/main.py --monitor
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable uptime-monitor
sudo systemctl start uptime-monitor
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.uptimemonitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.uptimemonitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/uptime-monitor/src/main.py</string>
        <string>--monitor</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/uptime-monitor</string>
</dict>
</plist>
```

Load service:
```bash
launchctl load ~/Library/LaunchAgents/com.uptimemonitor.plist
```

### Windows (Task Scheduler)

- Create a task to run `python src/main.py --monitor`
- Set trigger to "At startup"
- Set action to start program
- Use full path to Python executable

## Security Considerations

- **Database Access**: Database file contains system information - ensure appropriate permissions
- **System Information**: Tool queries system information - requires appropriate access
- **Continuous Monitoring**: Running as service requires appropriate user permissions
- **Data Privacy**: Boot/shutdown data may reveal usage patterns

## Use Cases

1. **System Usage Tracking**: Track how often system is booted and session durations
2. **Troubleshooting**: Identify unexpected reboots or shutdowns
3. **Compliance**: Maintain logs of system usage for compliance
4. **Analysis**: Analyze system usage patterns over time
5. **Monitoring**: Monitor system stability and uptime

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
