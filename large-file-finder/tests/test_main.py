"""Unit tests for Large File Finder."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import LargeFileFinder


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file."""
    config = {
        "scan_directory": str(temp_dir / "scan"),
        "archive_directory": str(temp_dir / "archive"),
        "size_threshold_mb": 1,
        "scan_options": {"recursive": True, "follow_symlinks": False},
        "exclusions": {"directories": [], "patterns": []},
        "archive_options": {
            "method": "move",
            "preserve_timestamps": True,
            "handle_conflicts": "rename",
        },
        "operations": {
            "create_archive_directory": True,
            "auto_archive": False,
            "dry_run": False,
        },
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
def scan_dir(temp_dir):
    """Create scan directory with test files."""
    scan_path = temp_dir / "scan"
    scan_path.mkdir()

    # Create small file (should not be found)
    small_file = scan_path / "small.txt"
    small_file.write_text("small content")

    # Create large file (should be found)
    large_file = scan_path / "large.txt"
    large_content = "x" * (2 * 1024 * 1024)  # 2 MB
    large_file.write_text(large_content)

    # Create subdirectory with large file
    subdir = scan_path / "subdir"
    subdir.mkdir()
    large_file_sub = subdir / "large_sub.txt"
    large_file_sub.write_text(large_content)

    return scan_path


def test_large_file_finder_initialization(config_file):
    """Test LargeFileFinder initialization."""
    finder = LargeFileFinder(config_path=config_file)
    assert finder.config is not None
    assert finder.scan_dir.exists()
    assert finder.archive_dir.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        LargeFileFinder(config_path="nonexistent.yaml")


def test_format_size():
    """Test file size formatting."""
    finder = LargeFileFinder.__new__(LargeFileFinder)
    finder.config = {"size_threshold_mb": 100}

    assert "B" in finder._format_size(500)
    assert "KB" in finder._format_size(2048)
    assert "MB" in finder._format_size(2 * 1024 * 1024)
    assert "GB" in finder._format_size(2 * 1024 * 1024 * 1024)


def test_get_size_threshold_bytes(config_file):
    """Test size threshold conversion to bytes."""
    finder = LargeFileFinder(config_path=config_file)
    bytes_threshold = finder._get_size_threshold_bytes()
    assert bytes_threshold == 1024 * 1024  # 1 MB


def test_should_scan_path_no_exclusions(config_file):
    """Test path scanning when no exclusions are configured."""
    finder = LargeFileFinder(config_path=config_file)
    test_path = Path("/some/path/file.txt")
    assert finder._should_scan_path(test_path) is True


def test_should_scan_path_with_exclusions(config_file, temp_dir):
    """Test path scanning with exclusions."""
    finder = LargeFileFinder(config_path=config_file)
    finder.config["exclusions"] = {
        "directories": [str(temp_dir / "excluded")],
        "patterns": [".DS_Store"],
    }

    excluded_dir = temp_dir / "excluded" / "file.txt"
    excluded_dir.parent.mkdir(parents=True)
    assert finder._should_scan_path(excluded_dir) is False

    excluded_pattern = Path("/some/path/.DS_Store")
    assert finder._should_scan_path(excluded_pattern) is False

    normal_path = Path("/some/path/normal.txt")
    assert finder._should_scan_path(normal_path) is True


def test_find_large_files(config_file, scan_dir):
    """Test finding large files."""
    finder = LargeFileFinder(config_path=config_file)
    large_files = finder.find_large_files()

    assert len(large_files) == 2
    assert all(file_info["size"] > finder._get_size_threshold_bytes() for file_info in large_files)
    assert large_files[0]["size"] >= large_files[1]["size"]


def test_find_large_files_non_recursive(config_file, scan_dir):
    """Test finding large files with non-recursive scan."""
    finder = LargeFileFinder(config_path=config_file)
    finder.config["scan_options"]["recursive"] = False
    large_files = finder.find_large_files()

    assert len(large_files) == 1
    assert large_files[0]["path"] == str(scan_dir / "large.txt")


def test_generate_report(config_file, scan_dir):
    """Test report generation."""
    finder = LargeFileFinder(config_path=config_file)
    finder.find_large_files()
    report = finder.generate_report()

    assert "Large File Finder Report" in report
    assert "Files Found: 2" in report
    assert "large.txt" in report or "large_sub.txt" in report


def test_generate_report_to_file(config_file, scan_dir, temp_dir):
    """Test saving report to file."""
    finder = LargeFileFinder(config_path=config_file)
    finder.find_large_files()
    report_file = str(temp_dir / "test_report.txt")
    report = finder.generate_report(output_file=report_file)

    assert Path(report_file).exists()
    assert "Large File Finder Report" in report


def test_archive_file_move(config_file, scan_dir):
    """Test archiving file with move method."""
    finder = LargeFileFinder(config_path=config_file)
    finder.find_large_files()
    file_info = finder.large_files[0]
    file_path = Path(file_info["path"])

    assert file_path.exists()
    finder._archive_file(file_path)
    assert not file_path.exists()
    assert (finder.archive_dir / file_path.name).exists()


def test_archive_file_copy(config_file, scan_dir):
    """Test archiving file with copy method."""
    finder = LargeFileFinder(config_path=config_file)
    finder.config["archive_options"]["method"] = "copy"
    finder.find_large_files()
    file_info = finder.large_files[0]
    file_path = Path(file_info["path"])

    assert file_path.exists()
    finder._archive_file(file_path)
    assert file_path.exists()
    assert (finder.archive_dir / file_path.name).exists()


def test_archive_file_dry_run(config_file, scan_dir):
    """Test archiving file in dry run mode."""
    finder = LargeFileFinder(config_path=config_file)
    finder.config["operations"]["dry_run"] = True
    finder.find_large_files()
    file_info = finder.large_files[0]
    file_path = Path(file_info["path"])

    assert file_path.exists()
    finder._archive_file(file_path)
    assert file_path.exists()
    assert not (finder.archive_dir / file_path.name).exists()


def test_archive_file_name_conflict_rename(config_file, scan_dir):
    """Test archiving file with name conflict using rename."""
    finder = LargeFileFinder(config_path=config_file)
    finder.find_large_files()
    file_info = finder.large_files[0]
    file_path = Path(file_info["path"])

    # Create file with same name in archive
    archive_file = finder.archive_dir / file_path.name
    archive_file.write_text("existing")

    finder._archive_file(file_path)
    assert (finder.archive_dir / f"{file_path.stem}_1{file_path.suffix}").exists()


def test_archive_file_name_conflict_skip(config_file, scan_dir):
    """Test archiving file with name conflict using skip."""
    finder = LargeFileFinder(config_path=config_file)
    finder.config["archive_options"]["handle_conflicts"] = "skip"
    finder.find_large_files()
    file_info = finder.large_files[0]
    file_path = Path(file_info["path"])

    # Create file with same name in archive
    archive_file = finder.archive_dir / file_path.name
    archive_file.write_text("existing")

    result = finder._archive_file(file_path)
    assert result is False
    assert file_path.exists()


def test_archive_files(config_file, scan_dir):
    """Test archiving all found files."""
    finder = LargeFileFinder(config_path=config_file)
    finder.find_large_files()
    stats = finder.archive_files()

    assert stats["archived"] == 2
    assert len(list(finder.archive_dir.iterdir())) == 2


def test_archive_files_none_found(config_file, temp_dir):
    """Test archiving when no large files are found."""
    finder = LargeFileFinder(config_path=config_file)
    finder.large_files = []
    stats = finder.archive_files()

    assert stats["archived"] == 0


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    config = {
        "scan_directory": str(temp_dir / "scan"),
        "archive_directory": str(temp_dir / "archive"),
        "size_threshold_mb": 1,
        "scan_options": {"recursive": True, "follow_symlinks": False},
        "exclusions": {"directories": [], "patterns": []},
        "archive_options": {
            "method": "move",
            "preserve_timestamps": True,
            "handle_conflicts": "rename",
        },
        "operations": {
            "create_archive_directory": True,
            "auto_archive": False,
            "dry_run": False,
        },
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

    with patch.dict(os.environ, {"SIZE_THRESHOLD_MB": "200"}):
        finder = LargeFileFinder(config_path=str(config_path))
        assert finder.config["size_threshold_mb"] == 200
