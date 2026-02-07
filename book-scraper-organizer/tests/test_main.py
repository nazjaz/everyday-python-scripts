"""Unit tests for book scraper and organizer."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    BookDatabase,
    BookScraper,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "database": "./books.db",
                "output_directory": "./books",
                "organize_by": "author",
                "rate_limit": 2.0,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["database"] == "./books.db"
            assert result["output_directory"] == "./books"
            assert result["organize_by"] == "author"
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


class TestBookDatabase:
    """Test BookDatabase class."""

    def test_init_database(self):
        """Test database initialization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            database = BookDatabase(db_path)
            assert db_path.exists()

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='books'"
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_add_book(self):
        """Test adding a book to database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            database = BookDatabase(db_path)

            book_data = {
                "title": "Test Book",
                "author": "Test Author",
                "genre": "Fiction",
                "publication_date": "2024",
            }

            book_id = database.add_book(book_data)
            assert book_id is not None
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_book_exists(self):
        """Test checking if book exists."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            database = BookDatabase(db_path)

            book_data = {
                "title": "Test Book",
                "author": "Test Author",
            }

            database.add_book(book_data)

            assert database.book_exists("Test Book", "Test Author") is True
            assert database.book_exists("Nonexistent Book") is False
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_get_books(self):
        """Test querying books from database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            database = BookDatabase(db_path)

            book_data = {
                "title": "Test Book",
                "author": "Test Author",
                "genre": "Fiction",
                "publication_date": "2024",
            }

            database.add_book(book_data)

            books = database.get_books(author="Test Author")
            assert len(books) == 1
            assert books[0]["title"] == "Test Book"
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_get_books_by_genre(self):
        """Test querying books by genre."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            database = BookDatabase(db_path)

            book_data = {
                "title": "Test Book",
                "author": "Test Author",
                "genre": "Fiction",
            }

            database.add_book(book_data)

            books = database.get_books(genre="Fiction")
            assert len(books) == 1
        finally:
            if db_path.exists():
                db_path.unlink()


class TestBookScraper:
    """Test BookScraper class."""

    @pytest.mark.skipif(
        not pytest.importorskip("requests", reason="requests not available"),
        reason="requests not available",
    )
    def test_init(self):
        """Test initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "books.db"
            output_dir = Path(tmpdir) / "books"

            database = BookDatabase(db_path)

            scraper = BookScraper(
                database=database,
                output_directory=output_dir,
            )

            assert scraper.database == database
            assert scraper.output_directory == output_dir.resolve()

    def test_get_organized_path_author(self):
        """Test organized path generation by author."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "books.db"
            output_dir = Path(tmpdir) / "books"

            database = BookDatabase(db_path)

            scraper = BookScraper(
                database=database,
                output_directory=output_dir,
            )

            book_data = {
                "title": "Test Book",
                "author": "Test Author",
            }

            path = scraper._get_organized_path(book_data, "author")
            assert "Test Author" in str(path)
            assert "Test Book" in str(path)

    def test_get_organized_path_genre(self):
        """Test organized path generation by genre."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "books.db"
            output_dir = Path(tmpdir) / "books"

            database = BookDatabase(db_path)

            scraper = BookScraper(
                database=database,
                output_directory=output_dir,
            )

            book_data = {
                "title": "Test Book",
                "genre": "Fiction",
            }

            path = scraper._get_organized_path(book_data, "genre")
            assert "Fiction" in str(path)

    def test_get_organized_path_date(self):
        """Test organized path generation by date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "books.db"
            output_dir = Path(tmpdir) / "books"

            database = BookDatabase(db_path)

            scraper = BookScraper(
                database=database,
                output_directory=output_dir,
            )

            book_data = {
                "title": "Test Book",
                "publication_date": "2024",
            }

            path = scraper._get_organized_path(book_data, "date")
            assert "2024" in str(path)
