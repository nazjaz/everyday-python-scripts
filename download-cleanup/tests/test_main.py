"""Unit tests for download cleanup script."""

import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    DownloadCleanup,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "download_folders": ["/test/path1", "/test/path2"],
                "retention_days": 30,
                "archive_root": "/test/archive",
                "action": "delete",
                "file_types": ["images", "documents"],
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["download_folders"] == ["/test/path1", "/test/path2"]
            assert result["retention_days"] == 30
            assert result["archive_root"] == "/test/archive"
            assert result["action"] == "delete"
            assert result["file_types"] == ["images", "documents"]
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


class TestDownloadCleanup:
    """Test DownloadCleanup class."""

    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
            )

            assert cleanup.retention_days == 30
            assert cleanup.action == "archive"
            assert cleanup.archive_root == archive_root.resolve()

    def test_init_invalid_action(self):
        """Test that invalid action raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            with pytest.raises(ValueError, match="action must be"):
                DownloadCleanup(
                    download_folders=[download_folder],
                    retention_days=30,
                    archive_root=archive_root,
                    action="invalid",
                )

    def test_init_archive_without_archive_root(self):
        """Test that archive action without archive_root raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()

            with pytest.raises(ValueError, match="archive_root is required"):
                DownloadCleanup(
                    download_folders=[download_folder],
                    retention_days=30,
                    action="archive",
                )

    def test_init_nonexistent_download_folder(self):
        """Test that nonexistent download folder raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "nonexistent"
            archive_root = Path(tmpdir) / "archived"

            with pytest.raises(FileNotFoundError):
                DownloadCleanup(
                    download_folders=[download_folder],
                    retention_days=30,
                    archive_root=archive_root,
                )

    def test_get_file_category(self):
        """Test file category detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
            )

            assert cleanup._get_file_category(Path("test.jpg")) == "images"
            assert cleanup._get_file_category(Path("test.pdf")) == "documents"
            assert cleanup._get_file_category(Path("test.mp4")) == "videos"
            assert cleanup._get_file_category(Path("test.zip")) == "archives"
            assert cleanup._get_file_category(Path("test.unknown")) == "other"
            assert cleanup._get_file_category(Path("test")) is None

    def test_is_file_old(self):
        """Test file age detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
            )

            old_file = download_folder / "old.txt"
            old_file.write_text("content")
            old_time = datetime.now() - timedelta(days=31)
            old_timestamp = old_time.timestamp()
            os.utime(old_file, (old_timestamp, old_timestamp))

            new_file = download_folder / "new.txt"
            new_file.write_text("content")

            assert cleanup._is_file_old(old_file) is True
            assert cleanup._is_file_old(new_file) is False

    def test_should_process_file_with_file_types(self):
        """Test file filtering by file types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
                file_types=["images", "documents"],
            )

            assert cleanup._should_process_file(Path("test.jpg")) is True
            assert cleanup._should_process_file(Path("test.pdf")) is True
            assert cleanup._should_process_file(Path("test.mp4")) is False

    def test_should_process_file_with_exclude_patterns(self):
        """Test file filtering by exclusion patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
                exclude_patterns=["important", "keep"],
            )

            assert cleanup._should_process_file(Path("test.jpg")) is True
            assert cleanup._should_process_file(Path("important_file.jpg")) is False
            assert cleanup._should_process_file(Path("keep_this.pdf")) is False

    def test_get_archive_path(self):
        """Test archive path generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
            )

            test_file = download_folder / "test.jpg"
            test_file.write_text("content")
            old_time = datetime.now() - timedelta(days=31)
            old_timestamp = old_time.timestamp()
            os.utime(test_file, (old_timestamp, old_timestamp))

            archive_path = cleanup._get_archive_path(test_file, "images")
            expected_year_month = old_time.strftime("%Y-%m")
            expected = archive_root / "images" / expected_year_month / "test.jpg"

            assert archive_path == expected

    def test_archive_file(self):
        """Test file archiving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
                dry_run=True,
            )

            test_file = download_folder / "test.jpg"
            test_file.write_text("content")

            result = cleanup._archive_file(test_file)
            assert result is True
            assert test_file.exists()

    def test_archive_file_actual_move(self):
        """Test actual file archiving (not dry run)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
                dry_run=False,
            )

            test_file = download_folder / "test.jpg"
            test_file.write_text("content")
            old_time = datetime.now() - timedelta(days=31)
            old_timestamp = old_time.timestamp()
            import os
            os.utime(test_file, (old_timestamp, old_timestamp))

            result = cleanup._archive_file(test_file)
            assert result is True
            assert not test_file.exists()

            expected_year_month = old_time.strftime("%Y-%m")
            archived_file = archive_root / "images" / expected_year_month / "test.jpg"
            assert archived_file.exists()

    def test_delete_file(self):
        """Test file deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                action="delete",
                dry_run=True,
            )

            test_file = download_folder / "test.txt"
            test_file.write_text("content")

            result = cleanup._delete_file(test_file)
            assert result is True
            assert test_file.exists()

    def test_delete_file_actual_delete(self):
        """Test actual file deletion (not dry run)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                action="delete",
                dry_run=False,
            )

            test_file = download_folder / "test.txt"
            test_file.write_text("content")

            result = cleanup._delete_file(test_file)
            assert result is True
            assert not test_file.exists()

    def test_cleanup_archives_old_files(self):
        """Test cleanup process with archiving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            old_file = download_folder / "old.jpg"
            old_file.write_text("content")
            old_time = datetime.now() - timedelta(days=31)
            old_timestamp = old_time.timestamp()
            import os
            os.utime(old_file, (old_timestamp, old_timestamp))

            new_file = download_folder / "new.jpg"
            new_file.write_text("content")

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
                file_types=["images"],
                dry_run=True,
            )

            stats = cleanup.cleanup()

            assert stats["scanned"] == 2
            assert stats["archived"] == 1
            assert stats["skipped"] == 1

    def test_cleanup_deletes_old_files(self):
        """Test cleanup process with deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()

            old_file = download_folder / "old.txt"
            old_file.write_text("content")
            old_time = datetime.now() - timedelta(days=31)
            old_timestamp = old_time.timestamp()
            import os
            os.utime(old_file, (old_timestamp, old_timestamp))

            new_file = download_folder / "new.txt"
            new_file.write_text("content")

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                action="delete",
                dry_run=True,
            )

            stats = cleanup.cleanup()

            assert stats["scanned"] == 2
            assert stats["deleted"] == 1
            assert stats["skipped"] == 1

    def test_get_summary(self):
        """Test summary report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            download_folder = Path(tmpdir) / "downloads"
            download_folder.mkdir()
            archive_root = Path(tmpdir) / "archived"

            cleanup = DownloadCleanup(
                download_folders=[download_folder],
                retention_days=30,
                archive_root=archive_root,
            )

            cleanup.stats = {
                "scanned": 10,
                "archived": 5,
                "deleted": 0,
                "skipped": 4,
                "errors": 1,
            }

            summary = cleanup.get_summary()
            assert "Cleanup Summary" in summary
            assert "10" in summary
            assert "5" in summary
