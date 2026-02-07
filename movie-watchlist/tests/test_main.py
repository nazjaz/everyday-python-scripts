"""Unit tests for Movie Watchlist."""

import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import MovieScraper, MovieWatchlist


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_movie_data():
    """Create sample movie data."""
    return {
        "imdbID": "tt0111161",
        "Title": "The Shawshank Redemption",
        "Year": "1994",
        "Rated": "R",
        "Released": "14 Oct 1994",
        "Runtime": "142 min",
        "Genre": "Drama",
        "Director": "Frank Darabont",
        "Writer": "Stephen King, Frank Darabont",
        "Actors": "Tim Robbins, Morgan Freeman, Bob Gunton",
        "Plot": "Two imprisoned men bond over a number of years...",
        "Language": "English",
        "Country": "USA",
        "Poster": "https://example.com/poster.jpg",
        "Ratings": [
            {"Source": "Internet Movie Database", "Value": "9.3/10"},
            {"Source": "Metacritic", "Value": "80/100"},
            {"Source": "Rotten Tomatoes", "Value": "91%"},
        ],
        "BoxOffice": "$28,341,469",
    }


def test_movie_scraper_initialization():
    """Test MovieScraper initialization."""
    scraper = MovieScraper(api_key="test_key")

    assert scraper.api_key == "test_key"
    assert scraper.base_url == "http://www.omdbapi.com"
    assert scraper.timeout == 10


def test_movie_scraper_no_api_key():
    """Test MovieScraper without API key."""
    scraper = MovieScraper()

    assert scraper.api_key is None


@patch("src.main.requests.get")
def test_search_movie_success(mock_get):
    """Test successful movie search."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "Response": "True",
        "Search": [
            {"Title": "Test Movie", "Year": "2020", "imdbID": "tt1234567"}
        ],
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    scraper = MovieScraper(api_key="test_key")
    results = scraper.search_movie("Test Movie")

    assert len(results) == 1
    assert results[0]["Title"] == "Test Movie"


@patch("src.main.requests.get")
def test_search_movie_not_found(mock_get):
    """Test movie search with no results."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "Response": "False",
        "Error": "Movie not found!",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    scraper = MovieScraper(api_key="test_key")
    results = scraper.search_movie("Nonexistent Movie")

    assert len(results) == 0


@patch("src.main.requests.get")
def test_get_movie_details_success(mock_get, sample_movie_data):
    """Test getting movie details successfully."""
    mock_response = Mock()
    mock_response.json.return_value = sample_movie_data
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    scraper = MovieScraper(api_key="test_key")
    movie = scraper.get_movie_details(imdb_id="tt0111161")

    assert movie is not None
    assert movie["Title"] == "The Shawshank Redemption"
    assert movie["Year"] == "1994"


def test_movie_watchlist_initialization(temp_dir):
    """Test MovieWatchlist initialization."""
    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)

    assert db_file.exists()


def test_add_movie(temp_dir, sample_movie_data):
    """Test adding movie to watchlist."""
    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)

    success = watchlist.add_movie(sample_movie_data, "to_watch")

    assert success is True

    # Verify movie was added
    movies = watchlist.get_movies()
    assert len(movies) == 1
    assert movies[0]["title"] == "The Shawshank Redemption"
    assert movies[0]["imdb_rating"] == 9.3
    assert movies[0]["metascore"] == 80


def test_add_duplicate_movie(temp_dir, sample_movie_data):
    """Test adding duplicate movie."""
    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)

    watchlist.add_movie(sample_movie_data, "to_watch")
    success = watchlist.add_movie(sample_movie_data, "to_watch")

    assert success is False  # Already exists


def test_get_movies(temp_dir, sample_movie_data):
    """Test getting movies from watchlist."""
    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)

    watchlist.add_movie(sample_movie_data, "to_watch")

    movies = watchlist.get_movies()

    assert len(movies) == 1
    assert movies[0]["title"] == "The Shawshank Redemption"


def test_get_movies_by_status(temp_dir, sample_movie_data):
    """Test getting movies filtered by status."""
    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)

    watchlist.add_movie(sample_movie_data, "watched")

    movies = watchlist.get_movies(status="watched")
    assert len(movies) == 1

    movies = watchlist.get_movies(status="to_watch")
    assert len(movies) == 0


def test_update_movie_status(temp_dir, sample_movie_data):
    """Test updating movie status."""
    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)

    watchlist.add_movie(sample_movie_data, "to_watch")

    success = watchlist.update_movie_status(
        sample_movie_data["imdbID"], "watched", user_rating=9
    )

    assert success is True

    movies = watchlist.get_movies()
    assert movies[0]["status"] == "watched"
    assert movies[0]["user_rating"] == 9
    assert movies[0]["watched_date"] is not None


def test_remove_movie(temp_dir, sample_movie_data):
    """Test removing movie from watchlist."""
    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)

    watchlist.add_movie(sample_movie_data, "to_watch")

    success = watchlist.remove_movie(sample_movie_data["imdbID"])

    assert success is True

    movies = watchlist.get_movies()
    assert len(movies) == 0


def test_remove_nonexistent_movie(temp_dir):
    """Test removing non-existent movie."""
    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)

    success = watchlist.remove_movie("tt9999999")

    assert success is False


def test_movie_ratings_extraction(temp_dir):
    """Test extraction of ratings from movie data."""
    movie_data = {
        "imdbID": "tt123",
        "Title": "Test Movie",
        "Year": "2020",
        "Ratings": [
            {"Source": "Internet Movie Database", "Value": "8.5/10"},
            {"Source": "Metacritic", "Value": "75/100"},
            {"Source": "Rotten Tomatoes", "Value": "85%"},
        ],
    }

    db_file = temp_dir / "test.db"
    watchlist = MovieWatchlist(db_file)
    watchlist.add_movie(movie_data)

    movies = watchlist.get_movies()
    assert movies[0]["imdb_rating"] == 8.5
    assert movies[0]["metascore"] == 75
    assert movies[0]["rotten_tomatoes"] == "85%"
