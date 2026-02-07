"""Unit tests for file usage tracker."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    FileUsageTracker,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "database": "./file_usage.db",
                "tracking_window_days": 60,
                "organize_by": "access",
                "recursive": True,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["database"] == "./file_usage.db"
            assert result["tracking_window_days"] == 60
            assert result["organize_by"] == "access"
        finally:
            config_path.unlink()

    def test_load_config_file_not_found(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_config_invalid_yaml(self):
        """Test that invalid YAML raises YAMLError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                load_config(config_path)
        finally:
            config_path.unlink()


class TestFileUsageTracker:
    """Test FileUsageTracker class."""

    def test_init(self):
        """Test initialization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(
                database_path=db_path,
                tracking_window_days=30,
                organize_by="frequency",
            )

            assert tracker.database_path == db_path.resolve()
            assert tracker.tracking_window_days == 30
            assert tracker.organize_by == "frequency"
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_init_invalid_organize_by(self):
        """Test that invalid organize_by raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="organize_by must be"):
                FileUsageTracker(
                    database_path=db_path,
                    organize_by="invalid",
                )
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_get_frequency_category(self):
        """Test frequency category calculation."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(database_path=db_path)

            assert tracker._get_frequency_category(50, 0) == "very_frequent"
            assert tracker._get_frequency_category(20, 0) == "frequent"
            assert tracker._get_frequency_category(5, 0) == "moderate"
            assert tracker._get_frequency_category(1, 0) == "occasional"
            assert tracker._get_frequency_category(0, 0) == "rare"
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_track_files(self):
        """Test file tracking."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(database_path=db_path)

            with tempfile.TemporaryDirectory() as tmpdir:
                dir_path = Path(tmpdir)
                file1 = dir_path / "file1.txt"
                file1.write_text("content")

                stats = tracker.track_files([dir_path])

                assert stats["files_scanned"] >= 1
                assert stats["access_records_added"] >= 1
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_track_files_recursive(self):
        """Test recursive file tracking."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(database_path=db_path)

            with tempfile.TemporaryDirectory() as tmpdir:
                dir_path = Path(tmpdir)
                subdir = dir_path / "subdir"
                subdir.mkdir()
                file1 = dir_path / "file1.txt"
                file1.write_text("content")
                file2 = subdir / "file2.txt"
                file2.write_text("content")

                stats = tracker.track_files([dir_path], recursive=True)

                assert stats["files_scanned"] >= 2
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_calculate_access_frequency(self):
        """Test access frequency calculation."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(database_path=db_path)

            with tempfile.TemporaryDirectory() as tmpdir:
                file_path = Path(tmpdir) / "test.txt"
                file_path.write_text("content")

                tracker.track_files([file_path])

                access_count, mod_count = tracker._calculate_access_frequency(
                    str(file_path)
                )

                assert access_count >= 0
                assert mod_count >= 0
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_get_usage_report(self):
        """Test usage report generation."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(database_path=db_path)

            with tempfile.TemporaryDirectory() as tmpdir:
                file_path = Path(tmpdir) / "test.txt"
                file_path.write_text("content")

                tracker.track_files([file_path])
                report = tracker.get_usage_report([file_path])

                assert isinstance(report, list)
                assert len(report) >= 1
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_format_report(self):
        """Test report formatting."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(database_path=db_path)

            report_data = [
                {
                    "path": "/path/to/file.txt",
                    "name": "file.txt",
                    "size": 1000,
                    "access_count": 10,
                    "modification_count": 2,
                    "frequency_category": "moderate",
                    "last_accessed": "2024-01-15T12:00:00",
                    "last_modified": "2024-01-10T10:00:00",
                }
            ]

            report = tracker.format_report(report_data)

            assert "File Usage Frequency Report" in report
            assert "/path/to/file.txt" in report
            assert "moderate" in report
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_format_report_empty(self):
        """Test report formatting with no data."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(database_path=db_path)
            report = tracker.format_report([])

            assert "No file usage data found" in report
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_organize_files_dry_run(self):
        """Test file organization in dry run mode."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            tracker = FileUsageTracker(database_path=db_path)

            with tempfile.TemporaryDirectory() as tmpdir:
                file_path = Path(tmpdir) / "test.txt"
                file_path.write_text("content")

                tracker.track_files([file_path])

                dest_dir = Path(tmpdir) / "organized"
                stats = tracker.organize_files(
                    [file_path], dest_dir, dry_run=True
                )

                assert stats["files_organized"] >= 1
                assert not (dest_dir / "rare" / "test.txt").exists()
        finally:
            if db_path.exists():
                db_path.unlink()
