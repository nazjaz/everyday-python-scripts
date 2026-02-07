"""Unit tests for image scraper."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlparse

import pytest
import yaml

from src.main import (
    ImageScraper,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "output_directory": "./downloads",
                "organize_by": "category",
                "max_images": 100,
                "rate_limit": 2.0,
                "timeout": 15,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["output_directory"] == "./downloads"
            assert result["organize_by"] == "category"
            assert result["max_images"] == 100
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


class TestImageScraper:
    """Test ImageScraper class."""

    @pytest.mark.skipif(
        not pytest.importorskip("requests", reason="requests not available"),
        reason="requests not available",
    )
    def test_init(self):
        """Test initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="date",
            )

            assert scraper.output_directory == output_dir.resolve()
            assert scraper.organize_by == "date"
            assert scraper.rate_limit == 1.0

    def test_init_invalid_organize_by(self):
        """Test that invalid organize_by raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            with pytest.raises(ValueError, match="organize_by must be"):
                ImageScraper(
                    output_directory=output_dir,
                    organize_by="invalid",
                )

    def test_is_image_url(self):
        """Test image URL detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="date",
            )

            assert scraper._is_image_url("https://example.com/image.jpg") is True
            assert scraper._is_image_url("https://example.com/image.png") is True
            assert scraper._is_image_url("https://example.com/page.html") is False

    def test_get_safe_filename(self):
        """Test safe filename generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="date",
            )

            filename = scraper._get_safe_filename("https://example.com/image.jpg")
            assert filename.endswith(".jpg")
            assert "image" in filename.lower()

    def test_get_safe_filename_with_category(self):
        """Test safe filename generation with category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="category",
            )

            filename = scraper._get_safe_filename(
                "https://example.com/image.jpg", category="nature"
            )
            assert "nature" in filename

    def test_get_image_category(self):
        """Test image category detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="category",
            )

            assert (
                scraper._get_image_category("https://example.com/nature/landscape.jpg")
                == "nature"
            )
            assert (
                scraper._get_image_category("https://example.com/portrait/person.jpg")
                == "portraits"
            )
            assert (
                scraper._get_image_category("https://example.com/image.jpg") == "other"
            )

    def test_get_organization_path_date(self):
        """Test organization path for date method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="date",
            )

            path = scraper._get_organization_path("https://example.com/image.jpg")
            assert "downloads" in str(path)
            assert path.parent == output_dir

    def test_get_organization_path_category(self):
        """Test organization path for category method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="category",
            )

            path = scraper._get_organization_path(
                "https://example.com/nature/image.jpg", category="nature"
            )
            assert "nature" in str(path)
            assert path.parent == output_dir / "nature"

    def test_download_image_duplicate(self):
        """Test that duplicate URLs are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="date",
            )

            url = "https://example.com/image.jpg"
            scraper.downloaded_urls.add(url)

            result = scraper.download_image(url)
            assert result is False
            assert scraper.stats["images_skipped"] > 0

    def test_download_image_max_limit(self):
        """Test that max image limit is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="date",
                max_images=0,
            )

            result = scraper.download_image("https://example.com/image.jpg")
            assert result is False

    @pytest.mark.skipif(
        not pytest.importorskip("requests", reason="requests not available"),
        reason="requests not available",
    )
    def test_scrape_pages_stats(self):
        """Test that scraping updates statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            scraper = ImageScraper(
                output_directory=output_dir,
                organize_by="date",
            )

            with patch.object(scraper, "scrape_page", return_value=0):
                stats = scraper.scrape_pages(["https://example.com"])

                assert "pages_visited" in stats
                assert "images_downloaded" in stats
