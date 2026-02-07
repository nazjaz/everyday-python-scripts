"""Unit tests for log compressor module."""

import gzip
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import LogCompressor


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    config = {
        "targets": [
            {"path": temp_dir, "enabled": True, "recursive": True},
        ],
        "file_patterns": ["*.log", "*.log.*"],
        "compression": {
            "enabled": True,
            "min_age_days": 0,  # Compress immediately for tests
            "compression_level": 6,
            "remove_original_after": False,  # Keep originals for tests
            "verify_compression": True,
        },
        "retention": {
            "enabled": True,
            "keep_original_days": 30,
            "keep_compressed_days": 365,
            "auto_cleanup": False,  # Disable for tests
        },
        "organization": {
            "enabled": True,
            "organize_by": "date",
            "date_format": "%Y-%m",
            "output_directory": f"{temp_dir}/compressed",
            "structure": "year/month",
        },
        "safety": {
            "dry_run": True,  # Use dry run for tests
            "confirm_before_delete": False,
            "max_file_size_mb": 0,
            "skip_recently_modified": False,  # Allow recent files in tests
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
            "log_compressions": True,
            "log_deletions": True,
        },
        "reporting": {
            "generate_report": True,
            "report_file": f"{temp_dir}/report.txt",
            "include_statistics": True,
            "include_file_list": True,
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_log_compressor_initialization(config_file):
    """Test LogCompressor initializes correctly."""
    compressor = LogCompressor(config_path=str(config_file))
    assert compressor.stats["files_scanned"] == 0
    assert compressor.stats["files_compressed"] == 0


def test_log_compressor_missing_config():
    """Test LogCompressor raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        LogCompressor(config_path="nonexistent.yaml")


def test_matches_pattern(config_file):
    """Test file pattern matching."""
    compressor = LogCompressor(config_path=str(config_file))

    log_file = Path("test.log")
    assert compressor._matches_pattern(log_file) is True

    rotated_log = Path("app.log.1")
    assert compressor._matches_pattern(rotated_log) is True

    other_file = Path("test.txt")
    assert compressor._matches_pattern(other_file) is False


def test_should_compress(config_file, temp_dir):
    """Test should compress logic."""
    compressor = LogCompressor(config_path=str(config_file))

    # Create old log file
    old_log = Path(temp_dir) / "old.log"
    old_log.write_text("test content")
    # Make file old
    old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
    os.utime(old_log, (old_time, old_time))

    assert compressor._should_compress(old_log) is True

    # Create recent log file
    recent_log = Path(temp_dir) / "recent.log"
    recent_log.write_text("test content")

    compressor.config["compression"]["min_age_days"] = 7
    assert compressor._should_compress(recent_log) is False


def test_get_compressed_path(config_file, temp_dir):
    """Test compressed path generation with date organization."""
    compressor = LogCompressor(config_path=str(config_file))

    log_file = Path(temp_dir) / "test.log"
    log_file.write_text("test content")
    # Set modification time to a specific date
    test_date = datetime(2024, 2, 7)
    os.utime(log_file, (test_date.timestamp(), test_date.timestamp()))

    compressed_path = compressor._get_compressed_path(log_file)

    # Should be organized by year/month
    assert "2024" in str(compressed_path)
    assert "02" in str(compressed_path)
    assert compressed_path.name == "test.log.gz"


def test_compress_file_dry_run(config_file, temp_dir):
    """Test file compression in dry run mode."""
    compressor = LogCompressor(config_path=str(config_file))

    log_file = Path(temp_dir) / "test.log"
    log_file.write_text("test content " * 100)
    old_time = time.time() - (8 * 24 * 60 * 60)
    os.utime(log_file, (old_time, old_time))

    result = compressor._compress_file(log_file)

    assert result is True
    # File should still exist in dry run
    assert log_file.exists()


def test_compress_file_actual(config_file, temp_dir):
    """Test actual file compression."""
    compressor = LogCompressor(config_path=str(config_file))
    compressor.config["safety"]["dry_run"] = False
    compressor.config["compression"]["remove_original_after"] = False

    log_file = Path(temp_dir) / "test.log"
    content = "test content " * 100
    log_file.write_text(content)
    old_time = time.time() - (8 * 24 * 60 * 60)
    os.utime(log_file, (old_time, old_time))

    result = compressor._compress_file(log_file)

    assert result is True

    # Check compressed file exists
    compressed_path = compressor._get_compressed_path(log_file)
    assert compressed_path.exists()

    # Verify it's a valid gzip file
    with gzip.open(compressed_path, "rb") as f:
        decompressed = f.read().decode()
        assert content in decompressed


def test_find_log_files(config_file, temp_dir):
    """Test finding log files."""
    compressor = LogCompressor(config_path=str(config_file))

    # Create log files
    log1 = Path(temp_dir) / "app.log"
    log1.write_text("log content")

    log2 = Path(temp_dir) / "error.log"
    log2.write_text("error content")

    # Create non-log file
    other = Path(temp_dir) / "data.txt"
    other.write_text("data")

    # Create subdirectory with log
    subdir = Path(temp_dir) / "subdir"
    subdir.mkdir()
    log3 = subdir / "sub.log"
    log3.write_text("sub log")

    files = compressor._find_log_files(Path(temp_dir), recursive=True)

    assert len(files) >= 3
    assert any(f.name == "app.log" for f in files)
    assert any(f.name == "error.log" for f in files)
    assert any(f.name == "sub.log" for f in files)


def test_compress_logs(config_file, temp_dir):
    """Test compressing logs."""
    compressor = LogCompressor(config_path=str(config_file))
    compressor.config["safety"]["dry_run"] = False
    compressor.config["compression"]["remove_original_after"] = False

    # Create old log files
    for i in range(3):
        log_file = Path(temp_dir) / f"log{i}.log"
        log_file.write_text(f"log content {i} " * 50)
        old_time = time.time() - (8 * 24 * 60 * 60)
        os.utime(log_file, (old_time, old_time))

    stats = compressor.compress_logs()

    assert stats["files_scanned"] >= 3
    assert stats["files_compressed"] >= 3
