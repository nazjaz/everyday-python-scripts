"""Network Monitor - CLI tool for monitoring network interface statistics.

This module provides a command-line tool for monitoring network interface
statistics, tracking bytes sent and received, and logging network activity
to a database file.
"""

import argparse
import logging
import logging.handlers
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Monitors network interface statistics and logs to database."""

    def __init__(self, config: Dict) -> None:
        """Initialize NetworkMonitor.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.database_file = Path(config.get("database_file", "data/network_activity.db"))
        self.monitoring_interval = config.get("monitoring_interval", 60)
        self.interfaces = config.get("interfaces", [])
        self.exclude_patterns = [
            re.compile(pattern)
            for pattern in config.get("exclude_interfaces", [])
        ]
        self.options = config.get("options", {})
        self.database_config = config.get("database", {})

        # Ensure database directory exists
        self.database_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database and create tables."""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            # Create network statistics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS network_stats (
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
                """
            )

            # Create index for faster queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON network_stats(timestamp)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_interface 
                ON network_stats(interface)
                """
            )

            conn.commit()
            conn.close()

            logger.info(f"Database initialized: {self.database_file}")

            # Cleanup old records if configured
            if self.database_config.get("cleanup_on_startup", True):
                self._cleanup_old_records()

        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def _cleanup_old_records(self) -> None:
        """Remove old records based on retention period."""
        retention_days = self.database_config.get("retention_days", 0)

        if retention_days <= 0:
            return

        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_str = cutoff_date.isoformat()

            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM network_stats WHERE timestamp < ?", (cutoff_str,)
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old records")

        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old records: {e}")

    def get_network_interfaces(self) -> List[str]:
        """Get list of network interfaces to monitor.

        Returns:
            List of interface names.
        """
        all_interfaces = list(psutil.net_io_counters(pernic=True).keys())

        # Filter by configured interfaces if specified
        if self.interfaces:
            filtered = [iface for iface in all_interfaces if iface in self.interfaces]
        else:
            filtered = all_interfaces

        # Exclude interfaces matching patterns
        result = []
        for iface in filtered:
            excluded = False
            for pattern in self.exclude_patterns:
                if pattern.search(iface):
                    excluded = True
                    break
            if not excluded:
                result.append(iface)

        return sorted(result)

    def get_network_stats(self, interface: Optional[str] = None) -> Dict:
        """Get network statistics for interface(s).

        Args:
            interface: Interface name. If None, returns total stats.

        Returns:
            Dictionary with network statistics.
        """
        if interface:
            try:
                stats = psutil.net_io_counters(pernic=True).get(interface)
                if stats is None:
                    return {}
                return {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "packets_sent": stats.packets_sent,
                    "packets_recv": stats.packets_recv,
                    "errin": stats.errin,
                    "errout": stats.errout,
                    "dropin": stats.dropin,
                    "dropout": stats.dropout,
                }
            except (KeyError, AttributeError):
                return {}
        else:
            stats = psutil.net_io_counters(pernic=False)
            return {
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
                "packets_sent": stats.packets_sent,
                "packets_recv": stats.packets_recv,
                "errin": stats.errin,
                "errout": stats.errout,
                "dropin": stats.dropin,
                "dropout": stats.dropout,
            }

    def calculate_rates(
        self, current_stats: Dict, previous_stats: Dict, interval: float
    ) -> Tuple[float, float]:
        """Calculate bytes per second rates.

        Args:
            current_stats: Current statistics dictionary.
            previous_stats: Previous statistics dictionary.
            interval: Time interval in seconds.

        Returns:
            Tuple of (bytes_sent_rate, bytes_recv_rate).
        """
        if not previous_stats or interval <= 0:
            return 0.0, 0.0

        bytes_sent_diff = current_stats.get("bytes_sent", 0) - previous_stats.get(
            "bytes_sent", 0
        )
        bytes_recv_diff = current_stats.get("bytes_recv", 0) - previous_stats.get(
            "bytes_recv", 0
        )

        bytes_sent_rate = bytes_sent_diff / interval if interval > 0 else 0.0
        bytes_recv_rate = bytes_recv_diff / interval if interval > 0 else 0.0

        return bytes_sent_rate, bytes_recv_rate

    def log_network_stats(
        self,
        interface: str,
        stats: Dict,
        bytes_sent_rate: Optional[float] = None,
        bytes_recv_rate: Optional[float] = None,
    ) -> None:
        """Log network statistics to database.

        Args:
            interface: Interface name.
            stats: Network statistics dictionary.
            bytes_sent_rate: Bytes sent per second (optional).
            bytes_recv_rate: Bytes received per second (optional).
        """
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            timestamp = datetime.now().isoformat()

            cursor.execute(
                """
                INSERT OR REPLACE INTO network_stats (
                    timestamp, interface, bytes_sent, bytes_recv,
                    packets_sent, packets_recv, errin, errout,
                    dropin, dropout, bytes_sent_rate, bytes_recv_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    interface,
                    stats.get("bytes_sent", 0),
                    stats.get("bytes_recv", 0),
                    stats.get("packets_sent", 0),
                    stats.get("packets_recv", 0),
                    stats.get("errin", 0),
                    stats.get("errout", 0),
                    stats.get("dropin", 0),
                    stats.get("dropout", 0),
                    bytes_sent_rate,
                    bytes_recv_rate,
                ),
            )

            conn.commit()
            conn.close()

            logger.debug(
                f"Logged stats for {interface}: "
                f"sent={stats.get('bytes_sent', 0)}, "
                f"recv={stats.get('bytes_recv', 0)}"
            )

        except sqlite3.Error as e:
            logger.error(f"Error logging network stats: {e}")

    def monitor_once(self, previous_stats: Dict[str, Dict]) -> Dict[str, Dict]:
        """Perform one monitoring cycle.

        Args:
            previous_stats: Previous statistics for each interface.

        Returns:
            Current statistics for each interface.
        """
        current_stats = {}
        interfaces = self.get_network_interfaces()

        for interface in interfaces:
            stats = self.get_network_stats(interface)
            if not stats:
                continue

            current_stats[interface] = stats

            # Calculate rates if enabled
            bytes_sent_rate = None
            bytes_recv_rate = None
            if self.options.get("calculate_rates", True):
                prev_stats = previous_stats.get(interface, {})
                if prev_stats:
                    bytes_sent_rate, bytes_recv_rate = self.calculate_rates(
                        stats, prev_stats, self.monitoring_interval
                    )

            # Log to database
            self.log_network_stats(interface, stats, bytes_sent_rate, bytes_recv_rate)

        # Log total statistics if enabled
        if self.options.get("track_total", True):
            total_stats = self.get_network_stats()
            if total_stats:
                prev_total = previous_stats.get("_total", {})
                bytes_sent_rate = None
                bytes_recv_rate = None

                if (
                    self.options.get("calculate_rates", True)
                    and prev_total
                ):
                    bytes_sent_rate, bytes_recv_rate = self.calculate_rates(
                        total_stats, prev_total, self.monitoring_interval
                    )

                self.log_network_stats(
                    "_total", total_stats, bytes_sent_rate, bytes_recv_rate
                )
                current_stats["_total"] = total_stats

        return current_stats

    def monitor_continuous(self) -> None:
        """Monitor network continuously."""
        logger.info("Starting continuous network monitoring")
        logger.info(f"Monitoring interval: {self.monitoring_interval} seconds")

        interfaces = self.get_network_interfaces()
        logger.info(f"Monitoring interfaces: {', '.join(interfaces)}")

        previous_stats = {}

        try:
            while True:
                current_stats = self.monitor_once(previous_stats)
                previous_stats = current_stats

                # Print summary
                self._print_summary(current_stats)

                time.sleep(self.monitoring_interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            print("\nMonitoring stopped.")

    def monitor_once_and_exit(self) -> None:
        """Perform one monitoring cycle and exit."""
        logger.info("Performing single monitoring cycle")
        stats = self.monitor_once({})
        self._print_summary(stats)

    def _print_summary(self, stats: Dict[str, Dict]) -> None:
        """Print summary of current statistics.

        Args:
            stats: Current statistics dictionary.
        """
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Network Statistics:")
        print("-" * 80)

        for interface, stat_data in sorted(stats.items()):
            if interface == "_total":
                interface_name = "TOTAL (all interfaces)"
            else:
                interface_name = interface

            bytes_sent = stat_data.get("bytes_sent", 0)
            bytes_recv = stat_data.get("bytes_recv", 0)

            print(f"{interface_name}:")
            print(f"  Sent:     {self._format_bytes(bytes_sent)}")
            print(f"  Received: {self._format_bytes(bytes_recv)}")
            print(f"  Total:    {self._format_bytes(bytes_sent + bytes_recv)}")

    def _format_bytes(self, bytes_count: int) -> str:
        """Format byte count in human-readable format.

        Args:
            bytes_count: Number of bytes.

        Returns:
            Formatted string.
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} PB"

    def get_statistics_summary(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict:
        """Get statistics summary from database.

        Args:
            start_time: Start time for query (optional).
            end_time: End time for query (optional).

        Returns:
            Dictionary with summary statistics.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            query = "SELECT * FROM network_stats WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            conn.close()

            # Get column names
            columns = [
                "id",
                "timestamp",
                "interface",
                "bytes_sent",
                "bytes_recv",
                "packets_sent",
                "packets_recv",
                "errin",
                "errout",
                "dropin",
                "dropout",
                "bytes_sent_rate",
                "bytes_recv_rate",
            ]

            records = []
            for row in rows:
                records.append(dict(zip(columns, row)))

            return {
                "total_records": len(records),
                "records": records,
            }

        except sqlite3.Error as e:
            logger.error(f"Error getting statistics summary: {e}")
            return {"total_records": 0, "records": []}


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/network_monitor.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Monitor network interface statistics and log to database"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Perform one monitoring cycle and exit",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Monitoring interval in seconds (overrides config)",
    )
    parser.add_argument(
        "--interfaces",
        nargs="+",
        help="Interfaces to monitor (overrides config)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show statistics summary from database",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        # Override config with command-line arguments
        if args.interval:
            config["monitoring_interval"] = args.interval
        if args.interfaces:
            config["interfaces"] = args.interfaces

        monitor = NetworkMonitor(config)

        if args.summary:
            summary = monitor.get_statistics_summary()
            print(f"Total records in database: {summary['total_records']}")
            if summary["records"]:
                print("\nRecent records:")
                for record in summary["records"][:10]:
                    print(
                        f"  {record['timestamp']} - {record['interface']}: "
                        f"sent={record['bytes_sent']}, recv={record['bytes_recv']}"
                    )
        elif args.once:
            monitor.monitor_once_and_exit()
        else:
            monitor.monitor_continuous()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
