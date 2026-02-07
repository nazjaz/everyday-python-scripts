"""Movie Watchlist - CLI tool for managing movie watchlist with ratings and information.

This module provides a command-line tool for scraping movie information from
public databases (OMDB API), creating a local movie watchlist, and managing
movies with ratings, genres, and release dates.
"""

import argparse
import json
import logging
import logging.handlers
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MovieScraper:
    """Scrapes movie information from OMDB API."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://www.omdbapi.com/", timeout: int = 10) -> None:
        """Initialize MovieScraper.

        Args:
            api_key: OMDB API key.
            base_url: OMDB API base URL.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.getenv("OMDB_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("OMDB API key not provided. Some features may not work.")

    def search_movie(self, title: str, year: Optional[int] = None) -> List[Dict]:
        """Search for movies by title.

        Args:
            title: Movie title to search for.
            year: Optional year to filter results.

        Returns:
            List of movie dictionaries from search results.

        Raises:
            requests.RequestException: If API request fails.
        """
        if not self.api_key:
            raise ValueError("OMDB API key is required for searching")

        params = {
            "apikey": self.api_key,
            "s": title,
            "type": "movie",
        }

        if year:
            params["y"] = year

        try:
            response = requests.get(
                f"{self.base_url}/", params=params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            if data.get("Response") == "False":
                logger.warning(f"Movie search failed: {data.get('Error', 'Unknown error')}")
                return []

            return data.get("Search", [])

        except requests.RequestException as e:
            logger.error(f"Error searching for movie '{title}': {e}")
            raise

    def get_movie_details(self, imdb_id: Optional[str] = None, title: Optional[str] = None, year: Optional[int] = None) -> Optional[Dict]:
        """Get detailed movie information.

        Args:
            imdb_id: IMDb ID of the movie.
            title: Movie title (requires year if using title).
            year: Movie release year (required if using title).

        Returns:
            Dictionary with movie details or None if not found.

        Raises:
            ValueError: If insufficient parameters provided.
            requests.RequestException: If API request fails.
        """
        if not self.api_key:
            raise ValueError("OMDB API key is required")

        params = {"apikey": self.api_key}

        if imdb_id:
            params["i"] = imdb_id
        elif title:
            params["t"] = title
            if year:
                params["y"] = year
            else:
                raise ValueError("Year is required when searching by title")
        else:
            raise ValueError("Either imdb_id or title must be provided")

        try:
            response = requests.get(
                f"{self.base_url}/", params=params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            if data.get("Response") == "False":
                logger.warning(f"Movie details not found: {data.get('Error', 'Unknown error')}")
                return None

            return data

        except requests.RequestException as e:
            logger.error(f"Error getting movie details: {e}")
            raise


class MovieWatchlist:
    """Manages local movie watchlist database."""

    def __init__(self, database_file: Path) -> None:
        """Initialize MovieWatchlist.

        Args:
            database_file: Path to SQLite database file.
        """
        self.database_file = database_file
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database and create tables."""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    imdb_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    year INTEGER,
                    rated TEXT,
                    released TEXT,
                    runtime TEXT,
                    genre TEXT,
                    director TEXT,
                    writer TEXT,
                    actors TEXT,
                    plot TEXT,
                    language TEXT,
                    country TEXT,
                    poster TEXT,
                    imdb_rating REAL,
                    metascore INTEGER,
                    rotten_tomatoes TEXT,
                    box_office TEXT,
                    added_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'to_watch',
                    watched_date TEXT,
                    user_rating INTEGER,
                    notes TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_imdb_id ON movies(imdb_id)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_status ON movies(status)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_title ON movies(title)
                """
            )

            conn.commit()
            conn.close()

            logger.info(f"Database initialized: {self.database_file}")

        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def add_movie(self, movie_data: Dict, status: str = "to_watch") -> bool:
        """Add movie to watchlist.

        Args:
            movie_data: Dictionary with movie information from API.
            status: Watchlist status (to_watch, watching, watched, dropped).

        Returns:
            True if movie added successfully, False if already exists.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            # Extract ratings
            ratings = movie_data.get("Ratings", [])
            imdb_rating = None
            metascore = None
            rotten_tomatoes = None

            for rating in ratings:
                source = rating.get("Source", "")
                value = rating.get("Value", "")
                if source == "Internet Movie Database":
                    imdb_rating = float(value.split("/")[0]) if value else None
                elif source == "Metacritic":
                    metascore = int(value.split("/")[0]) if value else None
                elif source == "Rotten Tomatoes":
                    rotten_tomatoes = value

            cursor.execute(
                """
                INSERT OR REPLACE INTO movies (
                    imdb_id, title, year, rated, released, runtime, genre,
                    director, writer, actors, plot, language, country, poster,
                    imdb_rating, metascore, rotten_tomatoes, box_office,
                    added_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    movie_data.get("imdbID"),
                    movie_data.get("Title"),
                    int(movie_data.get("Year", 0)) if movie_data.get("Year", "N/A") != "N/A" else None,
                    movie_data.get("Rated"),
                    movie_data.get("Released"),
                    movie_data.get("Runtime"),
                    movie_data.get("Genre"),
                    movie_data.get("Director"),
                    movie_data.get("Writer"),
                    movie_data.get("Actors"),
                    movie_data.get("Plot"),
                    movie_data.get("Language"),
                    movie_data.get("Country"),
                    movie_data.get("Poster"),
                    imdb_rating,
                    metascore,
                    rotten_tomatoes,
                    movie_data.get("BoxOffice"),
                    datetime.now().isoformat(),
                    status,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"Added movie to watchlist: {movie_data.get('Title')}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Movie already in watchlist: {movie_data.get('Title')}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding movie: {e}")
            raise

    def get_movies(
        self,
        status: Optional[str] = None,
        sort_by: str = "title",
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Get movies from watchlist.

        Args:
            status: Filter by status (optional).
            sort_by: Sort field (title, year, rating, added_date).
            limit: Maximum number of results (optional).

        Returns:
            List of movie dictionaries.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM movies WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            # Sort order
            sort_map = {
                "title": "title ASC",
                "year": "year DESC",
                "rating": "imdb_rating DESC",
                "added_date": "added_date DESC",
            }
            order_by = sort_map.get(sort_by, "title ASC")
            query += f" ORDER BY {order_by}"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            conn.close()

            movies = [dict(row) for row in rows]
            return movies

        except sqlite3.Error as e:
            logger.error(f"Error getting movies: {e}")
            return []

    def update_movie_status(self, imdb_id: str, status: str, user_rating: Optional[int] = None, notes: Optional[str] = None) -> bool:
        """Update movie status.

        Args:
            imdb_id: IMDb ID of the movie.
            status: New status.
            user_rating: User rating (1-10, optional).
            notes: User notes (optional).

        Returns:
            True if updated successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            watched_date = datetime.now().isoformat() if status == "watched" else None

            cursor.execute(
                """
                UPDATE movies 
                SET status = ?, watched_date = ?, user_rating = ?, notes = ?
                WHERE imdb_id = ?
                """,
                (status, watched_date, user_rating, notes, imdb_id),
            )

            if cursor.rowcount == 0:
                conn.close()
                return False

            conn.commit()
            conn.close()

            logger.info(f"Updated movie status: {imdb_id} -> {status}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error updating movie status: {e}")
            return False

    def remove_movie(self, imdb_id: str) -> bool:
        """Remove movie from watchlist.

        Args:
            imdb_id: IMDb ID of the movie.

        Returns:
            True if removed successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM movies WHERE imdb_id = ?", (imdb_id,))

            if cursor.rowcount == 0:
                conn.close()
                return False

            conn.commit()
            conn.close()

            logger.info(f"Removed movie from watchlist: {imdb_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error removing movie: {e}")
            return False


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/movie_watchlist.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Override API key from environment if available
    api_key = os.getenv("OMDB_API_KEY")
    if api_key and config.get("omdb_api"):
        config["omdb_api"]["api_key"] = api_key

    return config


def print_movie_list(movies: List[Dict], show_all_ratings: bool = True) -> None:
    """Print list of movies.

    Args:
        movies: List of movie dictionaries.
        show_all_ratings: Whether to show all rating sources.
    """
    if not movies:
        print("No movies found.")
        return

    print(f"\nFound {len(movies)} movie(s):\n")
    print("-" * 100)

    for i, movie in enumerate(movies, 1):
        title = movie.get("title", "Unknown")
        year = movie.get("year") or "N/A"
        genre = movie.get("genre", "N/A")
        status = movie.get("status", "to_watch")

        print(f"{i}. {title} ({year})")
        print(f"   Genre: {genre}")
        print(f"   Status: {status}")

        if show_all_ratings:
            ratings = []
            if movie.get("imdb_rating"):
                ratings.append(f"IMDb: {movie['imdb_rating']}/10")
            if movie.get("metascore"):
                ratings.append(f"Metacritic: {movie['metascore']}/100")
            if movie.get("rotten_tomatoes"):
                ratings.append(f"Rotten Tomatoes: {movie['rotten_tomatoes']}")

            if ratings:
                print(f"   Ratings: {', '.join(ratings)}")

        if movie.get("user_rating"):
            print(f"   Your Rating: {movie['user_rating']}/10")

        print()


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Movie Watchlist Manager")
    parser.add_argument(
        "command",
        choices=["search", "add", "list", "update", "remove", "show"],
        help="Command to execute",
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Movie title (for search, add, show)",
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Movie release year",
    )
    parser.add_argument(
        "--imdb-id",
        type=str,
        help="IMDb ID",
    )
    parser.add_argument(
        "--status",
        choices=["to_watch", "watching", "watched", "dropped"],
        help="Watchlist status",
    )
    parser.add_argument(
        "--rating",
        type=int,
        help="User rating (1-10)",
    )
    parser.add_argument(
        "--notes",
        type=str,
        help="User notes",
    )
    parser.add_argument(
        "--sort",
        choices=["title", "year", "rating", "added_date"],
        default="title",
        help="Sort order for list",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        omdb_config = config.get("omdb_api", {})
        scraper = MovieScraper(
            api_key=omdb_config.get("api_key"),
            base_url=omdb_config.get("base_url", "http://www.omdbapi.com/"),
            timeout=omdb_config.get("timeout", 10),
        )

        watchlist = MovieWatchlist(Path(config.get("database_file", "data/movie_watchlist.db")))

        if args.command == "search":
            if not args.title:
                print("Error: --title is required for search")
                sys.exit(1)

            print(f"Searching for: {args.title}")
            results = scraper.search_movie(args.title, args.year)

            if not results:
                print("No movies found.")
            else:
                print(f"\nFound {len(results)} result(s):\n")
                for i, movie in enumerate(results, 1):
                    print(f"{i}. {movie.get('Title')} ({movie.get('Year')}) - {movie.get('imdbID')}")

        elif args.command == "add":
            if not args.title and not args.imdb_id:
                print("Error: --title or --imdb-id is required for add")
                sys.exit(1)

            if args.imdb_id:
                movie_data = scraper.get_movie_details(imdb_id=args.imdb_id)
            else:
                movie_data = scraper.get_movie_details(title=args.title, year=args.year)

            if not movie_data:
                print("Error: Movie not found")
                sys.exit(1)

            status = args.status or config.get("watchlist", {}).get("default_status", "to_watch")
            success = watchlist.add_movie(movie_data, status)

            if success:
                print(f"Added: {movie_data.get('Title')} ({movie_data.get('Year')})")
            else:
                print(f"Movie already in watchlist: {movie_data.get('Title')}")

        elif args.command == "list":
            status = args.status
            movies = watchlist.get_movies(status=status, sort_by=args.sort)
            print_movie_list(movies, config.get("display", {}).get("show_all_ratings", True))

        elif args.command == "update":
            if not args.imdb_id:
                print("Error: --imdb-id is required for update")
                sys.exit(1)

            if not args.status:
                print("Error: --status is required for update")
                sys.exit(1)

            success = watchlist.update_movie_status(
                args.imdb_id, args.status, args.rating, args.notes
            )

            if success:
                print(f"Updated movie status: {args.imdb_id} -> {args.status}")
            else:
                print(f"Error: Movie not found: {args.imdb_id}")

        elif args.command == "remove":
            if not args.imdb_id:
                print("Error: --imdb-id is required for remove")
                sys.exit(1)

            success = watchlist.remove_movie(args.imdb_id)

            if success:
                print(f"Removed movie: {args.imdb_id}")
            else:
                print(f"Error: Movie not found: {args.imdb_id}")

        elif args.command == "show":
            if not args.imdb_id and not args.title:
                print("Error: --imdb-id or --title is required for show")
                sys.exit(1)

            if args.imdb_id:
                movie_data = scraper.get_movie_details(imdb_id=args.imdb_id)
            else:
                movie_data = scraper.get_movie_details(title=args.title, year=args.year)

            if not movie_data:
                print("Error: Movie not found")
                sys.exit(1)

            print(f"\n{movie_data.get('Title')} ({movie_data.get('Year')})")
            print("=" * 80)
            print(f"Genre: {movie_data.get('Genre', 'N/A')}")
            print(f"Director: {movie_data.get('Director', 'N/A')}")
            print(f"Actors: {movie_data.get('Actors', 'N/A')}")
            print(f"Released: {movie_data.get('Released', 'N/A')}")
            print(f"Runtime: {movie_data.get('Runtime', 'N/A')}")
            print(f"Rated: {movie_data.get('Rated', 'N/A')}")

            ratings = movie_data.get("Ratings", [])
            if ratings:
                print("\nRatings:")
                for rating in ratings:
                    print(f"  {rating.get('Source')}: {rating.get('Value')}")

            if config.get("watchlist", {}).get("include_plot", True):
                print(f"\nPlot: {movie_data.get('Plot', 'N/A')}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
