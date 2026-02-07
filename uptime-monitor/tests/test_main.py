"""Unit tests for uptime monitor."""

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.main import UptimeMonitor


class TestUptimeMonitor(unittest.TestCase):
    """Test cases for UptimeMonitor class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")
        self.db_path = os.path.join(self.temp_dir, "test_uptime.db")

        # Create test config
        config_content = f"""
database:
  file: "{self.db_path}"
  create_tables: true

monitoring:
  interval: 60
  log_snapshots: true

retention:
  auto_cleanup: false
  days_to_keep: 30

logging:
  level: "DEBUG"
  file: "{os.path.join(self.temp_dir, 'test.log')}"
  max_bytes: 1048576
  backup_count: 3
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""
        with open(self.config_path, "w") as f:
            f.write(config_content)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_loads_config(self) -> None:
        """Test that initialization loads configuration correctly."""
        monitor = UptimeMonitor(config_path=self.config_path)
        self.assertEqual(monitor.config["monitoring"]["interval"], 60)
        self.assertEqual(monitor.config["database"]["file"], self.db_path)

    def test_init_creates_database_tables(self) -> None:
        """Test that initialization creates database tables."""
        monitor = UptimeMonitor(config_path=self.config_path)
        self.assertTrue(os.path.exists(self.db_path))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('boot_events', 'shutdown_events', 'uptime_snapshots')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn("boot_events", tables)
        self.assertIn("shutdown_events", tables)
        self.assertIn("uptime_snapshots", tables)

    def test_get_boot_time_returns_datetime_or_none(self) -> None:
        """Test that get_boot_time returns datetime or None."""
        monitor = UptimeMonitor(config_path=self.config_path)
        boot_time = monitor._get_boot_time()
        self.assertTrue(boot_time is None or isinstance(boot_time, datetime))

    def test_get_uptime_seconds_returns_float_or_none(self) -> None:
        """Test that get_uptime_seconds returns float or None."""
        monitor = UptimeMonitor(config_path=self.config_path)
        uptime = monitor._get_uptime_seconds()
        self.assertTrue(uptime is None or isinstance(uptime, (int, float)))

    def test_format_uptime(self) -> None:
        """Test uptime formatting."""
        monitor = UptimeMonitor(config_path=self.config_path)

        # Test various uptime values
        self.assertIn("day", monitor._format_uptime(86400))
        self.assertIn("hour", monitor._format_uptime(3600))
        self.assertIn("minute", monitor._format_uptime(60))
        self.assertIn("second", monitor._format_uptime(1))
        self.assertEqual("0 seconds", monitor._format_uptime(0))

        # Test None
        self.assertEqual("Unknown", monitor._format_uptime(None))

    def test_log_boot_event(self) -> None:
        """Test logging boot event to database."""
        monitor = UptimeMonitor(config_path=self.config_path)
        boot_time = datetime.now()
        uptime_seconds = 3600.0

        result = monitor._log_boot_event(boot_time, uptime_seconds)
        self.assertTrue(result)

        # Verify in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT boot_time FROM boot_events WHERE boot_time = ?", (boot_time.isoformat(),))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], boot_time.isoformat())

    def test_log_boot_event_prevents_duplicates(self) -> None:
        """Test that duplicate boot events are not logged."""
        monitor = UptimeMonitor(config_path=self.config_path)
        boot_time = datetime.now()
        uptime_seconds = 3600.0

        # Log first time
        result1 = monitor._log_boot_event(boot_time, uptime_seconds)
        self.assertTrue(result1)

        # Try to log again
        result2 = monitor._log_boot_event(boot_time, uptime_seconds)
        self.assertFalse(result2)

    def test_log_uptime_snapshot(self) -> None:
        """Test logging uptime snapshot."""
        monitor = UptimeMonitor(config_path=self.config_path)
        uptime_seconds = 7200.0
        boot_time = datetime.now() - timedelta(seconds=7200)

        result = monitor._log_uptime_snapshot(uptime_seconds, boot_time)
        self.assertTrue(result)

        # Verify in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM uptime_snapshots")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 1)

    def test_get_boot_history(self) -> None:
        """Test retrieving boot history."""
        monitor = UptimeMonitor(config_path=self.config_path)

        # Log some boot events
        for i in range(5):
            boot_time = datetime.now() - timedelta(days=i)
            monitor._log_boot_event(boot_time, 3600.0)

        # Get history
        history = monitor.get_boot_history(limit=3)
        self.assertEqual(len(history), 3)
        self.assertIn("boot_time", history[0])

    def test_get_shutdown_history(self) -> None:
        """Test retrieving shutdown history."""
        monitor = UptimeMonitor(config_path=self.config_path)

        # Create shutdown events directly in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for i in range(3):
            session_start = datetime.now() - timedelta(days=i + 1)
            shutdown_time = datetime.now() - timedelta(days=i)
            duration = (shutdown_time - session_start).total_seconds()
            cursor.execute("""
                INSERT INTO shutdown_events 
                (session_start_time, shutdown_time, session_duration_seconds)
                VALUES (?, ?, ?)
            """, (session_start.isoformat(), shutdown_time.isoformat(), duration))
        conn.commit()
        conn.close()

        # Get history
        history = monitor.get_shutdown_history(limit=2)
        self.assertEqual(len(history), 2)
        self.assertIn("session_start_time", history[0])
        self.assertIn("session_duration_formatted", history[0])

    def test_get_statistics(self) -> None:
        """Test getting statistics."""
        monitor = UptimeMonitor(config_path=self.config_path)

        # Add some data
        boot_time = datetime.now()
        monitor._log_boot_event(boot_time, 3600.0)
        monitor._log_uptime_snapshot(3600.0, boot_time)

        stats = monitor.get_statistics()
        self.assertIn("total_boot_events", stats)
        self.assertIn("total_shutdown_events", stats)
        self.assertIn("total_snapshots", stats)
        self.assertGreaterEqual(stats["total_boot_events"], 1)
        self.assertGreaterEqual(stats["total_snapshots"], 1)

    def test_detect_shutdown_events(self) -> None:
        """Test shutdown event detection."""
        monitor = UptimeMonitor(config_path=self.config_path)

        # Log a boot event
        old_boot_time = datetime.now() - timedelta(hours=2)
        monitor._log_boot_event(old_boot_time, 3600.0)

        # Mock current boot time to be newer
        new_boot_time = datetime.now() - timedelta(hours=1)
        with patch.object(monitor, "_get_boot_time", return_value=new_boot_time):
            shutdown_count = monitor._detect_shutdown_events()
            self.assertEqual(shutdown_count, 1)

            # Verify shutdown event was logged
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shutdown_events")
            count = cursor.fetchone()[0]
            conn.close()

            self.assertEqual(count, 1)

    def test_detect_shutdown_events_no_previous_boot(self) -> None:
        """Test shutdown detection when no previous boot exists."""
        monitor = UptimeMonitor(config_path=self.config_path)

        shutdown_count = monitor._detect_shutdown_events()
        self.assertEqual(shutdown_count, 0)

    def test_cleanup_old_entries(self) -> None:
        """Test cleanup of old entries."""
        monitor = UptimeMonitor(config_path=self.config_path)

        # Add old snapshot
        old_timestamp = datetime.now() - timedelta(days=100)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO uptime_snapshots (timestamp, uptime_seconds, boot_time)
            VALUES (?, ?, ?)
        """, (old_timestamp.isoformat(), 3600.0, old_timestamp.isoformat()))
        conn.commit()
        conn.close()

        # Enable cleanup in config
        monitor.config["retention"]["auto_cleanup"] = True
        monitor.config["retention"]["days_to_keep"] = 90

        # Run cleanup
        monitor._cleanup_old_entries()

        # Verify old entry was removed
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM uptime_snapshots")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 0)

    def test_get_system_info(self) -> None:
        """Test system info generation."""
        monitor = UptimeMonitor(config_path=self.config_path)
        system_info = monitor._get_system_info()
        self.assertIsInstance(system_info, str)
        self.assertIn("Platform", system_info)

    @patch("src.main.UptimeMonitor._get_boot_time")
    @patch("src.main.UptimeMonitor._get_uptime_seconds")
    def test_check_and_log(self, mock_uptime, mock_boot) -> None:
        """Test check_and_log method."""
        mock_boot.return_value = datetime.now() - timedelta(hours=2)
        mock_uptime.return_value = 7200.0

        monitor = UptimeMonitor(config_path=self.config_path)
        results = monitor.check_and_log()

        self.assertIn("boot_time", results)
        self.assertIn("uptime_seconds", results)
        self.assertIn("uptime_formatted", results)
        self.assertIsNotNone(results["boot_time"])

    def test_config_file_not_found(self) -> None:
        """Test error handling for missing config file."""
        with self.assertRaises(FileNotFoundError):
            UptimeMonitor(config_path="nonexistent_config.yaml")


if __name__ == "__main__":
    unittest.main()
