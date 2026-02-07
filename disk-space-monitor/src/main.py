"""Disk Space Monitor - Monitor disk space and generate desktop alerts.

This module provides functionality to monitor disk space usage across all
drives, generate desktop alerts when free space falls below configured
thresholds, and provide cleanup suggestions. Includes comprehensive logging
and cross-platform support.
"""

import logging
import logging.handlers
import os
import platform
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DiskSpaceMonitor:
    """Monitors disk space and generates alerts with cleanup suggestions."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize DiskSpaceMonitor with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.alert_history: Dict[str, List[str]] = {}
        self.stats = {
            "drives_checked": 0,
            "alerts_sent": 0,
            "errors": 0,
            "errors_list": [],
        }

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
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("WARNING_THRESHOLD"):
            config["thresholds"]["warning"] = float(os.getenv("WARNING_THRESHOLD"))
        if os.getenv("CRITICAL_THRESHOLD"):
            config["thresholds"]["critical"] = float(os.getenv("CRITICAL_THRESHOLD"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/disk_space_monitor.log")

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

    def _format_size(self, size_bytes: int) -> str:
        """Format disk size in human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string (e.g., "1.5 GB").
        """
        if size_bytes == 0:
            return "0 B"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _get_disk_usage(self, path: str) -> Optional[Tuple[int, int, int]]:
        """Get disk usage for a path.

        Args:
            path: Path to check.

        Returns:
            Tuple of (total, used, free) in bytes, or None if error.
        """
        try:
            usage = shutil.disk_usage(path)
            return (usage.total, usage.used, usage.free)
        except Exception as e:
            logger.warning(f"Error getting disk usage for {path}: {e}")
            return None

    def _get_all_drives(self) -> List[str]:
        """Get list of all drives/partitions.

        Returns:
            List of drive paths.
        """
        drives = []

        try:
            if platform.system() == "Windows":
                # Windows: Get all drive letters
                import string
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        drives.append(drive)
            else:
                # Unix-like: Use psutil to get all partitions
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    if partition.mountpoint:
                        drives.append(partition.mountpoint)

        except Exception as e:
            logger.error(f"Error getting drives: {e}")
            # Fallback to current directory
            drives.append(os.path.expanduser("~"))

        return drives

    def _calculate_percentage_free(self, total: int, free: int) -> float:
        """Calculate percentage of free space.

        Args:
            total: Total disk space in bytes.
            free: Free disk space in bytes.

        Returns:
            Percentage of free space.
        """
        if total == 0:
            return 0.0
        return (free / total) * 100.0

    def _get_alert_level(
        self, free_percentage: float
    ) -> Optional[str]:
        """Determine alert level based on free space percentage.

        Args:
            free_percentage: Percentage of free space.

        Returns:
            Alert level ("critical", "warning", or None).
        """
        thresholds = self.config.get("thresholds", {})
        critical = thresholds.get("critical", 10.0)
        warning = thresholds.get("warning", 20.0)

        if free_percentage < critical:
            return "critical"
        elif free_percentage < warning:
            return "warning"
        return None

    def _should_send_alert(self, drive: str, level: str) -> bool:
        """Check if alert should be sent (avoid spam).

        Args:
            drive: Drive path.
            level: Alert level.

        Returns:
            True if alert should be sent, False otherwise.
        """
        cooldown_minutes = self.config.get("alert_cooldown_minutes", 60)

        if drive not in self.alert_history:
            self.alert_history[drive] = []

        # Remove old alerts outside cooldown period
        cutoff_time = datetime.now() - timedelta(minutes=cooldown_minutes)
        self.alert_history[drive] = [
            alert_time
            for alert_time in self.alert_history[drive]
            if alert_time > cutoff_time
        ]

        # Check if we've sent an alert recently
        if len(self.alert_history[drive]) > 0:
            return False

        # Record this alert
        self.alert_history[drive].append(datetime.now())
        return True

    def _send_desktop_notification(
        self, title: str, message: str, level: str = "warning"
    ) -> bool:
        """Send desktop notification.

        Args:
            title: Notification title.
            message: Notification message.
            level: Alert level ("critical" or "warning").

        Returns:
            True if notification sent successfully, False otherwise.
        """
        try:
            system = platform.system()

            if system == "Windows":
                # Try using Windows toast notifications
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    duration = 10 if level == "critical" else 5
                    toaster.show_toast(title, message, duration=duration)
                    return True
                except ImportError:
                    # Fallback to simple message box
                    try:
                        import ctypes
                        ctypes.windll.user32.MessageBoxW(
                            0, message, title, 0x40 | 0x1
                        )
                        return True
                    except Exception:
                        logger.warning("Could not send Windows notification")
                        return False

            elif system == "Darwin":  # macOS
                # Use osascript for macOS notifications
                script = (
                    f'display notification "{message}" with title "{title}"'
                )
                subprocess.run(
                    ["osascript", "-e", script],
                    check=False,
                    capture_output=True,
                )
                return True

            else:  # Linux
                # Try notify-send
                urgency = "critical" if level == "critical" else "normal"
                subprocess.run(
                    [
                        "notify-send",
                        "-u",
                        urgency,
                        title,
                        message,
                    ],
                    check=False,
                    capture_output=True,
                )
                return True

        except Exception as e:
            logger.warning(f"Error sending desktop notification: {e}")
            return False

    def _find_large_files(
        self, drive: str, limit: int = 10, min_size_mb: int = 100
    ) -> List[Tuple[str, int]]:
        """Find large files on a drive.

        Args:
            drive: Drive path to search.
            limit: Maximum number of files to return.
            min_size_mb: Minimum file size in MB.

        Returns:
            List of tuples (file_path, size_bytes).
        """
        large_files = []
        min_size_bytes = min_size_mb * 1024 * 1024

        try:
            for root, dirs, files in os.walk(drive):
                # Skip system directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for file in files:
                    try:
                        file_path = Path(root) / file
                        if file_path.is_file():
                            size = file_path.stat().st_size
                            if size >= min_size_bytes:
                                large_files.append((str(file_path), size))
                    except (OSError, PermissionError):
                        continue

                if len(large_files) >= limit * 2:
                    break

            # Sort by size and return top N
            large_files.sort(key=lambda x: x[1], reverse=True)
            return large_files[:limit]

        except Exception as e:
            logger.debug(f"Error finding large files on {drive}: {e}")
            return []

    def _get_cleanup_suggestions(
        self, drive: str, free_percentage: float
    ) -> List[str]:
        """Generate cleanup suggestions for a drive.

        Args:
            drive: Drive path.
            free_percentage: Current free space percentage.

        Returns:
            List of cleanup suggestion strings.
        """
        suggestions = []

        if free_percentage < 20:
            # Find large files
            large_files = self._find_large_files(drive, limit=5, min_size_mb=100)
            if large_files:
                suggestions.append("Large files found:")
                for file_path, size in large_files[:3]:
                    suggestions.append(
                        f"  - {Path(file_path).name}: {self._format_size(size)}"
                    )

            # System-specific suggestions
            system = platform.system()
            if system == "Windows":
                suggestions.append("Consider clearing:")
                suggestions.append("  - Windows Temp folder (%TEMP%)")
                suggestions.append("  - Recycle Bin")
                suggestions.append("  - Browser cache")
            elif system == "Darwin":  # macOS
                suggestions.append("Consider clearing:")
                suggestions.append("  - ~/Library/Caches")
                suggestions.append("  - ~/.Trash")
                suggestions.append("  - Browser cache")
            else:  # Linux
                suggestions.append("Consider clearing:")
                suggestions.append("  - /tmp directory")
                suggestions.append("  - ~/.cache")
                suggestions.append("  - Package cache (apt/yum)")

        return suggestions

    def _check_drive(self, drive: str) -> Optional[Dict]:
        """Check disk space for a single drive.

        Args:
            drive: Drive path to check.

        Returns:
            Dictionary with drive information, or None if error.
        """
        usage = self._get_disk_usage(drive)
        if usage is None:
            return None

        total, used, free = usage
        free_percentage = self._calculate_percentage_free(total, free)

        drive_info = {
            "drive": drive,
            "total": total,
            "used": used,
            "free": free,
            "free_percentage": free_percentage,
        }

        # Check if alert is needed
        alert_level = self._get_alert_level(free_percentage)
        if alert_level:
            if self._should_send_alert(drive, alert_level):
                title = f"Disk Space {alert_level.title()}: {drive}"
                message = (
                    f"Free space: {free_percentage:.1f}% "
                    f"({self._format_size(free)} free of {self._format_size(total)})"
                )

                # Get cleanup suggestions
                suggestions = self._get_cleanup_suggestions(drive, free_percentage)
                if suggestions:
                    message += "\n\nCleanup suggestions:\n" + "\n".join(
                        suggestions[:5]
                    )

                if self._send_desktop_notification(title, message, alert_level):
                    self.stats["alerts_sent"] += 1
                    logger.warning(
                        f"Alert sent for {drive}: {free_percentage:.1f}% free "
                        f"({alert_level})"
                    )

        return drive_info

    def monitor_disks(self) -> Dict[str, any]:
        """Monitor all drives and send alerts if needed.

        Returns:
            Dictionary with monitoring statistics and drive information.
        """
        logger.info("Starting disk space monitoring")

        drives = self._get_all_drives()
        logger.info(f"Found {len(drives)} drives to monitor")

        drive_info_list = []

        for drive in drives:
            self.stats["drives_checked"] += 1
            info = self._check_drive(drive)
            if info:
                drive_info_list.append(info)
                logger.info(
                    f"{drive}: {info['free_percentage']:.1f}% free "
                    f"({self._format_size(info['free'])} free)"
                )

        logger.info("Disk space monitoring completed")
        logger.info(f"Statistics: {self.stats}")

        return {
            "drives": drive_info_list,
            "stats": self.stats,
        }


def main() -> int:
    """Main entry point for disk space monitor."""
    import argparse
    import time

    parser = argparse.ArgumentParser(
        description="Monitor disk space and generate desktop alerts"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-w",
        "--watch",
        action="store_true",
        help="Run in watch mode (check periodically)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Check interval in seconds for watch mode (default: 3600)",
    )

    args = parser.parse_args()

    try:
        monitor = DiskSpaceMonitor(config_path=args.config)

        if args.watch:
            logger.info(f"Running in watch mode (interval: {args.interval}s)")
            try:
                while True:
                    monitor.monitor_disks()
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
        else:
            result = monitor.monitor_disks()

            # Print summary
            print("\n" + "=" * 60)
            print("Disk Space Monitoring Summary")
            print("=" * 60)
            for drive_info in result["drives"]:
                print(
                    f"{drive_info['drive']}: "
                    f"{drive_info['free_percentage']:.1f}% free "
                    f"({monitor._format_size(drive_info['free'])} free of "
                    f"{monitor._format_size(drive_info['total'])})"
                )

            print(f"\nDrives Checked: {result['stats']['drives_checked']}")
            print(f"Alerts Sent: {result['stats']['alerts_sent']}")
            print(f"Errors: {result['stats']['errors']}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
