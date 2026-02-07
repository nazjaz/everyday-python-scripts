"""Unit tests for priority file organizer module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import PriorityFileOrganizer


class TestPriorityFileOrganizer:
    """Test cases for PriorityFileOrganizer class."""

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
            "priorities": [
                {
                    "name": "high",
                    "priority": 4,
                    "folder": "High",
                    "criteria": {
                        "extensions": [".pdf", ".doc"],
                        "keywords": ["important"],
                    },
                },
                {
                    "name": "low",
                    "priority": 2,
                    "folder": "Low",
                    "criteria": {"extensions": [".txt"]},
                },
            ],
            "duplicates": {"action": "skip"},
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
        """Create PriorityFileOrganizer instance."""
        return PriorityFileOrganizer(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "organization": {"base_folder": "test"},
            "priorities": [
                {
                    "name": "test",
                    "priority": 1,
                    "folder": "Test",
                    "criteria": {},
                }
            ],
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        organizer = PriorityFileOrganizer(config_path=str(config_path))
        assert organizer.config["organization"]["base_folder"] == "test"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            PriorityFileOrganizer(config_path="nonexistent.yaml")

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test YAMLError when config file is invalid."""
        config_path = temp_dir / "invalid.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        with pytest.raises(yaml.YAMLError):
            PriorityFileOrganizer(config_path=str(config_path))

    def test_load_priority_levels_sorted(self, organizer):
        """Test that priority levels are sorted correctly."""
        priorities = organizer.priority_levels
        assert len(priorities) == 2
        assert priorities[0]["name"] == "high"
        assert priorities[1]["name"] == "low"

    def test_load_priority_levels_missing_name(self, temp_dir):
        """Test ValueError when priority level missing name."""
        config = {
            "priorities": [
                {"priority": 1, "folder": "Test", "criteria": {}}
            ],
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError, match="missing 'name' field"):
            PriorityFileOrganizer(config_path=str(config_path))

    def test_matches_extension(self, organizer):
        """Test extension matching."""
        file_path = Path("test.pdf")
        assert organizer._matches_extension(file_path, [".pdf", ".doc"])
        assert not organizer._matches_extension(file_path, [".txt"])

    def test_matches_extension_without_dot(self, organizer):
        """Test extension matching without dot prefix."""
        file_path = Path("test.pdf")
        assert organizer._matches_extension(file_path, ["pdf", "doc"])

    def test_matches_keywords(self, organizer):
        """Test keyword matching."""
        file_path = Path("/path/to/important_file.txt")
        assert organizer._matches_keywords(file_path, ["important"])
        assert not organizer._matches_keywords(file_path, ["unrelated"])

    def test_matches_pattern(self, organizer):
        """Test pattern matching."""
        file_path = Path("/path/to/test_file.txt")
        assert organizer._matches_pattern(file_path, "*test*")
        assert organizer._matches_pattern(file_path, "*.txt")
        assert not organizer._matches_pattern(file_path, "*.pdf")

    def test_determine_priority_by_extension(self, organizer):
        """Test priority determination by extension."""
        file_path = Path("document.pdf")
        priority = organizer._determine_priority(file_path)
        assert priority is not None
        assert priority["name"] == "high"

    def test_determine_priority_by_keyword(self, organizer):
        """Test priority determination by keyword."""
        file_path = Path("important_note.txt")
        priority = organizer._determine_priority(file_path)
        assert priority is not None
        assert priority["name"] == "high"

    def test_determine_priority_no_match(self, organizer):
        """Test priority determination when no criteria match."""
        file_path = Path("random_file.xyz")
        priority = organizer._determine_priority(file_path)
        assert priority is None

    def test_should_skip_path(self, organizer):
        """Test path skipping logic."""
        path = Path("/some/path/.git/config")
        assert organizer._should_skip_path(path) is True

        path = Path("/some/path/normal_file.txt")
        assert organizer._should_skip_path(path) is False

    def test_calculate_file_hash(self, organizer, temp_dir):
        """Test file hash calculation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        hash1 = organizer._calculate_file_hash(test_file)
        hash2 = organizer._calculate_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 32

    def test_is_duplicate_same_content(self, organizer, temp_dir):
        """Test duplicate detection with same content."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("same content")
        file2.write_text("same content")

        is_dup1, _ = organizer._is_duplicate(file1)
        is_dup2, dup_path = organizer._is_duplicate(file2)

        assert is_dup1 is False
        assert is_dup2 is True
        assert dup_path == str(file1)

    def test_is_duplicate_different_content(self, organizer, temp_dir):
        """Test duplicate detection with different content."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content one")
        file2.write_text("content two")

        is_dup1, _ = organizer._is_duplicate(file1)
        is_dup2, _ = organizer._is_duplicate(file2)

        assert is_dup1 is False
        assert is_dup2 is False

    def test_organize_directory_dry_run(self, organizer, temp_dir):
        """Test directory organization in dry-run mode."""
        # Create test files
        (temp_dir / "document.pdf").write_text("pdf content")
        (temp_dir / "note.txt").write_text("text content")

        organizer.organize_directory(str(temp_dir), dry_run=True)

        # Files should still be in original location
        assert (temp_dir / "document.pdf").exists()
        assert (temp_dir / "note.txt").exists()
        assert organizer.stats["files_scanned"] == 2

    def test_organize_directory_actual(self, organizer, temp_dir):
        """Test directory organization in actual mode."""
        # Create test files
        (temp_dir / "document.pdf").write_text("pdf content")
        (temp_dir / "note.txt").write_text("text content")

        organizer.organize_directory(str(temp_dir), dry_run=False)

        # Files should be moved to organized folders
        organized_base = temp_dir / "organized"
        assert (organized_base / "High" / "document.pdf").exists()
        assert (organized_base / "Low" / "note.txt").exists()
        assert organizer.stats["files_organized"] == 2

    def test_organize_directory_not_found(self, organizer):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            organizer.organize_directory("/nonexistent/path")

    def test_organize_directory_not_a_directory(self, organizer, temp_dir):
        """Test ValueError when path is not a directory."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            organizer.organize_directory(str(test_file))

    def test_generate_report(self, organizer, temp_dir):
        """Test report generation."""
        organizer.stats = {
            "files_scanned": 10,
            "files_organized": 5,
            "duplicates_found": 2,
            "errors": 0,
            "priority_distribution": {"high": 3, "low": 2},
        }

        report_path = temp_dir / "test_report.txt"
        organizer.generate_report(output_path=str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "PRIORITY-BASED FILE ORGANIZATION REPORT" in content
        assert "Files scanned: 10" in content
        assert "high: 3 files" in content
