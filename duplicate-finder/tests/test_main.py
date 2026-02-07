"""Unit tests for Duplicate File Finder."""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import DuplicateFinder


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
        "hash_algorithm": "md5",
        "min_file_size": 0,
        "max_file_size": 0,
        "chunk_size": 8192,
        "exclude_patterns": [],
        "exclude_directories": [],
        "recommendations": {
            "keep_oldest": True,
            "keep_shortest_path": False,
            "keep_directories": [],
        },
    }


def test_duplicate_finder_initialization(sample_config):
    """Test DuplicateFinder initialization."""
    finder = DuplicateFinder(sample_config)

    assert finder.hash_algorithm == "md5"
    assert finder.min_file_size == 0
    assert finder.chunk_size == 8192


def test_calculate_file_hash(sample_config, temp_dir):
    """Test file hash calculation."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    finder = DuplicateFinder(sample_config)
    file_hash = finder.calculate_file_hash(test_file)

    assert file_hash is not None
    assert len(file_hash) == 32  # MD5 hash length

    # Verify hash is correct
    expected_hash = hashlib.md5(b"test content").hexdigest()
    assert file_hash == expected_hash


def test_calculate_file_hash_sha256(sample_config, temp_dir):
    """Test SHA256 hash calculation."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    sample_config["hash_algorithm"] = "sha256"
    finder = DuplicateFinder(sample_config)
    file_hash = finder.calculate_file_hash(test_file)

    assert file_hash is not None
    assert len(file_hash) == 64  # SHA256 hash length


def test_calculate_file_hash_nonexistent(sample_config, temp_dir):
    """Test hash calculation for non-existent file."""
    nonexistent_file = temp_dir / "nonexistent.txt"

    finder = DuplicateFinder(sample_config)
    file_hash = finder.calculate_file_hash(nonexistent_file)

    assert file_hash is None


def test_should_exclude_file_by_pattern(sample_config, temp_dir):
    """Test file exclusion by pattern."""
    sample_config["exclude_patterns"] = ["\\.tmp$"]

    finder = DuplicateFinder(sample_config)

    assert finder.should_exclude_file(temp_dir / "file.tmp") is True
    assert finder.should_exclude_file(temp_dir / "file.txt") is False


def test_should_exclude_file_by_size(sample_config, temp_dir):
    """Test file exclusion by size."""
    sample_config["min_file_size"] = 100
    sample_config["max_file_size"] = 1000

    finder = DuplicateFinder(sample_config)

    # Create files of different sizes
    small_file = temp_dir / "small.txt"
    small_file.write_text("x" * 50)  # 50 bytes

    medium_file = temp_dir / "medium.txt"
    medium_file.write_text("x" * 500)  # 500 bytes

    large_file = temp_dir / "large.txt"
    large_file.write_text("x" * 2000)  # 2000 bytes

    assert finder.should_exclude_file(small_file) is True  # Too small
    assert finder.should_exclude_file(medium_file) is False  # Within range
    assert finder.should_exclude_file(large_file) is True  # Too large


def test_should_exclude_directory(sample_config, temp_dir):
    """Test directory exclusion."""
    sample_config["exclude_directories"] = ["^\\.git$"]

    finder = DuplicateFinder(sample_config)

    assert finder.should_exclude_directory(temp_dir / ".git") is True
    assert finder.should_exclude_directory(temp_dir / "normal_dir") is False


def test_find_duplicates(sample_config, temp_dir):
    """Test finding duplicate files."""
    # Create duplicate files
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"
    file3 = temp_dir / "file3.txt"

    content = "duplicate content"
    file1.write_text(content)
    file2.write_text(content)
    file3.write_text("different content")

    finder = DuplicateFinder(sample_config)
    duplicates = finder.find_duplicates([temp_dir], recursive=False)

    assert len(duplicates) == 1  # One duplicate group
    assert len(duplicates[list(duplicates.keys())[0]]) == 2  # Two duplicate files


def test_find_duplicates_no_duplicates(sample_config, temp_dir):
    """Test finding duplicates when none exist."""
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"

    file1.write_text("content 1")
    file2.write_text("content 2")

    finder = DuplicateFinder(sample_config)
    duplicates = finder.find_duplicates([temp_dir], recursive=False)

    assert len(duplicates) == 0


def test_generate_recommendations(sample_config, temp_dir):
    """Test generating recommendations."""
    # Create duplicate files with different modification times
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"

    content = "duplicate content"
    file1.write_text(content)
    file2.write_text(content)

    # Set different modification times
    import time
    old_time = time.time() - 3600  # 1 hour ago
    os.utime(file1, (old_time, old_time))

    finder = DuplicateFinder(sample_config)
    duplicates = finder.find_duplicates([temp_dir], recursive=False)
    recommendations = finder.generate_recommendations(duplicates)

    assert len(recommendations) == 1

    rec = list(recommendations.values())[0]
    assert "keep" in rec
    assert "delete" in rec
    assert len(rec["delete"]) == 1


def test_generate_recommendations_keep_oldest(sample_config, temp_dir):
    """Test recommendations keep oldest file."""
    sample_config["recommendations"]["keep_oldest"] = True

    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"

    content = "duplicate content"
    file1.write_text(content)
    file2.write_text(content)

    import time
    old_time = time.time() - 3600
    os.utime(file1, (old_time, old_time))

    finder = DuplicateFinder(sample_config)
    duplicates = finder.find_duplicates([temp_dir], recursive=False)
    recommendations = finder.generate_recommendations(duplicates)

    rec = list(recommendations.values())[0]
    # Oldest file should be kept
    assert "file1.txt" in rec["keep"]["path"]


def test_generate_json_report(sample_config, temp_dir):
    """Test generating JSON report."""
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"

    content = "duplicate content"
    file1.write_text(content)
    file2.write_text(content)

    finder = DuplicateFinder(sample_config)
    duplicates = finder.find_duplicates([temp_dir], recursive=False)
    recommendations = finder.generate_recommendations(duplicates)

    report_path = temp_dir / "report.json"
    finder.generate_report(duplicates, recommendations, report_path, "json")

    assert report_path.exists()

    import json
    with open(report_path, "r") as f:
        report = json.load(f)

    assert "duplicates" in report
    assert "recommendations" in report
    assert report["total_duplicate_groups"] == 1


def test_generate_txt_report(sample_config, temp_dir):
    """Test generating text report."""
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"

    content = "duplicate content"
    file1.write_text(content)
    file2.write_text(content)

    finder = DuplicateFinder(sample_config)
    duplicates = finder.find_duplicates([temp_dir], recursive=False)
    recommendations = finder.generate_recommendations(duplicates)

    report_path = temp_dir / "report.txt"
    finder.generate_report(duplicates, recommendations, report_path, "txt")

    assert report_path.exists()

    content = report_path.read_text()
    assert "DUPLICATE FILE REPORT" in content
    assert "KEEP" in content
    assert "DELETE" in content


def test_generate_csv_report(sample_config, temp_dir):
    """Test generating CSV report."""
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"

    content = "duplicate content"
    file1.write_text(content)
    file2.write_text(content)

    finder = DuplicateFinder(sample_config)
    duplicates = finder.find_duplicates([temp_dir], recursive=False)
    recommendations = finder.generate_recommendations(duplicates)

    report_path = temp_dir / "report.csv"
    finder.generate_report(duplicates, recommendations, report_path, "csv")

    assert report_path.exists()

    import csv
    with open(report_path, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) > 1  # Header + data rows
    assert "KEEP" in rows[1] or "DELETE" in rows[1]


def test_find_files_recursive(sample_config, temp_dir):
    """Test finding files recursively."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    file1 = temp_dir / "file1.txt"
    file2 = subdir / "file2.txt"

    file1.write_text("content")
    file2.write_text("content")

    finder = DuplicateFinder(sample_config)
    files = finder.find_files([temp_dir], recursive=True)

    assert len(files) == 2


def test_find_files_non_recursive(sample_config, temp_dir):
    """Test finding files non-recursively."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    file1 = temp_dir / "file1.txt"
    file2 = subdir / "file2.txt"

    file1.write_text("content")
    file2.write_text("content")

    finder = DuplicateFinder(sample_config)
    files = finder.find_files([temp_dir], recursive=False)

    assert len(files) == 1  # Only file in root directory
