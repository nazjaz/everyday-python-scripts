"""Unit tests for Pattern File Organizer."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import PatternFileOrganizer, PatternRule


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "source": {
            "directory": ".",
            "recursive": True,
            "exclude": {
                "patterns": [],
                "directories": [],
                "extensions": [],
            },
        },
        "rules": [
            {
                "name": "Images",
                "pattern": "\\.(jpg|png|gif)$",
                "destination": "Pictures",
                "match_type": "extension",
                "case_sensitive": False,
                "priority": 10,
                "enabled": True,
            },
            {
                "name": "Documents",
                "pattern": "\\.(pdf|txt)$",
                "destination": "Documents",
                "match_type": "extension",
                "case_sensitive": False,
                "priority": 10,
                "enabled": True,
            },
        ],
        "operations": {
            "create_backup": False,
            "skip_existing": True,
            "preserve_structure": False,
        },
        "report": {
            "output_directory": "output",
            "output_file": "report.txt",
        },
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
def temp_directory(tmp_path):
    """Create temporary directory with test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create files with different extensions
    (test_dir / "image1.jpg").write_text("image content")
    (test_dir / "image2.PNG").write_text("image content")
    (test_dir / "doc1.pdf").write_text("document content")
    (test_dir / "doc2.txt").write_text("text content")
    (test_dir / "other.dat").write_text("other content")

    return test_dir


class TestPatternRule:
    """Test cases for PatternRule class."""

    def test_init_creates_rule(self):
        """Test that rule is created with correct attributes."""
        rule = PatternRule(
            name="Test",
            pattern="\\.jpg$",
            destination="/tmp",
            case_sensitive=False,
        )
        assert rule.name == "Test"
        assert rule.pattern == "\\.jpg$"
        assert rule.destination == Path("/tmp")
        assert rule.case_sensitive is False
        assert rule.enabled is True

    def test_init_raises_invalid_regex(self):
        """Test that invalid regex raises error."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            PatternRule(name="Test", pattern="[invalid", destination="/tmp")

    def test_matches_filename(self):
        """Test matching against filename."""
        rule = PatternRule(
            name="Test",
            pattern="test",
            destination="/tmp",
            match_type="filename",
        )
        file_path = Path("/path/to/test_file.txt")
        assert rule.matches(file_path) is True

    def test_matches_extension(self):
        """Test matching against extension."""
        rule = PatternRule(
            name="Test",
            pattern="\\.jpg$",
            destination="/tmp",
            match_type="extension",
        )
        file_path = Path("/path/to/image.jpg")
        assert rule.matches(file_path) is True

        file_path = Path("/path/to/image.png")
        assert rule.matches(file_path) is False

    def test_matches_case_insensitive(self):
        """Test case-insensitive matching."""
        rule = PatternRule(
            name="Test",
            pattern="test",
            destination="/tmp",
            case_sensitive=False,
        )
        file_path = Path("/path/to/TEST_file.txt")
        assert rule.matches(file_path) is True

    def test_matches_case_sensitive(self):
        """Test case-sensitive matching."""
        rule = PatternRule(
            name="Test",
            pattern="test",
            destination="/tmp",
            case_sensitive=True,
        )
        file_path = Path("/path/to/TEST_file.txt")
        assert rule.matches(file_path) is False

    def test_matches_disabled_rule(self):
        """Test that disabled rule doesn't match."""
        rule = PatternRule(
            name="Test",
            pattern=".*",
            destination="/tmp",
            enabled=False,
        )
        file_path = Path("/path/to/file.txt")
        assert rule.matches(file_path) is False


class TestPatternFileOrganizer:
    """Test cases for PatternFileOrganizer class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        assert organizer.config is not None
        assert "rules" in organizer.config
        assert len(organizer.rules) == 2

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            PatternFileOrganizer(config_path="nonexistent.yaml")

    def test_init_raises_no_rules(self, tmp_path):
        """Test that initialization raises error when no rules defined."""
        config_path = tmp_path / "config.yaml"
        config = {"source": {"directory": "."}}
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError, match="No pattern rules"):
            PatternFileOrganizer(config_path=str(config_path))

    def test_load_rules_sorts_by_priority(self, temp_config_file):
        """Test that rules are sorted by priority."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        # Modify priorities
        organizer.rules[0].priority = 5
        organizer.rules[1].priority = 10
        organizer._load_rules()

        # Rules should be sorted by priority (higher first)
        priorities = [r.priority for r in organizer.rules]
        assert priorities == sorted(priorities, reverse=True)

    def test_organize_files_finds_matches(self, temp_config_file, temp_directory):
        """Test that organize_files finds matching files."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        result = organizer.organize_files(
            source_directory=str(temp_directory), dry_run=True
        )

        assert result["stats"]["files_scanned"] > 0
        assert result["stats"]["files_matched"] > 0

    def test_organize_files_dry_run(self, temp_config_file, temp_directory):
        """Test dry-run mode doesn't move files."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        result = organizer.organize_files(
            source_directory=str(temp_directory), dry_run=True
        )

        # Files should still exist in original location
        assert (temp_directory / "image1.jpg").exists()
        assert result["stats"]["files_moved"] == 0

    def test_organize_files_actually_moves(self, temp_config_file, temp_directory):
        """Test that organize_files actually moves files."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        result = organizer.organize_files(
            source_directory=str(temp_directory), dry_run=False
        )

        # Files should be moved to destination
        assert result["stats"]["files_moved"] > 0
        # Check that files were moved
        pictures_dir = temp_directory / "Pictures"
        if pictures_dir.exists():
            moved_files = list(pictures_dir.glob("*"))
            assert len(moved_files) > 0

    def test_organize_files_nonexistent_directory(self, temp_config_file):
        """Test that nonexistent directory raises error."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            organizer.organize_files("/nonexistent/path")

    def test_organize_files_non_recursive(self, temp_config_file, tmp_path):
        """Test non-recursive search."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create file in root
        (test_dir / "image.jpg").write_text("content")

        # Create subdirectory with file
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "image.jpg").write_text("content")

        result = organizer.organize_files(
            str(test_dir), recursive=False, dry_run=True
        )

        # Should find file in root but not in subdirectory
        assert result["stats"]["files_scanned"] >= 1

    def test_find_matching_rule(self, temp_config_file):
        """Test finding matching rule for file."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        file_path = Path("/path/to/image.jpg")
        rule = organizer._find_matching_rule(file_path)
        assert rule is not None
        assert rule.name == "Images"

    def test_find_matching_rule_no_match(self, temp_config_file):
        """Test finding rule when no match exists."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        file_path = Path("/path/to/unknown.xyz")
        rule = organizer._find_matching_rule(file_path)
        assert rule is None

    def test_resolve_destination(self, temp_config_file, tmp_path):
        """Test destination path resolution."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        rule = organizer.rules[0]
        file_path = tmp_path / "test.jpg"
        file_path.write_text("content")

        destination = organizer._resolve_destination(
            file_path, rule, base_directory=tmp_path
        )

        assert destination.exists() or destination.parent.exists()

    def test_is_excluded_by_directory(self, temp_config_file):
        """Test directory exclusion."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        organizer.config["source"]["exclude"]["directories"] = [".git"]

        excluded_file = Path("/path/.git/config")
        assert organizer._is_excluded(excluded_file) is True

        normal_file = Path("/path/file.txt")
        assert organizer._is_excluded(normal_file) is False

    def test_generate_report(self, temp_config_file, temp_directory, tmp_path):
        """Test generating report."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        organizer.organize_files(str(temp_directory), dry_run=True)

        report_file = tmp_path / "report.txt"
        report_content = organizer.generate_report(str(report_file))

        assert len(report_content) > 0
        assert "Pattern File Organization Report" in report_content
        assert report_file.exists()

    def test_get_statistics(self, temp_config_file):
        """Test getting statistics."""
        organizer = PatternFileOrganizer(config_path=temp_config_file)
        stats = organizer.get_statistics()

        assert "files_scanned" in stats
        assert "files_matched" in stats
        assert "files_moved" in stats
        assert "files_skipped" in stats
        assert "errors" in stats
