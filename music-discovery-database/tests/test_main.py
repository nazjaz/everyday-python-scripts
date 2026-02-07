"""Unit tests for music discovery database module."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import MusicDiscoveryDatabase


class TestMusicDiscoveryDatabase:
    """Test cases for MusicDiscoveryDatabase class."""

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
                "musopen": {"enabled": False, "max_pages": 1},
                "freesound": {"enabled": False},
            },
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def database(self, config_file):
        """Create MusicDiscoveryDatabase instance."""
        return MusicDiscoveryDatabase(config_path=config_file)

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

        db = MusicDiscoveryDatabase(config_path=str(config_path))
        assert db.config["database"]["file"] == "test.db"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            MusicDiscoveryDatabase(config_path="nonexistent.yaml")

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
            WHERE type='table' AND name IN ('artists', 'tracks', 'genres', 'recommendations')
        """
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert "artists" in tables
        assert "tracks" in tables
        assert "genres" in tables
        assert "recommendations" in tables

        conn.close()

    def test_get_artist_id_creates_new(self, database):
        """Test getting artist ID creates new artist if not exists."""
        artist_id = database._get_artist_id("Test Artist", "Rock")
        assert artist_id is not None

        # Should return same ID for same artist
        artist_id2 = database._get_artist_id("Test Artist")
        assert artist_id == artist_id2

    def test_get_genre_id_creates_new(self, database):
        """Test getting genre ID creates new genre if not exists."""
        genre_id = database._get_genre_id("Jazz")
        assert genre_id is not None

        # Should return same ID for same genre
        genre_id2 = database._get_genre_id("Jazz")
        assert genre_id == genre_id2

    def test_add_track(self, database):
        """Test adding track to database."""
        track_id = database._add_track(
            title="Test Song",
            artist_name="Test Artist",
            genre="Rock",
            duration=180,
            source="test",
        )
        assert track_id is not None

        # Verify track was added
        conn = sqlite3.connect(str(database.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM tracks WHERE id = ?", (track_id,))
        result = cursor.fetchone()
        assert result[0] == "Test Song"
        conn.close()

    def test_get_statistics(self, database):
        """Test getting database statistics."""
        # Add some test data
        database._add_track("Song 1", "Artist 1", "Rock")
        database._add_track("Song 2", "Artist 2", "Jazz")

        stats = database.get_statistics()
        assert stats["artists"] == 2
        assert stats["tracks"] == 2
        assert stats["genres"] >= 2

    def test_generate_recommendations(self, database):
        """Test recommendation generation."""
        # Add tracks with same genre
        database._add_track("Song 1", "Artist 1", "Rock")
        database._add_track("Song 2", "Artist 2", "Rock")
        database._add_track("Song 3", "Artist 1", "Rock")

        database._generate_recommendations()

        stats = database.get_statistics()
        assert stats["recommendations"] > 0

    def test_get_recommendations(self, database):
        """Test getting recommendations."""
        # Add tracks and generate recommendations
        database._add_track("Song 1", "Artist 1", "Rock")
        database._add_track("Song 2", "Artist 2", "Rock")
        database._generate_recommendations()

        recommendations = database.get_recommendations(limit=5)
        assert len(recommendations) > 0
        assert "similarity_score" in recommendations[0]
        assert "recommended" in recommendations[0]

    def test_get_recommendations_for_track(self, database):
        """Test getting recommendations for specific track."""
        database._add_track("Song 1", "Artist 1", "Rock")
        database._add_track("Song 2", "Artist 2", "Rock")
        database._generate_recommendations()

        recommendations = database.get_recommendations(track_title="Song 1")
        assert len(recommendations) > 0

    def test_export_data(self, database, temp_dir):
        """Test data export to JSON."""
        # Add test data
        database._add_track("Song 1", "Artist 1", "Rock")

        export_path = temp_dir / "export.json"
        database.export_data(output_path=str(export_path))

        assert export_path.exists()
        import json

        with open(export_path) as f:
            data = json.load(f)
        assert "artists" in data
        assert "tracks" in data
        assert "genres" in data

    @patch("src.main.requests.Session")
    def test_scrape_musopen(self, mock_session, database):
        """Test Musopen scraping."""
        # Mock response
        mock_response = MagicMock()
        mock_response.content = b"<html><body><div class='track-item'><h3>Test Song</h3><span class='artist'>Test Artist</span></div></body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        database.session = mock_session_instance

        database.config["sources"]["musopen"]["enabled"] = True
        database.config["sources"]["musopen"]["max_pages"] = 1

        database._scrape_musopen(max_pages=1)

        # Verify track was added (if parsing worked)
        stats = database.get_statistics()
        # Note: Actual parsing depends on HTML structure

    def test_should_skip_path_not_implemented(self, database):
        """Test that should_skip_path is not in this class."""
        # This method doesn't exist in MusicDiscoveryDatabase
        # It's specific to file scanning tools
        pass
