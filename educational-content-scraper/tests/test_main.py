"""Unit tests for Educational Content Scraper application."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import ContentScraper, load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestContentScraper:
    """Test cases for ContentScraper class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        library_dir = temp_dir / "library"
        library_dir.mkdir()

        return {
            "sources": {
                "project_gutenberg": {"enabled": False, "limit": 5},
                "openstax": {"enabled": False, "limit": 5},
                "custom_sources": [],
            },
            "organization": {
                "library_directory": str(library_dir),
                "subject_keywords": {
                    "mathematics": ["math", "algebra"],
                    "science": ["science", "physics"],
                },
            },
            "scraping": {
                "request_delay_seconds": 0.1,
                "max_content_size": 10000,
            },
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def scraper(self, config):
        """Create a ContentScraper instance."""
        return ContentScraper(config)

    def test_init(self, config):
        """Test ContentScraper initialization."""
        scraper = ContentScraper(config)
        assert scraper.config == config
        assert scraper.library_dir == Path(config["organization"]["library_directory"])

    def test_sanitize_filename(self, scraper):
        """Test filename sanitization."""
        assert scraper._sanitize_filename("test.txt") == "test.txt"
        assert scraper._sanitize_filename("test<>file.txt") == "test__file.txt"
        assert scraper._sanitize_filename("test/file.txt") == "test_file.txt"
        assert scraper._sanitize_filename(".") == ""
        long_name = "a" * 300
        assert len(scraper._sanitize_filename(long_name)) <= 200

    def test_categorize_subject(self, scraper):
        """Test subject categorization."""
        assert (
            scraper._categorize_subject("Introduction to Algebra", "")
            == "mathematics"
        )
        assert (
            scraper._categorize_subject("Physics for Beginners", "")
            == "science"
        )
        assert scraper._categorize_subject("Random Title", "") == "general"

    def test_determine_difficulty(self, scraper):
        """Test difficulty determination."""
        assert (
            scraper._determine_difficulty("Introduction to Math", "")
            == "beginner"
        )
        assert (
            scraper._determine_difficulty("Advanced Calculus", "")
            == "advanced"
        )
        assert (
            scraper._determine_difficulty("Regular Topic", "")
            == "intermediate"
        )

    def test_calculate_content_hash(self, scraper):
        """Test content hash calculation."""
        content = "test content"
        hash1 = scraper._calculate_content_hash(content)
        hash2 = scraper._calculate_content_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

        different_content = "different content"
        hash3 = scraper._calculate_content_hash(different_content)
        assert hash1 != hash3

    def test_save_content(self, scraper, temp_dir):
        """Test saving content."""
        content = {
            "title": "Test Content",
            "content": "This is test content.",
            "subject": "mathematics",
            "difficulty": "beginner",
            "source": "test",
            "url": "https://example.com",
        }

        result = scraper.save_content(content)
        assert result is True

        # Check file was created
        file_path = (
            scraper.library_dir
            / content["subject"]
            / content["difficulty"]
            / "Test_Content.txt"
        )
        assert file_path.exists()

        # Check content
        with open(file_path, "r", encoding="utf-8") as f:
            saved_content = f.read()
            assert "Test Content" in saved_content
            assert "This is test content." in saved_content

    def test_save_content_duplicate(self, scraper, temp_dir):
        """Test duplicate detection."""
        content = {
            "title": "Test Content",
            "content": "This is test content.",
            "subject": "mathematics",
            "difficulty": "beginner",
            "source": "test",
            "url": "https://example.com",
        }

        # Save first time
        result1 = scraper.save_content(content)
        assert result1 is True

        # Try to save duplicate
        result2 = scraper.save_content(content)
        assert result2 is False  # Should be skipped as duplicate

    @patch("src.main.ContentScraper._make_request")
    def test_scrape_project_gutenberg(self, mock_request, scraper):
        """Test Project Gutenberg scraping."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b'<html><body><a href="/ebooks/123">Book</a></body></html>'
        mock_response.text = "Book content here"
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        contents = scraper.scrape_project_gutenberg(limit=1)
        assert isinstance(contents, list)

    @patch("src.main.ContentScraper._make_request")
    def test_scrape_openstax(self, mock_request, scraper):
        """Test OpenStax scraping."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b'<html><body><main><h1>Book Title</h1><p>Content</p></main></body></html>'
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        contents = scraper.scrape_openstax(limit=1)
        assert isinstance(contents, list)

    def test_scrape_all_sources_dry_run(self, scraper):
        """Test scraping all sources in dry-run mode."""
        results = scraper.scrape_all_sources(dry_run=True)
        assert "scraped" in results
        assert "saved" in results
        assert "duplicates" in results
        assert "failed" in results


class TestLoadConfig:
    """Test cases for load_config function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_load_config_valid(self, temp_dir):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            "sources:\n  project_gutenberg:\n    enabled: true\n"
        )

        config = load_config(config_file)
        assert config["sources"]["project_gutenberg"]["enabled"] is True

    def test_load_config_nonexistent(self):
        """Test loading a nonexistent configuration file."""
        nonexistent = Path("/nonexistent/config.yaml")
        with pytest.raises(FileNotFoundError):
            load_config(nonexistent)

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading an invalid YAML file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(Exception):  # yaml.YAMLError
            load_config(config_file)
