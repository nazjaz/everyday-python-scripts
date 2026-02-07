# Recipe Scraper

Scrape recipes from recipe websites and save them to a local SQLite database. Search recipes by ingredients, cuisine type, or cooking time. Perfect for building a personal recipe collection and finding recipes based on available ingredients or dietary preferences.

## Project Description

Recipe Scraper solves the problem of managing recipes from multiple sources by automatically scraping recipe websites, storing them in a local database, and providing powerful search capabilities. Users can find recipes based on ingredients they have, cuisine preferences, or time constraints. Ideal for meal planning, cooking enthusiasts, and anyone building a personal recipe collection.

**Target Audience**: Cooking enthusiasts, meal planners, and anyone who wants to build and search a personal recipe database from multiple online sources.

## Features

- **Web Scraping**: Scrape recipes from multiple recipe websites
- **Local Database**: Store recipes in SQLite database for offline access
- **Ingredient Search**: Search recipes by ingredients (match any or all)
- **Cuisine Search**: Find recipes by cuisine type
- **Cooking Time Search**: Filter recipes by maximum cooking time
- **Configurable Selectors**: Customize CSS selectors for different recipe sites
- **Rate Limiting**: Respectful scraping with configurable delays
- **Duplicate Detection**: Prevents saving duplicate recipes
- **Comprehensive Logging**: Detailed logs of all operations
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for web scraping
- Understanding of CSS selectors for configuring recipe site selectors

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/recipe-scraper
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Settings

Edit `config.yaml` to configure recipe websites and selectors:

```yaml
recipe_sites:
  - name: "Example Recipe Site"
    base_url: "https://example-recipes.com"
    recipe_urls:
      - "/recipe/chocolate-cake"
    selectors:
      title: "h1.recipe-title"
      ingredients: ".ingredient-item"
      instructions: ".instruction-step"
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **database_path**: Path to SQLite database file (default: `data/recipes.db`)
- **recipe_sites**: List of recipe website configurations
  - **name**: Display name for the site
  - **base_url**: Base URL of the recipe website
  - **recipe_urls**: List of recipe page URLs to scrape
  - **selectors**: CSS selectors for extracting recipe data
- **rate_limiting**: Delay between requests
- **logging**: Log file location and rotation settings

### Recipe Selectors

Each recipe site requires CSS selectors to extract recipe information:

- **title**: Selector for recipe title
- **ingredients**: Selector for each ingredient (returns list)
- **instructions**: Selector for each instruction step (returns list)
- **cuisine_type**: Selector for cuisine type (optional)
- **cooking_time**: Selector for cooking time (optional)
- **prep_time**: Selector for preparation time (optional)
- **servings**: Selector for number of servings (optional)

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_PATH`: Override database file path

### Example Configuration

```yaml
database_path: data/recipes.db

recipe_sites:
  - name: "AllRecipes"
    base_url: "https://www.allrecipes.com"
    recipe_urls:
      - "/recipe/12345/chocolate-cake"
      - "/recipe/67890/pasta-carbonara"
    selectors:
      title: "h1.headline"
      ingredients: ".ingredients-item-name"
      instructions: ".instructions-section-item"
      cuisine_type: ".cuisine-type"
      cooking_time: ".recipe-meta-item .time"
      servings: ".servings-count"
```

## Usage

### Scrape Recipes

Scrape recipes from configured websites:

```bash
python src/main.py --scrape
```

### Search by Ingredients

Search recipes containing specific ingredients:

```bash
# Find recipes with any of these ingredients
python src/main.py --search-ingredients chicken tomato onion

# Find recipes with all of these ingredients
python src/main.py --search-ingredients chicken tomato --match-all
```

### Search by Cuisine

Find recipes by cuisine type:

```bash
python src/main.py --search-cuisine Italian
python src/main.py --search-cuisine Mexican
```

### Search by Cooking Time

Find recipes with cooking time under specified minutes:

```bash
python src/main.py --search-time 30
```

### List All Recipes

List all recipes in database:

```bash
python src/main.py --list-all
```

### Combine Operations

```bash
# Scrape and then search
python src/main.py --scrape --search-ingredients chicken
```

## Project Structure

```
recipe-scraper/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py         # Package initialization
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── data/
│   └── recipes.db          # SQLite database (created automatically)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core scraping logic, database operations, and search functionality
- **config.yaml**: YAML configuration file with recipe sites and selectors
- **data/recipes.db**: SQLite database storing all recipes
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Database Schema

The SQLite database contains two main tables:

**recipes**:
- id (primary key)
- title
- ingredients (text, newline-separated)
- instructions (text)
- cuisine_type
- cooking_time (minutes)
- prep_time (minutes)
- servings
- source_url
- source_name
- scraped_date

**recipe_ingredients**:
- id (primary key)
- recipe_id (foreign key)
- ingredient (indexed for fast searching)

## Finding CSS Selectors

To configure selectors for a recipe website:

1. Open the recipe page in a web browser
2. Right-click on the element you want to extract
3. Select "Inspect" or "Inspect Element"
4. Note the CSS selector or class/id of the element
5. Update `config.yaml` with the selector

Example: If recipe title is in `<h1 class="recipe-title">`, use selector: `h1.recipe-title`

## Search Examples

### Find Quick Recipes

```bash
# Recipes that take 30 minutes or less
python src/main.py --search-time 30
```

### Find Recipes with Available Ingredients

```bash
# Recipes using chicken and vegetables
python src/main.py --search-ingredients chicken vegetables --match-all
```

### Find Cuisine-Specific Recipes

```bash
# All Italian recipes
python src/main.py --search-cuisine Italian
```

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Database operations (add, search)
- Recipe data extraction
- Time and servings parsing
- Search functionality
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Configuration file not found`

**Solution**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option.

---

**Issue**: No recipes found or incorrect data extracted

**Solution**:
- Verify CSS selectors in `config.yaml` are correct for the recipe site
- Use browser developer tools to inspect HTML structure
- Check that recipe site HTML structure hasn't changed
- Enable DEBUG logging to see detailed extraction process

---

**Issue**: `ConnectionError` or timeout errors

**Solution**:
- Check internet connection
- Increase `request_timeout` in `config.yaml`
- Increase `delay_seconds` in rate_limiting to be more respectful
- Some recipe sites may block automated requests

---

**Issue**: Recipes not saving

**Solution**:
- Check database file permissions (ensure write access)
- Review logs for specific error messages
- Verify recipe data is being extracted correctly

---

**Issue**: Search not finding recipes

**Solution**:
- Verify recipes are in database (use `--list-all`)
- Check ingredient spelling (searches are case-insensitive)
- For ingredient search, ensure ingredients are stored correctly
- Review database schema matches expected format

### Error Messages

- **"Error fetching URL"**: Network issue or invalid URL; check internet connection and URL format
- **"Could not extract recipe data"**: HTML structure changed or selector incorrect; update selectors
- **"Database error"**: SQLite database issue; check file permissions and disk space
- **"Recipe already exists"**: Duplicate recipe detected (not an error, just logged)

## Legal and Ethical Considerations

- **Respect robots.txt**: Check recipe website's robots.txt file before scraping
- **Terms of Service**: Review and comply with each website's terms of service
- **Rate Limiting**: Use appropriate delays between requests to avoid overloading servers
- **Personal Use**: This tool is intended for personal use; commercial use may require permission
- **Data Usage**: Use scraped data responsibly and in accordance with applicable laws
- **Attribution**: Consider including source attribution when using scraped recipes

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov pytest-mock`
5. Create a feature branch: `git checkout -b feature/your-feature`

### Code Style Guidelines

- Follow PEP 8 style guide
- Maximum line length: 88 characters (Black formatter)
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Run tests before committing: `pytest tests/`

### Pull Request Process

1. Ensure all tests pass
2. Update README.md if adding new features
3. Add tests for new functionality
4. Submit pull request with clear description

## License

This project is provided as-is for educational and personal use. Users are responsible for ensuring compliance with recipe website terms of service and applicable laws.
