"""Recipe Scraper - Scrape recipes from websites and store in local database.

This module provides functionality to scrape recipes from recipe websites,
save them to a local SQLite database, and search by ingredients, cuisine
type, or cooking time. Includes comprehensive logging and error handling.
"""

import logging
import logging.handlers
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RecipeDatabase:
    """Manages recipe database operations."""

    def __init__(self, db_path: Path) -> None:
        """Initialize RecipeDatabase.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                instructions TEXT NOT NULL,
                cuisine_type TEXT,
                cooking_time INTEGER,
                prep_time INTEGER,
                servings INTEGER,
                source_url TEXT,
                source_name TEXT,
                scraped_date TEXT,
                UNIQUE(title, source_url)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                ingredient TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                UNIQUE(recipe_id, ingredient)
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cuisine ON recipes(cuisine_type)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cooking_time ON recipes(cooking_time)
            """
        )

        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")

    def add_recipe(
        self,
        title: str,
        ingredients: List[str],
        instructions: str,
        cuisine_type: Optional[str] = None,
        cooking_time: Optional[int] = None,
        prep_time: Optional[int] = None,
        servings: Optional[int] = None,
        source_url: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> Optional[int]:
        """Add a recipe to the database.

        Args:
            title: Recipe title.
            ingredients: List of ingredients.
            instructions: Recipe instructions.
            cuisine_type: Type of cuisine.
            cooking_time: Cooking time in minutes.
            prep_time: Preparation time in minutes.
            servings: Number of servings.
            source_url: URL where recipe was scraped from.
            source_name: Name of recipe website.

        Returns:
            Recipe ID if successful, None if duplicate or error.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if recipe already exists
            cursor.execute(
                "SELECT id FROM recipes WHERE title = ? AND source_url = ?",
                (title, source_url),
            )
            existing = cursor.fetchone()
            if existing:
                conn.close()
                logger.debug(f"Recipe already exists: {title}")
                return None

            # Insert recipe
            ingredients_text = "\n".join(ingredients)
            scraped_date = datetime.now().isoformat()

            cursor.execute(
                """
                INSERT INTO recipes (
                    title, ingredients, instructions, cuisine_type,
                    cooking_time, prep_time, servings, source_url,
                    source_name, scraped_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    ingredients_text,
                    instructions,
                    cuisine_type,
                    cooking_time,
                    prep_time,
                    servings,
                    source_url,
                    source_name,
                    scraped_date,
                ),
            )

            recipe_id = cursor.lastrowid

            # Insert ingredients
            for ingredient in ingredients:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO recipe_ingredients
                    (recipe_id, ingredient) VALUES (?, ?)
                    """,
                    (recipe_id, ingredient.strip()),
                )

            conn.commit()
            conn.close()

            logger.info(f"Added recipe: {title} (ID: {recipe_id})")
            return recipe_id

        except sqlite3.Error as e:
            logger.error(f"Database error adding recipe: {e}")
            return None

    def search_by_ingredients(
        self, ingredients: List[str], match_all: bool = False
    ) -> List[Dict]:
        """Search recipes by ingredients.

        Args:
            ingredients: List of ingredients to search for.
            match_all: If True, recipe must contain all ingredients.
                      If False, recipe must contain any ingredient.

        Returns:
            List of recipe dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if match_all:
                # Recipe must contain all ingredients
                placeholders = ",".join("?" * len(ingredients))
                query = f"""
                    SELECT DISTINCT r.* FROM recipes r
                    INNER JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                    WHERE LOWER(ri.ingredient) IN ({placeholders})
                    GROUP BY r.id
                    HAVING COUNT(DISTINCT ri.ingredient) = ?
                """
                params = [ing.lower() for ing in ingredients] + [len(ingredients)]
            else:
                # Recipe must contain any ingredient
                placeholders = ",".join("?" * len(ingredients))
                query = f"""
                    SELECT DISTINCT r.* FROM recipes r
                    INNER JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                    WHERE LOWER(ri.ingredient) IN ({placeholders})
                """
                params = [ing.lower() for ing in ingredients]

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            recipes = [dict(row) for row in rows]
            logger.info(f"Found {len(recipes)} recipes matching ingredients")
            return recipes

        except sqlite3.Error as e:
            logger.error(f"Database error searching by ingredients: {e}")
            return []

    def search_by_cuisine(self, cuisine_type: str) -> List[Dict]:
        """Search recipes by cuisine type.

        Args:
            cuisine_type: Type of cuisine to search for.

        Returns:
            List of recipe dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM recipes WHERE LOWER(cuisine_type) = LOWER(?)",
                (cuisine_type,),
            )
            rows = cursor.fetchall()
            conn.close()

            recipes = [dict(row) for row in rows]
            logger.info(f"Found {len(recipes)} recipes for cuisine: {cuisine_type}")
            return recipes

        except sqlite3.Error as e:
            logger.error(f"Database error searching by cuisine: {e}")
            return []

    def search_by_cooking_time(
        self, max_time: Optional[int] = None, min_time: Optional[int] = None
    ) -> List[Dict]:
        """Search recipes by cooking time.

        Args:
            max_time: Maximum cooking time in minutes.
            min_time: Minimum cooking time in minutes.

        Returns:
            List of recipe dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if max_time is not None and min_time is not None:
                cursor.execute(
                    "SELECT * FROM recipes WHERE cooking_time BETWEEN ? AND ?",
                    (min_time, max_time),
                )
            elif max_time is not None:
                cursor.execute(
                    "SELECT * FROM recipes WHERE cooking_time <= ?", (max_time,)
                )
            elif min_time is not None:
                cursor.execute(
                    "SELECT * FROM recipes WHERE cooking_time >= ?", (min_time,)
                )
            else:
                cursor.execute("SELECT * FROM recipes WHERE cooking_time IS NOT NULL")

            rows = cursor.fetchall()
            conn.close()

            recipes = [dict(row) for row in rows]
            logger.info(f"Found {len(recipes)} recipes matching cooking time")
            return recipes

        except sqlite3.Error as e:
            logger.error(f"Database error searching by cooking time: {e}")
            return []

    def get_all_recipes(self) -> List[Dict]:
        """Get all recipes from database.

        Returns:
            List of all recipe dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM recipes")
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Database error getting all recipes: {e}")
            return []


class RecipeScraper:
    """Scrapes recipes from recipe websites."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize RecipeScraper with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_database()
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
        self.stats = {
            "recipes_scraped": 0,
            "recipes_saved": 0,
            "errors": 0,
            "errors_list": [],
        }

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
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

        if os.getenv("DATABASE_PATH"):
            config["database_path"] = os.getenv("DATABASE_PATH")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/recipe_scraper.log")

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

    def _setup_database(self) -> None:
        """Set up database connection."""
        db_path = self.config.get("database_path", "data/recipes.db")
        db_file = Path(db_path)
        if not db_file.is_absolute():
            project_root = Path(__file__).parent.parent
            db_file = project_root / db_path

        self.database = RecipeDatabase(db_file)
        logger.info(f"Database path: {db_file}")

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        try:
            delay = self.config.get("rate_limiting", {}).get("delay_seconds", 1)
            time.sleep(delay)

            response = self.session.get(
                url, timeout=self.config.get("request_timeout", 30)
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            logger.debug(f"Fetched page: {url}")
            return soup

        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching {url}: {e}"
            logger.warning(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return None

    def _extract_recipe_data(
        self, soup: BeautifulSoup, recipe_site: Dict[str, str]
    ) -> Optional[Dict]:
        """Extract recipe data from parsed HTML."""
        selectors = recipe_site.get("selectors", {})
        base_url = recipe_site.get("base_url", "")

        recipe_data = {
            "title": "",
            "ingredients": [],
            "instructions": "",
            "cuisine_type": None,
            "cooking_time": None,
            "prep_time": None,
            "servings": None,
        }

        # Extract title
        title_selector = selectors.get("title", "")
        if title_selector:
            title_elem = soup.select_one(title_selector)
            if title_elem:
                recipe_data["title"] = title_elem.get_text(strip=True)

        # Extract ingredients
        ingredients_selector = selectors.get("ingredients", "")
        if ingredients_selector:
            ingredient_elems = soup.select(ingredients_selector)
            recipe_data["ingredients"] = [
                elem.get_text(strip=True) for elem in ingredient_elems
            ]

        # Extract instructions
        instructions_selector = selectors.get("instructions", "")
        if instructions_selector:
            instruction_elems = soup.select(instructions_selector)
            instructions = [
                elem.get_text(strip=True) for elem in instruction_elems
            ]
            recipe_data["instructions"] = "\n".join(instructions)

        # Extract cuisine type
        cuisine_selector = selectors.get("cuisine_type", "")
        if cuisine_selector:
            cuisine_elem = soup.select_one(cuisine_selector)
            if cuisine_elem:
                recipe_data["cuisine_type"] = cuisine_elem.get_text(strip=True)

        # Extract cooking time
        cooking_time_selector = selectors.get("cooking_time", "")
        if cooking_time_selector:
            time_elem = soup.select_one(cooking_time_selector)
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                recipe_data["cooking_time"] = self._parse_time(time_text)

        # Extract prep time
        prep_time_selector = selectors.get("prep_time", "")
        if prep_time_selector:
            prep_elem = soup.select_one(prep_time_selector)
            if prep_elem:
                prep_text = prep_elem.get_text(strip=True)
                recipe_data["prep_time"] = self._parse_time(prep_text)

        # Extract servings
        servings_selector = selectors.get("servings", "")
        if servings_selector:
            servings_elem = soup.select_one(servings_selector)
            if servings_elem:
                servings_text = servings_elem.get_text(strip=True)
                recipe_data["servings"] = self._parse_servings(servings_text)

        # Validate required fields
        if not recipe_data["title"] or not recipe_data["ingredients"]:
            return None

        return recipe_data

    def _parse_time(self, time_text: str) -> Optional[int]:
        """Parse time text to minutes.

        Args:
            time_text: Time string (e.g., "30 minutes", "1 hour 15 min").

        Returns:
            Time in minutes, or None if parsing fails.
        """
        time_text = time_text.lower()

        # Extract hours
        hours_match = re.search(r"(\d+)\s*h(?:our)?s?", time_text)
        hours = int(hours_match.group(1)) if hours_match else 0

        # Extract minutes
        minutes_match = re.search(r"(\d+)\s*m(?:in)?(?:ute)?s?", time_text)
        minutes = int(minutes_match.group(1)) if minutes_match else 0

        total_minutes = hours * 60 + minutes
        return total_minutes if total_minutes > 0 else None

    def _parse_servings(self, servings_text: str) -> Optional[int]:
        """Parse servings text to integer.

        Args:
            servings_text: Servings string (e.g., "4 servings", "Serves 6").

        Returns:
            Number of servings, or None if parsing fails.
        """
        import re

        match = re.search(r"(\d+)", servings_text)
        if match:
            return int(match.group(1))
        return None

    def _scrape_recipe_site(self, recipe_site: Dict[str, str]) -> int:
        """Scrape recipes from a recipe website.

        Args:
            recipe_site: Recipe site configuration.

        Returns:
            Number of recipes scraped.
        """
        site_name = recipe_site.get("name", "Unknown")
        base_url = recipe_site.get("base_url", "")
        recipe_urls = recipe_site.get("recipe_urls", [])

        logger.info(f"Scraping recipes from: {site_name}")

        recipes_scraped = 0

        for recipe_url in recipe_urls:
            full_url = urljoin(base_url, recipe_url) if not recipe_url.startswith(
                "http"
            ) else recipe_url

            logger.info(f"Scraping recipe: {full_url}")

            soup = self._fetch_page(full_url)
            if not soup:
                continue

            recipe_data = self._extract_recipe_data(soup, recipe_site)
            if not recipe_data:
                logger.warning(f"Could not extract recipe data from {full_url}")
                continue

            # Save to database
            recipe_id = self.database.add_recipe(
                title=recipe_data["title"],
                ingredients=recipe_data["ingredients"],
                instructions=recipe_data["instructions"],
                cuisine_type=recipe_data["cuisine_type"],
                cooking_time=recipe_data["cooking_time"],
                prep_time=recipe_data["prep_time"],
                servings=recipe_data["servings"],
                source_url=full_url,
                source_name=site_name,
            )

            if recipe_id:
                recipes_scraped += 1
                self.stats["recipes_saved"] += 1

            self.stats["recipes_scraped"] += 1

        logger.info(f"Scraped {recipes_scraped} recipes from {site_name}")
        return recipes_scraped

    def scrape_recipes(self) -> Dict[str, any]:
        """Scrape recipes from all configured sites.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting recipe scraping")
        recipe_sites = self.config.get("recipe_sites", [])

        if not recipe_sites:
            logger.warning("No recipe sites configured")
            return self.stats

        for recipe_site in recipe_sites:
            try:
                self._scrape_recipe_site(recipe_site)
            except Exception as e:
                error_msg = f"Error scraping {recipe_site.get('name', 'Unknown')}: {e}"
                logger.error(error_msg, exc_info=True)
                self.stats["errors"] += 1
                self.stats["errors_list"].append(error_msg)

        logger.info("Recipe scraping completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for recipe scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape recipes from websites and search local database"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Scrape recipes from configured websites",
    )
    parser.add_argument(
        "--search-ingredients",
        nargs="+",
        help="Search recipes by ingredients",
    )
    parser.add_argument(
        "--search-cuisine",
        help="Search recipes by cuisine type",
    )
    parser.add_argument(
        "--search-time",
        type=int,
        help="Search recipes by maximum cooking time (minutes)",
    )
    parser.add_argument(
        "--match-all",
        action="store_true",
        help="When searching by ingredients, match all ingredients (default: any)",
    )
    parser.add_argument(
        "--list-all",
        action="store_true",
        help="List all recipes in database",
    )

    args = parser.parse_args()

    try:
        scraper = RecipeScraper(config_path=args.config)

        # Scrape recipes if requested
        if args.scrape:
            stats = scraper.scrape_recipes()
            print("\n" + "=" * 60)
            print("Recipe Scraping Summary")
            print("=" * 60)
            print(f"Recipes Scraped: {stats['recipes_scraped']}")
            print(f"Recipes Saved: {stats['recipes_saved']}")
            print(f"Errors: {stats['errors']}")

        # Search by ingredients
        if args.search_ingredients:
            recipes = scraper.database.search_by_ingredients(
                args.search_ingredients, match_all=args.match_all
            )
            print(f"\nFound {len(recipes)} recipes:")
            for recipe in recipes:
                print(f"  - {recipe['title']} ({recipe.get('cuisine_type', 'N/A')})")

        # Search by cuisine
        if args.search_cuisine:
            recipes = scraper.database.search_by_cuisine(args.search_cuisine)
            print(f"\nFound {len(recipes)} {args.search_cuisine} recipes:")
            for recipe in recipes:
                print(f"  - {recipe['title']}")

        # Search by cooking time
        if args.search_time:
            recipes = scraper.database.search_by_cooking_time(max_time=args.search_time)
            print(f"\nFound {len(recipes)} recipes with cooking time <= {args.search_time} minutes:")
            for recipe in recipes:
                print(
                    f"  - {recipe['title']} "
                    f"({recipe.get('cooking_time', 'N/A')} min)"
                )

        # List all recipes
        if args.list_all:
            recipes = scraper.database.get_all_recipes()
            print(f"\nTotal recipes in database: {len(recipes)}")
            for recipe in recipes:
                print(f"  - {recipe['title']} ({recipe.get('source_name', 'Unknown')})")

        # If no action specified, show help
        if not any(
            [
                args.scrape,
                args.search_ingredients,
                args.search_cuisine,
                args.search_time,
                args.list_all,
            ]
        ):
            parser.print_help()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
