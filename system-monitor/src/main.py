"""System Monitor - Monitor CPU, memory, and disk usage.

This module provides functionality to continuously monitor system resources,
log metrics to CSV files, and send desktop notifications when thresholds
are exceeded.
"""

import csv
import logging
import logging.handlers
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import yaml
from dotenv import load_dotenv
from plyer import notification

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors system resources and logs metrics."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize SystemMonitor with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_csv_logging()
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.csv_log_thread: Optional[threading.Thread] = None
        self.last_notification_time: Dict[str, float] = {}
        self.stats = {
            "checks_performed": 0,
            "warnings_sent": 0,
            "critical_alerts_sent": 0,
            "csv_entries_logged": 0,
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

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

        # If relative path, try to find it relative to project root
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
        if os.getenv("MONITORING_INTERVAL"):
            config["monitoring"]["interval"] = int(os.getenv("MONITORING_INTERVAL"))
        if os.getenv("CSV_LOG_FILE"):
            config["csv_logging"]["file"] = os.getenv("CSV_LOG_FILE")
        if os.getenv("NOTIFICATIONS_ENABLED"):
            config["notifications"]["enabled"] = (
                os.getenv("NOTIFICATIONS_ENABLED").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/system_monitor.log")

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

    def _setup_csv_logging(self) -> None:
        """Set up CSV logging file and headers."""
        csv_config = self.config.get("csv_logging", {})
        if not csv_config.get("enabled", True):
            return

        csv_file = csv_config.get("file", "logs/system_metrics.csv")
        csv_path = Path(csv_file)
        if not csv_path.is_absolute():
            project_root = Path(__file__).parent.parent
            csv_path = project_root / csv_file

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_path = csv_path

        # Write headers if file doesn't exist
        if not csv_path.exists():
            headers = []
            if csv_config.get("include_timestamp", True):
                headers.append("timestamp")
            if csv_config.get("include_cpu", True):
                headers.append("cpu_percent")
            if csv_config.get("include_memory", True):
                headers.extend(["memory_percent", "memory_used_gb", "memory_total_gb"])
            if csv_config.get("include_disk", True):
                headers.extend(["disk_percent", "disk_used_gb", "disk_total_gb"])
            if csv_config.get("include_network", False):
                headers.extend(["network_sent_mb", "network_recv_mb"])

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"CSV log file initialized: {csv_path}")

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage.

        Returns:
            CPU usage as percentage (0-100).
        """
        return psutil.cpu_percent(interval=1)

    def _get_memory_usage(self) -> Tuple[float, float, float]:
        """Get current memory usage.

        Returns:
            Tuple of (percentage, used_gb, total_gb).
        """
        memory = psutil.virtual_memory()
        used_gb = memory.used / (1024 ** 3)
        total_gb = memory.total / (1024 ** 3)
        return memory.percent, used_gb, total_gb

    def _get_disk_usage(self, path: str = "/") -> Tuple[float, float, float]:
        """Get current disk usage for a path.

        Args:
            path: Path to check disk usage for.

        Returns:
            Tuple of (percentage, used_gb, total_gb).
        """
        disk = psutil.disk_usage(path)
        used_gb = disk.used / (1024 ** 3)
        total_gb = disk.total / (1024 ** 3)
        return disk.percent, used_gb, total_gb

    def _check_thresholds(
        self, value: float, warning: float, critical: float
    ) -> Optional[str]:
        """Check if value exceeds thresholds.

        Args:
            value: Current value to check.
            warning: Warning threshold.
            critical: Critical threshold.

        Returns:
            Alert level ('warning' or 'critical') or None.
        """
        if value >= critical:
            return "critical"
        elif value >= warning:
            return "warning"
        return None

    def _should_send_notification(
        self, alert_type: str, level: str
    ) -> bool:
        """Check if notification should be sent based on cooldown.

        Args:
            alert_type: Type of alert (cpu, memory, disk).
            level: Alert level (warning, critical).

        Returns:
            True if notification should be sent.
        """
        if not self.config["notifications"]["enabled"]:
            return False

        key = f"{alert_type}_{level}"
        cooldown = self.config["notifications"]["cooldown_period"]
        current_time = time.time()

        if key in self.last_notification_time:
            if current_time - self.last_notification_time[key] < cooldown:
                return False

        self.last_notification_time[key] = current_time
        return True

    def _send_notification(
        self, title: str, message: str, level: str
    ) -> None:
        """Send desktop notification.

        Args:
            title: Notification title.
            message: Notification message.
            level: Alert level (warning, critical).
        """
        if not self.config["notifications"]["enabled"]:
            return

        duration = self.config["notifications"].get(
            f"{level}_duration", 5
        )

        try:
            notification.notify(
                title=title,
                message=message,
                timeout=duration,
                app_name="System Monitor",
            )
            logger.info(f"Notification sent: {title} - {message}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def _check_cpu(self) -> None:
        """Check CPU usage and send notifications if needed."""
        if not self.config["cpu"]["enabled"]:
            return

        cpu_percent = self._get_cpu_usage()
        warning_threshold = self.config["cpu"]["warning_threshold"]
        critical_threshold = self.config["cpu"]["critical_threshold"]

        alert_level = self._check_thresholds(
            cpu_percent, warning_threshold, critical_threshold
        )

        if alert_level:
            if alert_level == "critical" and self.config["cpu"]["notify_on_critical"]:
                if self._should_send_notification("cpu", "critical"):
                    self._send_notification(
                        "CPU Critical Alert",
                        f"CPU usage is at {cpu_percent:.1f}% (threshold: {critical_threshold}%)",
                        "critical",
                    )
                    self.stats["critical_alerts_sent"] += 1

            elif alert_level == "warning" and self.config["cpu"]["notify_on_warning"]:
                if self._should_send_notification("cpu", "warning"):
                    self._send_notification(
                        "CPU Warning",
                        f"CPU usage is at {cpu_percent:.1f}% (threshold: {warning_threshold}%)",
                        "warning",
                    )
                    self.stats["warnings_sent"] += 1

    def _check_memory(self) -> None:
        """Check memory usage and send notifications if needed."""
        if not self.config["memory"]["enabled"]:
            return

        memory_percent, used_gb, total_gb = self._get_memory_usage()
        warning_threshold = self.config["memory"]["warning_threshold"]
        critical_threshold = self.config["memory"]["critical_threshold"]

        alert_level = self._check_thresholds(
            memory_percent, warning_threshold, critical_threshold
        )

        if alert_level:
            message = (
                f"Memory usage is at {memory_percent:.1f}% "
                f"({used_gb:.2f} GB / {total_gb:.2f} GB)"
            )

            if alert_level == "critical" and self.config["memory"]["notify_on_critical"]:
                if self._should_send_notification("memory", "critical"):
                    threshold_msg = f" (threshold: {critical_threshold}%)"
                    self._send_notification(
                        "Memory Critical Alert", message + threshold_msg, "critical"
                    )
                    self.stats["critical_alerts_sent"] += 1

            elif alert_level == "warning" and self.config["memory"]["notify_on_warning"]:
                if self._should_send_notification("memory", "warning"):
                    threshold_msg = f" (threshold: {warning_threshold}%)"
                    self._send_notification(
                        "Memory Warning", message + threshold_msg, "warning"
                    )
                    self.stats["warnings_sent"] += 1

    def _check_disk(self) -> None:
        """Check disk usage and send notifications if needed."""
        if not self.config["disk"]["enabled"]:
            return

        monitor_paths = self.config["disk"].get("monitor_paths", ["/"])

        for path in monitor_paths:
            try:
                disk_percent, used_gb, total_gb = self._get_disk_usage(path)
                warning_threshold = self.config["disk"]["warning_threshold"]
                critical_threshold = self.config["disk"]["critical_threshold"]

                alert_level = self._check_thresholds(
                    disk_percent, warning_threshold, critical_threshold
                )

                if alert_level:
                    message = (
                        f"Disk usage on {path} is at {disk_percent:.1f}% "
                        f"({used_gb:.2f} GB / {total_gb:.2f} GB)"
                    )

                    if alert_level == "critical" and self.config["disk"]["notify_on_critical"]:
                        if self._should_send_notification(f"disk_{path}", "critical"):
                            threshold_msg = f" (threshold: {critical_threshold}%)"
                            self._send_notification(
                                f"Disk Critical Alert - {path}",
                                message + threshold_msg,
                                "critical",
                            )
                            self.stats["critical_alerts_sent"] += 1

                    elif alert_level == "warning" and self.config["disk"]["notify_on_warning"]:
                        if self._should_send_notification(f"disk_{path}", "warning"):
                            threshold_msg = f" (threshold: {warning_threshold}%)"
                            self._send_notification(
                                f"Disk Warning - {path}",
                                message + threshold_msg,
                                "warning",
                            )
                            self.stats["warnings_sent"] += 1

            except PermissionError:
                logger.warning(f"Permission denied accessing disk path: {path}")
            except Exception as e:
                logger.error(f"Error checking disk usage for {path}: {e}")

    def _log_to_csv(self) -> None:
        """Log current system metrics to CSV file."""
        csv_config = self.config.get("csv_logging", {})
        if not csv_config.get("enabled", True):
            return

        try:
            row = []

            if csv_config.get("include_timestamp", True):
                row.append(datetime.now().isoformat())

            if csv_config.get("include_cpu", True):
                row.append(self._get_cpu_usage())

            if csv_config.get("include_memory", True):
                memory_percent, used_gb, total_gb = self._get_memory_usage()
                row.extend([memory_percent, used_gb, total_gb])

            if csv_config.get("include_disk", True):
                disk_percent, used_gb, total_gb = self._get_disk_usage()
                row.extend([disk_percent, used_gb, total_gb])

            if csv_config.get("include_network", False):
                net_io = psutil.net_io_counters()
                row.extend(
                    [
                        net_io.bytes_sent / (1024 ** 2),
                        net_io.bytes_recv / (1024 ** 2),
                    ]
                )

            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)

            self.stats["csv_entries_logged"] += 1
            logger.debug(f"Logged metrics to CSV: {row}")

        except Exception as e:
            logger.error(f"Error logging to CSV: {e}")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Starting system monitoring")
        interval = self.config["monitoring"]["interval"]

        while self.running:
            try:
                self._check_cpu()
                self._check_memory()
                self._check_disk()

                self.stats["checks_performed"] += 1
                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(interval)

    def _csv_log_loop(self) -> None:
        """CSV logging loop."""
        logger.info("Starting CSV logging")
        interval = self.config["monitoring"]["csv_log_interval"]

        while self.running:
            try:
                self._log_to_csv()
                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in CSV logging loop: {e}", exc_info=True)
                time.sleep(interval)

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def start(self) -> None:
        """Start monitoring system resources."""
        if self.running:
            logger.warning("Monitor is already running")
            return

        self.running = True

        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self.monitor_thread.start()

        # Start CSV logging thread
        csv_config = self.config.get("csv_logging", {})
        if csv_config.get("enabled", True):
            self.csv_log_thread = threading.Thread(
                target=self._csv_log_loop, daemon=True
            )
            self.csv_log_thread.start()

        logger.info("System monitor started")

    def stop(self) -> None:
        """Stop monitoring system resources."""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping system monitor...")

        # Wait for threads to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        if self.csv_log_thread:
            self.csv_log_thread.join(timeout=5)

        logger.info("System monitor stopped")
        logger.info(f"Final statistics: {self.stats}")

    def run(self) -> None:
        """Run monitor until interrupted."""
        self.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()


def main() -> int:
    """Main entry point for system monitor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor system CPU, memory, and disk usage"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--daemon",
        action="store_true",
        help="Run as daemon (runs until interrupted)",
    )

    args = parser.parse_args()

    try:
        monitor = SystemMonitor(config_path=args.config)
        monitor.run()

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
