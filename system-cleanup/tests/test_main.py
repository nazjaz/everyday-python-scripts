"""Unit tests for System Cleanup application."""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import SystemCleanup, load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestSystemCleanup:
    """Test cases for SystemCleanup class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "cleanup": {
                "cache_patterns": ["cache", ".cache"],
                "temp_patterns": [".tmp", ".temp"],
                "artifact_patterns": [".log", ".old"],
            },
            "safety": {
                "min_age_days": 0,
                "unsafe_extensions": [".exe", ".dll"],
                "unsafe_patterns": ["system", "kernel"],
                "protected_directories": ["/System"],
            },
            "logging": {"level": "INFO", "file": "logs/test.log"},
        }

    @pytest.fixture
    def cleanup(self, config):
        """Create a SystemCleanup instance."""
        return SystemCleanup(config)

    def test_init(self, config):
        """Test SystemCleanup initialization."""
        cleanup = SystemCleanup(config)
        assert cleanup.config == config
        assert cleanup.platform_name is not None

    def test_is_safe_to_delete_safe_file(self, cleanup, temp_dir):
        """Test that safe files are identified correctly."""
        test_file = temp_dir / "test.tmp"
        test_file.write_text("content")

        assert cleanup.is_safe_to_delete(test_file) is True

    def test_is_safe_to_delete_unsafe_extension(self, cleanup, temp_dir):
        """Test that unsafe extensions are rejected."""
        test_file = temp_dir / "test.exe"
        test_file.write_text("content")

        assert cleanup.is_safe_to_delete(test_file) is False

    def test_is_safe_to_delete_unsafe_pattern(self, cleanup, temp_dir):
        """Test that unsafe patterns are rejected."""
        test_file = temp_dir / "system_file.tmp"
        test_file.write_text("content")

        assert cleanup.is_safe_to_delete(test_file) is False

    def test_is_safe_to_delete_protected_directory(self, cleanup):
        """Test that files in protected directories are rejected."""
        # This test may not work on all systems, so we'll skip if /System doesn't exist
        protected_file = Path("/System/test.tmp")
        if protected_file.parent.exists():
            assert cleanup.is_safe_to_delete(protected_file) is False

    def test_is_safe_to_delete_min_age(self, cleanup, temp_dir):
        """Test minimum age requirement."""
        # Set min_age_days
        cleanup.safety_config["min_age_days"] = 7

        # Create recent file
        test_file = temp_dir / "recent.tmp"
        test_file.write_text("content")

        assert cleanup.is_safe_to_delete(test_file) is False

        # Create old file
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        old_file = temp_dir / "old.tmp"
        old_file.write_text("content")
        os.utime(old_file, (old_time, old_time))

        assert cleanup.is_safe_to_delete(old_file) is True

    def test_delete_file_dry_run(self, cleanup, temp_dir):
        """Test file deletion in dry-run mode."""
        test_file = temp_dir / "test.tmp"
        test_file.write_text("content")

        success, message = cleanup.delete_file(test_file, dry_run=True)
        assert success is True
        assert "[DRY RUN]" in message
        assert test_file.exists()  # Should still exist

    def test_delete_file(self, cleanup, temp_dir):
        """Test file deletion."""
        test_file = temp_dir / "test.tmp"
        test_file.write_text("content")

        success, message = cleanup.delete_file(test_file, dry_run=False)
        assert success is True
        assert not test_file.exists()  # Should be deleted

    def test_format_size(self, cleanup):
        """Test size formatting."""
        assert "B" in cleanup.format_size(500)
        assert "KB" in cleanup.format_size(2048)
        assert "MB" in cleanup.format_size(1048576)
        assert "GB" in cleanup.format_size(1073741824)

    def test_scan_temp_files(self, cleanup, temp_dir):
        """Test scanning for temporary files."""
        # Create temp files
        temp_file1 = temp_dir / "file1.tmp"
        temp_file1.write_text("content")
        temp_file2 = temp_dir / "file2.temp"
        temp_file2.write_text("content")

        # Add temp_dir to temp_paths for testing
        cleanup.temp_paths = [temp_dir]

        temp_files = cleanup.scan_temp_files()
        assert len(temp_files) >= 2

    def test_cleanup_dry_run(self, cleanup, temp_dir):
        """Test cleanup in dry-run mode."""
        # Create test files
        temp_file = temp_dir / "test.tmp"
        temp_file.write_text("content")

        # Add temp_dir to temp_paths for testing
        cleanup.temp_paths = [temp_dir]

        results = cleanup.cleanup(dry_run=True)
        assert results["scanned"]["temp"] >= 1
        assert temp_file.exists()  # Should still exist in dry-run


class TestLoadConfig:
    """Test cases for load_config function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_load_config_valid(self, temp_dir):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            "cleanup:\n  cache_patterns: [cache]\nsafety:\n  min_age_days: 7\n"
        )

        config = load_config(config_file)
        assert config["cleanup"]["cache_patterns"] == ["cache"]
        assert config["safety"]["min_age_days"] == 7

    def test_load_config_nonexistent(self):
        """Test loading a nonexistent configuration file."""
        nonexistent = Path("/nonexistent/config.yaml")
        with pytest.raises(FileNotFoundError):
            load_config(nonexistent)

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading an invalid YAML file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(Exception):  # yaml.YAMLError
            load_config(config_file)
