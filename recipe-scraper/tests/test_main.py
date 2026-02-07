"""Unit tests for Recipe Scraper."""

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import RecipeDatabase, RecipeScraper


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def db_file(temp_dir):
    """Create a temporary database file."""
    return temp_dir / "test_recipes.db"


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file."""
    config = {
        "database_path": str(temp_dir / "test_recipes.db"),
        "user_agent": "Test Agent",
        "request_timeout": 30,
        "rate_limiting": {"delay_seconds": 0.1},
        "recipe_sites": [],
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


def test_recipe_database_initialization(db_file):
    """Test RecipeDatabase initialization."""
    db = RecipeDatabase(db_file)
    assert db.db_path == db_file
    assert db_file.exists()


def test_add_recipe(db_file):
    """Test adding a recipe to database."""
    db = RecipeDatabase(db_file)

    recipe_id = db.add_recipe(
        title="Test Recipe",
        ingredients=["chicken", "salt", "pepper"],
        instructions="Cook the chicken",
        cuisine_type="American",
        cooking_time=30,
        servings=4,
    )

    assert recipe_id is not None
    assert recipe_id > 0


def test_add_duplicate_recipe(db_file):
    """Test adding duplicate recipe."""
    db = RecipeDatabase(db_file)

    db.add_recipe(
        title="Test Recipe",
        ingredients=["chicken"],
        instructions="Cook",
        source_url="http://test.com/recipe",
    )

    recipe_id = db.add_recipe(
        title="Test Recipe",
        ingredients=["chicken"],
        instructions="Cook",
        source_url="http://test.com/recipe",
    )

    assert recipe_id is None  # Duplicate should return None


def test_search_by_ingredients_any(db_file):
    """Test searching recipes by ingredients (match any)."""
    db = RecipeDatabase(db_file)

    db.add_recipe(
        title="Chicken Recipe",
        ingredients=["chicken", "salt", "pepper"],
        instructions="Cook chicken",
    )

    db.add_recipe(
        title="Beef Recipe",
        ingredients=["beef", "salt"],
        instructions="Cook beef",
    )

    recipes = db.search_by_ingredients(["chicken", "beef"], match_all=False)

    assert len(recipes) == 2  # Both recipes match


def test_search_by_ingredients_all(db_file):
    """Test searching recipes by ingredients (match all)."""
    db = RecipeDatabase(db_file)

    db.add_recipe(
        title="Chicken Recipe",
        ingredients=["chicken", "salt", "pepper"],
        instructions="Cook chicken",
    )

    db.add_recipe(
        title="Beef Recipe",
        ingredients=["beef", "salt"],
        instructions="Cook beef",
    )

    recipes = db.search_by_ingredients(["chicken", "salt"], match_all=True)

    assert len(recipes) == 1  # Only chicken recipe has both


def test_search_by_cuisine(db_file):
    """Test searching recipes by cuisine type."""
    db = RecipeDatabase(db_file)

    db.add_recipe(
        title="Italian Pasta",
        ingredients=["pasta", "tomato"],
        instructions="Cook pasta",
        cuisine_type="Italian",
    )

    db.add_recipe(
        title="Mexican Tacos",
        ingredients=["tortilla", "beef"],
        instructions="Make tacos",
        cuisine_type="Mexican",
    )

    recipes = db.search_by_cuisine("Italian")

    assert len(recipes) == 1
    assert recipes[0]["title"] == "Italian Pasta"


def test_search_by_cooking_time(db_file):
    """Test searching recipes by cooking time."""
    db = RecipeDatabase(db_file)

    db.add_recipe(
        title="Quick Recipe",
        ingredients=["chicken"],
        instructions="Cook quickly",
        cooking_time=15,
    )

    db.add_recipe(
        title="Slow Recipe",
        ingredients=["beef"],
        instructions="Cook slowly",
        cooking_time=120,
    )

    recipes = db.search_by_cooking_time(max_time=30)

    assert len(recipes) == 1
    assert recipes[0]["title"] == "Quick Recipe"


def test_parse_time():
    """Test time parsing."""
    scraper = RecipeScraper.__new__(RecipeScraper)
    scraper.config = {}

    assert scraper._parse_time("30 minutes") == 30
    assert scraper._parse_time("1 hour") == 60
    assert scraper._parse_time("1 hour 30 minutes") == 90
    assert scraper._parse_time("45 min") == 45


def test_parse_servings():
    """Test servings parsing."""
    scraper = RecipeScraper.__new__(RecipeScraper)
    scraper.config = {}

    assert scraper._parse_servings("4 servings") == 4
    assert scraper._parse_servings("Serves 6") == 6
    assert scraper._parse_servings("8") == 8


@patch("src.main.requests.Session")
def test_fetch_page_success(mock_session, config_file):
    """Test successful page fetch."""
    mock_response = Mock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.raise_for_status = Mock()
    mock_session.return_value.get.return_value = mock_response

    scraper = RecipeScraper(config_path=config_file)
    scraper.session = mock_session.return_value

    soup = scraper._fetch_page("https://example.com")

    assert soup is not None


def test_extract_recipe_data(config_file):
    """Test recipe data extraction."""
    from bs4 import BeautifulSoup

    scraper = RecipeScraper(config_path=config_file)

    html = """
    <html>
        <body>
            <h1 class="recipe-title">Chocolate Cake</h1>
            <div class="ingredient-item">2 cups flour</div>
            <div class="ingredient-item">1 cup sugar</div>
            <div class="instruction-step">Mix ingredients</div>
        </body>
    </html>
    """

    soup = BeautifulSoup(html, "html.parser")
    recipe_site = {
        "base_url": "https://example.com",
        "selectors": {
            "title": "h1.recipe-title",
            "ingredients": ".ingredient-item",
            "instructions": ".instruction-step",
        },
    }

    recipe_data = scraper._extract_recipe_data(soup, recipe_site)

    assert recipe_data is not None
    assert recipe_data["title"] == "Chocolate Cake"
    assert len(recipe_data["ingredients"]) == 2


def test_get_all_recipes(db_file):
    """Test getting all recipes."""
    db = RecipeDatabase(db_file)

    db.add_recipe(
        title="Recipe 1",
        ingredients=["ingredient1"],
        instructions="Instructions 1",
    )

    db.add_recipe(
        title="Recipe 2",
        ingredients=["ingredient2"],
        instructions="Instructions 2",
    )

    recipes = db.get_all_recipes()

    assert len(recipes) == 2
