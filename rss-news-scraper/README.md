# RSS News Scraper

Scrape news headlines from RSS feeds, save them to a local database, categorize by topic, and generate daily summaries. This tool helps you stay informed by automatically collecting and organizing news from multiple sources.

## Project Description

RSS News Scraper solves the problem of tracking news from multiple sources by automatically scraping RSS feeds, storing headlines in a local database, categorizing them by topic using keyword matching, and generating daily summaries for easy review.

**Target Audience**: News enthusiasts, researchers, content creators, and anyone who wants to track and organize news from multiple RSS sources.

## Features

- **RSS Feed Scraping**: Scrape headlines from multiple RSS feeds simultaneously
- **Local Database Storage**: Store headlines in SQLite database for persistence
- **Topic Categorization**: Automatically categorize headlines by topic using keyword matching
- **Daily Summaries**: Generate daily summaries with category breakdowns and top headlines
- **Duplicate Detection**: Automatically skip duplicate headlines based on URL
- **Data Retention**: Automatic cleanup of old entries based on retention policy
- **Configurable Categories**: Define custom categories with keyword lists
- **Multiple Feed Support**: Process multiple RSS feeds in a single run

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for RSS feed access

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/rss-news-scraper
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

1. Copy the example environment file (if needed):
   ```bash
   cp .env.example .env
   ```

2. Edit `config.yaml` to add your RSS feeds:
   ```yaml
   rss_feeds:
     - name: "BBC News"
       url: "http://feeds.bbci.co.uk/news/rss.xml"
       category: "general"
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **rss_feeds**: List of RSS feed sources with name, URL, and default category
- **database**: SQLite database file path and table creation settings
- **categorization**: Topic categorization settings with keyword lists per category
- **daily_summary**: Daily summary generation settings
- **scraping**: Scraping interval, timeout, and item limits
- **retention**: Data retention policy for old headlines

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_FILE`: Override database file path
- `SCRAPING_INTERVAL`: Override scraping interval in seconds

### Example Configuration

```yaml
rss_feeds:
  - name: "TechCrunch"
    url: "https://techcrunch.com/feed/"
    category: "technology"

categorization:
  categories:
    technology:
      keywords: ["tech", "software", "ai", "digital"]
    science:
      keywords: ["science", "research", "study"]

daily_summary:
  enabled: true
  include_categories: true
  top_headlines_count: 5
```

## Usage

### Basic Usage

Scrape feeds and generate summary:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Scrape feeds only
python src/main.py --scrape

# Generate summary only
python src/main.py --generate-summary

# Generate summary for specific date
python src/main.py --generate-summary --date 2024-02-07

# Combine options
python src/main.py -c config.yaml --scrape --generate-summary
```

### Common Use Cases

1. **Scrape News Feeds**:
   ```bash
   python src/main.py --scrape
   ```

2. **Generate Daily Summary**:
   ```bash
   python src/main.py --generate-summary
   ```

3. **Scrape and Summarize**:
   ```bash
   python src/main.py
   ```

4. **Add Custom RSS Feeds**:
   - Edit `rss_feeds` section in `config.yaml`
   - Add feed name, URL, and default category

5. **Customize Categories**:
   - Edit `categorization.categories` in `config.yaml`
   - Add keywords for each category

## Project Structure

```
rss-news-scraper/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── data/
│   └── news_database.db    # SQLite database (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── rss_scraper.log     # Application logs
    └── daily_summary_*.txt # Daily summary files
```

### File Descriptions

- **src/main.py**: Core RSS scraping, database operations, categorization, and summary generation
- **config.yaml**: YAML configuration file with RSS feeds and settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/news_database.db**: SQLite database storing all headlines
- **logs/rss_scraper.log**: Application log file with rotation
- **logs/daily_summary_*.txt**: Daily summary text files

## Database Schema

The SQLite database contains two main tables:

### headlines
- `id`: Primary key
- `title`: Headline title
- `link`: Article URL (unique)
- `description`: Article description
- `published_date`: Original publication date
- `feed_name`: Source feed name
- `feed_url`: Source feed URL
- `category`: Assigned category
- `scraped_at`: Timestamp when scraped

### categories
- `id`: Primary key
- `name`: Category name (unique)
- `headline_count`: Number of headlines in category

## Topic Categorization

Headlines are categorized using keyword matching:

1. **Keyword Matching**: Checks headline title and description for category keywords
2. **Case Insensitive**: Matching is case-insensitive
3. **First Match**: Uses first matching category
4. **Default Category**: Unmatched headlines go to default category

### Supported Categories (Configurable)

- Technology
- Science
- Business
- Politics
- Sports
- Entertainment
- General (default)

## Daily Summary Format

Daily summaries include:

- **Date Header**: Summary date
- **Category Breakdown**: Count of headlines per category
- **Total Headlines**: Total number of headlines for the day
- **Top Headlines**: Top N headlines per category with:
  - Headline title
  - Source feed name
  - Article link

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- RSS feed parsing
- Headline categorization
- Database operations
- Daily summary generation
- Duplicate detection
- Data cleanup

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'feedparser'`

**Solution**: Install dependencies: `pip install -r requirements.txt`

---

**Issue**: RSS feed parsing errors

**Solution**: 
- Verify RSS feed URLs are correct and accessible
- Check internet connection
- Some feeds may require authentication or have rate limits
- Check feed format (should be RSS or Atom)

---

**Issue**: No headlines being saved

**Solution**: 
- Check that RSS feeds are returning entries
- Verify database file path is writable
- Check logs for parsing errors
- Ensure feed URLs are valid and accessible

---

**Issue**: Headlines not being categorized correctly

**Solution**: 
- Review keyword lists in `categorization.categories`
- Add more keywords for better matching
- Check that keywords match common terms in headlines
- Adjust keyword matching logic if needed

---

**Issue**: Database locked errors

**Solution**: 
- Ensure only one instance of scraper is running
- Check database file permissions
- Close any database viewers that might have the file open

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"No RSS feeds configured"**: Add at least one RSS feed to `rss_feeds` in config.yaml
- **"Feed parsing error"**: RSS feed URL may be invalid or inaccessible
- **"Database error"**: Check database file permissions and disk space

## RSS Feed Sources

Example RSS feed URLs you can use:

- **BBC News**: `http://feeds.bbci.co.uk/news/rss.xml`
- **Reuters**: `https://www.reuters.com/rssFeed/topNews`
- **TechCrunch**: `https://techcrunch.com/feed/`
- **Science Daily**: `https://www.sciencedaily.com/rss/all.xml`
- **CNN**: `http://rss.cnn.com/rss/edition.rss`

Note: Always respect feed providers' terms of service and rate limits.

## Automation

You can automate the scraper using cron (Linux/Mac) or Task Scheduler (Windows):

### Linux/Mac (cron)
```bash
# Run every hour
0 * * * * cd /path/to/rss-news-scraper && /path/to/venv/bin/python src/main.py --scrape

# Generate daily summary at midnight
0 0 * * * cd /path/to/rss-news-scraper && /path/to/venv/bin/python src/main.py --generate-summary
```

### Windows (Task Scheduler)
- Create a task to run `python src/main.py --scrape` on a schedule
- Set working directory to project folder
- Use full path to Python executable

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-mock pytest-cov`
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

This project is provided as-is for educational and personal use.
