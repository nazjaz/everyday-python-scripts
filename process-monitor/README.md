# Process Monitor

Monitor running processes and automatically kill processes that exceed CPU or memory usage limits. Includes logging, desktop notifications, and comprehensive reporting to help manage system resources.

## Project Description

Process Monitor solves the problem of runaway processes consuming excessive system resources. It continuously monitors all running processes, detects those exceeding configured CPU or memory thresholds, and automatically terminates them after a grace period, with full logging and notification support.

**Target Audience**: System administrators, developers, and users who need to automatically manage resource-intensive processes on their systems.

## ⚠️ WARNING

**This tool can kill processes, including important applications. Use with caution.**

- Always configure whitelist to protect critical system processes
- Test configuration thoroughly before running in production
- Monitor logs to ensure expected behavior
- May require elevated permissions on some systems

## Features

- **Process Monitoring**: Continuously monitor all running processes
- **CPU Usage Limits**: Detect and kill processes exceeding CPU usage thresholds
- **Memory Usage Limits**: Detect and kill processes exceeding memory usage thresholds
- **Configurable Thresholds**: Set warning and kill thresholds separately
- **Grace Period**: Processes must exceed limits for a duration before being killed
- **Whitelist Protection**: Protect critical processes from being killed
- **Desktop Notifications**: Get notified when processes are killed or exceed warnings
- **Comprehensive Logging**: Detailed logs of all monitoring activities
- **Statistics Tracking**: Track checks performed, warnings sent, and processes killed
- **Periodic Reports**: Generate reports with monitoring statistics

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Appropriate system permissions (may require sudo/administrator rights)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/process-monitor
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

1. Copy the example environment file (if needed):
   ```bash
   cp .env.example .env
   ```

2. **IMPORTANT**: Edit `config.yaml` to configure:
   - CPU and memory thresholds
   - Whitelist of processes to protect
   - Monitoring intervals
   - Notification settings

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **monitoring**: Monitoring interval and enable/disable
- **cpu**: CPU usage thresholds and check duration
- **memory**: Memory usage thresholds and check duration
- **whitelist**: Processes that should never be killed
- **notifications**: Desktop notification settings
- **logging**: Logging configuration

### Critical Configuration: Whitelist

**Always configure the whitelist** to protect important processes:

```yaml
whitelist:
  enabled: true
  process_names:
    - "kernel_task"
    - "WindowServer"
    - "loginwindow"
    - "SystemUIServer"
    - "Dock"
    - "Finder"
    - "python"  # Protect Python processes if needed
```

### Example Configuration

```yaml
cpu:
  enabled: true
  warning_threshold: 80.0  # Warn at 80%
  kill_threshold: 95.0  # Kill at 95%
  check_duration: 10  # Must exceed for 10 seconds

memory:
  enabled: true
  warning_threshold: 80.0  # Warn at 80%
  kill_threshold: 90.0  # Kill at 90%
  check_duration: 10  # Must exceed for 10 seconds
```

### Environment Variables

Optional environment variables can override config.yaml settings:

- `MONITORING_INTERVAL`: Override monitoring interval in seconds
- `CPU_KILL_THRESHOLD`: Override CPU kill threshold percentage
- `MEMORY_KILL_THRESHOLD`: Override memory kill threshold percentage
- `NOTIFICATIONS_ENABLED`: Enable/disable notifications (true/false)

## Usage

### Basic Usage

Start monitoring (runs until interrupted):

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Run as daemon (same as default)
python src/main.py -d
```

### Running with Elevated Permissions

On Linux/macOS, you may need sudo to kill processes:

```bash
sudo python src/main.py
```

**Note**: Be extra careful when running with elevated permissions. Ensure whitelist is properly configured.

### Stopping the Monitor

Press `Ctrl+C` to stop monitoring gracefully. The monitor will:
- Stop checking processes
- Generate a final report
- Display final statistics

## How It Works

1. **Monitoring Loop**: Checks all processes at configured intervals (default: 5 seconds)
2. **Resource Checking**: For each process:
   - Checks CPU usage percentage
   - Checks memory usage percentage
   - Compares against configured thresholds
3. **Warning Phase**: If process exceeds warning threshold:
   - Sends desktop notification (if enabled)
   - Logs warning
   - Tracks process
4. **Kill Phase**: If process exceeds kill threshold for required duration:
   - Attempts graceful termination (SIGTERM)
   - If still running, force kills (SIGKILL)
   - Logs the action
   - Sends notification
   - Updates statistics

## Project Structure

```
process-monitor/
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
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── process_monitor.log # Application logs
    └── process_monitor_report.txt  # Generated reports
```

### File Descriptions

- **src/main.py**: Process monitoring, resource checking, process killing, logging, and notifications
- **config.yaml**: YAML configuration file with thresholds and settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/process_monitor.log**: Application log file with rotation
- **logs/process_monitor_report.txt**: Periodic monitoring reports

## Monitoring Behavior

### CPU Monitoring

- Checks CPU usage percentage for each process
- Processes exceeding `kill_threshold` for `check_duration` seconds are killed
- Processes exceeding `warning_threshold` receive warnings

### Memory Monitoring

- Checks memory usage percentage (relative to total system memory)
- Optionally checks absolute memory limit (in MB)
- Processes exceeding limits for `check_duration` seconds are killed

### Grace Period

Processes must exceed kill thresholds for the configured `check_duration` (default: 10 seconds) before being killed. This prevents killing processes with temporary spikes.

## Statistics

The monitor tracks:

- **Checks Performed**: Total number of monitoring cycles
- **Processes Checked**: Total number of processes examined
- **Warnings Sent**: Number of warning notifications sent
- **Processes Killed**: Number of processes terminated
- **Killed Processes List**: Details of all killed processes

## Reports

Periodic reports are generated (default: every hour) containing:

- Monitoring statistics
- List of killed processes (last 50)
- Timestamps and resource usage details

Reports are saved to `logs/process_monitor_report.txt`.

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

**Note**: Tests use mocks and do not actually kill processes.

## Troubleshooting

### Common Issues

**Issue**: `PermissionError` when trying to kill processes

**Solution**: 
- Run with elevated permissions: `sudo python src/main.py`
- On Windows, run as Administrator
- Check that process is not protected by system

---

**Issue**: Important processes being killed

**Solution**: 
- Add process names to whitelist in `config.yaml`
- Check whitelist configuration is enabled
- Review logs to see which processes were killed

---

**Issue**: Too many notifications

**Solution**: 
- Adjust warning thresholds higher
- Disable notifications: `notifications.enabled: false`
- Increase monitoring interval

---

**Issue**: Processes not being killed when they should

**Solution**: 
- Check that kill thresholds are appropriate
- Verify `check_duration` is not too long
- Ensure monitoring is enabled: `monitoring.enabled: true`
- Check logs for errors

---

**Issue**: High CPU usage from monitor itself

**Solution**: 
- Increase monitoring interval
- Reduce number of processes checked (if possible)
- Check for infinite loops in logs

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Permission denied"**: Run with appropriate permissions (sudo/Administrator)
- **"Process not found"**: Process terminated between check and kill (normal, not an error)

## Security Considerations

- **Whitelist Critical Processes**: Always whitelist system processes and important applications
- **Test Configuration**: Test with non-critical processes first
- **Monitor Logs**: Regularly review logs to ensure expected behavior
- **Use Appropriate Permissions**: Only run with elevated permissions when necessary
- **Backup Important Work**: Ensure important work is saved before running

## Best Practices

1. **Start Conservative**: Begin with high thresholds and gradually lower if needed
2. **Whitelist First**: Configure whitelist before enabling monitoring
3. **Monitor Logs**: Regularly check logs to understand behavior
4. **Test Thoroughly**: Test configuration in a safe environment first
5. **Use Grace Periods**: Set appropriate `check_duration` to avoid killing temporary spikes
6. **Review Reports**: Regularly review generated reports

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

**Disclaimer**: Use at your own risk. The authors are not responsible for any data loss or system issues resulting from use of this tool.
