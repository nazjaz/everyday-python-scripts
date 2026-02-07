"""Scientific Paper Database - Scrape and organize public domain papers.

This module provides functionality to scrape public domain scientific papers
from various sources, store them in a local database, and organize them by
subject, author, or publication date with search capabilities.
"""

import logging
import logging.handlers
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ScientificPaperDatabase:
    """Scrapes and manages scientific paper database."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize ScientificPaperDatabase with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.db_path = Path(
            self.config.get("database", {}).get(
                "file", "papers_database.db"
            )
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.get("scraper", {}).get(
                    "user_agent",
                    "Mozilla/5.0 (compatible; ScientificPaperBot/1.0)",
                )
            }
        )
        self._init_database()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Dictionary containing configuration settings.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if not config:
                raise ValueError("Configuration file is empty")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file: {e}")
            raise

    def _setup_logging(self) -> None:
        """Configure logging based on configuration settings."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/app.log")
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(message)s"
        )

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(),
            ],
        )

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Papers table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                subject TEXT,
                publication_date DATE,
                abstract TEXT,
                url TEXT,
                source TEXT,
                pdf_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, authors, publication_date)
            )
        """
        )

        # Subjects table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Authors table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                affiliation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Paper-Author junction table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_authors (
                paper_id INTEGER,
                author_id INTEGER,
                PRIMARY KEY (paper_id, author_id),
                FOREIGN KEY (paper_id) REFERENCES papers(id),
                FOREIGN KEY (author_id) REFERENCES authors(id)
            )
        """
        )

        # Create indexes for search performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_subject ON papers(subject)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_date ON papers(publication_date)"
        )

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def _get_or_create_author(self, author_name: str) -> int:
        """Get or create author ID.

        Args:
            author_name: Name of the author.

        Returns:
            Author ID.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM authors WHERE name = ?", (author_name,))
        result = cursor.fetchone()

        if result:
            author_id = result[0]
        else:
            cursor.execute(
                "INSERT INTO authors (name) VALUES (?)", (author_name,)
            )
            author_id = cursor.lastrowid
            logger.debug(f"Created new author: {author_name}")

        conn.commit()
        conn.close()
        return author_id

    def _get_or_create_subject(self, subject_name: str) -> int:
        """Get or create subject ID.

        Args:
            subject_name: Name of the subject.

        Returns:
            Subject ID.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM subjects WHERE name = ?", (subject_name,)
        )
        result = cursor.fetchone()

        if result:
            subject_id = result[0]
        else:
            cursor.execute(
                "INSERT INTO subjects (name) VALUES (?)", (subject_name,)
            )
            subject_id = cursor.lastrowid
            logger.debug(f"Created new subject: {subject_name}")

        conn.commit()
        conn.close()
        return subject_id

    def _add_paper(
        self,
        title: str,
        authors: List[str],
        subject: Optional[str] = None,
        publication_date: Optional[str] = None,
        abstract: Optional[str] = None,
        url: Optional[str] = None,
        source: Optional[str] = None,
        pdf_url: Optional[str] = None,
    ) -> Optional[int]:
        """Add paper to database.

        Args:
            title: Paper title.
            authors: List of author names.
            subject: Subject/category.
            publication_date: Publication date (YYYY-MM-DD).
            abstract: Paper abstract.
            url: Paper URL.
            source: Source identifier.
            pdf_url: PDF download URL.

        Returns:
            Paper ID or None if duplicate.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Check for duplicate
        cursor.execute(
            """
            SELECT id FROM papers
            WHERE title = ? AND authors = ? AND publication_date = ?
        """,
            (title, ", ".join(authors), publication_date),
        )
        if cursor.fetchone():
            conn.close()
            return None

        # Insert paper
        cursor.execute(
            """
            INSERT INTO papers (
                title, authors, subject, publication_date,
                abstract, url, source, pdf_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                title,
                ", ".join(authors),
                subject,
                publication_date,
                abstract,
                url,
                source,
                pdf_url,
            ),
        )

        paper_id = cursor.lastrowid

        # Link authors
        for author_name in authors:
            author_id = self._get_or_create_author(author_name)
            cursor.execute(
                """
                INSERT OR IGNORE INTO paper_authors (paper_id, author_id)
                VALUES (?, ?)
            """,
                (paper_id, author_id),
            )

        # Link subject
        if subject:
            subject_id = self._get_or_create_subject(subject)
            # Note: Subject is stored as text in papers table for simplicity

        conn.commit()
        conn.close()

        logger.debug(f"Added paper: {title}")
        return paper_id

    def _scrape_arxiv(self, query: str = "machine learning", max_results: int = 50) -> None:
        """Scrape papers from arXiv (public domain preprints).

        Args:
            query: Search query.
            max_results: Maximum number of results to scrape.
        """
        base_url = "http://export.arxiv.org/api/query"
        logger.info(f"Scraping arXiv for '{query}' (max {max_results} results)")

        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": min(max_results, 100),  # arXiv API limit
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }

            response = self.session.get(base_url, params=params, timeout=30)
            response.raise_for_status()

            # Parse XML response
            from xml.etree import ElementTree as ET

            root = ET.fromstring(response.content)

            # Namespace for arXiv XML
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entries = root.findall("atom:entry", ns)
            count = 0

            for entry in entries:
                try:
                    title_elem = entry.find("atom:title", ns)
                    title = title_elem.text.strip() if title_elem is not None else "Untitled"

                    # Extract authors
                    authors = []
                    for author in entry.findall("atom:author", ns):
                        name_elem = author.find("atom:name", ns)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())

                    # Extract abstract
                    summary_elem = entry.find("atom:summary", ns)
                    abstract = summary_elem.text.strip() if summary_elem is not None else None

                    # Extract publication date
                    published_elem = entry.find("atom:published", ns)
                    publication_date = None
                    if published_elem is not None:
                        date_str = published_elem.text
                        # Convert from arXiv format to YYYY-MM-DD
                        try:
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            publication_date = dt.strftime("%Y-%m-%d")
                        except ValueError:
                            pass

                    # Extract subject (primary category)
                    category_elem = entry.find("atom:category", ns)
                    subject = None
                    if category_elem is not None:
                        subject = category_elem.get("term", "").split(".")[0]  # Primary category

                    # Extract URLs
                    id_elem = entry.find("atom:id", ns)
                    url = id_elem.text if id_elem is not None else None

                    pdf_url = None
                    if url:
                        pdf_url = url.replace("/abs/", "/pdf/") + ".pdf"

                    # Add to database
                    paper_id = self._add_paper(
                        title=title,
                        authors=authors if authors else ["Unknown"],
                        subject=subject,
                        publication_date=publication_date,
                        abstract=abstract,
                        url=url,
                        source="arxiv",
                        pdf_url=pdf_url,
                    )

                    if paper_id:
                        count += 1

                except Exception as e:
                    logger.warning(f"Error parsing arXiv entry: {e}")
                    continue

            logger.info(f"Scraped {count} papers from arXiv")

        except requests.RequestException as e:
            logger.error(f"Error scraping arXiv: {e}")
        except ET.ParseError as e:
            logger.error(f"Error parsing arXiv XML: {e}")

    def scrape_sources(self) -> None:
        """Scrape papers from all configured sources."""
        sources = self.config.get("sources", {})

        if sources.get("arxiv", {}).get("enabled", False):
            query = sources.get("arxiv", {}).get("query", "machine learning")
            max_results = sources.get("arxiv", {}).get("max_results", 50)
            self._scrape_arxiv(query=query, max_results=max_results)

        logger.info("Scraping completed")

    def search_papers(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        subject: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search papers in database.

        Args:
            title: Search term for title.
            author: Author name to search for.
            subject: Subject to filter by.
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).
            limit: Maximum number of results.

        Returns:
            List of paper dictionaries.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        query = "SELECT * FROM papers WHERE 1=1"
        params = []

        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")

        if author:
            query += " AND authors LIKE ?"
            params.append(f"%{author}%")

        if subject:
            query += " AND subject LIKE ?"
            params.append(f"%{subject}%")

        if date_from:
            query += " AND publication_date >= ?"
            params.append(date_from)

        if date_to:
            query += " AND publication_date <= ?"
            params.append(date_to)

        query += " ORDER BY publication_date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Get column names
        column_names = [description[0] for description in cursor.description]

        papers = []
        for row in rows:
            paper_dict = dict(zip(column_names, row))
            papers.append(paper_dict)

        conn.close()
        return papers

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with statistics.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM papers")
        paper_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM authors")
        author_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(DISTINCT subject) FROM papers WHERE subject IS NOT NULL"
        )
        subject_used_count = cursor.fetchone()[0]

        conn.close()

        return {
            "papers": paper_count,
            "authors": author_count,
            "subjects": subject_count,
            "subjects_used": subject_used_count,
        }

    def organize_by_subject(self) -> Dict[str, int]:
        """Get paper count by subject.

        Returns:
            Dictionary mapping subjects to paper counts.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT subject, COUNT(*) as count
            FROM papers
            WHERE subject IS NOT NULL
            GROUP BY subject
            ORDER BY count DESC
        """
        )

        result = dict(cursor.fetchall())
        conn.close()
        return result

    def organize_by_author(self, limit: int = 20) -> Dict[str, int]:
        """Get paper count by author.

        Args:
            limit: Maximum number of authors to return.

        Returns:
            Dictionary mapping author names to paper counts.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT a.name, COUNT(pa.paper_id) as count
            FROM authors a
            JOIN paper_authors pa ON a.id = pa.author_id
            GROUP BY a.id, a.name
            ORDER BY count DESC
            LIMIT ?
        """,
            (limit,),
        )

        result = dict(cursor.fetchall())
        conn.close()
        return result

    def organize_by_date(self, year: Optional[int] = None) -> Dict[str, int]:
        """Get paper count by publication date.

        Args:
            year: Optional year to filter by.

        Returns:
            Dictionary mapping dates to paper counts.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        if year:
            cursor.execute(
                """
                SELECT publication_date, COUNT(*) as count
                FROM papers
                WHERE publication_date LIKE ?
                GROUP BY publication_date
                ORDER BY publication_date DESC
            """,
                (f"{year}%",),
            )
        else:
            cursor.execute(
                """
                SELECT publication_date, COUNT(*) as count
                FROM papers
                WHERE publication_date IS NOT NULL
                GROUP BY publication_date
                ORDER BY publication_date DESC
            """
            )

        result = dict(cursor.fetchall())
        conn.close()
        return result


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape and organize public domain scientific papers"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-s",
        "--scrape",
        action="store_true",
        help="Scrape papers from configured sources",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics",
    )
    parser.add_argument(
        "--search",
        help="Search papers by title",
    )
    parser.add_argument(
        "--author",
        help="Search papers by author",
    )
    parser.add_argument(
        "--subject",
        help="Filter papers by subject",
    )
    parser.add_argument(
        "--by-subject",
        action="store_true",
        help="Show papers organized by subject",
    )
    parser.add_argument(
        "--by-author",
        action="store_true",
        help="Show papers organized by author",
    )
    parser.add_argument(
        "--by-date",
        action="store_true",
        help="Show papers organized by date",
    )

    args = parser.parse_args()

    try:
        db = ScientificPaperDatabase(config_path=args.config)

        if args.scrape:
            db.scrape_sources()

        if args.stats:
            stats = db.get_statistics()
            print("\nDatabase Statistics:")
            print(f"  Papers: {stats['papers']}")
            print(f"  Authors: {stats['authors']}")
            print(f"  Subjects: {stats['subjects']}")
            print(f"  Subjects in use: {stats['subjects_used']}")

        if args.search or args.author or args.subject:
            papers = db.search_papers(
                title=args.search,
                author=args.author,
                subject=args.subject,
            )
            print(f"\nFound {len(papers)} papers:")
            for paper in papers[:10]:
                print(f"  - {paper['title']}")
                print(f"    Authors: {paper['authors']}")
                print(f"    Subject: {paper['subject']}")
                print(f"    Date: {paper['publication_date']}")
                print()

        if args.by_subject:
            org = db.organize_by_subject()
            print("\nPapers by Subject:")
            for subject, count in sorted(org.items(), key=lambda x: x[1], reverse=True):
                print(f"  {subject}: {count} papers")

        if args.by_author:
            org = db.organize_by_author()
            print("\nPapers by Author (Top 20):")
            for author, count in sorted(org.items(), key=lambda x: x[1], reverse=True):
                print(f"  {author}: {count} papers")

        if args.by_date:
            org = db.organize_by_date()
            print("\nPapers by Date:")
            for date, count in sorted(org.items(), reverse=True)[:20]:
                print(f"  {date}: {count} papers")

        if not any(
            [
                args.scrape,
                args.stats,
                args.search,
                args.author,
                args.subject,
                args.by_subject,
                args.by_author,
                args.by_date,
            ]
        ):
            print("Use --help to see available options")
            print("Example: python src/main.py --scrape --stats")

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
