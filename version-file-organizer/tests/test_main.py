"""Unit tests for version file organizer module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import VersionFileOrganizer


class TestVersionFileOrganizer:
    """Test cases for VersionFileOrganizer class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "organization": {"base_folder": "organized"},
            "version": {
                "filename_patterns": [
                    "v(\\d+\\.\\d+\\.\\d+)",
                    "v(\\d+)",
                ],
                "use_metadata": False,
                "compatibility": {"mode": "major"},
            },
            "scan": {"skip_patterns": [".git"]},
            "report": {"output_file": "report.txt"},
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def organizer(self, config_file):
        """Create VersionFileOrganizer instance."""
        return VersionFileOrganizer(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "organization": {"base_folder": "test"},
            "version": {"compatibility": {"mode": "minor"}},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        organizer = VersionFileOrganizer(config_path=str(config_path))
        assert organizer.config["organization"]["base_folder"] == "test"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            VersionFileOrganizer(config_path="nonexistent.yaml")

    def test_parse_version_from_filename(self, organizer, temp_dir):
        """Test version parsing from filename."""
        test_file = temp_dir / "app_v1.2.3.exe"
        version = organizer._parse_version_from_filename(test_file)
        assert version == "1.2.3"

    def test_parse_version_from_filename_v_prefix(self, organizer, temp_dir):
        """Test version parsing with v prefix."""
        test_file = temp_dir / "document_v2.pdf"
        version = organizer._parse_version_from_filename(test_file)
        assert version == "2"

    def test_parse_version_from_filename_separator(self, organizer, temp_dir):
        """Test version parsing with separator."""
        test_file = temp_dir / "file-1.0.0.txt"
        version = organizer._parse_version_from_filename(test_file)
        assert version == "1.0.0"

    def test_parse_version_from_filename_no_version(self, organizer, temp_dir):
        """Test version parsing with no version."""
        test_file = temp_dir / "normal_file.txt"
        version = organizer._parse_version_from_filename(test_file)
        assert version is None

    def test_normalize_version(self, organizer):
        """Test version normalization."""
        assert organizer._normalize_version("v1.2.3") == "1.2.3"
        assert organizer._normalize_version("V2.0") == "2.0"
        assert organizer._normalize_version("1.2.3") == "1.2.3"
        assert organizer._normalize_version("r5") == "5"

    def test_are_versions_compatible_major(self, organizer):
        """Test version compatibility in major mode."""
        organizer.config["version"]["compatibility"]["mode"] = "major"
        assert organizer._are_versions_compatible("1.2.3", "1.3.0") is True
        assert organizer._are_versions_compatible("1.2.3", "2.0.0") is False

    def test_are_versions_compatible_minor(self, organizer):
        """Test version compatibility in minor mode."""
        organizer.config["version"]["compatibility"]["mode"] = "minor"
        assert organizer._are_versions_compatible("1.2.3", "1.2.4") is True
        assert organizer._are_versions_compatible("1.2.3", "1.3.0") is False

    def test_are_versions_compatible_exact(self, organizer):
        """Test version compatibility in exact mode."""
        organizer.config["version"]["compatibility"]["mode"] = "exact"
        assert organizer._are_versions_compatible("1.2.3", "1.2.3") is True
        assert organizer._are_versions_compatible("1.2.3", "1.2.4") is False

    def test_get_version_group_key_major(self, organizer):
        """Test version group key for major mode."""
        organizer.config["version"]["compatibility"]["mode"] = "major"
        assert organizer._get_version_group_key("1.2.3") == "1"
        assert organizer._get_version_group_key("2.0.0") == "2"

    def test_get_version_group_key_minor(self, organizer):
        """Test version group key for minor mode."""
        organizer.config["version"]["compatibility"]["mode"] = "minor"
        assert organizer._get_version_group_key("1.2.3") == "1.2"
        assert organizer._get_version_group_key("1.3.0") == "1.3"

    def test_should_skip_path(self, organizer):
        """Test path skipping logic."""
        path = Path("/some/path/.git/config")
        assert organizer._should_skip_path(path) is True

        path = Path("/some/path/normal_file.txt")
        assert organizer._should_skip_path(path) is False

    def test_scan_directory(self, organizer, temp_dir):
        """Test directory scanning."""
        # Create files with versions
        (temp_dir / "app_v1.0.0.exe").write_text("content")
        (temp_dir / "app_v1.1.0.exe").write_text("content")
        (temp_dir / "app_v2.0.0.exe").write_text("content")
        (temp_dir / "normal.txt").write_text("content")

        organizer.scan_directory(str(temp_dir))

        assert organizer.stats["files_scanned"] == 4
        assert organizer.stats["files_with_versions"] == 3
        assert organizer.stats["version_groups_created"] >= 2

    def test_scan_directory_not_found(self, organizer):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            organizer.scan_directory("/nonexistent/path")

    def test_organize_files_dry_run(self, organizer, temp_dir):
        """Test file organization in dry-run mode."""
        # Create files with versions
        (temp_dir / "app_v1.0.0.exe").write_text("content")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=True)

        # Files should still be in original location
        assert (temp_dir / "app_v1.0.0.exe").exists()

    def test_organize_files_actual(self, organizer, temp_dir):
        """Test file organization in actual mode."""
        # Create files with versions
        (temp_dir / "app_v1.0.0.exe").write_text("content")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=False)

        # Files should be moved to organized folder
        organized_base = temp_dir / "organized"
        assert (organized_base / "v1" / "app_v1.0.0.exe").exists()

    def test_generate_report(self, organizer, temp_dir):
        """Test report generation."""
        # Create files and scan
        (temp_dir / "app_v1.0.0.exe").write_text("content")

        organizer.scan_directory(str(temp_dir))
        report_path = temp_dir / "test_report.txt"
        organizer.generate_report(output_path=str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "VERSION-BASED FILE ORGANIZATION REPORT" in content
        assert "VERSION GROUPS" in content
