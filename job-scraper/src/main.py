"""Job Scraper - Scrape and filter job listings from job board websites.

This module provides functionality to scrape job listings from various
job board websites, filter them based on keywords, and save matching
jobs to a CSV file with details. Includes rate limiting, error handling,
and support for multiple job board formats.
"""

import csv
import logging
import logging.handlers
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class JobScraper:
    """Scrapes job listings from job board websites and filters by keywords."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize JobScraper with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_output()
        self.jobs: List[Dict[str, str]] = []
        self.stats = {
            "pages_scraped": 0,
            "jobs_found": 0,
            "jobs_matched": 0,
            "errors": 0,
            "errors_list": [],
        }
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36",
                )
            }
        )

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid.
        """
        config_file = Path(config_path)

        if not config_file.is_absolute():
            if not config_file.exists():
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    cwd_config = Path.cwd() / config_path
                    if cwd_config.exists():
                        config_file = cwd_config

        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("OUTPUT_FILE"):
            config["output_file"] = os.getenv("OUTPUT_FILE")
        if os.getenv("KEYWORDS"):
            config["filters"]["keywords"] = os.getenv("KEYWORDS").split(",")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/job_scraper.log")

        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=log_config.get("max_bytes", 10485760),
            backupCount=log_config.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logger.info("Logging configured successfully")

    def _setup_output(self) -> None:
        """Set up output file path."""
        output_file = self.config.get("output_file", "jobs.csv")
        output_path = Path(output_file)

        if not output_path.is_absolute():
            project_root = Path(__file__).parent.parent
            output_path = project_root / output_file

        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path = output_path

        logger.info(f"Output file: {self.output_path}")

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page.

        Args:
            url: URL to fetch.

        Returns:
            BeautifulSoup object or None if fetch failed.
        """
        try:
            delay = self.config.get("rate_limiting", {}).get("delay_seconds", 1)
            time.sleep(delay)

            response = self.session.get(
                url, timeout=self.config.get("request_timeout", 30)
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            self.stats["pages_scraped"] += 1
            logger.debug(f"Fetched page: {url}")
            return soup

        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching {url}: {e}"
            logger.warning(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return None

    def _extract_job_data(
        self, soup: BeautifulSoup, job_board: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """Extract job data from parsed HTML.

        Args:
            soup: BeautifulSoup object containing page HTML.
            job_board: Job board configuration with selectors.

        Returns:
            List of job dictionaries.
        """
        jobs = []
        job_selector = job_board.get("selectors", {}).get("job_item", "")

        if not job_selector:
            logger.warning("No job item selector configured")
            return jobs

        job_elements = soup.select(job_selector)

        for job_elem in job_elements:
            try:
                job_data = self._parse_job_element(job_elem, job_board)
                if job_data:
                    jobs.append(job_data)
                    self.stats["jobs_found"] += 1
            except Exception as e:
                error_msg = f"Error parsing job element: {e}"
                logger.debug(error_msg)
                self.stats["errors"] += 1
                if error_msg not in self.stats["errors_list"]:
                    self.stats["errors_list"].append(error_msg)

        return jobs

    def _parse_job_element(
        self, job_elem: BeautifulSoup, job_board: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """Parse a single job element into a dictionary.

        Args:
            job_elem: BeautifulSoup element containing job data.
            job_board: Job board configuration with selectors.

        Returns:
            Dictionary with job data or None if parsing failed.
        """
        selectors = job_board.get("selectors", {})
        base_url = job_board.get("base_url", "")

        job_data = {
            "title": "",
            "company": "",
            "location": "",
            "description": "",
            "url": "",
            "source": job_board.get("name", "Unknown"),
        }

        # Extract title
        title_selector = selectors.get("title", "")
        if title_selector:
            title_elem = job_elem.select_one(title_selector)
            if title_elem:
                job_data["title"] = title_elem.get_text(strip=True)

        # Extract company
        company_selector = selectors.get("company", "")
        if company_selector:
            company_elem = job_elem.select_one(company_selector)
            if company_elem:
                job_data["company"] = company_elem.get_text(strip=True)

        # Extract location
        location_selector = selectors.get("location", "")
        if location_selector:
            location_elem = job_elem.select_one(location_selector)
            if location_elem:
                job_data["location"] = location_elem.get_text(strip=True)

        # Extract description
        description_selector = selectors.get("description", "")
        if description_selector:
            desc_elem = job_elem.select_one(description_selector)
            if desc_elem:
                job_data["description"] = desc_elem.get_text(strip=True)

        # Extract URL
        url_selector = selectors.get("url", "")
        if url_selector:
            url_elem = job_elem.select_one(url_selector)
            if url_elem:
                href = url_elem.get("href", "")
                if href:
                    job_data["url"] = urljoin(base_url, href)

        # If no URL found, try to get href from title element
        if not job_data["url"] and title_selector:
            title_elem = job_elem.select_one(title_selector)
            if title_elem:
                href = title_elem.get("href", "")
                if href:
                    job_data["url"] = urljoin(base_url, href)

        # Validate that we have at least a title
        if not job_data["title"]:
            return None

        return job_data

    def _matches_keywords(self, job: Dict[str, str]) -> bool:
        """Check if job matches keyword filters.

        Args:
            job: Job dictionary to check.

        Returns:
            True if job matches keywords, False otherwise.
        """
        filters = self.config.get("filters", {})
        keywords = filters.get("keywords", [])
        exclude_keywords = filters.get("exclude_keywords", [])

        if not keywords and not exclude_keywords:
            return True

        # Combine all job text for searching
        job_text = " ".join(
            [
                job.get("title", "").lower(),
                job.get("description", "").lower(),
                job.get("company", "").lower(),
                job.get("location", "").lower(),
            ]
        )

        # Check exclude keywords first
        if exclude_keywords:
            for exclude_keyword in exclude_keywords:
                if exclude_keyword.lower() in job_text:
                    return False

        # Check include keywords
        if keywords:
            match_any = filters.get("match_any", True)
            if match_any:
                # Match if any keyword is found
                for keyword in keywords:
                    if keyword.lower() in job_text:
                        return True
                return False
            else:
                # Match only if all keywords are found
                for keyword in keywords:
                    if keyword.lower() not in job_text:
                        return False
                return True

        return True

    def _scrape_job_board(self, job_board: Dict[str, str]) -> List[Dict[str, str]]:
        """Scrape jobs from a single job board.

        Args:
            job_board: Job board configuration.

        Returns:
            List of job dictionaries.
        """
        board_name = job_board.get("name", "Unknown")
        base_url = job_board.get("base_url", "")
        search_url = job_board.get("search_url", base_url)
        max_pages = job_board.get("max_pages", 1)

        logger.info(f"Scraping job board: {board_name}")
        logger.info(f"Search URL: {search_url}")

        all_jobs = []

        for page in range(1, max_pages + 1):
            # Construct URL for this page
            if "{page}" in search_url:
                url = search_url.replace("{page}", str(page))
            else:
                url = search_url
                if page > 1:
                    # Try to append page parameter
                    separator = "&" if "?" in url else "?"
                    url = f"{url}{separator}page={page}"

            logger.info(f"Scraping page {page}: {url}")

            soup = self._fetch_page(url)
            if not soup:
                logger.warning(f"Failed to fetch page {page}, stopping")
                break

            jobs = self._extract_job_data(soup, job_board)
            if not jobs:
                logger.info(f"No jobs found on page {page}, stopping")
                break

            all_jobs.extend(jobs)
            logger.info(f"Found {len(jobs)} jobs on page {page}")

        logger.info(f"Total jobs found from {board_name}: {len(all_jobs)}")
        return all_jobs

    def scrape_jobs(self) -> List[Dict[str, str]]:
        """Scrape jobs from all configured job boards.

        Returns:
            List of all job dictionaries.
        """
        logger.info("Starting job scraping")
        job_boards = self.config.get("job_boards", [])

        if not job_boards:
            logger.warning("No job boards configured")
            return []

        all_jobs = []

        for job_board in job_boards:
            try:
                jobs = self._scrape_job_board(job_board)
                all_jobs.extend(jobs)
            except Exception as e:
                error_msg = f"Error scraping {job_board.get('name', 'Unknown')}: {e}"
                logger.error(error_msg, exc_info=True)
                self.stats["errors"] += 1
                self.stats["errors_list"].append(error_msg)

        logger.info(f"Total jobs scraped: {len(all_jobs)}")
        return all_jobs

    def filter_jobs(self, jobs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Filter jobs based on keyword criteria.

        Args:
            jobs: List of job dictionaries to filter.

        Returns:
            List of filtered job dictionaries.
        """
        logger.info("Filtering jobs by keywords")
        filtered_jobs = []

        for job in jobs:
            if self._matches_keywords(job):
                filtered_jobs.append(job)
                self.stats["jobs_matched"] += 1

        logger.info(
            f"Filtered {len(jobs)} jobs to {len(filtered_jobs)} matching jobs"
        )
        return filtered_jobs

    def save_to_csv(self, jobs: List[Dict[str, str]]) -> Path:
        """Save jobs to CSV file.

        Args:
            jobs: List of job dictionaries to save.

        Returns:
            Path to saved CSV file.
        """
        if not jobs:
            logger.warning("No jobs to save")
            return self.output_path

        fieldnames = ["title", "company", "location", "description", "url", "source"]

        with open(self.output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs)

        logger.info(f"Saved {len(jobs)} jobs to {self.output_path}")
        return self.output_path


def main() -> int:
    """Main entry point for job scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape job listings from job board websites "
        "and filter by keywords"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output CSV file path (overrides config)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip keyword filtering, save all scraped jobs",
    )

    args = parser.parse_args()

    try:
        scraper = JobScraper(config_path=args.config)

        if args.output:
            scraper.output_path = Path(args.output)
            scraper.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Scrape jobs
        jobs = scraper.scrape_jobs()

        # Filter jobs
        if not args.no_filter:
            jobs = scraper.filter_jobs(jobs)

        # Save to CSV
        output_path = scraper.save_to_csv(jobs)

        # Print summary
        print("\n" + "=" * 60)
        print("Job Scraping Summary")
        print("=" * 60)
        print(f"Pages Scraped: {scraper.stats['pages_scraped']}")
        print(f"Jobs Found: {scraper.stats['jobs_found']}")
        print(f"Jobs Matched: {scraper.stats['jobs_matched']}")
        print(f"Jobs Saved: {len(jobs)}")
        print(f"Output File: {output_path}")
        print(f"Errors: {scraper.stats['errors']}")

        if scraper.stats["errors_list"]:
            print("\nErrors:")
            for error in scraper.stats["errors_list"][:5]:
                print(f"  - {error}")
            if len(scraper.stats["errors_list"]) > 5:
                print(f"  ... and {len(scraper.stats['errors_list']) - 5} more")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
