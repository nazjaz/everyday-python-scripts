"""Unit tests for Job Scraper."""

import csv
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import JobScraper


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file."""
    config = {
        "output_file": str(temp_dir / "jobs.csv"),
        "user_agent": "Test Agent",
        "request_timeout": 30,
        "rate_limiting": {"delay_seconds": 0.1},
        "filters": {
            "keywords": ["python"],
            "exclude_keywords": [],
            "match_any": True,
        },
        "job_boards": [
            {
                "name": "Test Board",
                "base_url": "https://test-jobs.com",
                "search_url": "https://test-jobs.com/search",
                "max_pages": 1,
                "selectors": {
                    "job_item": ".job",
                    "title": ".title",
                    "company": ".company",
                    "location": ".location",
                    "description": ".description",
                    "url": ".title a",
                },
            }
        ],
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


@pytest.fixture
def mock_html():
    """Create mock HTML content."""
    return """
    <html>
        <body>
            <div class="job">
                <h2 class="title"><a href="/job/1">Python Developer</a></h2>
                <div class="company">Tech Corp</div>
                <div class="location">San Francisco, CA</div>
                <div class="description">We are looking for a Python developer</div>
            </div>
            <div class="job">
                <h2 class="title"><a href="/job/2">Java Developer</a></h2>
                <div class="company">Other Corp</div>
                <div class="location">New York, NY</div>
                <div class="description">We are looking for a Java developer</div>
            </div>
        </body>
    </html>
    """


def test_job_scraper_initialization(config_file):
    """Test JobScraper initialization."""
    scraper = JobScraper(config_path=config_file)
    assert scraper.config is not None
    assert scraper.output_path.exists() or scraper.output_path.parent.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        JobScraper(config_path="nonexistent.yaml")


def test_matches_keywords_include(config_file):
    """Test keyword matching with include keywords."""
    scraper = JobScraper(config_path=config_file)
    scraper.config["filters"]["keywords"] = ["python"]
    scraper.config["filters"]["match_any"] = True

    job = {
        "title": "Python Developer",
        "description": "Looking for Python developer",
        "company": "Tech Corp",
        "location": "SF",
    }

    assert scraper._matches_keywords(job) is True

    job_no_match = {
        "title": "Java Developer",
        "description": "Looking for Java developer",
        "company": "Tech Corp",
        "location": "SF",
    }

    assert scraper._matches_keywords(job_no_match) is False


def test_matches_keywords_exclude(config_file):
    """Test keyword matching with exclude keywords."""
    scraper = JobScraper(config_path=config_file)
    scraper.config["filters"]["keywords"] = []
    scraper.config["filters"]["exclude_keywords"] = ["intern"]

    job = {
        "title": "Python Developer Intern",
        "description": "Internship position",
        "company": "Tech Corp",
        "location": "SF",
    }

    assert scraper._matches_keywords(job) is False

    job_no_exclude = {
        "title": "Python Developer",
        "description": "Full-time position",
        "company": "Tech Corp",
        "location": "SF",
    }

    assert scraper._matches_keywords(job_no_exclude) is True


def test_matches_keywords_match_all(config_file):
    """Test keyword matching with match_all option."""
    scraper = JobScraper(config_path=config_file)
    scraper.config["filters"]["keywords"] = ["python", "developer"]
    scraper.config["filters"]["match_any"] = False

    job_both = {
        "title": "Python Developer",
        "description": "Looking for Python developer",
        "company": "Tech Corp",
        "location": "SF",
    }

    assert scraper._matches_keywords(job_both) is True

    job_one = {
        "title": "Python Engineer",
        "description": "Looking for Python engineer",
        "company": "Tech Corp",
        "location": "SF",
    }

    assert scraper._matches_keywords(job_one) is False


def test_parse_job_element(config_file, mock_html):
    """Test parsing job element from HTML."""
    from bs4 import BeautifulSoup

    scraper = JobScraper(config_path=config_file)
    soup = BeautifulSoup(mock_html, "html.parser")
    job_elem = soup.select_one(".job")

    job_data = scraper._parse_job_element(
        job_elem, scraper.config["job_boards"][0]
    )

    assert job_data is not None
    assert "Python Developer" in job_data["title"]
    assert "Tech Corp" in job_data["company"]
    assert "San Francisco" in job_data["location"]


def test_extract_job_data(config_file, mock_html):
    """Test extracting job data from HTML."""
    from bs4 import BeautifulSoup

    scraper = JobScraper(config_path=config_file)
    soup = BeautifulSoup(mock_html, "html.parser")

    jobs = scraper._extract_job_data(soup, scraper.config["job_boards"][0])

    assert len(jobs) == 2
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[1]["title"] == "Java Developer"


@patch("src.main.requests.Session")
def test_fetch_page_success(mock_session, config_file):
    """Test successful page fetch."""
    mock_response = Mock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.raise_for_status = Mock()
    mock_session.return_value.get.return_value = mock_response

    scraper = JobScraper(config_path=config_file)
    scraper.session = mock_session.return_value

    soup = scraper._fetch_page("https://example.com")

    assert soup is not None
    assert scraper.stats["pages_scraped"] == 1


@patch("src.main.requests.Session")
def test_fetch_page_failure(mock_session, config_file):
    """Test page fetch failure handling."""
    import requests

    mock_session.return_value.get.side_effect = requests.RequestException("Error")

    scraper = JobScraper(config_path=config_file)
    scraper.session = mock_session.return_value

    soup = scraper._fetch_page("https://example.com")

    assert soup is None
    assert scraper.stats["errors"] > 0


def test_filter_jobs(config_file):
    """Test filtering jobs by keywords."""
    scraper = JobScraper(config_path=config_file)
    scraper.config["filters"]["keywords"] = ["python"]

    jobs = [
        {
            "title": "Python Developer",
            "description": "Python job",
            "company": "Tech",
            "location": "SF",
        },
        {
            "title": "Java Developer",
            "description": "Java job",
            "company": "Tech",
            "location": "NY",
        },
    ]

    filtered = scraper.filter_jobs(jobs)

    assert len(filtered) == 1
    assert filtered[0]["title"] == "Python Developer"


def test_save_to_csv(config_file, temp_dir):
    """Test saving jobs to CSV file."""
    scraper = JobScraper(config_path=config_file)
    scraper.output_path = temp_dir / "test_jobs.csv"

    jobs = [
        {
            "title": "Python Developer",
            "company": "Tech Corp",
            "location": "SF",
            "description": "Python job",
            "url": "https://example.com/job/1",
            "source": "Test Board",
        }
    ]

    output_path = scraper.save_to_csv(jobs)

    assert output_path.exists()
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["title"] == "Python Developer"


def test_save_to_csv_empty_list(config_file, temp_dir):
    """Test saving empty job list."""
    scraper = JobScraper(config_path=config_file)
    scraper.output_path = temp_dir / "empty_jobs.csv"

    output_path = scraper.save_to_csv([])

    assert output_path.exists()
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 0


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    config = {
        "output_file": str(temp_dir / "jobs.csv"),
        "filters": {"keywords": ["java"]},
        "job_boards": [],
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    with patch.dict(os.environ, {"KEYWORDS": "python,javascript"}):
        scraper = JobScraper(config_path=str(config_path))
        assert "python" in scraper.config["filters"]["keywords"]
        assert "javascript" in scraper.config["filters"]["keywords"]
