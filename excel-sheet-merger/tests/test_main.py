"""Unit tests for Excel Sheet Merger."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import yaml

from src.main import ExcelSheetMerger


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "files": {
            "input_file": "test_input.xlsx",
            "output_file": "test_output.csv",
        },
        "sheets": {"names": None},
        "reading": {"header_row": 0},
        "merging": {
            "strategy": "concat",
            "add_sheet_column": True,
        },
        "cleaning": {
            "enabled": True,
            "remove_duplicates": False,
            "remove_empty_rows": False,
            "remove_empty_columns": False,
        },
        "validation": {
            "enabled": True,
            "check_duplicates": False,
            "required_columns": [],
            "critical_columns": [],
            "check_data_types": False,
            "column_types": {},
        },
        "csv_export": {
            "include_index": False,
            "encoding": "utf-8",
            "separator": ",",
            "na_representation": "",
        },
        "error_handling": {"skip_invalid_sheets": False},
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
def sample_excel_file(tmp_path):
    """Create sample Excel file with multiple sheets."""
    excel_path = tmp_path / "test.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df1 = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"]})
        df2 = pd.DataFrame({"id": [4, 5, 6], "name": ["D", "E", "F"]})
        df1.to_excel(writer, sheet_name="Sheet1", index=False)
        df2.to_excel(writer, sheet_name="Sheet2", index=False)
    return str(excel_path)


class TestExcelSheetMerger:
    """Test cases for ExcelSheetMerger class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        assert merger.config is not None
        assert "files" in merger.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            ExcelSheetMerger(config_path="nonexistent.yaml")

    def test_validate_excel_file_valid(self, temp_config_file, sample_excel_file):
        """Test validation of valid Excel file."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        excel_path = Path(sample_excel_file)
        assert merger._validate_excel_file(excel_path) is True

    def test_validate_excel_file_not_found(self, temp_config_file):
        """Test validation of non-existent file."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        excel_path = Path("nonexistent.xlsx")
        assert merger._validate_excel_file(excel_path) is False
        assert len(merger.validation_errors) > 0

    def test_validate_excel_file_invalid_extension(self, temp_config_file, tmp_path):
        """Test validation of file with invalid extension."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not an excel file")
        assert merger._validate_excel_file(invalid_file) is False

    def test_load_excel_sheets_all_sheets(
        self, temp_config_file, sample_excel_file
    ):
        """Test loading all sheets from Excel file."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["files"]["input_file"] = sample_excel_file

        sheets = merger.load_excel_sheets(sample_excel_file)

        assert len(sheets) == 2
        assert "Sheet1" in sheets
        assert "Sheet2" in sheets
        assert len(sheets["Sheet1"]) == 3
        assert len(sheets["Sheet2"]) == 3

    def test_load_excel_sheets_specific_sheets(
        self, temp_config_file, sample_excel_file
    ):
        """Test loading specific sheets from Excel file."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        sheets = merger.load_excel_sheets(sample_excel_file, ["Sheet1"])

        assert len(sheets) == 1
        assert "Sheet1" in sheets

    def test_load_excel_sheets_missing_sheet(
        self, temp_config_file, sample_excel_file
    ):
        """Test loading non-existent sheet raises error."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        with pytest.raises(ValueError):
            merger.load_excel_sheets(sample_excel_file, ["NonexistentSheet"])

    def test_load_excel_sheets_invalid_file(self, temp_config_file, tmp_path):
        """Test loading invalid Excel file raises error."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        invalid_file = tmp_path / "invalid.xlsx"
        invalid_file.write_text("not an excel file")

        with pytest.raises(pd.errors.ExcelFileError):
            merger.load_excel_sheets(str(invalid_file))

    def test_validate_dataframe_empty(self, temp_config_file):
        """Test validation of empty DataFrame."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        empty_df = pd.DataFrame()
        errors = merger._validate_dataframe(empty_df, "TestSheet")

        assert len(errors) > 0
        assert any("empty" in error.lower() for error in errors)

    def test_validate_dataframe_missing_required_columns(self, temp_config_file):
        """Test validation detects missing required columns."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["validation"]["required_columns"] = ["id", "name"]
        df = pd.DataFrame({"id": [1, 2]})
        errors = merger._validate_dataframe(df, "TestSheet")

        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)

    def test_merge_dataframes_concat(self, temp_config_file, sample_excel_file):
        """Test concatenation merge strategy."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.load_excel_sheets(sample_excel_file)
        merged = merger._merge_dataframes()

        assert len(merged) == 6
        assert "source_sheet" in merged.columns

    def test_merge_dataframes_union(self, temp_config_file, sample_excel_file):
        """Test union merge strategy."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["merging"]["strategy"] = "union"
        merger.load_excel_sheets(sample_excel_file)
        merged = merger._merge_dataframes()

        assert len(merged) == 6
        assert "id" in merged.columns
        assert "name" in merged.columns

    def test_merge_dataframes_intersection(self, temp_config_file, sample_excel_file):
        """Test intersection merge strategy."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["merging"]["strategy"] = "intersection"
        merger.load_excel_sheets(sample_excel_file)
        merged = merger._merge_dataframes()

        assert len(merged) == 6
        assert "id" in merged.columns
        assert "name" in merged.columns

    def test_merge_dataframes_no_sheets(self, temp_config_file):
        """Test merge raises error when no sheets loaded."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        with pytest.raises(ValueError):
            merger._merge_dataframes()

    def test_merge_dataframes_invalid_strategy(self, temp_config_file, sample_excel_file):
        """Test merge raises error for invalid strategy."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["merging"]["strategy"] = "invalid_strategy"
        merger.load_excel_sheets(sample_excel_file)

        with pytest.raises(ValueError):
            merger._merge_dataframes()

    def test_clean_merged_data_remove_duplicates(
        self, temp_config_file, sample_excel_file
    ):
        """Test cleaning removes duplicates when enabled."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["cleaning"]["remove_duplicates"] = True
        merger.load_excel_sheets(sample_excel_file)
        merged = merger._merge_dataframes()

        # Add duplicate row
        duplicate_row = merged.iloc[0:1].copy()
        merged_with_dup = pd.concat([merged, duplicate_row], ignore_index=True)

        cleaned = merger._clean_merged_data(merged_with_dup)
        assert len(cleaned) == len(merged)

    def test_clean_merged_data_remove_empty_rows(
        self, temp_config_file, sample_excel_file
    ):
        """Test cleaning removes empty rows when enabled."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["cleaning"]["remove_empty_rows"] = True
        merger.load_excel_sheets(sample_excel_file)
        merged = merger._merge_dataframes()

        # Add empty row
        empty_row = pd.DataFrame({col: [None] for col in merged.columns})
        merged_with_empty = pd.concat([merged, empty_row], ignore_index=True)

        cleaned = merger._clean_merged_data(merged_with_empty)
        assert len(cleaned) == len(merged)

    def test_process_complete_workflow(
        self, temp_config_file, sample_excel_file, tmp_path
    ):
        """Test complete processing workflow."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["files"]["input_file"] = sample_excel_file
        merger.config["files"]["output_file"] = str(tmp_path / "output.csv")

        stats = merger.process()

        assert stats["sheets_processed"] == 2
        assert stats["total_rows"] == 6
        assert merger.merged_df is not None

    def test_export_to_csv(self, temp_config_file, sample_excel_file, tmp_path):
        """Test CSV export functionality."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.load_excel_sheets(sample_excel_file)
        merger.merged_df = merger._merge_dataframes()

        output_path = tmp_path / "output.csv"
        merger.export_to_csv(str(output_path))

        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(merger.merged_df)

    def test_export_to_csv_no_data(self, temp_config_file):
        """Test CSV export raises error when no data available."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        with pytest.raises(ValueError):
            merger.export_to_csv("output.csv")

    def test_process_missing_input_file(self, temp_config_file):
        """Test process raises error when input file not specified."""
        merger = ExcelSheetMerger(config_path=temp_config_file)
        merger.config["files"]["input_file"] = ""

        with pytest.raises(ValueError):
            merger.process()
