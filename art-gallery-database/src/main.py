"""Art Gallery Database - Scrape public domain art collections.

This module provides functionality to scrape public domain art collections,
create a local database with searchable metadata, and organize images.
"""

import hashlib
import json
import logging
import logging.handlers
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ArtGalleryDatabase:
    """Manages art gallery database with scraping and search capabilities."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize ArtGalleryDatabase with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.db_path = Path(
            self.config.get("database", {}).get("path", "art_gallery.db")
        )
        self.images_dir = Path(
            self.config.get("images", {}).get("directory", "images")
        )
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.stats = {
            "artworks_scraped": 0,
            "images_downloaded": 0,
            "errors": 0,
        }

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

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS artworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT,
                year INTEGER,
                medium TEXT,
                dimensions TEXT,
                description TEXT,
                source_url TEXT,
                image_url TEXT,
                image_path TEXT,
                image_hash TEXT,
                category TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_title ON artworks(title)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_artist ON artworks(artist)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_category ON artworks(category)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tags ON artworks(tags)
            """
        )

        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.db_path}")

    def _calculate_image_hash(self, image_path: Path) -> str:
        """Calculate MD5 hash of image file.

        Args:
            image_path: Path to image file.

        Returns:
            MD5 hash string.
        """
        hash_md5 = hashlib.md5()
        try:
            with open(image_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError as e:
            logger.error(f"Cannot read image for hashing: {image_path} - {e}")
            raise

    def _download_image(
        self, image_url: str, artwork_id: str
    ) -> Optional[Path]:
        """Download image from URL and save to images directory.

        Args:
            image_url: URL of image to download.
            artwork_id: Unique identifier for artwork.

        Returns:
            Path to downloaded image or None if error.
        """
        try:
            parsed_url = urlparse(image_url)
            file_ext = Path(parsed_url.path).suffix or ".jpg"
            filename = f"{artwork_id}{file_ext}"
            image_path = self.images_dir / filename

            if image_path.exists():
                logger.debug(f"Image already exists: {image_path}")
                return image_path

            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; ArtGalleryBot/1.0)"
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()

            with open(image_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded image: {image_path}")
            return image_path

        except requests.RequestException as e:
            logger.error(f"Failed to download image {image_url}: {e}")
            self.stats["errors"] += 1
            return None
        except IOError as e:
            logger.error(f"Failed to save image {image_url}: {e}")
            self.stats["errors"] += 1
            return None

    def _scrape_wikimedia_commons(
        self, limit: int = 50, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Scrape artworks from Wikimedia Commons.

        Args:
            limit: Maximum number of artworks to scrape.
            category: Optional category to filter by.

        Returns:
            List of artwork dictionaries.
        """
        artworks = []
        base_url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmnamespace": 6,
            "cmlimit": min(limit, 50),
            "cmprop": "title|timestamp",
        }

        if category:
            params["cmtitle"] = f"Category:{category}"

        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "query" not in data or "categorymembers" not in data["query"]:
                logger.warning("No artworks found in Wikimedia Commons")
                return artworks

            for item in data["query"]["categorymembers"][:limit]:
                title = item.get("title", "").replace("File:", "")
                if not title:
                    continue

                image_url = (
                    f"https://commons.wikimedia.org/wiki/Special:FilePath/{title}"
                )

                artwork = {
                    "title": title.replace("_", " ").replace(".jpg", "").replace(
                        ".png", ""
                    ),
                    "artist": None,
                    "year": None,
                    "medium": None,
                    "dimensions": None,
                    "description": f"Public domain artwork from Wikimedia Commons: {title}",
                    "source_url": f"https://commons.wikimedia.org/wiki/File:{title}",
                    "image_url": image_url,
                    "category": category or "general",
                    "tags": f"wikimedia,commons,{category or 'general'}",
                }

                artworks.append(artwork)

            logger.info(f"Scraped {len(artworks)} artworks from Wikimedia Commons")

        except requests.RequestException as e:
            logger.error(f"Error scraping Wikimedia Commons: {e}")
            self.stats["errors"] += 1

        return artworks

    def _scrape_met_museum(
        self, limit: int = 50, department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Scrape artworks from Metropolitan Museum API.

        Args:
            limit: Maximum number of artworks to scrape.
            department_id: Optional department ID to filter by.

        Returns:
            List of artwork dictionaries.
        """
        artworks = []
        base_url = "https://collectionapi.metmuseum.org/public/collection/v1/objects"

        try:
            if department_id:
                params = {"departmentIds": department_id}
            else:
                params = {}

            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "objectIDs" not in data:
                logger.warning("No artworks found in Met Museum API")
                return artworks

            object_ids = data["objectIDs"][:limit]

            for obj_id in object_ids:
                try:
                    obj_url = f"{base_url}/{obj_id}"
                    obj_response = requests.get(obj_url, timeout=30)
                    obj_response.raise_for_status()
                    obj_data = obj_response.json()

                    if not obj_data.get("isPublicDomain", False):
                        continue

                    image_url = obj_data.get("primaryImage", "")
                    if not image_url:
                        continue

                    artwork = {
                        "title": obj_data.get("title", "Untitled"),
                        "artist": obj_data.get("artistDisplayName", "Unknown"),
                        "year": obj_data.get("objectDate", ""),
                        "medium": obj_data.get("medium", ""),
                        "dimensions": obj_data.get("dimensions", ""),
                        "description": obj_data.get("title", ""),
                        "source_url": obj_data.get("objectURL", ""),
                        "image_url": image_url,
                        "category": obj_data.get("department", "general"),
                        "tags": f"metmuseum,{obj_data.get('tags', [{}])[0].get('term', 'general') if obj_data.get('tags') else 'general'}",
                    }

                    artworks.append(artwork)
                    time.sleep(0.5)

                except requests.RequestException as e:
                    logger.debug(f"Error fetching Met Museum object {obj_id}: {e}")
                    continue

            logger.info(f"Scraped {len(artworks)} artworks from Met Museum")

        except requests.RequestException as e:
            logger.error(f"Error scraping Met Museum: {e}")
            self.stats["errors"] += 1

        return artworks

    def _save_artwork(self, artwork: Dict[str, Any]) -> Optional[int]:
        """Save artwork to database.

        Args:
            artwork: Artwork dictionary with metadata.

        Returns:
            Database ID of saved artwork or None if error.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            image_path = None
            image_hash = None

            if artwork.get("image_url"):
                artwork_id = str(int(time.time() * 1000))
                image_path_obj = self._download_image(
                    artwork["image_url"], artwork_id
                )
                if image_path_obj:
                    image_path = str(image_path_obj)
                    image_hash = self._calculate_image_hash(image_path_obj)
                    self.stats["images_downloaded"] += 1

            cursor.execute(
                """
                INSERT INTO artworks (
                    title, artist, year, medium, dimensions, description,
                    source_url, image_url, image_path, image_hash, category, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artwork.get("title", "Untitled"),
                    artwork.get("artist"),
                    artwork.get("year"),
                    artwork.get("medium"),
                    artwork.get("dimensions"),
                    artwork.get("description"),
                    artwork.get("source_url"),
                    artwork.get("image_url"),
                    image_path,
                    image_hash,
                    artwork.get("category", "general"),
                    artwork.get("tags", ""),
                ),
            )

            artwork_id = cursor.lastrowid
            conn.commit()
            self.stats["artworks_scraped"] += 1

            logger.info(f"Saved artwork: {artwork.get('title', 'Untitled')}")

            return artwork_id

        except sqlite3.Error as e:
            logger.error(f"Database error saving artwork: {e}")
            conn.rollback()
            self.stats["errors"] += 1
            return None
        finally:
            conn.close()

    def scrape_collections(
        self,
        sources: Optional[List[str]] = None,
        limit: int = 50,
        **kwargs: Any
    ) -> None:
        """Scrape artworks from specified sources.

        Args:
            sources: List of sources to scrape. If None, uses config defaults.
            limit: Maximum number of artworks per source.
            **kwargs: Additional source-specific parameters.
        """
        if sources is None:
            sources = self.config.get("scraping", {}).get("sources", [])

        logger.info(
            f"Starting scraping from {len(sources)} sources",
            extra={"sources": sources, "limit": limit},
        )

        for source in sources:
            try:
                if source == "wikimedia":
                    category = kwargs.get("category")
                    artworks = self._scrape_wikimedia_commons(limit, category)
                elif source == "metmuseum":
                    department_id = kwargs.get("department_id")
                    artworks = self._scrape_met_museum(limit, department_id)
                else:
                    logger.warning(f"Unknown source: {source}")
                    continue

                for artwork in artworks:
                    self._save_artwork(artwork)
                    time.sleep(0.2)

            except Exception as e:
                logger.error(f"Error scraping from {source}: {e}", exc_info=True)
                self.stats["errors"] += 1

        logger.info(
            f"Scraping completed: {self.stats['artworks_scraped']} artworks "
            f"scraped, {self.stats['images_downloaded']} images downloaded"
        )

    def search_artworks(
        self,
        query: Optional[str] = None,
        artist: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search artworks in database.

        Args:
            query: Text query to search in title, description, tags.
            artist: Filter by artist name.
            category: Filter by category.
            limit: Maximum number of results.

        Returns:
            List of artwork dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []

        if query:
            conditions.append(
                "(title LIKE ? OR description LIKE ? OR tags LIKE ?)"
            )
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term])

        if artist:
            conditions.append("artist LIKE ?")
            params.append(f"%{artist}%")

        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        query_sql = f"""
            SELECT * FROM artworks
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """

        try:
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()

            artworks = []
            for row in rows:
                artwork = dict(row)
                artworks.append(artwork)

            logger.info(
                f"Search returned {len(artworks)} results",
                extra={"query": query, "artist": artist, "category": category},
            )

            return artworks

        except sqlite3.Error as e:
            logger.error(f"Database error during search: {e}")
            return []
        finally:
            conn.close()

    def get_artwork_by_id(self, artwork_id: int) -> Optional[Dict[str, Any]]:
        """Get artwork by database ID.

        Args:
            artwork_id: Database ID of artwork.

        Returns:
            Artwork dictionary or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Database error fetching artwork {artwork_id}: {e}")
            return None
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with statistics.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM artworks")
            total_artworks = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(DISTINCT artist) FROM artworks WHERE artist IS NOT NULL"
            )
            total_artists = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT category) FROM artworks")
            total_categories = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM artworks WHERE image_path IS NOT NULL"
            )
            artworks_with_images = cursor.fetchone()[0]

            return {
                "total_artworks": total_artworks,
                "total_artists": total_artists,
                "total_categories": total_categories,
                "artworks_with_images": artworks_with_images,
                "scraping_stats": self.stats,
            }

        except sqlite3.Error as e:
            logger.error(f"Database error getting statistics: {e}")
            return {}
        finally:
            conn.close()


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape public domain art collections and create "
        "local gallery database"
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
        help="Scrape art collections",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Sources to scrape (wikimedia, metmuseum)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum artworks per source (default: 50)",
    )
    parser.add_argument(
        "--search",
        help="Search query for artworks",
    )
    parser.add_argument(
        "--artist",
        help="Filter search by artist",
    )
    parser.add_argument(
        "--category",
        help="Filter search by category",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics",
    )

    args = parser.parse_args()

    try:
        gallery = ArtGalleryDatabase(config_path=args.config)

        if args.scrape:
            gallery.scrape_collections(sources=args.sources, limit=args.limit)
            print(
                f"\nScraping complete. "
                f"Scraped {gallery.stats['artworks_scraped']} artworks, "
                f"downloaded {gallery.stats['images_downloaded']} images."
            )

        if args.search:
            results = gallery.search_artworks(
                query=args.search, artist=args.artist, category=args.category
            )
            print(f"\nFound {len(results)} artworks:")
            for artwork in results[:10]:
                print(
                    f"  [{artwork['id']}] {artwork['title']} "
                    f"by {artwork.get('artist', 'Unknown')}"
                )
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more")

        if args.stats:
            stats = gallery.get_statistics()
            print("\nDatabase Statistics:")
            print(f"  Total artworks: {stats.get('total_artworks', 0)}")
            print(f"  Total artists: {stats.get('total_artists', 0)}")
            print(f"  Total categories: {stats.get('total_categories', 0)}")
            print(
                f"  Artworks with images: "
                f"{stats.get('artworks_with_images', 0)}"
            )

        if not any([args.scrape, args.search, args.stats]):
            parser.print_help()

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
