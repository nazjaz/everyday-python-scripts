"""Unit tests for Directory Statistics."""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import DirectoryStatistics


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config():
    """Create a sample configuration."""
    return {
        "file_type_categories": {
            "images": {
                "extensions": ["jpg", "png"],
                "name": "Images",
            },
            "documents": {
                "extensions": ["pdf", "txt"],
                "name": "Documents",
            },
            "other": {
                "extensions": [],
                "name": "Other Files",
            },
        },
        "exclude_patterns": [],
        "exclude_directories": [],
        "options": {
            "include_hidden": False,
            "include_empty": True,
            "min_file_size": 0,
            "max_file_size": 0,
        },
    }


def test_directory_statistics_initialization(sample_config):
    """Test DirectoryStatistics initialization."""
    analyzer = DirectoryStatistics(sample_config)

    assert "jpg" in analyzer.extension_to_category
    assert analyzer.extension_to_category["jpg"] == "images"
    assert analyzer.extension_to_category["pdf"] == "documents"


def test_get_file_category(sample_config, temp_dir):
    """Test file category detection."""
    analyzer = DirectoryStatistics(sample_config)

    assert analyzer.get_file_category(Path("test.jpg")) == "images"
    assert analyzer.get_file_category(Path("test.pdf")) == "documents"
    assert analyzer.get_file_category(Path("test.unknown")) == "other"


def test_should_exclude_file_hidden(sample_config, temp_dir):
    """Test excluding hidden files."""
    sample_config["options"]["include_hidden"] = False
    analyzer = DirectoryStatistics(sample_config)

    assert analyzer.should_exclude_file(temp_dir / ".hidden") is True
    assert analyzer.should_exclude_file(temp_dir / "visible") is False


def test_should_exclude_file_by_pattern(sample_config, temp_dir):
    """Test excluding files by pattern."""
    sample_config["exclude_patterns"] = ["\\.tmp$"]
    analyzer = DirectoryStatistics(sample_config)

    assert analyzer.should_exclude_file(temp_dir / "file.tmp") is True
    assert analyzer.should_exclude_file(temp_dir / "file.txt") is False


def test_should_exclude_file_by_size(sample_config, temp_dir):
    """Test excluding files by size."""
    sample_config["options"]["min_file_size"] = 100
    sample_config["options"]["max_file_size"] = 1000
    analyzer = DirectoryStatistics(sample_config)

    small_file = temp_dir / "small.txt"
    small_file.write_text("x" * 50)

    medium_file = temp_dir / "medium.txt"
    medium_file.write_text("x" * 500)

    large_file = temp_dir / "large.txt"
    large_file.write_text("x" * 2000)

    assert analyzer.should_exclude_file(small_file) is True
    assert analyzer.should_exclude_file(medium_file) is False
    assert analyzer.should_exclude_file(large_file) is True


def test_should_exclude_directory(sample_config, temp_dir):
    """Test directory exclusion."""
    sample_config["exclude_directories"] = ["^\\.git$"]
    analyzer = DirectoryStatistics(sample_config)

    assert analyzer.should_exclude_directory(temp_dir / ".git") is True
    assert analyzer.should_exclude_directory(temp_dir / "normal_dir") is False


def test_analyze_directory(sample_config, temp_dir):
    """Test directory analysis."""
    # Create test files
    (temp_dir / "test1.jpg").write_text("image content")
    (temp_dir / "test2.pdf").write_text("document content")
    (temp_dir / "test3.txt").write_text("text content")

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=False)

    assert stats["total_files"] == 3
    assert stats["total_size"] > 0
    assert "images" in stats["categories"]
    assert "documents" in stats["categories"]


def test_analyze_directory_recursive(sample_config, temp_dir):
    """Test recursive directory analysis."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    (temp_dir / "file1.txt").write_text("content")
    (subdir / "file2.txt").write_text("content")

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=True)

    assert stats["total_files"] == 2
    assert stats["total_directories"] >= 1


def test_analyze_directory_non_recursive(sample_config, temp_dir):
    """Test non-recursive directory analysis."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    (temp_dir / "file1.txt").write_text("content")
    (subdir / "file2.txt").write_text("content")

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=False)

    assert stats["total_files"] == 1  # Only file in root


def test_analyze_directory_oldest_newest(sample_config, temp_dir):
    """Test finding oldest and newest files."""
    import time

    file1 = temp_dir / "file1.txt"
    file1.write_text("content 1")
    old_time = time.time() - 3600  # 1 hour ago
    os.utime(file1, (old_time, old_time))

    file2 = temp_dir / "file2.txt"
    file2.write_text("content 2")
    # file2 has current time (newer)

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=False)

    assert stats["oldest_file"] is not None
    assert stats["newest_file"] is not None
    assert "file1.txt" in stats["oldest_file"]["path"]
    assert "file2.txt" in stats["newest_file"]["path"]


def test_analyze_directory_largest(sample_config, temp_dir):
    """Test finding largest file."""
    file1 = temp_dir / "file1.txt"
    file1.write_text("x" * 100)

    file2 = temp_dir / "file2.txt"
    file2.write_text("x" * 500)

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=False)

    assert stats["largest_file"] is not None
    assert stats["largest_file"]["size"] == 500


def test_generate_json_report(sample_config, temp_dir):
    """Test generating JSON report."""
    (temp_dir / "test.txt").write_text("content")

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=False)

    report_path = temp_dir / "report.json"
    analyzer.generate_report(stats, report_path, "json")

    assert report_path.exists()

    with open(report_path, "r") as f:
        report = json.load(f)

    assert "summary" in report
    assert "total_files" in report["summary"]
    assert "top_largest_files" in report


def test_generate_txt_report(sample_config, temp_dir):
    """Test generating text report."""
    (temp_dir / "test.txt").write_text("content")

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=False)

    report_path = temp_dir / "report.txt"
    analyzer.generate_report(stats, report_path, "txt")

    assert report_path.exists()

    content = report_path.read_text()
    assert "DIRECTORY STATISTICS REPORT" in content
    assert "SUMMARY" in content
    assert "STORAGE BREAKDOWN" in content


def test_generate_csv_report(sample_config, temp_dir):
    """Test generating CSV report."""
    (temp_dir / "test.txt").write_text("content")

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=False)

    report_path = temp_dir / "report.csv"
    analyzer.generate_report(stats, report_path, "csv")

    assert report_path.exists()

    import csv
    with open(report_path, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) > 0
    assert "Statistic" in rows[0] or "Category" in rows[0]


def test_format_size():
    """Test size formatting."""
    analyzer = DirectoryStatistics({})

    assert "B" in analyzer._format_size(500)
    assert "KB" in analyzer._format_size(2048)
    assert "MB" in analyzer._format_size(1048576)
    assert "GB" in analyzer._format_size(1073741824)


def test_file_type_statistics(sample_config, temp_dir):
    """Test file type statistics."""
    (temp_dir / "test1.jpg").write_text("image")
    (temp_dir / "test2.jpg").write_text("image")
    (temp_dir / "test3.pdf").write_text("doc")

    analyzer = DirectoryStatistics(sample_config)
    stats = analyzer.analyze_directory(temp_dir, recursive=False)

    assert stats["file_types"]["jpg"]["count"] == 2
    assert stats["file_types"]["pdf"]["count"] == 1
    assert stats["categories"]["images"]["count"] == 2
    assert stats["categories"]["documents"]["count"] == 1
