"""Process Monitor - Monitor and kill processes exceeding resource limits.

This module provides functionality to monitor running processes, detect those
exceeding CPU or memory usage limits, and automatically kill them with logging
and desktop notifications.
"""

import logging
import logging.handlers
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import psutil
import yaml
from dotenv import load_dotenv

try:
    from plyer import notification
except ImportError:
    notification = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """Monitors processes and kills those exceeding resource limits."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize ProcessMonitor with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.process_tracking: Dict[int, Dict] = {}  # Track processes over time
        self.warning_sent: Set[int] = set()  # Processes that received warnings
        self.stats = {
            "checks_performed": 0,
            "processes_checked": 0,
            "warnings_sent": 0,
            "processes_killed": 0,
            "killed_processes": [],
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
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("MONITORING_INTERVAL"):
            config["monitoring"]["interval"] = int(os.getenv("MONITORING_INTERVAL"))
        if os.getenv("CPU_KILL_THRESHOLD"):
            config["cpu"]["kill_threshold"] = float(os.getenv("CPU_KILL_THRESHOLD"))
        if os.getenv("MEMORY_KILL_THRESHOLD"):
            config["memory"]["kill_threshold"] = float(os.getenv("MEMORY_KILL_THRESHOLD"))
        if os.getenv("NOTIFICATIONS_ENABLED"):
            config["notifications"]["enabled"] = (
                os.getenv("NOTIFICATIONS_ENABLED").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/process_monitor.log")

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

    def _is_whitelisted(self, process: psutil.Process) -> bool:
        """Check if process is whitelisted.

        Args:
            process: Process object to check.

        Returns:
            True if process is whitelisted.
        """
        if not self.config.get("whitelist", {}).get("enabled", True):
            return False

        try:
            process_name = process.name()
            process_id = process.pid

            whitelist_names = self.config.get("whitelist", {}).get("process_names", [])
            whitelist_ids = self.config.get("whitelist", {}).get("process_ids", [])

            if process_name in whitelist_names:
                return True
            if process_id in whitelist_ids:
                return True

            # Check if it's a system process (running as root/system)
            try:
                if process.username() in ["root", "SYSTEM", "LOCAL SERVICE"]:
                    return True
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        return False

    def _get_process_usage(self, process: psutil.Process) -> Tuple[float, float]:
        """Get CPU and memory usage for a process.

        Args:
            process: Process object.

        Returns:
            Tuple of (cpu_percent, memory_percent).
        """
        try:
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory().total
            memory_percent = (memory_info.rss / system_memory) * 100

            return cpu_percent, memory_percent

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return 0.0, 0.0

    def _check_process(self, process: psutil.Process) -> None:
        """Check a single process for resource limits.

        Args:
            process: Process object to check.
        """
        try:
            pid = process.pid

            # Skip whitelisted processes
            if self._is_whitelisted(process):
                return

            # Get usage
            cpu_percent, memory_percent = self._get_process_usage(process)

            if cpu_percent == 0.0 and memory_percent == 0.0:
                # Process may have terminated
                if pid in self.process_tracking:
                    del self.process_tracking[pid]
                return

            # Check CPU limits
            if self.config.get("cpu", {}).get("enabled", True):
                self._check_cpu_limit(process, cpu_percent, pid)

            # Check memory limits
            if self.config.get("memory", {}).get("enabled", True):
                self._check_memory_limit(process, memory_percent, pid)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process terminated or access denied
            if pid in self.process_tracking:
                del self.process_tracking[pid]

    def _check_cpu_limit(
        self, process: psutil.Process, cpu_percent: float, pid: int
    ) -> None:
        """Check CPU usage limit for a process.

        Args:
            process: Process object.
            cpu_percent: Current CPU usage percentage.
            pid: Process ID.
        """
        cpu_config = self.config.get("cpu", {})
        kill_threshold = cpu_config.get("kill_threshold", 95.0)
        warning_threshold = cpu_config.get("warning_threshold", 80.0)
        check_duration = cpu_config.get("check_duration", 10)

        if cpu_percent >= kill_threshold:
            # Track how long process has exceeded limit
            if pid not in self.process_tracking:
                self.process_tracking[pid] = {
                    "cpu_exceed_start": time.time(),
                    "memory_exceed_start": None,
                    "warned": False,
                }
            else:
                if self.process_tracking[pid].get("cpu_exceed_start") is None:
                    self.process_tracking[pid]["cpu_exceed_start"] = time.time()

            exceed_duration = time.time() - self.process_tracking[pid]["cpu_exceed_start"]

            if exceed_duration >= check_duration:
                # Process has exceeded limit for required duration
                if self.config.get("actions", {}).get("kill_on_cpu_exceed", True):
                    self._kill_process(process, pid, "CPU", cpu_percent)

        elif cpu_percent >= warning_threshold:
            # Send warning if not already sent
            if pid not in self.warning_sent:
                self._send_warning(process, pid, "CPU", cpu_percent)
                self.warning_sent.add(pid)
        else:
            # Reset tracking if below threshold
            if pid in self.process_tracking:
                self.process_tracking[pid]["cpu_exceed_start"] = None

    def _check_memory_limit(
        self, process: psutil.Process, memory_percent: float, pid: int
    ) -> None:
        """Check memory usage limit for a process.

        Args:
            process: Process object.
            memory_percent: Current memory usage percentage.
            pid: Process ID.
        """
        memory_config = self.config.get("memory", {})
        kill_threshold = memory_config.get("kill_threshold", 90.0)
        warning_threshold = memory_config.get("warning_threshold", 80.0)
        check_duration = memory_config.get("check_duration", 10)
        absolute_limit_mb = memory_config.get("absolute_limit_mb", 0)

        should_kill = False

        # Check percentage limit
        if memory_percent >= kill_threshold:
            should_kill = True

        # Check absolute limit if configured
        if absolute_limit_mb > 0:
            try:
                memory_mb = process.memory_info().rss / (1024 ** 2)
                if memory_mb >= absolute_limit_mb:
                    should_kill = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return

        if should_kill:
            # Track how long process has exceeded limit
            if pid not in self.process_tracking:
                self.process_tracking[pid] = {
                    "cpu_exceed_start": None,
                    "memory_exceed_start": time.time(),
                    "warned": False,
                }
            else:
                if self.process_tracking[pid].get("memory_exceed_start") is None:
                    self.process_tracking[pid]["memory_exceed_start"] = time.time()

            exceed_duration = (
                time.time() - self.process_tracking[pid]["memory_exceed_start"]
            )

            if exceed_duration >= check_duration:
                # Process has exceeded limit for required duration
                if self.config.get("actions", {}).get("kill_on_memory_exceed", True):
                    self._kill_process(process, pid, "Memory", memory_percent)

        elif memory_percent >= warning_threshold:
            # Send warning if not already sent
            if pid not in self.warning_sent:
                self._send_warning(process, pid, "Memory", memory_percent)
                self.warning_sent.add(pid)
        else:
            # Reset tracking if below threshold
            if pid in self.process_tracking:
                self.process_tracking[pid]["memory_exceed_start"] = None

    def _send_warning(
        self, process: psutil.Process, pid: int, resource_type: str, usage: float
    ) -> None:
        """Send warning notification for process exceeding warning threshold.

        Args:
            process: Process object.
            pid: Process ID.
            resource_type: Type of resource (CPU or Memory).
            usage: Current usage percentage.
        """
        if not self.config.get("notifications", {}).get("notify_on_warning", True):
            return

        try:
            process_name = process.name()
            message = (
                f"Process '{process_name}' (PID: {pid}) is using "
                f"{usage:.1f}% {resource_type.lower()}"
            )

            logger.warning(message)

            if notification and self.config.get("notifications", {}).get("enabled", True):
                try:
                    notification.notify(
                        title=f"Process {resource_type} Warning",
                        message=message,
                        timeout=self.config.get("notifications", {}).get(
                            "notification_duration", 10
                        ),
                        app_name="Process Monitor",
                    )
                except Exception as e:
                    logger.warning(f"Could not send notification: {e}")

            self.stats["warnings_sent"] += 1

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def _kill_process(
        self, process: psutil.Process, pid: int, resource_type: str, usage: float
    ) -> None:
        """Kill a process that exceeds resource limits.

        Args:
            process: Process object to kill.
            pid: Process ID.
            resource_type: Type of resource that exceeded limit (CPU or Memory).
            usage: Current usage percentage.
        """
        try:
            process_name = process.name()
            process_cmdline = " ".join(process.cmdline()[:3]) if process.cmdline() else ""

            # Try graceful termination first
            try:
                process.terminate()
                time.sleep(2)

                # Check if process is still running
                if process.is_running():
                    # Force kill
                    process.kill()
                    logger.warning(f"Force killed process: {process_name} (PID: {pid})")
                else:
                    logger.info(f"Terminated process: {process_name} (PID: {pid})")

            except psutil.NoSuchProcess:
                # Process already terminated
                logger.debug(f"Process already terminated: {process_name} (PID: {pid})")
                return

            # Log the kill
            kill_info = {
                "pid": pid,
                "name": process_name,
                "resource": resource_type,
                "usage": usage,
                "timestamp": datetime.now().isoformat(),
                "command": process_cmdline,
            }

            if self.config.get("logging", {}).get("log_killed_processes", True):
                logger.warning(
                    f"Killed process: {process_name} (PID: {pid}) - "
                    f"{resource_type} usage: {usage:.1f}%"
                )

            self.stats["processes_killed"] += 1
            self.stats["killed_processes"].append(kill_info)

            # Send notification
            if self.config.get("notifications", {}).get("notify_on_kill", True):
                if notification and self.config.get("notifications", {}).get("enabled", True):
                    try:
                        notification.notify(
                            title="Process Killed",
                            message=(
                                f"Killed '{process_name}' (PID: {pid})\n"
                                f"{resource_type} usage: {usage:.1f}%"
                            ),
                            timeout=self.config.get("notifications", {}).get(
                                "notification_duration", 10
                            ),
                            app_name="Process Monitor",
                        )
                    except Exception as e:
                        logger.warning(f"Could not send notification: {e}")

            # Clean up tracking
            if pid in self.process_tracking:
                del self.process_tracking[pid]
            if pid in self.warning_sent:
                self.warning_sent.remove(pid)

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Could not kill process {pid}: {e}")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Starting process monitoring")
        interval = self.config["monitoring"]["interval"]

        while self.running:
            try:
                # Get all processes
                processes = list(psutil.process_iter(["pid", "name"]))

                self.stats["checks_performed"] += 1
                self.stats["processes_checked"] += len(processes)

                # Check each process
                for proc_info in processes:
                    try:
                        process = psutil.Process(proc_info.info["pid"])
                        self._check_process(process)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process terminated or access denied, skip
                        continue

                # Clean up tracking for processes that no longer exist
                existing_pids = {p.info["pid"] for p in psutil.process_iter(["pid"])}
                dead_pids = set(self.process_tracking.keys()) - existing_pids
                for pid in dead_pids:
                    del self.process_tracking[pid]
                    self.warning_sent.discard(pid)

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(interval)

    def _generate_report(self) -> None:
        """Generate monitoring report."""
        if not self.config.get("reporting", {}).get("generate_reports", True):
            return

        report_config = self.config.get("reporting", {})
        report_file = report_config.get("report_file", "logs/process_monitor_report.txt")

        report_path = Path(report_file)
        if not report_path.is_absolute():
            project_root = Path(__file__).parent.parent
            report_path = project_root / report_file

        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("Process Monitor Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            f.write("Statistics\n")
            f.write("-" * 60 + "\n")
            f.write(f"Checks Performed: {self.stats['checks_performed']}\n")
            f.write(f"Processes Checked: {self.stats['processes_checked']}\n")
            f.write(f"Warnings Sent: {self.stats['warnings_sent']}\n")
            f.write(f"Processes Killed: {self.stats['processes_killed']}\n")
            f.write("\n")

            if self.stats["killed_processes"]:
                f.write("Killed Processes\n")
                f.write("-" * 60 + "\n")
                for kill_info in self.stats["killed_processes"][-50:]:  # Last 50
                    f.write(
                        f"PID: {kill_info['pid']}, Name: {kill_info['name']}, "
                        f"Resource: {kill_info['resource']}, Usage: {kill_info['usage']:.1f}%, "
                        f"Time: {kill_info['timestamp']}\n"
                    )

        logger.info(f"Report generated: {report_path}")

    def start(self) -> None:
        """Start process monitoring."""
        if self.running:
            logger.warning("Monitor is already running")
            return

        self.running = True

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Process monitor started")

    def stop(self) -> None:
        """Stop process monitoring."""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping process monitor...")

        # Wait for thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        # Generate final report
        self._generate_report()

        logger.info("Process monitor stopped")
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
    """Main entry point for process monitor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor and kill processes exceeding resource limits"
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
        monitor = ProcessMonitor(config_path=args.config)
        monitor.run()

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except PermissionError as e:
        logger.error(f"Permission error: {e}. May need to run with appropriate permissions.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
