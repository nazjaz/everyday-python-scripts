"""Unit tests for RSS news scraper module."""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import RSSNewsScraper


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    db_file = Path(temp_dir) / "test.db"
    config = {
        "rss_feeds": [
            {
                "name": "Test Feed",
                "url": "https://example.com/feed.xml",
                "category": "general",
            }
        ],
        "database": {
            "file": str(db_file),
            "create_tables": True,
        },
        "categorization": {
            "enabled": True,
            "method": "keyword",
            "categories": {
                "technology": {
                    "keywords": ["tech", "software", "ai"],
                },
                "science": {
                    "keywords": ["science", "research"],
                },
            },
            "default_category": "general",
        },
        "daily_summary": {
            "enabled": True,
            "include_categories": True,
            "include_top_headlines": True,
            "top_headlines_count": 5,
        },
        "scraping": {
            "interval": 3600,
            "max_items_per_feed": 50,
            "timeout": 30,
        },
        "retention": {
            "days_to_keep": 30,
            "auto_cleanup": True,
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_rss_scraper_initialization(config_file):
    """Test RSSNewsScraper initializes correctly."""
    scraper = RSSNewsScraper(config_path=str(config_file))
    assert scraper.db_path.exists()
    assert scraper.stats["feeds_processed"] == 0


def test_rss_scraper_missing_config():
    """Test RSSNewsScraper raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        RSSNewsScraper(config_path="nonexistent.yaml")


def test_categorize_headline(config_file):
    """Test headline categorization."""
    scraper = RSSNewsScraper(config_path=str(config_file))

    # Technology category
    category = scraper._categorize_headline("New AI software released", "")
    assert category == "technology"

    # Science category
    category = scraper._categorize_headline("New research study published", "")
    assert category == "science"

    # Default category
    category = scraper._categorize_headline("Random news headline", "")
    assert category == "general"


def test_parse_published_date(config_file):
    """Test published date parsing."""
    scraper = RSSNewsScraper(config_path=str(config_file))

    # Mock feed item with published_parsed
    mock_item = MagicMock()
    mock_item.published_parsed = (2024, 2, 7, 14, 30, 45, 0, 0, 0)

    date = scraper._parse_published_date(mock_item)
    assert date is not None
    assert "2024-02-07" in date


def test_save_headline(config_file):
    """Test saving headline to database."""
    scraper = RSSNewsScraper(config_path=str(config_file))

    headline = {
        "title": "Test Headline",
        "link": "https://example.com/article1",
        "description": "Test description",
        "published_date": "2024-02-07T14:30:00",
        "feed_name": "Test Feed",
        "feed_url": "https://example.com/feed.xml",
        "category": "technology",
    }

    result = scraper._save_headline(headline)
    assert result is True

    # Verify headline was saved
    conn = sqlite3.connect(scraper.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM headlines WHERE link = ?", (headline["link"],))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1


def test_save_duplicate_headline(config_file):
    """Test that duplicate headlines are not saved."""
    scraper = RSSNewsScraper(config_path=str(config_file))

    headline = {
        "title": "Test Headline",
        "link": "https://example.com/article1",
        "description": "Test description",
        "published_date": "2024-02-07T14:30:00",
        "feed_name": "Test Feed",
        "feed_url": "https://example.com/feed.xml",
        "category": "technology",
    }

    # Save first time
    result1 = scraper._save_headline(headline)
    assert result1 is True

    # Try to save duplicate
    result2 = scraper._save_headline(headline)
    assert result2 is False

    # Verify only one entry exists
    conn = sqlite3.connect(scraper.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM headlines WHERE link = ?", (headline["link"],))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1


@patch("src.main.feedparser.parse")
def test_parse_feed(mock_parse, config_file):
    """Test RSS feed parsing."""
    # Mock feedparser response
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_entry = MagicMock()
    mock_entry.title = "Test Headline"
    mock_entry.link = "https://example.com/article"
    mock_entry.description = "Test description"
    mock_entry.published_parsed = (2024, 2, 7, 14, 30, 45, 0, 0, 0)
    mock_feed.entries = [mock_entry]
    mock_parse.return_value = mock_feed

    scraper = RSSNewsScraper(config_path=str(config_file))
    headlines = scraper._parse_feed("https://example.com/feed.xml", "Test Feed")

    assert len(headlines) == 1
    assert headlines[0]["title"] == "Test Headline"
    assert headlines[0]["link"] == "https://example.com/article"


def test_generate_daily_summary(config_file):
    """Test daily summary generation."""
    scraper = RSSNewsScraper(config_path=str(config_file))

    # Add test headlines to database
    test_headlines = [
        {
            "title": "Tech News 1",
            "link": "https://example.com/tech1",
            "description": "",
            "published_date": datetime.now().isoformat(),
            "feed_name": "Test Feed",
            "feed_url": "https://example.com/feed.xml",
            "category": "technology",
        },
        {
            "title": "Science News 1",
            "link": "https://example.com/science1",
            "description": "",
            "published_date": datetime.now().isoformat(),
            "feed_name": "Test Feed",
            "feed_url": "https://example.com/feed.xml",
            "category": "science",
        },
    ]

    for headline in test_headlines:
        scraper._save_headline(headline)

    summary = scraper.generate_daily_summary()

    assert "Daily News Summary" in summary
    assert "Category Breakdown" in summary or "technology" in summary.lower()


def test_cleanup_old_entries(config_file):
    """Test cleanup of old database entries."""
    scraper = RSSNewsScraper(config_path=str(config_file))

    # Add old headline (simulate by setting old scraped_at)
    conn = sqlite3.connect(scraper.db_path)
    cursor = conn.cursor()
    old_date = (datetime.now() - timedelta(days=35)).isoformat()
    cursor.execute("""
        INSERT INTO headlines 
        (title, link, description, published_date, feed_name, feed_url, category, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Old Headline",
        "https://example.com/old",
        "",
        old_date,
        "Test Feed",
        "https://example.com/feed.xml",
        "general",
        old_date,
    ))
    conn.commit()
    conn.close()

    # Run cleanup
    scraper._cleanup_old_entries()

    # Verify old entry was removed
    conn = sqlite3.connect(scraper.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM headlines WHERE link = ?", ("https://example.com/old",))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0
