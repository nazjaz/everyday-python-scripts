"""Unit tests for art gallery database module."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import ArtGalleryDatabase


class TestArtGalleryDatabase:
    """Test cases for ArtGalleryDatabase class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "database": {"path": str(temp_dir / "test.db")},
            "images": {"directory": str(temp_dir / "images")},
            "scraping": {"sources": ["wikimedia"], "default_limit": 10},
            "logging": {"level": "INFO", "file": str(temp_dir / "app.log")},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def gallery(self, config_file):
        """Create ArtGalleryDatabase instance."""
        return ArtGalleryDatabase(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "database": {"path": "test.db"},
            "images": {"directory": "images"},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        gallery = ArtGalleryDatabase(config_path=str(config_path))
        assert gallery.config["database"]["path"] == "test.db"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            ArtGalleryDatabase(config_path="nonexistent.yaml")

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test YAMLError when config file is invalid."""
        config_path = temp_dir / "invalid.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        import yaml

        with pytest.raises(yaml.YAMLError):
            ArtGalleryDatabase(config_path=str(config_path))

    def test_init_database(self, gallery, temp_dir):
        """Test database initialization."""
        db_path = Path(gallery.db_path)
        assert db_path.exists()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='artworks'"
        )
        result = cursor.fetchone()
        assert result is not None

        cursor.execute("PRAGMA table_info(artworks)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "title" in columns
        assert "artist" in columns
        assert "image_path" in columns

        conn.close()

    def test_calculate_image_hash(self, gallery, temp_dir):
        """Test image hash calculation."""
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"test image content")

        hash1 = gallery._calculate_image_hash(test_file)
        hash2 = gallery._calculate_image_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 32

    @patch("src.main.requests.get")
    def test_download_image(self, mock_get, gallery, temp_dir):
        """Test image downloading."""
        mock_response = MagicMock()
        mock_response.content = b"fake image data"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        image_url = "https://example.com/image.jpg"
        artwork_id = "test123"
        image_path = gallery._download_image(image_url, artwork_id)

        assert image_path is not None
        assert image_path.exists()
        assert image_path.read_bytes() == b"fake image data"
        mock_get.assert_called_once()

    @patch("src.main.requests.get")
    def test_download_image_failure(self, mock_get, gallery):
        """Test image download failure handling."""
        mock_get.side_effect = Exception("Network error")

        image_url = "https://example.com/image.jpg"
        artwork_id = "test123"
        image_path = gallery._download_image(image_url, artwork_id)

        assert image_path is None

    def test_save_artwork(self, gallery, temp_dir):
        """Test saving artwork to database."""
        artwork = {
            "title": "Test Artwork",
            "artist": "Test Artist",
            "year": 2020,
            "medium": "Oil on canvas",
            "description": "A test artwork",
            "source_url": "https://example.com",
            "image_url": None,
            "category": "test",
            "tags": "test,artwork",
        }

        artwork_id = gallery._save_artwork(artwork)

        assert artwork_id is not None

        conn = sqlite3.connect(gallery.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "Test Artwork"
        conn.close()

    def test_search_artworks(self, gallery):
        """Test artwork search functionality."""
        artwork1 = {
            "title": "Sunset Landscape",
            "artist": "John Doe",
            "description": "Beautiful sunset",
            "source_url": "https://example.com/1",
            "image_url": None,
            "category": "landscape",
            "tags": "sunset,landscape",
        }
        artwork2 = {
            "title": "Portrait of Jane",
            "artist": "Jane Smith",
            "description": "Portrait painting",
            "source_url": "https://example.com/2",
            "image_url": None,
            "category": "portrait",
            "tags": "portrait,person",
        }

        gallery._save_artwork(artwork1)
        gallery._save_artwork(artwork2)

        results = gallery.search_artworks(query="sunset")
        assert len(results) >= 1
        assert any("Sunset" in r["title"] for r in results)

        results = gallery.search_artworks(artist="John Doe")
        assert len(results) >= 1
        assert any("John Doe" in r.get("artist", "") for r in results)

        results = gallery.search_artworks(category="portrait")
        assert len(results) >= 1
        assert any("portrait" in r.get("category", "").lower() for r in results)

    def test_get_artwork_by_id(self, gallery):
        """Test getting artwork by ID."""
        artwork = {
            "title": "Test Artwork",
            "artist": "Test Artist",
            "description": "Test description",
            "source_url": "https://example.com",
            "image_url": None,
            "category": "test",
            "tags": "test",
        }

        artwork_id = gallery._save_artwork(artwork)
        retrieved = gallery.get_artwork_by_id(artwork_id)

        assert retrieved is not None
        assert retrieved["title"] == "Test Artwork"
        assert retrieved["artist"] == "Test Artist"

    def test_get_statistics(self, gallery):
        """Test getting database statistics."""
        artwork1 = {
            "title": "Artwork 1",
            "artist": "Artist 1",
            "description": "Description 1",
            "source_url": "https://example.com/1",
            "image_url": None,
            "category": "category1",
            "tags": "tag1",
        }
        artwork2 = {
            "title": "Artwork 2",
            "artist": "Artist 2",
            "description": "Description 2",
            "source_url": "https://example.com/2",
            "image_url": None,
            "category": "category2",
            "tags": "tag2",
        }

        gallery._save_artwork(artwork1)
        gallery._save_artwork(artwork2)

        stats = gallery.get_statistics()

        assert stats["total_artworks"] >= 2
        assert stats["total_artists"] >= 2
        assert stats["total_categories"] >= 2
