"""Unit tests for source folder organizer."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    SourceFolderOrganizer,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "source_folders": ["/test/path1", "/test/path2"],
                "destination": "/test/dest",
                "mapping_file": "/test/mapping.json",
                "handle_duplicates": "rename",
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["source_folders"] == ["/test/path1", "/test/path2"]
            assert result["destination"] == "/test/dest"
            assert result["mapping_file"] == "/test/mapping.json"
            assert result["handle_duplicates"] == "rename"
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


class TestSourceFolderOrganizer:
    """Test SourceFolderOrganizer class."""

    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
            )

            assert organizer.source_folders == [source_folder.resolve()]
            assert organizer.destination_root == destination.resolve()
            assert organizer.mapping_file == mapping_file.resolve()
            assert organizer.dry_run is False
            assert organizer.handle_duplicates == "skip"

    def test_init_invalid_duplicate_handling(self):
        """Test that invalid duplicate handling raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            with pytest.raises(ValueError, match="handle_duplicates must be"):
                SourceFolderOrganizer(
                    source_folders=[source_folder],
                    destination_root=destination,
                    mapping_file=mapping_file,
                    handle_duplicates="invalid",
                )

    def test_init_nonexistent_source_folder(self):
        """Test that nonexistent source folder raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "nonexistent"
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            with pytest.raises(FileNotFoundError):
                SourceFolderOrganizer(
                    source_folders=[source_folder],
                    destination_root=destination,
                    mapping_file=mapping_file,
                )

    def test_init_file_not_directory(self):
        """Test that file path as source raises NotADirectoryError."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = Path(f.name)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                destination = Path(tmpdir) / "organized"
                mapping_file = Path(tmpdir) / "mapping.json"

                with pytest.raises(NotADirectoryError):
                    SourceFolderOrganizer(
                        source_folders=[file_path],
                        destination_root=destination,
                        mapping_file=mapping_file,
                    )
        finally:
            file_path.unlink()

    def test_load_mapping_existing_file(self):
        """Test loading existing mapping file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            mapping_data = {
                "/organized/file1.txt": "/source/file1.txt",
                "/organized/file2.txt": "/source/file2.txt",
            }
            with open(mapping_file, "w") as f:
                json.dump(mapping_data, f)

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
            )

            assert len(organizer.location_mapping) == 2
            assert "/organized/file1.txt" in organizer.location_mapping

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            file_path = Path(f.name)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                source_folder = Path(tmpdir) / "source"
                source_folder.mkdir()
                destination = Path(tmpdir) / "organized"
                mapping_file = Path(tmpdir) / "mapping.json"

                organizer = SourceFolderOrganizer(
                    source_folders=[source_folder],
                    destination_root=destination,
                    mapping_file=mapping_file,
                )

                hash1 = organizer._calculate_file_hash(file_path)
                hash2 = organizer._calculate_file_hash(file_path)

                assert hash1 == hash2
                assert len(hash1) == 64
        finally:
            file_path.unlink()

    def test_get_organized_path(self):
        """Test organized path generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            subdir = source_folder / "subdir"
            subdir.mkdir()
            test_file = subdir / "file.txt"
            test_file.write_text("content")

            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
            )

            organized_path = organizer._get_organized_path(test_file, source_folder)
            expected = destination / "source" / "subdir" / "file.txt"

            assert organized_path == expected

    def test_handle_duplicate_skip(self):
        """Test duplicate handling with skip strategy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            source_file = source_folder / "file.txt"
            source_file.write_text("same content")

            dest_file = destination / "source" / "file.txt"
            dest_file.parent.mkdir(parents=True)
            dest_file.write_text("same content")

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
                handle_duplicates="skip",
            )

            result = organizer._handle_duplicate(source_file, dest_file)
            assert result is None

    def test_handle_duplicate_rename(self):
        """Test duplicate handling with rename strategy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            source_file = source_folder / "file.txt"
            source_file.write_text("same content")

            dest_file = destination / "source" / "file.txt"
            dest_file.parent.mkdir(parents=True)
            dest_file.write_text("same content")

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
                handle_duplicates="rename",
            )

            result = organizer._handle_duplicate(source_file, dest_file)
            assert result is not None
            assert result.name == "file_copy1.txt"

    def test_organize_files_single_file(self):
        """Test organizing a single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            test_file = source_folder / "test.txt"
            test_file.write_text("test content")

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
                dry_run=True,
            )

            stats = organizer.organize_files()

            assert stats["processed"] == 1
            assert stats["moved"] == 1
            assert stats["duplicates"] == 0
            assert stats["errors"] == 0

    def test_organize_files_multiple_folders(self):
        """Test organizing files from multiple source folders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source1 = Path(tmpdir) / "source1"
            source1.mkdir()
            source2 = Path(tmpdir) / "source2"
            source2.mkdir()

            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            file1 = source1 / "file1.txt"
            file1.write_text("content1")
            file2 = source2 / "file2.txt"
            file2.write_text("content2")

            organizer = SourceFolderOrganizer(
                source_folders=[source1, source2],
                destination_root=destination,
                mapping_file=mapping_file,
                dry_run=True,
            )

            stats = organizer.organize_files()

            assert stats["processed"] == 2
            assert stats["moved"] == 2

    def test_organize_files_preserves_structure(self):
        """Test that file organization preserves directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            subdir = source_folder / "subdir"
            subdir.mkdir()
            nested = subdir / "nested"
            nested.mkdir()

            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            test_file = nested / "file.txt"
            test_file.write_text("content")

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
                dry_run=True,
            )

            stats = organizer.organize_files()

            assert stats["moved"] == 1
            expected_path = destination / "source" / "subdir" / "nested" / "file.txt"
            assert str(expected_path) in organizer.location_mapping

    def test_get_mapping_report(self):
        """Test mapping report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
            )

            organizer.location_mapping = {
                "/organized/file1.txt": "/source/file1.txt",
            }

            report = organizer.get_mapping_report()
            assert "Location Mapping Report" in report
            assert "/organized/file1.txt" in report
            assert "/source/file1.txt" in report

    def test_get_mapping_report_empty(self):
        """Test mapping report with no mappings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = Path(tmpdir) / "source"
            source_folder.mkdir()
            destination = Path(tmpdir) / "organized"
            mapping_file = Path(tmpdir) / "mapping.json"

            organizer = SourceFolderOrganizer(
                source_folders=[source_folder],
                destination_root=destination,
                mapping_file=mapping_file,
            )

            report = organizer.get_mapping_report()
            assert "No location mappings found" in report
