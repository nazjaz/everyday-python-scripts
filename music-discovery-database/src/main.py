"""Music Discovery Database - Scrape and store public domain music information.

This module provides functionality to scrape public domain music information
from various sources, store it in a local database, and generate music
recommendations based on genres and artists.
"""

import json
import logging
import logging.handlers
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MusicDiscoveryDatabase:
    """Scrapes and manages public domain music discovery database."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize MusicDiscoveryDatabase with configuration.

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
                "file", "music_database.db"
            )
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.get("scraper", {}).get(
                    "user_agent",
                    "Mozilla/5.0 (compatible; MusicDiscoveryBot/1.0)",
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

        # Artists table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                genre TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Tracks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist_id INTEGER,
                genre TEXT,
                duration INTEGER,
                url TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artist_id) REFERENCES artists(id)
            )
        """
        )

        # Genres table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Recommendations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER,
                recommended_track_id INTEGER,
                similarity_score REAL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_id) REFERENCES tracks(id),
                FOREIGN KEY (recommended_track_id) REFERENCES tracks(id)
            )
        """
        )

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def _get_artist_id(self, artist_name: str, genre: Optional[str] = None) -> int:
        """Get or create artist ID.

        Args:
            artist_name: Name of the artist.
            genre: Optional genre for the artist.

        Returns:
            Artist ID.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM artists WHERE name = ?", (artist_name,))
        result = cursor.fetchone()

        if result:
            artist_id = result[0]
        else:
            cursor.execute(
                "INSERT INTO artists (name, genre) VALUES (?, ?)",
                (artist_name, genre),
            )
            artist_id = cursor.lastrowid
            logger.debug(f"Created new artist: {artist_name}")

        conn.commit()
        conn.close()
        return artist_id

    def _get_genre_id(self, genre_name: str) -> int:
        """Get or create genre ID.

        Args:
            genre_name: Name of the genre.

        Returns:
            Genre ID.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM genres WHERE name = ?", (genre_name,))
        result = cursor.fetchone()

        if result:
            genre_id = result[0]
        else:
            cursor.execute(
                "INSERT INTO genres (name) VALUES (?)", (genre_name,)
            )
            genre_id = cursor.lastrowid
            logger.debug(f"Created new genre: {genre_name}")

        conn.commit()
        conn.close()
        return genre_id

    def _add_track(
        self,
        title: str,
        artist_name: str,
        genre: Optional[str] = None,
        duration: Optional[int] = None,
        url: Optional[str] = None,
        source: Optional[str] = None,
    ) -> int:
        """Add track to database.

        Args:
            title: Track title.
            artist_name: Artist name.
            genre: Optional genre.
            duration: Optional duration in seconds.
            url: Optional track URL.
            source: Optional source identifier.

        Returns:
            Track ID.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        artist_id = self._get_artist_id(artist_name, genre)

        cursor.execute(
            """
            INSERT INTO tracks (title, artist_id, genre, duration, url, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (title, artist_id, genre, duration, url, source),
        )

        track_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.debug(f"Added track: {title} by {artist_name}")
        return track_id

    def _scrape_musopen(self, max_pages: int = 5) -> None:
        """Scrape music from Musopen (public domain music archive).

        Args:
            max_pages: Maximum number of pages to scrape.
        """
        base_url = "https://musopen.org/music/"
        logger.info(f"Scraping Musopen (max {max_pages} pages)")

        for page in range(1, max_pages + 1):
            try:
                url = f"{base_url}?page={page}"
                logger.info(f"Scraping page {page}: {url}")

                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")

                # Find track listings (adjust selectors based on actual site)
                tracks = soup.find_all("div", class_="track-item")

                if not tracks:
                    logger.warning(f"No tracks found on page {page}")
                    break

                for track_elem in tracks:
                    try:
                        title_elem = track_elem.find("h3") or track_elem.find(
                            "a"
                        )
                        artist_elem = track_elem.find("span", class_="artist")

                        if title_elem and artist_elem:
                            title = title_elem.get_text(strip=True)
                            artist = artist_elem.get_text(strip=True)
                            genre = "Classical"

                            self._add_track(
                                title=title,
                                artist_name=artist,
                                genre=genre,
                                source="musopen",
                            )
                    except Exception as e:
                        logger.warning(f"Error parsing track: {e}")
                        continue

                # Rate limiting
                time.sleep(
                    self.config.get("scraper", {}).get("delay", 2)
                )

            except requests.RequestException as e:
                logger.error(f"Error scraping page {page}: {e}")
                continue

    def _scrape_freesound(self, query: str = "music", max_results: int = 50) -> None:
        """Scrape music from Freesound (public domain sounds).

        Args:
            query: Search query.
            max_results: Maximum number of results to scrape.
        """
        # Note: Freesound requires API key for proper access
        # This is a simplified example that would need API integration
        logger.info(f"Scraping Freesound for '{query}' (max {max_results} results)")

        # In a real implementation, you would use the Freesound API
        # For now, this is a placeholder that demonstrates the structure
        logger.warning(
            "Freesound scraping requires API key. "
            "Please configure API credentials in config."
        )

    def scrape_sources(self) -> None:
        """Scrape music from all configured sources."""
        sources = self.config.get("sources", {})

        if sources.get("musopen", {}).get("enabled", False):
            max_pages = sources.get("musopen", {}).get("max_pages", 5)
            self._scrape_musopen(max_pages=max_pages)

        if sources.get("freesound", {}).get("enabled", False):
            query = sources.get("freesound", {}).get("query", "music")
            max_results = sources.get("freesound", {}).get("max_results", 50)
            self._scrape_freesound(query=query, max_results=max_results)

        logger.info("Scraping completed")

    def _generate_recommendations(self) -> None:
        """Generate music recommendations based on genres and artists."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Get all tracks with their genres and artists
        cursor.execute(
            """
            SELECT t.id, t.title, t.genre, a.name as artist_name
            FROM tracks t
            JOIN artists a ON t.artist_id = a.id
        """
        )
        tracks = cursor.fetchall()

        logger.info(f"Generating recommendations for {len(tracks)} tracks")

        # Generate recommendations based on genre and artist similarity
        for track_id, title, genre, artist_name in tracks:
            # Find similar tracks (same genre or same artist)
            cursor.execute(
                """
                SELECT t.id, t.title, t.genre, a.name as artist_name
                FROM tracks t
                JOIN artists a ON t.artist_id = a.id
                WHERE t.id != ? AND (t.genre = ? OR a.name = ?)
                LIMIT 5
            """,
                (track_id, genre, artist_name),
            )
            similar_tracks = cursor.fetchall()

            for rec_track_id, rec_title, rec_genre, rec_artist in similar_tracks:
                # Calculate similarity score
                score = 0.5
                if rec_genre == genre:
                    score += 0.3
                if rec_artist == artist_name:
                    score += 0.2

                reason = f"Similar genre: {genre}" if rec_genre == genre else ""
                if rec_artist == artist_name:
                    reason += f" Same artist: {artist_name}"

                # Check if recommendation already exists
                cursor.execute(
                    """
                    SELECT id FROM recommendations
                    WHERE track_id = ? AND recommended_track_id = ?
                """,
                    (track_id, rec_track_id),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        """
                        INSERT INTO recommendations
                        (track_id, recommended_track_id, similarity_score, reason)
                        VALUES (?, ?, ?, ?)
                    """,
                        (track_id, rec_track_id, score, reason),
                    )

        conn.commit()
        conn.close()
        logger.info("Recommendations generated")

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with statistics.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM artists")
        artist_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tracks")
        track_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM genres")
        genre_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM recommendations")
        recommendation_count = cursor.fetchone()[0]

        conn.close()

        return {
            "artists": artist_count,
            "tracks": track_count,
            "genres": genre_count,
            "recommendations": recommendation_count,
        }

    def get_recommendations(
        self, track_title: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get music recommendations.

        Args:
            track_title: Optional track title to get recommendations for.
            limit: Maximum number of recommendations to return.

        Returns:
            List of recommendation dictionaries.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        if track_title:
            cursor.execute(
                """
                SELECT r.similarity_score, r.reason,
                       t1.title as track_title, a1.name as artist_name,
                       t2.title as recommended_title, a2.name as recommended_artist
                FROM recommendations r
                JOIN tracks t1 ON r.track_id = t1.id
                JOIN artists a1 ON t1.artist_id = a1.id
                JOIN tracks t2 ON r.recommended_track_id = t2.id
                JOIN artists a2 ON t2.artist_id = a2.id
                WHERE t1.title LIKE ?
                ORDER BY r.similarity_score DESC
                LIMIT ?
            """,
                (f"%{track_title}%", limit),
            )
        else:
            cursor.execute(
                """
                SELECT r.similarity_score, r.reason,
                       t1.title as track_title, a1.name as artist_name,
                       t2.title as recommended_title, a2.name as recommended_artist
                FROM recommendations r
                JOIN tracks t1 ON r.track_id = t1.id
                JOIN artists a1 ON t1.artist_id = a1.id
                JOIN tracks t2 ON r.recommended_track_id = t2.id
                JOIN artists a2 ON t2.artist_id = a2.id
                ORDER BY r.similarity_score DESC
                LIMIT ?
            """,
                (limit,),
            )

        results = cursor.fetchall()
        conn.close()

        recommendations = []
        for row in results:
            recommendations.append(
                {
                    "similarity_score": row[0],
                    "reason": row[1],
                    "track": f"{row[2]} by {row[3]}",
                    "recommended": f"{row[4]} by {row[5]}",
                }
            )

        return recommendations

    def export_data(self, output_path: Optional[str] = None) -> str:
        """Export database data to JSON.

        Args:
            output_path: Optional path to save JSON file.

        Returns:
            Path to saved JSON file.
        """
        default_output = "music_database_export.json"
        output_file = output_path or default_output

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Export artists
        cursor.execute("SELECT name, genre, bio FROM artists")
        artists = [
            {"name": row[0], "genre": row[1], "bio": row[2]}
            for row in cursor.fetchall()
        ]

        # Export tracks
        cursor.execute(
            """
            SELECT t.title, a.name as artist, t.genre, t.duration, t.source
            FROM tracks t
            JOIN artists a ON t.artist_id = a.id
        """
        )
        tracks = [
            {
                "title": row[0],
                "artist": row[1],
                "genre": row[2],
                "duration": row[3],
                "source": row[4],
            }
            for row in cursor.fetchall()
        ]

        # Export genres
        cursor.execute("SELECT name, description FROM genres")
        genres = [
            {"name": row[0], "description": row[1]}
            for row in cursor.fetchall()
        ]

        conn.close()

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "artists": artists,
            "tracks": tracks,
            "genres": genres,
        }

        output_path_obj = Path(output_file)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path_obj, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Data exported to {output_file}")
        return output_file


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape public domain music and create discovery database"
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
        help="Scrape music from configured sources",
    )
    parser.add_argument(
        "-r",
        "--recommendations",
        action="store_true",
        help="Generate recommendations",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics",
    )
    parser.add_argument(
        "--recommend",
        help="Get recommendations for a track title",
    )
    parser.add_argument(
        "-e",
        "--export",
        help="Export data to JSON file",
    )

    args = parser.parse_args()

    try:
        db = MusicDiscoveryDatabase(config_path=args.config)

        if args.scrape:
            db.scrape_sources()

        if args.recommendations:
            db._generate_recommendations()

        if args.stats:
            stats = db.get_statistics()
            print("\nDatabase Statistics:")
            print(f"  Artists: {stats['artists']}")
            print(f"  Tracks: {stats['tracks']}")
            print(f"  Genres: {stats['genres']}")
            print(f"  Recommendations: {stats['recommendations']}")

        if args.recommend:
            recommendations = db.get_recommendations(track_title=args.recommend)
            print(f"\nRecommendations for '{args.recommend}':")
            for rec in recommendations:
                print(f"  {rec['recommended']} (score: {rec['similarity_score']:.2f})")
                print(f"    Reason: {rec['reason']}")

        if args.export:
            db.export_data(output_path=args.export)
            print(f"\nData exported to {args.export}")

        if not any([args.scrape, args.recommendations, args.stats, args.recommend, args.export]):
            print("Use --help to see available options")
            print("Example: python src/main.py --scrape --recommendations --stats")

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
