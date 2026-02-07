"""Unit tests for cache cleaner."""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import CacheCleaner


class TestCacheCleaner:
    """Test cases for CacheCleaner class."""

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return {
            "cache_directories": {
                "macos": ["~/Library/Caches"],
                "linux": ["~/.cache"],
                "windows": ["%TEMP%"],
            },
            "filtering": {
                "min_age_days": 7,
                "max_age_days": 0,
                "min_file_size": 0,
                "max_file_size": 0,
                "include_hidden": True,
                "include_empty": True,
            },
            "include_patterns": [".*\\.cache$", ".*\\.tmp$"],
            "exclude_patterns": ["^\\.git"],
            "exclude_directories": ["^\\.git$"],
            "safety": {
                "dry_run": False,
                "require_confirmation": True,
                "max_delete_size": 0,
            },
            "reporting": {
                "detailed_report": True,
                "show_directory_breakdown": True,
                "show_largest_files": True,
            },
        }

    @pytest.fixture
    def cleaner(self, sample_config):
        """Create CacheCleaner instance."""
        return CacheCleaner(sample_config)

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create test cache files
            old_file = tmp_path / "old_file.cache"
            old_file.write_text("test content")
            # Make file old
            old_time = (datetime.now() - timedelta(days=10)).timestamp()
            os.utime(old_file, (old_time, old_time))

            new_file = tmp_path / "new_file.cache"
            new_file.write_text("test content")
            # Make file new
            new_time = (datetime.now() - timedelta(days=1)).timestamp()
            os.utime(new_file, (new_time, new_time))

            # Create non-cache file
            normal_file = tmp_path / "normal.txt"
            normal_file.write_text("test content")
            old_time = (datetime.now() - timedelta(days=10)).timestamp()
            os.utime(normal_file, (old_time, old_time))

            yield tmp_path

    def test_should_include_file_cache_pattern(self, cleaner, temp_dir):
        """Test that cache files are included."""
        cache_file = temp_dir / "test.cache"
        cache_file.write_text("test")
        
        assert cleaner.should_include_file(cache_file) is True

    def test_should_include_file_tmp_pattern(self, cleaner, temp_dir):
        """Test that tmp files are included."""
        tmp_file = temp_dir / "test.tmp"
        tmp_file.write_text("test")
        
        assert cleaner.should_include_file(tmp_file) is True

    def test_should_include_file_excluded_pattern(self, cleaner, temp_dir):
        """Test that excluded patterns are not included."""
        git_file = temp_dir / ".git"
        git_file.mkdir()
        
        # Should exclude .git directories
        assert cleaner.should_exclude_directory(git_file) is True

    def test_is_file_old_enough(self, cleaner, temp_dir):
        """Test age filtering."""
        old_file = temp_dir / "old.cache"
        old_file.write_text("test")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        assert cleaner.is_file_old_enough(old_file) is True

    def test_is_file_old_enough_too_new(self, cleaner, temp_dir):
        """Test that new files are not old enough."""
        new_file = temp_dir / "new.cache"
        new_file.write_text("test")
        new_time = (datetime.now() - timedelta(days=1)).timestamp()
        os.utime(new_file, (new_time, new_time))
        
        assert cleaner.is_file_old_enough(new_file) is False

    def test_is_file_size_acceptable(self, cleaner, temp_dir):
        """Test size filtering."""
        test_file = temp_dir / "test.cache"
        test_file.write_text("test content")
        
        assert cleaner.is_file_size_acceptable(test_file) is True

    def test_is_file_size_acceptable_min_size(self, cleaner, temp_dir):
        """Test minimum size filtering."""
        cleaner.filter_config["min_file_size"] = 100
        
        small_file = temp_dir / "small.cache"
        small_file.write_text("x")
        
        assert cleaner.is_file_size_acceptable(small_file) is False

    def test_scan_directory(self, cleaner, temp_dir):
        """Test directory scanning."""
        files = cleaner.scan_directory(temp_dir, recursive=False)
        
        # Should find old cache file but not new one (age filter)
        assert len(files) >= 1
        file_paths = [f[0] for f in files]
        assert any("old_file.cache" in str(p) for p in file_paths)

    def test_scan_directory_recursive(self, cleaner, temp_dir):
        """Test recursive directory scanning."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        old_file = subdir / "old.cache"
        old_file.write_text("test")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        files = cleaner.scan_directory(temp_dir, recursive=True)
        file_paths = [f[0] for f in files]
        assert any("subdir" in str(p) for p in file_paths)

    def test_delete_file(self, cleaner, temp_dir):
        """Test file deletion."""
        test_file = temp_dir / "to_delete.cache"
        test_file.write_text("test")
        
        assert test_file.exists()
        result = cleaner.delete_file(test_file)
        assert result is True
        assert not test_file.exists()

    def test_delete_file_nonexistent(self, cleaner, temp_dir):
        """Test deleting non-existent file."""
        nonexistent = temp_dir / "nonexistent.cache"
        result = cleaner.delete_file(nonexistent)
        assert result is False

    def test_cleanup_files_dry_run(self, cleaner, temp_dir):
        """Test cleanup in dry run mode."""
        old_file = temp_dir / "old.cache"
        old_file.write_text("test")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        files = [(old_file, old_file.stat().st_size, datetime.fromtimestamp(old_time))]
        
        deleted, failed, size = cleaner.cleanup_files(files, dry_run=True)
        
        assert deleted == 1
        assert failed == 0
        assert old_file.exists()  # File should still exist in dry run

    def test_cleanup_files_actual(self, cleaner, temp_dir):
        """Test actual file cleanup."""
        old_file = temp_dir / "old.cache"
        old_file.write_text("test")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        file_size = old_file.stat().st_size
        
        files = [(old_file, file_size, datetime.fromtimestamp(old_time))]
        
        deleted, failed, size = cleaner.cleanup_files(files, dry_run=False)
        
        assert deleted == 1
        assert failed == 0
        assert not old_file.exists()  # File should be deleted

    def test_generate_report(self, cleaner, temp_dir):
        """Test report generation."""
        old_file = temp_dir / "old.cache"
        old_file.write_text("test")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        file_size = old_file.stat().st_size
        
        files = [(old_file, file_size, datetime.fromtimestamp(old_time))]
        
        report = cleaner.generate_report(files, deleted_count=1, failed_count=0, total_size=file_size)
        
        assert "CACHE CLEANUP REPORT" in report
        assert "Files deleted: 1" in report
        assert "Total size deleted" in report

    def test_format_size(self, cleaner):
        """Test size formatting."""
        assert "B" in cleaner._format_size(500)
        assert "KB" in cleaner._format_size(2048)
        assert "MB" in cleaner._format_size(1048576)
        assert "GB" in cleaner._format_size(1073741824)

    @patch("platform.system")
    def test_get_cache_directories_macos(self, mock_system, cleaner):
        """Test getting cache directories for macOS."""
        mock_system.return_value = "Darwin"
        
        # Mock directory existence
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.expanduser") as mock_expand:
                mock_expand.return_value = Path("/test/cache")
                dirs = cleaner.get_cache_directories()
                assert len(dirs) > 0

    @patch("platform.system")
    def test_get_cache_directories_linux(self, mock_system, cleaner):
        """Test getting cache directories for Linux."""
        mock_system.return_value = "Linux"
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.expanduser") as mock_expand:
                mock_expand.return_value = Path("/test/cache")
                dirs = cleaner.get_cache_directories()
                assert len(dirs) > 0
