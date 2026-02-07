"""Unit tests for intelligent file organizer module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import IntelligentFileOrganizer


class TestIntelligentFileOrganizer:
    """Test cases for IntelligentFileOrganizer class."""

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
            "analysis": {
                "use_filename": True,
                "use_directory": True,
                "use_content": True,
                "max_content_size": 10000,
                "text_extensions": [".txt", ".md"],
            },
            "categories": {
                "documents": {
                    "folder": "Documents",
                    "keywords": ["document", "doc", "report"],
                    "patterns": [".*\\.pdf$"],
                    "directory_keywords": ["documents"],
                    "content_keywords": ["report", "analysis"],
                },
                "images": {
                    "folder": "Images",
                    "keywords": ["image", "photo"],
                    "patterns": [".*\\.(jpg|png)$"],
                },
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
        """Create IntelligentFileOrganizer instance."""
        return IntelligentFileOrganizer(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "organization": {"base_folder": "test"},
            "categories": {
                "test": {"folder": "Test", "keywords": ["test"]}
            },
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        organizer = IntelligentFileOrganizer(config_path=str(config_path))
        assert organizer.config["organization"]["base_folder"] == "test"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            IntelligentFileOrganizer(config_path="nonexistent.yaml")

    def test_load_categories(self, organizer):
        """Test category loading."""
        assert "documents" in organizer.categories
        assert "images" in organizer.categories

    def test_extract_keywords_from_text(self, organizer):
        """Test keyword extraction from text."""
        text = "This is a test document about reports and analysis."
        keywords = organizer._extract_keywords_from_text(text, max_keywords=5)
        assert len(keywords) > 0
        assert "test" in keywords or "document" in keywords

    def test_extract_keywords_from_text_empty(self, organizer):
        """Test keyword extraction from empty text."""
        keywords = organizer._extract_keywords_from_text("")
        assert keywords == []

    def test_extract_tags_from_filename(self, organizer, temp_dir):
        """Test tag extraction from filename."""
        file_path = temp_dir / "document_report.txt"
        tags = organizer._extract_tags_from_filename(file_path)
        assert "documents" in tags

    def test_extract_tags_from_filename_no_match(self, organizer, temp_dir):
        """Test tag extraction from filename with no matches."""
        file_path = temp_dir / "random_file.txt"
        tags = organizer._extract_tags_from_filename(file_path)
        assert len(tags) == 0

    def test_extract_tags_from_directory(self, organizer, temp_dir):
        """Test tag extraction from directory context."""
        documents_dir = temp_dir / "documents"
        documents_dir.mkdir()
        file_path = documents_dir / "file.txt"
        file_path.write_text("content")

        tags = organizer._extract_tags_from_directory(file_path)
        assert "documents" in tags

    def test_extract_tags_from_content(self, organizer, temp_dir):
        """Test tag extraction from file content."""
        file_path = temp_dir / "report.txt"
        file_path.write_text("This is a report with analysis and summary.")

        tags = organizer._extract_tags_from_content(file_path)
        assert "documents" in tags

    def test_extract_tags_from_content_non_text(self, organizer, temp_dir):
        """Test tag extraction from non-text file."""
        file_path = temp_dir / "image.jpg"
        file_path.write_bytes(b"binary content")

        tags = organizer._extract_tags_from_content(file_path)
        assert len(tags) == 0

    def test_extract_all_tags(self, organizer, temp_dir):
        """Test extracting all tags from multiple sources."""
        documents_dir = temp_dir / "documents"
        documents_dir.mkdir()
        file_path = documents_dir / "document_report.txt"
        file_path.write_text("This is a report with analysis.")

        tags = organizer._extract_all_tags(file_path)
        assert len(tags) > 0
        assert "documents" in tags

    def test_determine_category(self, organizer):
        """Test category determination from tags."""
        tags = ["documents", "images"]
        category = organizer._determine_category(Path("dummy"), tags)
        assert category == "documents"

    def test_determine_category_no_tags(self, organizer):
        """Test category determination with no tags."""
        category = organizer._determine_category(Path("dummy"), [])
        assert category is None

    def test_should_skip_path(self, organizer):
        """Test path skipping logic."""
        path = Path("/some/path/.git/config")
        assert organizer._should_skip_path(path) is True

        path = Path("/some/path/normal_file.txt")
        assert organizer._should_skip_path(path) is False

    def test_scan_directory(self, organizer, temp_dir):
        """Test directory scanning."""
        # Create test files
        (temp_dir / "document1.txt").write_text("report content")
        (temp_dir / "image1.jpg").write_bytes(b"fake image")

        organizer.scan_directory(str(temp_dir))

        assert organizer.stats["files_scanned"] == 2
        assert len(organizer.file_tags) == 2

    def test_scan_directory_not_found(self, organizer):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            organizer.scan_directory("/nonexistent/path")

    def test_organize_files_dry_run(self, organizer, temp_dir):
        """Test file organization in dry-run mode."""
        # Create test files
        (temp_dir / "document.txt").write_text("report content")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=True)

        # Files should still be in original location
        assert (temp_dir / "document.txt").exists()

    def test_organize_files_actual(self, organizer, temp_dir):
        """Test file organization in actual mode."""
        # Create test files
        (temp_dir / "document.txt").write_text("report content")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=False)

        # Files should be moved to organized folder
        organized_base = temp_dir / "organized"
        assert (organized_base / "Documents" / "document.txt").exists()

    def test_generate_report(self, organizer, temp_dir):
        """Test report generation."""
        # Create test files and scan
        (temp_dir / "document.txt").write_text("report content")

        organizer.scan_directory(str(temp_dir))
        report_path = temp_dir / "test_report.txt"
        organizer.generate_report(output_path=str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "INTELLIGENT FILE ORGANIZATION REPORT" in content
        assert "SUMMARY" in content
