"""Unit tests for Checksum Generator."""

import csv
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import ChecksumGenerator


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
        "output_file": str(temp_dir / "checksums.csv"),
        "hash_algorithm": "sha256",
        "chunk_size": 8192,
        "min_file_size_bytes": 0,
        "exclusions": {"directories": [], "patterns": [], "extensions": []},
        "operations": {"recursive": True},
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
def test_files(temp_dir):
    """Create test files."""
    scan_dir = temp_dir / "scan"
    scan_dir.mkdir()

    file1 = scan_dir / "file1.txt"
    file1.write_text("test content 1")

    file2 = scan_dir / "file2.txt"
    file2.write_text("test content 2")

    return scan_dir, file1, file2


def test_checksum_generator_initialization(config_file):
    """Test ChecksumGenerator initialization."""
    generator = ChecksumGenerator(config_path=config_file)
    assert generator.config is not None
    assert generator.scan_dir.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        ChecksumGenerator(config_path="nonexistent.yaml")


def test_calculate_checksum_sha256(config_file, test_files):
    """Test SHA256 checksum calculation."""
    generator = ChecksumGenerator(config_path=config_file)
    scan_dir, file1, file2 = test_files

    checksum = generator._calculate_checksum(file1)

    assert checksum is not None
    assert len(checksum) == 64  # SHA256 produces 64 hex characters

    # Verify checksum is correct
    expected = hashlib.sha256(file1.read_bytes()).hexdigest()
    assert checksum == expected


def test_calculate_checksum_md5(config_file, test_files):
    """Test MD5 checksum calculation."""
    generator = ChecksumGenerator(config_path=config_file)
    generator.config["hash_algorithm"] = "md5"
    scan_dir, file1, file2 = test_files

    checksum = generator._calculate_checksum(file1)

    assert checksum is not None
    assert len(checksum) == 32  # MD5 produces 32 hex characters

    # Verify checksum is correct
    expected = hashlib.md5(file1.read_bytes()).hexdigest()
    assert checksum == expected


def test_calculate_checksum_different_files(config_file, test_files):
    """Test that different files produce different checksums."""
    generator = ChecksumGenerator(config_path=config_file)
    scan_dir, file1, file2 = test_files

    checksum1 = generator._calculate_checksum(file1)
    checksum2 = generator._calculate_checksum(file2)

    assert checksum1 != checksum2


def test_should_process_file(config_file, temp_dir):
    """Test file exclusion logic."""
    generator = ChecksumGenerator(config_path=config_file)

    normal_file = temp_dir / "normal.txt"
    normal_file.write_text("test")
    assert generator._should_process_file(normal_file) is True

    # Test exclusion by pattern
    generator.config["exclusions"]["patterns"] = [".tmp"]
    excluded_file = temp_dir / "file.tmp"
    excluded_file.write_text("test")
    assert generator._should_process_file(excluded_file) is False


def test_process_file(config_file, test_files):
    """Test processing a single file."""
    generator = ChecksumGenerator(config_path=config_file)
    scan_dir, file1, file2 = test_files

    result = generator._process_file(file1)

    assert result is True
    assert len(generator.checksums) == 1
    assert generator.checksums[0]["file_path"] == "file1.txt"
    assert generator.checksums[0]["checksum"] is not None


def test_generate_checksums(config_file, test_files):
    """Test generating checksums for multiple files."""
    generator = ChecksumGenerator(config_path=config_file)
    scan_dir, file1, file2 = test_files

    stats = generator.generate_checksums()

    assert stats["files_scanned"] >= 2
    assert stats["checksums_generated"] >= 2
    assert len(generator.checksums) >= 2


def test_save_to_csv(config_file, test_files):
    """Test saving checksums to CSV file."""
    generator = ChecksumGenerator(config_path=config_file)
    scan_dir, file1, file2 = test_files

    generator.generate_checksums()
    csv_path = generator.save_to_csv()

    assert csv_path.exists()

    # Verify CSV content
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) >= 2
        assert "file_path" in rows[0]
        assert "checksum" in rows[0]
        assert "algorithm" in rows[0]


def test_save_to_csv_custom_path(config_file, test_files, temp_dir):
    """Test saving CSV to custom path."""
    generator = ChecksumGenerator(config_path=config_file)
    scan_dir, file1, file2 = test_files

    generator.generate_checksums()
    custom_path = temp_dir / "custom_checksums.csv"
    csv_path = generator.save_to_csv(output_file=str(custom_path))

    assert csv_path == custom_path
    assert custom_path.exists()


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    scan_dir = temp_dir / "scan"
    scan_dir.mkdir()

    config = {
        "scan_directory": str(scan_dir),
        "output_file": str(temp_dir / "checksums.csv"),
        "hash_algorithm": "sha256",
        "chunk_size": 8192,
        "min_file_size_bytes": 0,
        "exclusions": {"directories": [], "patterns": [], "extensions": []},
        "operations": {"recursive": True},
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

    with patch.dict(os.environ, {"HASH_ALGORITHM": "md5"}):
        generator = ChecksumGenerator(config_path=str(config_path))
        assert generator.config["hash_algorithm"] == "md5"
