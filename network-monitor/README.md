# Network Monitor

A command-line tool for monitoring network interface statistics, tracking bytes sent and received, and logging network activity to a SQLite database. Provides continuous monitoring, rate calculations, and historical data analysis.

## Project Description

Network Monitor solves the problem of tracking network usage over time by providing continuous monitoring of network interfaces, calculating data transfer rates, and storing historical statistics in a database. It helps users understand network usage patterns, identify bandwidth consumption, and maintain records of network activity for analysis and troubleshooting.

**Target Audience**: System administrators, network engineers, and users who need to monitor network usage, track bandwidth consumption, or maintain historical records of network activity.

## Features

- **Network Interface Monitoring**: Monitor all network interfaces or specific ones
- **Bytes Tracking**: Track bytes sent and received per interface
- **Packet Statistics**: Track packets sent, received, errors, and drops
- **Rate Calculation**: Calculate bytes per second transfer rates
- **Database Logging**: Store all statistics in SQLite database
- **Continuous Monitoring**: Monitor network continuously at configurable intervals
- **Historical Data**: Query and analyze historical network statistics
- **Automatic Cleanup**: Optional automatic cleanup of old records
- **Flexible Filtering**: Exclude specific interfaces (e.g., loopback)
- **Comprehensive Logging**: Detailed logs of all operations

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- psutil library (installed via requirements.txt)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/network-monitor
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

Edit `config.yaml` to customize monitoring options:

```yaml
monitoring_interval: 60  # seconds
interfaces: []  # empty = monitor all
database_file: data/network_activity.db
```

## Usage

### Basic Usage

Start continuous monitoring:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Perform one monitoring cycle and exit
python src/main.py --once

# Set custom monitoring interval
python src/main.py --interval 30

# Monitor specific interfaces
python src/main.py --interfaces eth0 wlan0

# Show statistics summary from database
python src/main.py --summary

# Use custom configuration file
python src/main.py -c /path/to/config.yaml
```

### Common Use Cases

**Monitor continuously**:
```bash
python src/main.py
```

**Single snapshot**:
```bash
python src/main.py --once
```

**Monitor specific interface**:
```bash
python src/main.py --interfaces eth0
```

**View historical data**:
```bash
python src/main.py --summary
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

#### Monitoring Settings

```yaml
monitoring_interval: 60  # Seconds between monitoring cycles
interfaces: []  # Empty list = monitor all interfaces
exclude_interfaces:
  - '^lo$'  # Exclude loopback
  - '^docker'  # Exclude Docker interfaces
```

#### Database Settings

```yaml
database_file: data/network_activity.db
database:
  retention_days: 30  # Keep records for 30 days (0 = forever)
  cleanup_on_startup: true  # Clean old records on startup
```

#### Statistics Options

```yaml
options:
  track_per_interface: true  # Track each interface separately
  track_total: true  # Track total across all interfaces
  calculate_rates: true  # Calculate bytes per second
  store_raw_counts: true  # Store raw byte counts
```

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Database Schema

The tool creates a SQLite database with the following schema:

```sql
CREATE TABLE network_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    interface TEXT NOT NULL,
    bytes_sent INTEGER NOT NULL,
    bytes_recv INTEGER NOT NULL,
    packets_sent INTEGER NOT NULL,
    packets_recv INTEGER NOT NULL,
    errin INTEGER NOT NULL,
    errout INTEGER NOT NULL,
    dropin INTEGER NOT NULL,
    dropout INTEGER NOT NULL,
    bytes_sent_rate REAL,
    bytes_recv_rate REAL,
    UNIQUE(timestamp, interface)
)
```

## Statistics Tracked

### Per Interface
- **Bytes Sent**: Total bytes sent on interface
- **Bytes Received**: Total bytes received on interface
- **Packets Sent**: Total packets sent
- **Packets Received**: Total packets received
- **Errors In**: Input errors
- **Errors Out**: Output errors
- **Drops In**: Input packet drops
- **Drops Out**: Output packet drops
- **Bytes Sent Rate**: Bytes per second sent
- **Bytes Received Rate**: Bytes per second received

### Total Statistics
- Same statistics aggregated across all interfaces (if enabled)

## Project Structure

```
network-monitor/
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
│   └── network_activity.db  # SQLite database
└── logs/
    └── network_monitor.log  # Application logs
```

## Querying the Database

You can query the database directly using SQLite:

```bash
sqlite3 data/network_activity.db

# View all records
SELECT * FROM network_stats;

# View records for specific interface
SELECT * FROM network_stats WHERE interface = 'eth0';

# View recent records
SELECT * FROM network_stats ORDER BY timestamp DESC LIMIT 10;

# Calculate total bytes sent today
SELECT SUM(bytes_sent) FROM network_stats 
WHERE date(timestamp) = date('now') AND interface = 'eth0';
```

## Performance Considerations

- **Monitoring Interval**: Lower intervals provide more granular data but increase database writes
- **Database Size**: Database grows over time; use retention_days to limit growth
- **Multiple Interfaces**: Monitoring many interfaces increases processing time
- **Rate Calculation**: Requires storing previous statistics in memory

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
- Database initialization
- Network statistics retrieval
- Rate calculations
- Database logging
- Statistics summary retrieval
- Old record cleanup
- Interface filtering

## Troubleshooting

### No Interfaces Found

**Check interface names**:
- List available interfaces: `ip link show` (Linux) or `ifconfig` (macOS)
- Verify interface names in config match system interfaces
- Check exclusion patterns aren't too broad

**Permissions**:
- Some systems may require elevated permissions to access network statistics
- Try running with appropriate permissions

### Database Errors

**Database locked**:
- Ensure only one instance is running
- Check file permissions on database directory
- Verify disk space available

**Database corruption**:
- Backup database regularly
- Check disk health
- Recreate database if corrupted

### Missing Statistics

**Interface not monitored**:
- Check interface is not excluded
- Verify interface exists on system
- Check interface is active

**No data in database**:
- Verify monitoring is running
- Check logs for errors
- Ensure database file is writable

## Best Practices

1. **Set appropriate interval**: Balance between data granularity and resource usage
2. **Use retention**: Set retention_days to prevent database from growing indefinitely
3. **Exclude unnecessary interfaces**: Exclude loopback and virtual interfaces if not needed
4. **Monitor specific interfaces**: Monitor only interfaces of interest to reduce overhead
5. **Regular backups**: Backup database regularly for historical analysis
6. **Review logs**: Check logs regularly for errors or warnings

## Security Considerations

- **Database Access**: Database file contains network statistics; protect appropriately
- **Permissions**: Tool requires read access to network interfaces
- **Data Privacy**: Network statistics may reveal usage patterns; handle appropriately

## Limitations

- **Platform Differences**: Network interface names vary by platform
- **Cumulative Counters**: Statistics are cumulative since system boot
- **Database Growth**: Database grows over time; use retention to manage
- **Single Instance**: Running multiple instances may cause database locking

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
