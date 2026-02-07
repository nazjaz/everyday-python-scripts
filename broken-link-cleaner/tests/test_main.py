"""Unit tests for Broken Link Cleaner."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import BrokenLinkCleaner


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file."""
    scan_dir = temp_dir / "scan"
    scan_dir.mkdir()

    config = {
        "scan_directory": str(scan_dir),
        "removal_log_file": str(temp_dir / "removed_links.txt"),
        "exclusions": {"directories": [], "patterns": []},
        "operations": {"recursive": True, "dry_run": False},
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


@pytest.fixture
def test_symlinks(temp_dir):
    """Create test symlinks."""
    scan_dir = temp_dir / "scan"
    scan_dir.mkdir()

    # Create a valid target and symlink
    valid_target = scan_dir / "valid_target.txt"
    valid_target.write_text("content")
    valid_link = scan_dir / "valid_link"
    valid_link.symlink_to(valid_target)

    # Create a broken symlink (target doesn't exist)
    broken_link = scan_dir / "broken_link"
    broken_link.symlink_to(scan_dir / "nonexistent_target.txt")

    return scan_dir, broken_link, valid_link


def test_broken_link_cleaner_initialization(config_file):
    """Test BrokenLinkCleaner initialization."""
    cleaner = BrokenLinkCleaner(config_path=config_file)
    assert cleaner.config is not None
    assert cleaner.scan_dir.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        BrokenLinkCleaner(config_path="nonexistent.yaml")


def test_is_broken_symlink_broken(config_file, test_symlinks):
    """Test detection of broken symlink."""
    cleaner = BrokenLinkCleaner(config_path=config_file)
    scan_dir, broken_link, valid_link = test_symlinks

    assert cleaner._is_broken_symlink(broken_link) is True
    assert cleaner._is_broken_symlink(valid_link) is False


def test_is_broken_symlink_not_symlink(config_file, temp_dir):
    """Test that regular files are not detected as broken symlinks."""
    cleaner = BrokenLinkCleaner(config_path=config_file)

    regular_file = temp_dir / "regular_file.txt"
    regular_file.write_text("content")

    assert cleaner._is_broken_symlink(regular_file) is False


def test_get_symlink_target(config_file, test_symlinks):
    """Test getting symlink target."""
    cleaner = BrokenLinkCleaner(config_path=config_file)
    scan_dir, broken_link, valid_link = test_symlinks

    target = cleaner._get_symlink_target(broken_link)
    assert target is not None
    assert "nonexistent_target" in target


def test_should_process_link(config_file, temp_dir):
    """Test link exclusion logic."""
    cleaner = BrokenLinkCleaner(config_path=config_file)

    normal_link = temp_dir / "normal_link"
    normal_link.symlink_to("target")
    assert cleaner._should_process_link(normal_link) is True

    # Test exclusion by pattern
    cleaner.config["exclusions"]["patterns"] = [".git"]
    excluded_link = temp_dir / ".git_link"
    excluded_link.symlink_to("target")
    assert cleaner._should_process_link(excluded_link) is False


def test_remove_symlink_dry_run(config_file, test_symlinks):
    """Test symlink removal in dry run mode."""
    cleaner = BrokenLinkCleaner(config_path=config_file)
    cleaner.config["operations"]["dry_run"] = True
    scan_dir, broken_link, valid_link = test_symlinks

    assert broken_link.exists()
    result = cleaner._remove_symlink(broken_link)

    assert result is True
    assert broken_link.exists()  # Link should still exist in dry run
    assert len(cleaner.removed_links) > 0


def test_remove_symlink_actual(config_file, test_symlinks):
    """Test actual symlink removal."""
    cleaner = BrokenLinkCleaner(config_path=config_file)
    cleaner.config["operations"]["dry_run"] = False
    scan_dir, broken_link, valid_link = test_symlinks

    assert broken_link.exists()
    result = cleaner._remove_symlink(broken_link)

    assert result is True
    assert not broken_link.exists()  # Link should be removed
    assert len(cleaner.removed_links) > 0


def test_clean_broken_links(config_file, test_symlinks):
    """Test cleaning broken links."""
    cleaner = BrokenLinkCleaner(config_path=config_file)
    cleaner.config["operations"]["dry_run"] = False
    scan_dir, broken_link, valid_link = test_symlinks

    stats = cleaner.clean_broken_links()

    assert stats["broken_links_found"] > 0
    assert stats["links_removed"] > 0
    assert not broken_link.exists()  # Broken link should be removed
    assert valid_link.exists()  # Valid link should remain


def test_save_removal_log(config_file, test_symlinks):
    """Test saving removal log."""
    cleaner = BrokenLinkCleaner(config_path=config_file)
    cleaner.config["operations"]["dry_run"] = False
    scan_dir, broken_link, valid_link = test_symlinks

    cleaner._remove_symlink(broken_link)
    log_path = cleaner.save_removal_log()

    assert log_path.exists()
    content = log_path.read_text()
    assert "Broken Symbolic Links Removed" in content
    assert str(broken_link) in content


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    scan_dir = temp_dir / "scan"
    scan_dir.mkdir()

    config = {
        "scan_directory": str(scan_dir),
        "removal_log_file": str(temp_dir / "removed_links.txt"),
        "exclusions": {"directories": [], "patterns": []},
        "operations": {"recursive": True, "dry_run": False},
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    with patch.dict(os.environ, {"DRY_RUN": "true"}):
        cleaner = BrokenLinkCleaner(config_path=str(config_path))
        assert cleaner.config["operations"]["dry_run"] is True
