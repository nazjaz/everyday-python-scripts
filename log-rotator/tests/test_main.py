"""Unit tests for Log Rotator."""

import gzip
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import LogRotator


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "rotation": {
            "log_directory": ".",
            "archive_directory": "archive",
            "keep_count": 5,
            "patterns": ["*.log"],
            "compress": True,
            "add_date_stamp": True,
            "date_format": "%Y%m%d",
            "max_age_days": 0,
        },
        "logging": {
            "level": "INFO",
            "file": "logs/test.log",
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def temp_config_file(sample_config, tmp_path):
    """Create temporary configuration file."""
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)
    return str(config_path)


@pytest.fixture
def temp_log_directory(tmp_path):
    """Create temporary directory with test log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Create test log files with different modification times
    for i in range(10):
        log_file = log_dir / f"app.log.{i}"
        log_file.write_text(f"Log content {i}")
        # Set modification time (older files have lower timestamps)
        import time
        mtime = time.time() - (i * 3600)  # 1 hour apart
        os.utime(log_file, (mtime, mtime))

    return log_dir


class TestLogRotator:
    """Test cases for LogRotator class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        rotator = LogRotator(config_path=temp_config_file)
        assert rotator.config is not None
        assert "rotation" in rotator.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            LogRotator(config_path="nonexistent.yaml")

    def test_get_log_files(self, temp_config_file, temp_log_directory):
        """Test getting log files matching patterns."""
        rotator = LogRotator(config_path=temp_config_file)
        log_files = rotator._get_log_files(temp_log_directory, ["*.log.*"])

        assert len(log_files) == 10
        # Should be sorted by modification time (newest first)
        assert log_files[0][1] > log_files[-1][1]

    def test_get_log_files_no_match(self, temp_config_file, tmp_path):
        """Test getting log files when none match."""
        rotator = LogRotator(config_path=temp_config_file)
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        log_files = rotator._get_log_files(empty_dir, ["*.log"])
        assert len(log_files) == 0

    def test_add_date_stamp(self, temp_config_file):
        """Test adding date stamp to filename."""
        rotator = LogRotator(config_path=temp_config_file)
        file_path = Path("app.log")
        stamped_path = rotator._add_date_stamp(file_path, "%Y%m%d")

        assert "app" in str(stamped_path)
        assert ".log" in str(stamped_path)
        assert len(str(stamped_path)) > len(str(file_path))

    def test_compress_file(self, temp_config_file, tmp_path):
        """Test compressing a file."""
        rotator = LogRotator(config_path=temp_config_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for compression")

        compressed_path = rotator._compress_file(test_file)

        assert compressed_path.exists()
        assert compressed_path.suffix == ".gz"
        # Verify it's actually compressed
        with gzip.open(compressed_path, "rt") as f:
            content = f.read()
            assert "Test content" in content

    def test_compress_file_custom_dest(self, temp_config_file, tmp_path):
        """Test compressing file to custom destination."""
        rotator = LogRotator(config_path=temp_config_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        dest_path = tmp_path / "custom.gz"

        compressed_path = rotator._compress_file(test_file, dest_path)

        assert compressed_path == dest_path
        assert dest_path.exists()

    def test_archive_file(self, temp_config_file, tmp_path):
        """Test archiving a file."""
        rotator = LogRotator(config_path=temp_config_file)
        log_file = tmp_path / "app.log"
        log_file.write_text("Log content")
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        archived_path = rotator._archive_file(log_file, archive_dir, compress=True)

        assert archived_path is not None
        assert archived_path.exists()
        assert not log_file.exists()  # Original should be removed
        assert archive_dir.exists()

    def test_archive_file_no_compress(self, temp_config_file, tmp_path):
        """Test archiving without compression."""
        rotator = LogRotator(config_path=temp_config_file)
        log_file = tmp_path / "app.log"
        log_file.write_text("Log content")
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        archived_path = rotator._archive_file(
            log_file, archive_dir, compress=False, add_date_stamp=False
        )

        assert archived_path is not None
        assert archived_path.exists()
        assert archived_path.suffix == ".log"  # Not compressed

    def test_rotate_logs(self, temp_config_file, temp_log_directory, tmp_path):
        """Test rotating log files."""
        rotator = LogRotator(config_path=temp_config_file)
        rotator.config["rotation"]["keep_count"] = 3
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        stats = rotator.rotate_logs(
            log_directory=str(temp_log_directory),
            archive_directory=str(archive_dir),
        )

        # Should keep 3 most recent
        remaining_logs = list(temp_log_directory.glob("*.log.*"))
        assert len(remaining_logs) == 3

        # Should archive the rest
        archived_files = list(archive_dir.glob("*"))
        assert len(archived_files) == 7

        assert stats["files_kept"] == 3
        assert stats["files_archived"] == 7

    def test_rotate_logs_keep_all(self, temp_config_file, temp_log_directory, tmp_path):
        """Test rotation when keep_count exceeds file count."""
        rotator = LogRotator(config_path=temp_config_file)
        rotator.config["rotation"]["keep_count"] = 20  # More than files
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        stats = rotator.rotate_logs(
            log_directory=str(temp_log_directory),
            archive_directory=str(archive_dir),
        )

        # Should keep all files
        remaining_logs = list(temp_log_directory.glob("*.log.*"))
        assert len(remaining_logs) == 10

        assert stats["files_kept"] == 10
        assert stats["files_archived"] == 0

    def test_rotate_logs_nonexistent_directory(self, temp_config_file):
        """Test rotation with nonexistent directory raises error."""
        rotator = LogRotator(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            rotator.rotate_logs(log_directory="/nonexistent/path")

    def test_delete_old_files(self, temp_config_file, tmp_path):
        """Test deleting old archived files."""
        import time

        rotator = LogRotator(config_path=temp_config_file)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        # Create old file (100 days ago)
        old_file = archive_dir / "old.log.gz"
        old_file.write_text("old content")
        old_mtime = time.time() - (100 * 24 * 60 * 60)
        os.utime(old_file, (old_mtime, old_mtime))

        # Create recent file
        recent_file = archive_dir / "recent.log.gz"
        recent_file.write_text("recent content")

        deleted = rotator._delete_old_files(archive_dir, max_age_days=90)

        assert deleted == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_get_statistics(self, temp_config_file):
        """Test getting statistics."""
        rotator = LogRotator(config_path=temp_config_file)
        stats = rotator.get_statistics()

        assert "files_processed" in stats
        assert "files_kept" in stats
        assert "files_archived" in stats
        assert "files_compressed" in stats
        assert "files_deleted" in stats
        assert "errors" in stats
