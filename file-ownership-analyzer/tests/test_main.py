"""Unit tests for File Ownership Analyzer."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import FileOwnershipAnalyzer


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "scan": {
            "directory": ".",
            "recursive": True,
            "exclude": {
                "patterns": [],
                "directories": [],
            },
        },
        "output": {"directory": "output"},
        "report": {
            "include_file_list": False,
            "max_files_per_owner": 100,
            "max_files_per_group": 100,
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
def temp_directory(tmp_path):
    """Create temporary directory with test files."""
    test_dir = tmp_path / "test_scan"
    test_dir.mkdir()

    # Create test files
    (test_dir / "file1.txt").write_text("Test file 1")
    (test_dir / "file2.log").write_text("Test file 2")
    (test_dir / "file3.py").write_text("Test file 3")

    # Create subdirectory
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested file")

    return test_dir


class TestFileOwnershipAnalyzer:
    """Test cases for FileOwnershipAnalyzer class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        assert analyzer.config is not None
        assert "scan" in analyzer.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            FileOwnershipAnalyzer(config_path="nonexistent.yaml")

    def test_get_owner_name(self, temp_config_file):
        """Test getting owner name from UID."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        current_uid = os.getuid()
        owner_name = analyzer._get_owner_name(current_uid)
        assert isinstance(owner_name, str)
        assert len(owner_name) > 0

    def test_get_group_name(self, temp_config_file):
        """Test getting group name from GID."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        current_gid = os.getgid()
        group_name = analyzer._get_group_name(current_gid)
        assert isinstance(group_name, str)
        assert len(group_name) > 0

    def test_get_file_permissions(self, temp_config_file, tmp_path):
        """Test getting file permissions."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        perms = analyzer._get_file_permissions(test_file)

        assert "path" in perms
        assert "owner_name" in perms
        assert "group_name" in perms
        assert "permissions" in perms
        assert "octal_permission" in perms
        assert perms["is_file"] is True

    def test_get_file_permissions_nonexistent(self, temp_config_file):
        """Test getting permissions for nonexistent file."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        nonexistent = Path("/nonexistent/file.txt")

        perms = analyzer._get_file_permissions(nonexistent)
        assert perms == {}

    def test_is_excluded_by_directory(self, temp_config_file):
        """Test directory exclusion."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.config["scan"]["exclude"]["directories"] = [".git"]

        excluded_file = Path("/path/.git/config")
        assert analyzer._is_excluded(excluded_file) is True

        normal_file = Path("/path/file.txt")
        assert analyzer._is_excluded(normal_file) is False

    def test_scan_directory(self, temp_config_file, temp_directory):
        """Test scanning directory."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        files = analyzer.scan_directory(str(temp_directory), recursive=True)

        assert len(files) >= 3
        assert analyzer.stats["files_scanned"] >= 3

    def test_scan_directory_non_recursive(self, temp_config_file, temp_directory):
        """Test non-recursive directory scan."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        files = analyzer.scan_directory(str(temp_directory), recursive=False)

        # Should not find nested.txt in subdirectory
        file_paths = [f["path"] for f in files]
        assert not any("nested.txt" in path for path in file_paths)

    def test_scan_directory_nonexistent(self, temp_config_file):
        """Test scanning nonexistent directory raises error."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            analyzer.scan_directory("/nonexistent/path")

    def test_organize_by_owner(self, temp_config_file, temp_directory):
        """Test organizing files by owner."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))
        owner_files = analyzer.organize_by_owner()

        assert isinstance(owner_files, dict)
        assert len(owner_files) > 0

    def test_organize_by_group(self, temp_config_file, temp_directory):
        """Test organizing files by group."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))
        group_files = analyzer.organize_by_group()

        assert isinstance(group_files, dict)
        assert len(group_files) > 0

    def test_calculate_owner_statistics(self, temp_config_file, temp_directory):
        """Test calculating owner statistics."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))
        owner_stats = analyzer.calculate_owner_statistics()

        assert isinstance(owner_stats, dict)
        assert len(owner_stats) > 0

        # Check stats structure
        for owner, stats in owner_stats.items():
            assert "file_count" in stats
            assert "total_size" in stats
            assert "extensions" in stats
            assert "groups" in stats

    def test_calculate_group_statistics(self, temp_config_file, temp_directory):
        """Test calculating group statistics."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))
        group_stats = analyzer.calculate_group_statistics()

        assert isinstance(group_stats, dict)
        assert len(group_stats) > 0

        # Check stats structure
        for group, stats in group_stats.items():
            assert "file_count" in stats
            assert "total_size" in stats
            assert "owners" in stats
            assert "extensions" in stats

    def test_identify_patterns(self, temp_config_file, temp_directory):
        """Test identifying ownership patterns."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))
        patterns = analyzer.identify_patterns()

        assert "top_owners_by_count" in patterns
        assert "top_owners_by_size" in patterns
        assert "top_groups_by_count" in patterns
        assert "top_groups_by_size" in patterns
        assert "common_ownership_patterns" in patterns

    def test_get_files_by_owner(self, temp_config_file, temp_directory):
        """Test getting files by owner."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))
        owner_files = analyzer.organize_by_owner()

        if owner_files:
            first_owner = list(owner_files.keys())[0]
            files = analyzer.get_files_by_owner(first_owner)
            assert len(files) > 0

    def test_get_files_by_group(self, temp_config_file, temp_directory):
        """Test getting files by group."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))
        group_files = analyzer.organize_by_group()

        if group_files:
            first_group = list(group_files.keys())[0]
            files = analyzer.get_files_by_group(first_group)
            assert len(files) > 0

    def test_generate_report(self, temp_config_file, temp_directory, tmp_path):
        """Test generating report."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))
        analyzer.calculate_owner_statistics()
        analyzer.calculate_group_statistics()

        report_file = tmp_path / "report.txt"
        report_content = analyzer.generate_report(str(report_file))

        assert len(report_content) > 0
        assert "File Ownership Analysis Report" in report_content
        assert report_file.exists()

    def test_get_statistics(self, temp_config_file):
        """Test getting statistics."""
        analyzer = FileOwnershipAnalyzer(config_path=temp_config_file)
        stats = analyzer.get_statistics()

        assert "files_scanned" in stats
        assert "directories_scanned" in stats
        assert "errors" in stats
        assert "unique_owners" in stats
        assert "unique_groups" in stats
