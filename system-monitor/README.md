# System Monitor

Continuously monitor system CPU, memory, and disk usage with automatic CSV logging and desktop notifications when thresholds are exceeded. This tool helps track system resource utilization over time and alerts you to potential performance issues.

## Project Description

System Monitor solves the problem of tracking and alerting on system resource usage. It continuously monitors CPU, memory, and disk utilization, logs metrics to CSV files for historical analysis, and sends desktop notifications when usage exceeds configured thresholds.

**Target Audience**: System administrators, developers, and users who need to monitor system performance and receive alerts about resource usage.

## Features

- Real-time monitoring of CPU, memory, and disk usage
- Configurable warning and critical thresholds for each resource
- CSV logging for historical data analysis
- Desktop notifications when thresholds are exceeded
- Notification cooldown periods to prevent spam
- Multi-threaded monitoring for efficient operation
- Cross-platform support (Windows, macOS, Linux)
- Configurable monitoring intervals
- Graceful shutdown handling

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Appropriate system permissions to read system metrics
- Desktop environment for notifications (optional)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/system-monitor
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

2. Edit `config.yaml` to customize monitoring thresholds and intervals:
   ```yaml
   cpu:
     warning_threshold: 70.0
     critical_threshold: 90.0
   
   memory:
     warning_threshold: 75.0
     critical_threshold: 90.0
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **monitoring**: Monitoring intervals and CSV log frequency
- **csv_logging**: CSV file location and which metrics to log
- **cpu**: CPU monitoring thresholds and notification settings
- **memory**: Memory monitoring thresholds and notification settings
- **disk**: Disk monitoring thresholds, paths to monitor, and notification settings
- **notifications**: Notification duration and cooldown periods
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `MONITORING_INTERVAL`: Override monitoring interval in seconds
- `CSV_LOG_FILE`: Override CSV log file path
- `NOTIFICATIONS_ENABLED`: Enable/disable notifications (`true`/`false`)

### Example Configuration

```yaml
monitoring:
  interval: 5  # Check every 5 seconds
  csv_log_interval: 60  # Log to CSV every 60 seconds

cpu:
  warning_threshold: 70.0
  critical_threshold: 90.0
  notify_on_warning: true
  notify_on_critical: true

memory:
  warning_threshold: 75.0
  critical_threshold: 90.0

disk:
  warning_threshold: 80.0
  critical_threshold: 95.0
  monitor_paths:
    - /
    - /home
```

## Usage

### Basic Usage

Start monitoring with default configuration:

```bash
python src/main.py
```

The monitor will run continuously until interrupted with Ctrl+C.

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Run as daemon (same as default behavior)
python src/main.py --daemon
```

### Common Use Cases

1. **Monitor System Resources**:
   ```bash
   python src/main.py
   ```

2. **Custom Monitoring Intervals**:
   - Edit `config.yaml` to change `monitoring.interval`
   - Or set environment variable: `export MONITORING_INTERVAL=10`

3. **Disable Notifications**:
   - Set `notifications.enabled: false` in config.yaml
   - Or set environment variable: `export NOTIFICATIONS_ENABLED=false`

4. **Monitor Specific Disk Paths**:
   - Edit `disk.monitor_paths` in config.yaml to add custom paths

5. **Analyze Historical Data**:
   - CSV logs are saved to `logs/system_metrics.csv`
   - Import into spreadsheet or data analysis tools

## Project Structure

```
system-monitor/
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
    ├── system_monitor.log   # Application logs
    └── system_metrics.csv  # System metrics data
```

### File Descriptions

- **src/main.py**: Core monitoring logic, CSV logging, and notification system
- **config.yaml**: YAML configuration file with all monitoring settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/system_monitor.log**: Application log file with rotation
- **logs/system_metrics.csv**: CSV file with timestamped system metrics

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
- System metric retrieval (CPU, memory, disk)
- Threshold checking logic
- Notification sending
- CSV logging functionality
- Cooldown mechanism
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'psutil'`

**Solution**: Install dependencies: `pip install -r requirements.txt`

---

**Issue**: Notifications not appearing

**Solution**: 
- Verify `notifications.enabled: true` in config.yaml
- Check that your desktop environment supports notifications
- On Linux, ensure notification daemon is running
- On macOS, check System Preferences for notification permissions

---

**Issue**: Permission denied when accessing disk paths

**Solution**: 
- Remove restricted paths from `disk.monitor_paths` in config.yaml
- Or run with appropriate permissions (not recommended for security)

---

**Issue**: CSV file not being created

**Solution**: 
- Verify `csv_logging.enabled: true` in config.yaml
- Check that logs directory exists and is writable
- Ensure `csv_log_interval` is set appropriately

---

**Issue**: High CPU usage from monitoring

**Solution**: 
- Increase `monitoring.interval` in config.yaml (e.g., 10 seconds)
- Disable unnecessary monitoring (set `enabled: false` for unused resources)

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Permission denied"**: Check file permissions for logs directory and CSV file location
- **"Failed to send notification"**: Desktop notification system may not be available or configured

## CSV Log Format

The CSV file contains timestamped system metrics with the following columns (configurable):

- **timestamp**: ISO format timestamp
- **cpu_percent**: CPU usage percentage
- **memory_percent**: Memory usage percentage
- **memory_used_gb**: Memory used in GB
- **memory_total_gb**: Total memory in GB
- **disk_percent**: Disk usage percentage
- **disk_used_gb**: Disk space used in GB
- **disk_total_gb**: Total disk space in GB

Example CSV row:
```
2024-02-07T10:30:00,45.2,62.5,8.0,16.0,55.3,100.5,500.0
```

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
