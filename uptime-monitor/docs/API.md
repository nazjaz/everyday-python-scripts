# API Documentation

## UptimeMonitor Class

Main class for monitoring system uptime and logging boot/shutdown events.

### Methods

#### `__init__(config_path: str = "config.yaml") -> None`

Initialize UptimeMonitor with configuration.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

---

#### `check_and_log() -> Dict[str, any]`

Check current system state and log events.

**Returns:**
Dictionary with check results:
- `boot_time`: Boot time ISO string or None
- `uptime_seconds`: Current uptime in seconds
- `uptime_formatted`: Human-readable uptime string
- `boot_event_logged`: Whether boot event was logged
- `shutdown_events_detected`: Number of shutdown events detected
- `snapshot_logged`: Whether snapshot was logged

---

#### `get_boot_history(limit: Optional[int] = None) -> List[Dict[str, any]]`

Get boot event history.

**Parameters:**
- `limit`: Maximum number of records to return

**Returns:**
List of boot event dictionaries with keys:
- `id`: Event ID
- `boot_time`: Boot time ISO string
- `detected_at`: Detection timestamp
- `uptime_seconds`: Uptime at detection
- `system_info`: System information string

---

#### `get_shutdown_history(limit: Optional[int] = None) -> List[Dict[str, any]]`

Get shutdown event history.

**Parameters:**
- `limit`: Maximum number of records to return

**Returns:**
List of shutdown event dictionaries with keys:
- `id`: Event ID
- `session_start_time`: Session start time ISO string
- `shutdown_time`: Shutdown time ISO string
- `session_duration_seconds`: Session duration in seconds
- `session_duration_formatted`: Human-readable duration
- `detected_at`: Detection timestamp

---

#### `get_statistics() -> Dict[str, any]`

Get uptime monitoring statistics.

**Returns:**
Dictionary with statistics:
- `total_boot_events`: Total number of boot events
- `total_shutdown_events`: Total number of shutdown events
- `total_snapshots`: Total number of uptime snapshots
- `average_session_duration_seconds`: Average session duration
- `average_session_duration_formatted`: Human-readable average duration
- `last_boot_time`: Last boot time ISO string
- `current_uptime_seconds`: Current uptime in seconds
- `current_uptime_formatted`: Human-readable current uptime

---

#### `monitor_continuous() -> None`

Monitor system continuously and log events periodically.

Uses monitoring interval from configuration. Runs until interrupted.

---

#### `_get_boot_time() -> Optional[datetime]`

Get system boot time (internal method).

**Returns:**
Boot time as datetime object or None if unable to determine.

---

#### `_get_uptime_seconds() -> Optional[float]`

Get system uptime in seconds (internal method).

**Returns:**
Uptime in seconds or None if unable to determine.

---

#### `_format_uptime(seconds: float) -> str`

Format uptime seconds to human-readable string (internal method).

**Parameters:**
- `seconds`: Uptime in seconds

**Returns:**
Formatted uptime string (e.g., "2 days, 3 hours, 15 minutes")
