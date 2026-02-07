"""Unit tests for scientific paper database module."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import ScientificPaperDatabase


class TestScientificPaperDatabase:
    """Test cases for ScientificPaperDatabase class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "database": {"file": str(temp_dir / "test.db")},
            "scraper": {"user_agent": "TestBot", "delay": 1, "timeout": 5},
            "sources": {
                "arxiv": {"enabled": False, "query": "test", "max_results": 10}
            },
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def database(self, config_file):
        """Create ScientificPaperDatabase instance."""
        return ScientificPaperDatabase(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "database": {"file": "test.db"},
            "scraper": {"delay": 2},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        db = ScientificPaperDatabase(config_path=str(config_path))
        assert db.config["database"]["file"] == "test.db"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            ScientificPaperDatabase(config_path="nonexistent.yaml")

    def test_init_database_creates_tables(self, database, temp_dir):
        """Test that database initialization creates tables."""
        db_file = temp_dir / "test.db"
        assert db_file.exists()

        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # Check that tables exist
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('papers', 'authors', 'subjects', 'paper_authors')
        """
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert "papers" in tables
        assert "authors" in tables
        assert "subjects" in tables
        assert "paper_authors" in tables

        conn.close()

    def test_add_paper(self, database):
        """Test adding paper to database."""
        paper_id = database._add_paper(
            title="Test Paper",
            authors=["Author One", "Author Two"],
            subject="cs.AI",
            publication_date="2024-01-01",
            abstract="Test abstract",
            url="http://example.com",
            source="test",
        )
        assert paper_id is not None

        # Verify paper was added
        conn = sqlite3.connect(str(database.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM papers WHERE id = ?", (paper_id,))
        result = cursor.fetchone()
        assert result[0] == "Test Paper"
        conn.close()

    def test_add_paper_duplicate(self, database):
        """Test that duplicate papers are not added."""
        paper_id1 = database._add_paper(
            title="Test Paper",
            authors=["Author One"],
            publication_date="2024-01-01",
        )
        assert paper_id1 is not None

        paper_id2 = database._add_paper(
            title="Test Paper",
            authors=["Author One"],
            publication_date="2024-01-01",
        )
        assert paper_id2 is None  # Duplicate

    def test_get_or_create_author(self, database):
        """Test getting or creating author."""
        author_id = database._get_or_create_author("Test Author")
        assert author_id is not None

        # Should return same ID for same author
        author_id2 = database._get_or_create_author("Test Author")
        assert author_id == author_id2

    def test_get_or_create_subject(self, database):
        """Test getting or creating subject."""
        subject_id = database._get_or_create_subject("cs.AI")
        assert subject_id is not None

        # Should return same ID for same subject
        subject_id2 = database._get_or_create_subject("cs.AI")
        assert subject_id == subject_id2

    def test_get_statistics(self, database):
        """Test getting database statistics."""
        # Add some test data
        database._add_paper("Paper 1", ["Author 1"], "cs.AI")
        database._add_paper("Paper 2", ["Author 2"], "cs.LG")

        stats = database.get_statistics()
        assert stats["papers"] == 2
        assert stats["authors"] == 2
        assert stats["subjects"] >= 2

    def test_search_papers_by_title(self, database):
        """Test searching papers by title."""
        database._add_paper("Machine Learning Paper", ["Author 1"])
        database._add_paper("Deep Learning Paper", ["Author 2"])

        results = database.search_papers(title="Machine")
        assert len(results) == 1
        assert "Machine Learning" in results[0]["title"]

    def test_search_papers_by_author(self, database):
        """Test searching papers by author."""
        database._add_paper("Paper 1", ["John Smith"])
        database._add_paper("Paper 2", ["Jane Doe"])

        results = database.search_papers(author="Smith")
        assert len(results) == 1
        assert "John Smith" in results[0]["authors"]

    def test_search_papers_by_subject(self, database):
        """Test searching papers by subject."""
        database._add_paper("Paper 1", ["Author 1"], subject="cs.AI")
        database._add_paper("Paper 2", ["Author 2"], subject="cs.LG")

        results = database.search_papers(subject="cs.AI")
        assert len(results) == 1
        assert results[0]["subject"] == "cs.AI"

    def test_organize_by_subject(self, database):
        """Test organizing papers by subject."""
        database._add_paper("Paper 1", ["Author 1"], subject="cs.AI")
        database._add_paper("Paper 2", ["Author 2"], subject="cs.AI")
        database._add_paper("Paper 3", ["Author 3"], subject="cs.LG")

        org = database.organize_by_subject()
        assert org["cs.AI"] == 2
        assert org["cs.LG"] == 1

    def test_organize_by_author(self, database):
        """Test organizing papers by author."""
        database._add_paper("Paper 1", ["Author One"])
        database._add_paper("Paper 2", ["Author One"])
        database._add_paper("Paper 3", ["Author Two"])

        org = database.organize_by_author()
        assert org["Author One"] == 2
        assert org["Author Two"] == 1

    def test_organize_by_date(self, database):
        """Test organizing papers by date."""
        database._add_paper("Paper 1", ["Author 1"], publication_date="2024-01-01")
        database._add_paper("Paper 2", ["Author 2"], publication_date="2024-01-01")
        database._add_paper("Paper 3", ["Author 3"], publication_date="2024-02-01")

        org = database.organize_by_date()
        assert org["2024-01-01"] == 2
        assert org["2024-02-01"] == 1

    @patch("src.main.requests.Session")
    def test_scrape_arxiv(self, mock_session, database):
        """Test arXiv scraping."""
        # Mock XML response
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Paper Title</title>
                <author><name>Test Author</name></author>
                <published>2024-01-01T00:00:00Z</published>
                <category term="cs.AI" />
                <summary>Test abstract</summary>
                <id>http://arxiv.org/abs/1234.5678</id>
            </entry>
        </feed>"""

        mock_response = MagicMock()
        mock_response.content = xml_content.encode()
        mock_response.raise_for_status = MagicMock()

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        database.session = mock_session_instance
        database.config["sources"]["arxiv"]["enabled"] = True

        database._scrape_arxiv(query="test", max_results=10)

        # Verify paper was added
        stats = database.get_statistics()
        assert stats["papers"] > 0
