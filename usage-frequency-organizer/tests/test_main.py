"""Unit tests for Usage Frequency Organizer application."""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import (
    UsageFrequencyAnalyzer,
    UsageFrequencyOrganizer,
    load_config,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestUsageFrequencyAnalyzer:
    """Test cases for UsageFrequencyAnalyzer class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "frequency_thresholds": {
                "frequent_days": 7,
                "occasional_days": 30,
                "rare_days": 90,
            },
            "analysis": {"use_modification_time_fallback": True},
        }

    @pytest.fixture
    def analyzer(self, config):
        """Create a UsageFrequencyAnalyzer instance."""
        return UsageFrequencyAnalyzer(config)

    def test_init(self, config):
        """Test UsageFrequencyAnalyzer initialization."""
        analyzer = UsageFrequencyAnalyzer(config)
        assert analyzer.config == config

    def test_get_file_access_times(self, analyzer, temp_dir):
        """Test getting file access times."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        access_info = analyzer.get_file_access_times(test_file)
        assert access_info is not None
        assert "access_time" in access_info
        assert "modification_time" in access_info
        assert isinstance(access_info["access_time"], datetime)

    def test_get_file_access_times_nonexistent(self, analyzer):
        """Test getting access times for nonexistent file."""
        nonexistent = Path("/nonexistent/file.txt")
        result = analyzer.get_file_access_times(nonexistent)
        assert result is None

    def test_calculate_access_frequency_frequent(self, analyzer):
        """Test frequency calculation for frequent files."""
        now = datetime.now()
        access_info = {
            "access_time": now - timedelta(days=2),
            "modification_time": now - timedelta(days=2),
        }

        category, score = analyzer.calculate_access_frequency(
            Path("/test"), access_info, now
        )
        assert category == "frequent"
        assert 0.0 <= score <= 1.0

    def test_calculate_access_frequency_occasional(self, analyzer):
        """Test frequency calculation for occasional files."""
        now = datetime.now()
        access_info = {
            "access_time": now - timedelta(days=15),
            "modification_time": now - timedelta(days=15),
        }

        category, score = analyzer.calculate_access_frequency(
            Path("/test"), access_info, now
        )
        assert category == "occasional"
        assert 0.0 <= score <= 1.0

    def test_calculate_access_frequency_rare(self, analyzer):
        """Test frequency calculation for rare files."""
        now = datetime.now()
        access_info = {
            "access_time": now - timedelta(days=60),
            "modification_time": now - timedelta(days=60),
        }

        category, score = analyzer.calculate_access_frequency(
            Path("/test"), access_info, now
        )
        assert category == "rare"
        assert 0.0 <= score <= 1.0

    def test_calculate_access_frequency_archive(self, analyzer):
        """Test frequency calculation for archive files."""
        now = datetime.now()
        access_info = {
            "access_time": now - timedelta(days=200),
            "modification_time": now - timedelta(days=200),
        }

        category, score = analyzer.calculate_access_frequency(
            Path("/test"), access_info, now
        )
        assert category == "archive"
        assert 0.0 <= score <= 1.0

    def test_analyze_file_usage(self, analyzer, temp_dir):
        """Test file usage analysis."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        now = datetime.now()
        usage_info = analyzer.analyze_file_usage(test_file, now)

        assert usage_info is not None
        assert "category" in usage_info
        assert "frequency_score" in usage_info
        assert "days_since_access" in usage_info
        assert usage_info["category"] in ["frequent", "occasional", "rare", "archive"]


class TestUsageFrequencyOrganizer:
    """Test cases for UsageFrequencyOrganizer class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        return {
            "source_directory": str(source_dir),
            "frequency_thresholds": {
                "frequent_days": 7,
                "occasional_days": 30,
                "rare_days": 90,
            },
            "organization": {
                "frequent_directory": str(temp_dir / "frequent"),
                "occasional_directory": str(temp_dir / "occasional"),
                "rare_directory": str(temp_dir / "rare"),
                "archive_directory": str(temp_dir / "archive"),
                "preserve_structure": False,
                "check_duplicates": True,
                "skip_duplicates": True,
            },
            "filtering": {
                "exclude_directories": [".git"],
                "exclude_files": [".DS_Store"],
                "exclude_extensions": [".tmp"],
            },
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def organizer(self, config):
        """Create a UsageFrequencyOrganizer instance."""
        return UsageFrequencyOrganizer(config)

    def test_init(self, config):
        """Test UsageFrequencyOrganizer initialization."""
        organizer = UsageFrequencyOrganizer(config)
        assert organizer.config == config
        assert organizer.source_dir == Path(config["source_directory"])

    def test_should_exclude_file(self, organizer):
        """Test file exclusion logic."""
        excluded = Path("/some/.DS_Store")
        assert organizer.should_exclude_file(excluded) is True

        excluded = Path("/some/file.tmp")
        assert organizer.should_exclude_file(excluded) is True

        included = Path("/some/file.txt")
        assert organizer.should_exclude_file(included) is False

    def test_should_exclude_directory(self, organizer):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert organizer.should_exclude_directory(excluded) is True

        excluded = Path("/some/frequent")
        assert organizer.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert organizer.should_exclude_directory(included) is False

    def test_get_destination_path(self, organizer, temp_dir):
        """Test destination path generation."""
        test_file = temp_dir / "test.txt"

        dest_path = organizer.get_destination_path(test_file, "frequent")
        assert "frequent" in str(dest_path)

        dest_path = organizer.get_destination_path(test_file, "archive")
        assert "archive" in str(dest_path)

    def test_organize_file_dry_run(self, organizer, temp_dir):
        """Test organizing file in dry-run mode."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        test_file = source_dir / "test.txt"
        test_file.write_text("content")

        usage_info = {
            "path": test_file,
            "category": "frequent",
            "frequency_score": 0.9,
            "days_since_access": 2,
            "access_time": datetime.now(),
            "size": 100,
        }

        success, category = organizer.organize_file(usage_info, dry_run=True)
        assert success is True
        assert category == "frequent"
        assert test_file.exists()  # Should still exist in dry-run

    def test_organize_file(self, organizer, temp_dir):
        """Test organizing file."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        test_file = source_dir / "test.txt"
        test_file.write_text("content")

        usage_info = {
            "path": test_file,
            "category": "frequent",
            "frequency_score": 0.9,
            "days_since_access": 2,
            "access_time": datetime.now(),
            "size": 100,
        }

        success, category = organizer.organize_file(usage_info, dry_run=False)
        assert success is True
        assert not test_file.exists()  # Should be moved

        # Check destination
        dest_file = organizer.frequent_dir / "test.txt"
        assert dest_file.exists()

    def test_scan_files(self, organizer, temp_dir):
        """Test scanning files."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        file1 = source_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = source_dir / "file2.txt"
        file2.write_text("content 2")

        files = organizer.scan_files()
        assert len(files) >= 2

    def test_organize_files_dry_run(self, organizer, temp_dir):
        """Test organizing files in dry-run mode."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create test files with different access times
        file1 = source_dir / "recent.txt"
        file1.write_text("recent content")
        # Set recent access time
        recent_time = (datetime.now() - timedelta(days=2)).timestamp()
        os.utime(file1, (recent_time, recent_time))

        file2 = source_dir / "old.txt"
        file2.write_text("old content")
        # Set old access time
        old_time = (datetime.now() - timedelta(days=200)).timestamp()
        os.utime(file2, (old_time, old_time))

        results = organizer.organize_files(dry_run=True)
        assert results["scanned"] >= 2
        assert file1.exists()  # Should still exist in dry-run
        assert file2.exists()  # Should still exist in dry-run


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
            "source_directory: /test\nfrequency_thresholds:\n  frequent_days: 7\n"
        )

        config = load_config(config_file)
        assert config["source_directory"] == "/test"
        assert config["frequency_thresholds"]["frequent_days"] == 7

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
