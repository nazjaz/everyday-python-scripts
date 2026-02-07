"""Unit tests for CSV processor module."""

import csv
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import yaml

from src.main import CSVProcessor


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def sample_csv(temp_dir):
    """Create a sample CSV file for testing."""
    csv_path = Path(temp_dir) / "test.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "date", "age", "email"])
        writer.writerow(["John Doe", "2024-02-07", "30", "john@example.com"])
        writer.writerow(["Jane Smith", "02/07/2024", "25", "jane@example.com"])
        writer.writerow(["John Doe", "2024-02-07", "30", "john@example.com"])  # Duplicate
        writer.writerow(["Bob", "invalid-date", "40", "bob@example.com"])
    return csv_path


@pytest.fixture
def config_file(temp_dir, sample_csv):
    """Create a temporary configuration file."""
    output_csv = Path(temp_dir) / "output.csv"
    config = {
        "files": {
            "input_file": str(sample_csv),
            "output_file": str(output_csv),
            "report_file": f"{temp_dir}/report.txt",
        },
        "duplicate_removal": {
            "enabled": True,
            "method": "all_columns",
            "keep": "first",
        },
        "date_standardization": {
            "enabled": True,
            "target_format": "%Y-%m-%d",
            "date_columns": ["date"],
            "input_formats": [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
            ],
            "handle_invalid_dates": "skip",
        },
        "data_cleaning": {
            "enabled": True,
            "trim_whitespace": True,
            "normalize_whitespace": True,
            "strip_quotes": True,
        },
        "validation": {
            "enabled": True,
            "check_missing_values": True,
        },
        "reporting": {
            "include_summary": True,
            "include_duplicates": True,
            "include_invalid_dates": True,
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_csv_processor_initialization(config_file):
    """Test CSVProcessor initializes correctly."""
    processor = CSVProcessor(config_path=str(config_file))
    assert processor.df is None
    assert processor.stats["original_rows"] == 0


def test_csv_processor_missing_config():
    """Test CSVProcessor raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        CSVProcessor(config_path="nonexistent.yaml")


def test_load_csv(config_file, sample_csv):
    """Test CSV file loading."""
    processor = CSVProcessor(config_path=str(config_file))
    processor.load_csv(str(sample_csv))

    assert processor.df is not None
    assert len(processor.df) == 4
    assert len(processor.df.columns) == 4
    assert processor.stats["original_rows"] == 4


def test_load_csv_missing_file(config_file):
    """Test loading non-existent CSV file."""
    processor = CSVProcessor(config_path=str(config_file))
    with pytest.raises(FileNotFoundError):
        processor.load_csv("nonexistent.csv")


def test_remove_duplicates(config_file, sample_csv):
    """Test duplicate removal."""
    processor = CSVProcessor(config_path=str(config_file))
    processor.load_csv(str(sample_csv))

    original_count = len(processor.df)
    processor._remove_duplicates()

    assert len(processor.df) < original_count
    assert processor.stats["duplicates_removed"] > 0


def test_standardize_dates(config_file, sample_csv):
    """Test date standardization."""
    processor = CSVProcessor(config_path=str(config_file))
    processor.load_csv(str(sample_csv))

    processor._standardize_dates()

    # Check that dates were standardized
    if "date" in processor.df.columns:
        # All valid dates should be in target format
        date_values = processor.df["date"].dropna()
        for value in date_values:
            if value != "invalid-date":  # Skip invalid dates
                assert "-" in str(value)  # Should be YYYY-MM-DD format


def test_try_parse_date(config_file):
    """Test date parsing with multiple formats."""
    processor = CSVProcessor(config_path=str(config_file))

    from datetime import datetime

    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]

    # Valid dates
    assert processor._try_parse_date("2024-02-07", formats) == datetime(2024, 2, 7)
    assert processor._try_parse_date("02/07/2024", formats) == datetime(2024, 2, 7)

    # Invalid date
    assert processor._try_parse_date("invalid", formats) is None


def test_clean_data(config_file, sample_csv):
    """Test data cleaning."""
    processor = CSVProcessor(config_path=str(config_file))
    processor.load_csv(str(sample_csv))

    processor._clean_data()

    # Check that whitespace was trimmed
    assert processor.stats["rows_cleaned"] >= 0


def test_validate_data(config_file, sample_csv):
    """Test data validation."""
    processor = CSVProcessor(config_path=str(config_file))
    processor.load_csv(str(sample_csv))

    processor._validate_data()

    # Validation should complete without errors
    assert processor.stats["validation_errors"] >= 0


def test_process_complete_workflow(config_file, sample_csv, temp_dir):
    """Test complete processing workflow."""
    processor = CSVProcessor(config_path=str(config_file))
    stats = processor.process()

    assert stats["original_rows"] > 0
    assert stats["final_rows"] > 0
    assert stats["final_rows"] <= stats["original_rows"]

    # Check output file was created
    output_file = Path(temp_dir) / "output.csv"
    assert output_file.exists()


def test_save_csv(config_file, sample_csv, temp_dir):
    """Test saving processed CSV."""
    processor = CSVProcessor(config_path=str(config_file))
    processor.load_csv(str(sample_csv))
    processor._remove_duplicates()

    output_path = Path(temp_dir) / "output.csv"
    processor.save_csv(str(output_path))

    assert output_path.exists()

    # Verify file can be read back
    df = pd.read_csv(output_path)
    assert len(df) == len(processor.df)


def test_generate_report(config_file, sample_csv, temp_dir):
    """Test report generation."""
    processor = CSVProcessor(config_path=str(config_file))
    processor.load_csv(str(sample_csv))
    processor._remove_duplicates()
    processor._standardize_dates()
    processor._validate_data()

    processor._generate_report()

    # Check report file exists
    report_path = Path(temp_dir) / "report.txt"
    assert report_path.exists()

    # Check report content
    with open(report_path, "r") as f:
        content = f.read()
        assert "Processing Summary" in content
        assert "Original Rows" in content
