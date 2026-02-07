"""Uptime Monitor - Monitor system uptime and log boot/shutdown events.

This module provides functionality to monitor system uptime and log system
boot times, shutdown events, and session durations to a local database.
"""

import logging
import logging.handlers
import os
import platform
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class UptimeMonitor:
    """Monitors system uptime and logs boot/shutdown events."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize UptimeMonitor with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_database()
        self.system_name = platform.system().lower()
        self.last_boot_time = None
        self.last_uptime = None

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid.
        """
        config_file = Path(config_path)

        if not config_file.is_absolute():
            if not config_file.exists():
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    cwd_config = Path.cwd() / config_path
                    if cwd_config.exists():
                        config_file = cwd_config

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("DATABASE_FILE"):
            config["database"]["file"] = os.getenv("DATABASE_FILE")
        if os.getenv("MONITORING_INTERVAL"):
            config["monitoring"]["interval"] = int(os.getenv("MONITORING_INTERVAL"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/uptime_monitor.log")

        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=log_config.get("max_bytes", 10485760),
            backupCount=log_config.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logger.info("Logging configured successfully")

    def _setup_database(self) -> None:
        """Set up SQLite database and create tables if needed."""
        db_file = self.config["database"]["file"]
        db_path = Path(db_file)
        if not db_path.is_absolute():
            project_root = Path(__file__).parent.parent
            db_path = project_root / db_file

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

        if self.config["database"].get("create_tables", True):
            self._create_tables()

        logger.info(f"Database initialized: {db_path}")

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Boot events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS boot_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boot_time TEXT NOT NULL,
                detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                uptime_seconds REAL,
                system_info TEXT
            )
        """)

        # Shutdown events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shutdown_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_start_time TEXT NOT NULL,
                shutdown_time TEXT NOT NULL,
                session_duration_seconds REAL,
                detected_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Uptime snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uptime_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                uptime_seconds REAL,
                boot_time TEXT,
                system_info TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.debug("Database tables created/verified")

    def _get_boot_time(self) -> Optional[datetime]:
        """Get system boot time.

        Returns:
            Boot time as datetime object or None if unable to determine.
        """
        try:
            if self.system_name == "windows":
                # Windows: use uptime to calculate boot time
                import subprocess
                result = subprocess.run(
                    ["wmic", "os", "get", "lastbootuptime", "/value"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.split("\n"):
                    if "LastBootUpTime=" in line:
                        boot_str = line.split("=")[1].strip()
                        # Format: YYYYMMDDHHmmss.microseconds+timezone
                        if len(boot_str) >= 14:
                            year = int(boot_str[0:4])
                            month = int(boot_str[4:6])
                            day = int(boot_str[6:8])
                            hour = int(boot_str[8:10])
                            minute = int(boot_str[10:12])
                            second = int(boot_str[12:14])
                            return datetime(year, month, day, hour, minute, second)

            elif self.system_name == "darwin":
                # macOS: use sysctl
                import subprocess
                result = subprocess.run(
                    ["sysctl", "-n", "kern.boottime"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    # Format: { sec = 1234567890, usec = 123456 }
                    boot_timestamp = result.stdout.strip()
                    # Extract seconds value
                    import re
                    match = re.search(r"sec\s*=\s*(\d+)", boot_timestamp)
                    if match:
                        boot_seconds = int(match.group(1))
                        return datetime.fromtimestamp(boot_seconds)

            else:
                # Linux: read from /proc/uptime and calculate
                try:
                    with open("/proc/uptime", "r") as f:
                        uptime_seconds = float(f.read().split()[0])
                    boot_time = datetime.now() - timedelta(seconds=uptime_seconds)
                    return boot_time
                except (FileNotFoundError, ValueError):
                    pass

            # Fallback: try psutil if available
            try:
                import psutil
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                return boot_time
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Error using psutil: {e}")

        except Exception as e:
            logger.warning(f"Error getting boot time: {e}")

        return None

    def _get_uptime_seconds(self) -> Optional[float]:
        """Get system uptime in seconds.

        Returns:
            Uptime in seconds or None if unable to determine.
        """
        try:
            if self.system_name == "windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "os", "get", "lastbootuptime", "/value"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.split("\n"):
                    if "LastBootUpTime=" in line:
                        boot_str = line.split("=")[1].strip()
                        if len(boot_str) >= 14:
                            year = int(boot_str[0:4])
                            month = int(boot_str[4:6])
                            day = int(boot_str[6:8])
                            hour = int(boot_str[8:10])
                            minute = int(boot_str[12:14])
                            second = int(boot_str[12:14])
                            boot_time = datetime(year, month, day, hour, minute, second)
                            uptime = (datetime.now() - boot_time).total_seconds()
                            return uptime

            elif self.system_name == "darwin":
                import subprocess
                result = subprocess.run(
                    ["sysctl", "-n", "kern.boottime"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    import re
                    match = re.search(r"sec\s*=\s*(\d+)", result.stdout.strip())
                    if match:
                        boot_seconds = int(match.group(1))
                        uptime = (datetime.now() - datetime.fromtimestamp(boot_seconds)).total_seconds()
                        return uptime

            else:
                # Linux: read from /proc/uptime
                try:
                    with open("/proc/uptime", "r") as f:
                        uptime_seconds = float(f.read().split()[0])
                    return uptime_seconds
                except (FileNotFoundError, ValueError):
                    pass

            # Fallback: use psutil if available
            try:
                import psutil
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = (datetime.now() - boot_time).total_seconds()
                return uptime
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Error using psutil: {e}")

        except Exception as e:
            logger.warning(f"Error getting uptime: {e}")

        return None

    def _get_system_info(self) -> str:
        """Get system information string.

        Returns:
            System information string.
        """
        info_parts = [
            f"Platform: {platform.system()}",
            f"Release: {platform.release()}",
            f"Version: {platform.version()}",
            f"Machine: {platform.machine()}",
        ]
        return "; ".join(info_parts)

    def _log_boot_event(self, boot_time: datetime, uptime_seconds: Optional[float]) -> bool:
        """Log boot event to database.

        Args:
            boot_time: Boot time datetime.
            uptime_seconds: Current uptime in seconds.

        Returns:
            True if logged successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if this boot event already exists
            cursor.execute("""
                SELECT id FROM boot_events
                WHERE boot_time = ?
            """, (boot_time.isoformat(),))

            if cursor.fetchone():
                logger.debug(f"Boot event already logged: {boot_time.isoformat()}")
                return False

            system_info = self._get_system_info()

            cursor.execute("""
                INSERT INTO boot_events (boot_time, uptime_seconds, system_info)
                VALUES (?, ?, ?)
            """, (
                boot_time.isoformat(),
                uptime_seconds,
                system_info,
            ))

            conn.commit()
            logger.info(f"Logged boot event: {boot_time.isoformat()}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error logging boot event: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def _detect_shutdown_events(self) -> int:
        """Detect and log shutdown events from previous session.

        Returns:
            Number of shutdown events detected.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        shutdown_count = 0

        try:
            # Get last boot event
            cursor.execute("""
                SELECT boot_time FROM boot_events
                ORDER BY id DESC LIMIT 1
            """)
            last_boot_row = cursor.fetchone()

            if not last_boot_row:
                return 0

            last_boot_time_str = last_boot_row[0]
            last_boot_time = datetime.fromisoformat(last_boot_time_str)

            # Get current boot time
            current_boot_time = self._get_boot_time()
            if not current_boot_time:
                return 0

            # If current boot time is different from last logged boot time,
            # and it's more recent, we had a shutdown/reboot
            if current_boot_time > last_boot_time:
                # Check if shutdown event already exists for this session
                cursor.execute("""
                    SELECT id FROM shutdown_events
                    WHERE session_start_time = ?
                """, (last_boot_time_str,))

                if not cursor.fetchone():
                    # Calculate session duration
                    session_duration = (current_boot_time - last_boot_time).total_seconds()

                    # Log shutdown event
                    cursor.execute("""
                        INSERT INTO shutdown_events 
                        (session_start_time, shutdown_time, session_duration_seconds)
                        VALUES (?, ?, ?)
                    """, (
                        last_boot_time_str,
                        current_boot_time.isoformat(),
                        session_duration,
                    ))

                    conn.commit()
                    shutdown_count = 1
                    logger.info(
                        f"Detected shutdown event: "
                        f"Session from {last_boot_time_str} to {current_boot_time.isoformat()}, "
                        f"Duration: {session_duration:.0f} seconds"
                    )

        except sqlite3.Error as e:
            logger.error(f"Database error detecting shutdown events: {e}")
            conn.rollback()
        except Exception as e:
            logger.error(f"Error detecting shutdown events: {e}")
        finally:
            conn.close()

        return shutdown_count

    def _log_uptime_snapshot(self, uptime_seconds: Optional[float], boot_time: Optional[datetime]) -> bool:
        """Log current uptime snapshot to database.

        Args:
            uptime_seconds: Current uptime in seconds.
            boot_time: Boot time datetime.

        Returns:
            True if logged successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            system_info = self._get_system_info()

            cursor.execute("""
                INSERT INTO uptime_snapshots (timestamp, uptime_seconds, boot_time, system_info)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                uptime_seconds,
                boot_time.isoformat() if boot_time else None,
                system_info,
            ))

            conn.commit()
            logger.debug("Logged uptime snapshot")
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error logging uptime snapshot: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def check_and_log(self) -> Dict[str, any]:
        """Check current system state and log events.

        Returns:
            Dictionary with check results and statistics.
        """
        logger.info("Checking system uptime and logging events")

        boot_time = self._get_boot_time()
        uptime_seconds = self._get_uptime_seconds()

        results = {
            "boot_time": boot_time.isoformat() if boot_time else None,
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": self._format_uptime(uptime_seconds) if uptime_seconds else None,
            "boot_event_logged": False,
            "shutdown_events_detected": 0,
            "snapshot_logged": False,
        }

        # Detect shutdown events from previous session
        shutdown_count = self._detect_shutdown_events()
        results["shutdown_events_detected"] = shutdown_count

        # Log current boot event if new
        if boot_time:
            boot_logged = self._log_boot_event(boot_time, uptime_seconds)
            results["boot_event_logged"] = boot_logged

        # Log uptime snapshot
        snapshot_logged = self._log_uptime_snapshot(uptime_seconds, boot_time)
        results["snapshot_logged"] = snapshot_logged

        # Update last known values
        self.last_boot_time = boot_time
        self.last_uptime = uptime_seconds

        return results

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime seconds to human-readable string.

        Args:
            seconds: Uptime in seconds.

        Returns:
            Formatted uptime string.
        """
        if seconds is None:
            return "Unknown"

        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if secs > 0 or not parts:
            parts.append(f"{secs} second{'s' if secs != 1 else ''}")

        return ", ".join(parts)

    def get_boot_history(self, limit: Optional[int] = None) -> List[Dict[str, any]]:
        """Get boot event history.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of boot event dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, boot_time, detected_at, uptime_seconds, system_info
                FROM boot_events
                ORDER BY id DESC
            """
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            events = []
            for row in rows:
                event = dict(zip(columns, row))
                events.append(event)

            return events

        except sqlite3.Error as e:
            logger.error(f"Database error getting boot history: {e}")
            return []
        finally:
            conn.close()

    def get_shutdown_history(self, limit: Optional[int] = None) -> List[Dict[str, any]]:
        """Get shutdown event history.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of shutdown event dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, session_start_time, shutdown_time, 
                       session_duration_seconds, detected_at
                FROM shutdown_events
                ORDER BY id DESC
            """
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            events = []
            for row in rows:
                event = dict(zip(columns, row))
                event["session_duration_formatted"] = self._format_uptime(
                    event.get("session_duration_seconds", 0)
                )
                events.append(event)

            return events

        except sqlite3.Error as e:
            logger.error(f"Database error getting shutdown history: {e}")
            return []
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, any]:
        """Get uptime monitoring statistics.

        Returns:
            Dictionary with statistics.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        try:
            # Boot events count
            cursor.execute("SELECT COUNT(*) FROM boot_events")
            stats["total_boot_events"] = cursor.fetchone()[0]

            # Shutdown events count
            cursor.execute("SELECT COUNT(*) FROM shutdown_events")
            stats["total_shutdown_events"] = cursor.fetchone()[0]

            # Uptime snapshots count
            cursor.execute("SELECT COUNT(*) FROM uptime_snapshots")
            stats["total_snapshots"] = cursor.fetchone()[0]

            # Average session duration
            cursor.execute("""
                SELECT AVG(session_duration_seconds) FROM shutdown_events
            """)
            avg_duration = cursor.fetchone()[0]
            stats["average_session_duration_seconds"] = avg_duration
            stats["average_session_duration_formatted"] = (
                self._format_uptime(avg_duration) if avg_duration else None
            )

            # Last boot time
            cursor.execute("""
                SELECT boot_time FROM boot_events ORDER BY id DESC LIMIT 1
            """)
            last_boot = cursor.fetchone()
            stats["last_boot_time"] = last_boot[0] if last_boot else None

            # Current uptime
            current_uptime = self._get_uptime_seconds()
            stats["current_uptime_seconds"] = current_uptime
            stats["current_uptime_formatted"] = (
                self._format_uptime(current_uptime) if current_uptime else None
            )

        except sqlite3.Error as e:
            logger.error(f"Database error getting statistics: {e}")
        finally:
            conn.close()

        return stats

    def monitor_continuous(self) -> None:
        """Monitor system continuously and log events periodically."""
        monitoring_config = self.config.get("monitoring", {})
        interval = monitoring_config.get("interval", 300)  # Default 5 minutes

        logger.info(f"Starting continuous monitoring (interval: {interval} seconds)")

        try:
            while True:
                self.check_and_log()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}", exc_info=True)

    def _cleanup_old_entries(self) -> None:
        """Remove old entries from database based on retention policy."""
        if not self.config.get("retention", {}).get("auto_cleanup", True):
            return

        days_to_keep = self.config.get("retention", {}).get("days_to_keep", 90)
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Cleanup old snapshots
            cursor.execute("""
                DELETE FROM uptime_snapshots
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))

            deleted_snapshots = cursor.rowcount

            conn.commit()

            if deleted_snapshots > 0:
                logger.info(f"Cleaned up {deleted_snapshots} old snapshot(s)")

        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old entries: {e}")
            conn.rollback()
        finally:
            conn.close()


def main() -> int:
    """Main entry point for uptime monitor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor system uptime and log boot/shutdown events"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check and log current system state",
    )
    parser.add_argument(
        "-m",
        "--monitor",
        action="store_true",
        help="Monitor system continuously",
    )
    parser.add_argument(
        "--boot-history",
        type=int,
        metavar="N",
        help="Show last N boot events",
    )
    parser.add_argument(
        "--shutdown-history",
        type=int,
        metavar="N",
        help="Show last N shutdown events",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics",
    )

    args = parser.parse_args()

    try:
        monitor = UptimeMonitor(config_path=args.config)

        if args.boot_history:
            events = monitor.get_boot_history(limit=args.boot_history)
            print("\n" + "=" * 80)
            print(f"BOOT HISTORY (Last {args.boot_history})")
            print("=" * 80)
            for event in events:
                print(f"Boot Time: {event['boot_time']}")
                print(f"Detected At: {event['detected_at']}")
                if event.get("uptime_seconds"):
                    print(f"Uptime: {monitor._format_uptime(event['uptime_seconds'])}")
                print("-" * 80)

        if args.shutdown_history:
            events = monitor.get_shutdown_history(limit=args.shutdown_history)
            print("\n" + "=" * 80)
            print(f"SHUTDOWN HISTORY (Last {args.shutdown_history})")
            print("=" * 80)
            for event in events:
                print(f"Session Start: {event['session_start_time']}")
                print(f"Shutdown Time: {event['shutdown_time']}")
                print(f"Duration: {event['session_duration_formatted']}")
                print("-" * 80)

        if args.stats:
            stats = monitor.get_statistics()
            print("\n" + "=" * 80)
            print("UPTIME MONITOR STATISTICS")
            print("=" * 80)
            print(f"Total Boot Events: {stats.get('total_boot_events', 0)}")
            print(f"Total Shutdown Events: {stats.get('total_shutdown_events', 0)}")
            print(f"Total Snapshots: {stats.get('total_snapshots', 0)}")
            if stats.get("average_session_duration_formatted"):
                print(f"Average Session Duration: {stats['average_session_duration_formatted']}")
            if stats.get("last_boot_time"):
                print(f"Last Boot Time: {stats['last_boot_time']}")
            if stats.get("current_uptime_formatted"):
                print(f"Current Uptime: {stats['current_uptime_formatted']}")
            print("=" * 80)

        if args.monitor:
            monitor.monitor_continuous()
        elif args.check or (not args.boot_history and not args.shutdown_history and not args.stats):
            # Default action: check and log
            results = monitor.check_and_log()
            print("\n" + "=" * 80)
            print("UPTIME CHECK RESULTS")
            print("=" * 80)
            if results.get("boot_time"):
                print(f"Boot Time: {results['boot_time']}")
            if results.get("uptime_formatted"):
                print(f"Current Uptime: {results['uptime_formatted']}")
            if results.get("boot_event_logged"):
                print("Boot event logged")
            if results.get("shutdown_events_detected", 0) > 0:
                print(f"Detected {results['shutdown_events_detected']} shutdown event(s)")
            print("=" * 80)

        # Cleanup old entries
        monitor._cleanup_old_entries()

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
