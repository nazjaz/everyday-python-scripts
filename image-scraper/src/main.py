"""Image Scraper.

A Python script that scrapes public domain images from websites and downloads
them to a local directory, organizing by category or date.
"""

import argparse
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.error("requests and beautifulsoup4 are required. Install with: pip install requests beautifulsoup4")


class ImageScraper:
    """Scrapes and downloads images from websites."""

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"}
    IMAGE_CONTENT_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
        "image/svg+xml",
    }

    def __init__(
        self,
        output_directory: Path,
        organize_by: str = "date",
        max_images: Optional[int] = None,
        rate_limit: float = 1.0,
        user_agent: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        """Initialize the image scraper.

        Args:
            output_directory: Directory to save downloaded images
            organize_by: Organization method - "date" or "category"
            max_images: Maximum number of images to download (None = unlimited)
            rate_limit: Delay between requests in seconds
            user_agent: Custom user agent string
            timeout: Request timeout in seconds

        Raises:
            ValueError: If organize_by is invalid
        """
        if organize_by not in ["date", "category"]:
            raise ValueError("organize_by must be either 'date' or 'category'")

        if not REQUESTS_AVAILABLE:
            raise ImportError("requests and beautifulsoup4 are required")

        self.output_directory = Path(output_directory).expanduser().resolve()
        self.organize_by = organize_by
        self.max_images = max_images
        self.rate_limit = rate_limit
        self.timeout = timeout

        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

        self.downloaded_urls: Set[str] = set()
        self.stats = {
            "pages_visited": 0,
            "images_found": 0,
            "images_downloaded": 0,
            "images_skipped": 0,
            "errors": 0,
        }

        self.output_directory.mkdir(parents=True, exist_ok=True)

    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image.

        Args:
            url: URL to check

        Returns:
            True if URL appears to be an image, False otherwise
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in self.IMAGE_EXTENSIONS)

    def _get_image_urls_from_page(self, url: str) -> List[str]:
        """Extract image URLs from a web page.

        Args:
            url: URL of the page to scrape

        Returns:
            List of image URLs found on the page
        """
        image_urls: List[str] = []

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            for img_tag in soup.find_all("img"):
                src = img_tag.get("src")
                if src:
                    absolute_url = urljoin(url, src)
                    if self._is_image_url(absolute_url):
                        image_urls.append(absolute_url)

                data_src = img_tag.get("data-src")
                if data_src:
                    absolute_url = urljoin(url, data_src)
                    if self._is_image_url(absolute_url):
                        image_urls.append(absolute_url)

            for link_tag in soup.find_all("a", href=True):
                href = link_tag.get("href")
                if href and self._is_image_url(href):
                    absolute_url = urljoin(url, href)
                    image_urls.append(absolute_url)

            self.stats["pages_visited"] += 1

        except requests.RequestException as e:
            logger.warning(f"Error fetching page {url}: {e}")
            self.stats["errors"] += 1

        return image_urls

    def _get_image_category(self, url: str, content: Optional[bytes] = None) -> str:
        """Determine image category from URL or content.

        Args:
            url: Image URL
            content: Optional image content for analysis

        Returns:
            Category name
        """
        url_lower = url.lower()
        path = urlparse(url).path.lower()

        if any(word in url_lower for word in ["nature", "landscape", "outdoor"]):
            return "nature"
        elif any(word in url_lower for word in ["portrait", "person", "people"]):
            return "portraits"
        elif any(word in url_lower for word in ["animal", "pet", "wildlife"]):
            return "animals"
        elif any(word in url_lower for word in ["food", "meal", "cooking"]):
            return "food"
        elif any(word in url_lower for word in ["architecture", "building", "city"]):
            return "architecture"
        elif any(word in url_lower for word in ["art", "painting", "drawing"]):
            return "art"
        else:
            return "other"

    def _get_safe_filename(self, url: str, category: Optional[str] = None) -> str:
        """Generate a safe filename from URL.

        Args:
            url: Image URL
            category: Optional category name

        Returns:
            Safe filename
        """
        parsed = urlparse(url)
        path = parsed.path
        filename = Path(path).name

        if not filename or "." not in filename:
            filename = "image.jpg"

        safe_name = re.sub(r"[^\w\-_.]", "_", filename)
        safe_name = safe_name[:200]

        if category:
            safe_name = f"{category}_{safe_name}"

        return safe_name

    def _download_image(self, url: str, file_path: Path) -> bool:
        """Download an image from URL.

        Args:
            url: Image URL
            file_path: Destination file path

        Returns:
            True if download was successful, False otherwise
        """
        try:
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if content_type and not any(
                ct in content_type.lower() for ct in self.IMAGE_CONTENT_TYPES
            ):
                logger.debug(f"Skipping non-image content: {url}")
                return False

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = file_path.stat().st_size
            if file_size == 0:
                file_path.unlink()
                logger.warning(f"Downloaded empty file: {url}")
                return False

            logger.info(f"Downloaded: {url} -> {file_path} ({file_size:,} bytes)")
            return True

        except requests.RequestException as e:
            logger.warning(f"Error downloading {url}: {e}")
            self.stats["errors"] += 1
            return False
        except (IOError, OSError) as e:
            logger.error(f"Error saving file {file_path}: {e}")
            self.stats["errors"] += 1
            return False

    def _get_organization_path(self, url: str, category: Optional[str] = None) -> Path:
        """Get the destination path based on organization method.

        Args:
            url: Image URL
            category: Image category

        Returns:
            Destination path
        """
        if self.organize_by == "date":
            date_str = datetime.now().strftime("%Y-%m-%d")
            org_path = self.output_directory / date_str
        elif self.organize_by == "category":
            category = category or self._get_image_category(url)
            org_path = self.output_directory / category
        else:
            org_path = self.output_directory

        return org_path

    def download_image(self, url: str) -> bool:
        """Download a single image.

        Args:
            url: Image URL to download

        Returns:
            True if download was successful, False otherwise
        """
        if url in self.downloaded_urls:
            logger.debug(f"Already downloaded: {url}")
            self.stats["images_skipped"] += 1
            return False

        if self.max_images and self.stats["images_downloaded"] >= self.max_images:
            logger.info(f"Reached maximum image limit: {self.max_images}")
            return False

        category = None
        if self.organize_by == "category":
            category = self._get_image_category(url)

        org_path = self._get_organization_path(url, category)
        filename = self._get_safe_filename(url, category)
        file_path = org_path / filename

        if file_path.exists():
            logger.debug(f"File already exists: {file_path}")
            self.stats["images_skipped"] += 1
            return False

        if self._download_image(url, file_path):
            self.downloaded_urls.add(url)
            self.stats["images_downloaded"] += 1
            return True

        return False

    def scrape_page(self, url: str) -> int:
        """Scrape images from a web page.

        Args:
            url: URL of the page to scrape

        Returns:
            Number of images downloaded
        """
        logger.info(f"Scraping page: {url}")

        image_urls = self._get_image_urls_from_page(url)
        self.stats["images_found"] += len(image_urls)

        downloaded_count = 0

        for image_url in image_urls:
            if self.download_image(image_url):
                downloaded_count += 1

            time.sleep(self.rate_limit)

        return downloaded_count

    def scrape_pages(self, urls: List[str]) -> dict:
        """Scrape images from multiple pages.

        Args:
            urls: List of URLs to scrape

        Returns:
            Dictionary with statistics
        """
        logger.info(f"Starting scrape of {len(urls)} page(s)")

        for url in urls:
            self.scrape_page(url)
            time.sleep(self.rate_limit)

        logger.info("Scraping complete")
        logger.info(
            f"Statistics: {self.stats['images_downloaded']} downloaded, "
            f"{self.stats['images_skipped']} skipped, "
            f"{self.stats['errors']} errors"
        )

        return self.stats.copy()


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Scrape public domain images from websites"
    )
    parser.add_argument(
        "urls",
        type=str,
        nargs="+",
        help="URLs of web pages to scrape for images",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output directory for downloaded images",
    )
    parser.add_argument(
        "--organize-by",
        type=str,
        choices=["date", "category"],
        default="date",
        help="Organization method: date or category (default: date)",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Maximum number of images to download",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default=None,
        help="Custom user agent string",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        if not REQUESTS_AVAILABLE:
            logger.error("Required libraries not available. Install with: pip install requests beautifulsoup4")
            return 1

        output_dir = Path(args.output)
        organize_by = args.organize_by
        max_images = args.max_images
        rate_limit = args.rate_limit
        user_agent = args.user_agent
        timeout = args.timeout

        if args.config:
            config = load_config(Path(args.config))
            if "output_directory" in config:
                output_dir = Path(config["output_directory"])
            if "organize_by" in config:
                organize_by = config["organize_by"]
            if "max_images" in config:
                max_images = config["max_images"]
            if "rate_limit" in config:
                rate_limit = config["rate_limit"]
            if "user_agent" in config:
                user_agent = config["user_agent"]
            if "timeout" in config:
                timeout = config["timeout"]
            if "urls" in config:
                args.urls = config["urls"]

        scraper = ImageScraper(
            output_directory=output_dir,
            organize_by=organize_by,
            max_images=max_images,
            rate_limit=rate_limit,
            user_agent=user_agent,
            timeout=timeout,
        )

        stats = scraper.scrape_pages(args.urls)

        print("\nScraping Statistics:")
        print(f"  Pages visited: {stats['pages_visited']}")
        print(f"  Images found: {stats['images_found']}")
        print(f"  Images downloaded: {stats['images_downloaded']}")
        print(f"  Images skipped: {stats['images_skipped']}")
        print(f"  Errors: {stats['errors']}")

        return 0

    except (ValueError, FileNotFoundError, ImportError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
