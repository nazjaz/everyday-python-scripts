# Scientific Paper Database

A Python automation tool that scrapes public domain scientific papers from sources like arXiv, stores them in a local SQLite database, and organizes them by subject, author, or publication date. The tool provides search capabilities to find papers based on various criteria.

## Project Title and Description

The Scientific Paper Database scrapes public domain scientific papers from legitimate sources, extracts metadata (title, authors, subject, publication date, abstract), and stores them in a searchable local database. Papers can be organized and searched by subject, author, or publication date, making it easy to build a personal research library.

This tool solves the problem of collecting and organizing scientific papers from public domain sources, providing a local, searchable database for research purposes.

**Target Audience**: Researchers, students, academics, and anyone who needs to collect and organize scientific papers for research or study.

## Features

- **Web scraping from public domain sources:**
  - arXiv (preprint server)
  - Extensible for other sources
- **Comprehensive metadata extraction:**
  - Title, authors, subject/category
  - Publication date, abstract
  - URLs and PDF links
- **SQLite database storage:** Local, searchable database
- **Organization capabilities:**
  - By subject/category
  - By author
  - By publication date
- **Search functionality:**
  - Search by title
  - Search by author
  - Filter by subject
  - Filter by date range
- **Database statistics:** Track papers, authors, and subjects
- **Duplicate detection:** Prevents adding duplicate papers
- **Rate limiting:** Respectful scraping with configurable delays

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection for web scraping

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/scientific-paper-database
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

### Step 4: Verify Installation

```bash
python src/main.py --help
```

## Configuration

### Configuration File (config.yaml)

The tool uses a YAML configuration file for settings. The default configuration file is `config.yaml` in the project root.

#### Key Configuration Options

**Database Settings:**
- `database.file`: SQLite database file path (default: "papers_database.db")

**Scraper Settings:**
- `scraper.user_agent`: User agent string for HTTP requests
- `scraper.delay`: Delay between requests in seconds (default: 2)
- `scraper.timeout`: Request timeout in seconds (default: 30)

**Source Configuration:**
- `sources.arxiv.enabled`: Enable/disable arXiv scraping
- `sources.arxiv.query`: Search query for arXiv (default: "machine learning")
- `sources.arxiv.max_results`: Maximum results to scrape (default: 50)

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
database:
  file: "my_papers.db"

scraper:
  user_agent: "MyResearchBot/1.0"
  delay: 3
  timeout: 45

sources:
  arxiv:
    enabled: true
    query: "deep learning"
    max_results: 100

logging:
  level: "INFO"
  file: "logs/app.log"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Scrape Papers from Sources

```bash
python src/main.py --scrape
```

### View Database Statistics

```bash
python src/main.py --stats
```

### Search Papers

```bash
# Search by title
python src/main.py --search "neural network"

# Search by author
python src/main.py --author "Smith"

# Filter by subject
python src/main.py --subject "cs.AI"

# Combined search
python src/main.py --search "transformer" --subject "cs.LG"
```

### Organize Papers

```bash
# Show papers organized by subject
python src/main.py --by-subject

# Show papers organized by author
python src/main.py --by-author

# Show papers organized by date
python src/main.py --by-date
```

### Combined Operations

```bash
# Scrape, then show statistics
python src/main.py --scrape --stats

# Full workflow with custom config
python src/main.py -c custom_config.yaml --scrape --stats --by-subject
```

### Command-Line Arguments

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-s, --scrape`: Scrape papers from configured sources
- `--stats`: Show database statistics
- `--search TITLE`: Search papers by title
- `--author NAME`: Search papers by author
- `--subject SUBJECT`: Filter papers by subject
- `--by-subject`: Show papers organized by subject
- `--by-author`: Show papers organized by author
- `--by-date`: Show papers organized by publication date

### Common Use Cases

**Initial Setup:**
1. Configure sources in `config.yaml`
2. Run: `python src/main.py --scrape`
3. View stats: `python src/main.py --stats`

**Regular Updates:**
```bash
# Scrape new papers
python src/main.py --scrape
```

**Research Specific Topic:**
```bash
# Update config with topic query, then scrape
python src/main.py --scrape --by-subject
```

**Find Papers by Author:**
```bash
python src/main.py --author "Einstein"
```

## Project Structure

```
scientific-paper-database/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation
└── logs/
    └── .gitkeep             # Placeholder for logs directory
```

### File Descriptions

- `src/main.py`: Contains the `ScientificPaperDatabase` class and main logic
- `config.yaml`: Configuration file with database, scraper, and source settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `papers_database.db`: SQLite database file (created at runtime)
- `logs/`: Directory for application log files

## Database Schema

The SQLite database contains the following tables:

- **papers**: Paper information (title, authors, subject, publication_date, abstract, url, pdf_url, source)
- **authors**: Author information (name, affiliation)
- **subjects**: Subject/category information (name, description)
- **paper_authors**: Junction table linking papers to authors (many-to-many relationship)

## Testing

### Run Tests

```bash
python -m pytest tests/
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage, testing:
- Database initialization
- Paper addition and duplicate detection
- Author and subject management
- Search functionality
- Organization methods
- Error handling

## Troubleshooting

### Common Issues

**Scraping Fails:**
- Check internet connection
- Verify source URLs are accessible
- Review rate limiting settings
- Check logs for specific error messages
- arXiv API may have rate limits

**No Papers Found:**
- Verify search query is appropriate
- Check that sources are enabled in config
- Review logs for parsing errors
- Try different search terms

**Database Errors:**
- Ensure write permissions in project directory
- Check disk space availability
- Verify database file isn't locked by another process

**Search Returns No Results:**
- Verify papers have been scraped first
- Check search terms match stored data
- Review database statistics to confirm papers exist

### Error Messages

**"Configuration file not found"**: The config.yaml file is missing. Create it or use `-c` to specify a different path.

**"Invalid YAML in configuration file"**: The config.yaml file has syntax errors. Check YAML formatting.

**"Database locked"**: Another process is using the database. Close other instances or wait.

**"Connection timeout"**: Network issues or source website is slow. Increase timeout in config.

### Best Practices

1. **Respect rate limits**: Use appropriate delays between requests
2. **Check terms of service**: Ensure scraping is allowed by source websites
3. **Regular updates**: Scrape new papers periodically
4. **Backup database**: Regularly backup the SQLite database file
5. **Monitor logs**: Review logs for errors and warnings
6. **Use specific queries**: More specific search queries yield better results

## Legal and Ethical Considerations

- **Respect robots.txt**: Check and follow robots.txt files from source websites
- **Rate limiting**: Use appropriate delays to avoid overloading servers
- **Terms of service**: Ensure compliance with website terms of service
- **Public domain only**: Only scrape public domain or freely available content
- **Attribution**: Maintain proper attribution for scraped papers
- **Fair use**: Respect copyright and fair use guidelines

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guidelines
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Include docstrings for all public functions and classes
- Use meaningful variable names
- Write tests for all new functionality

### Pull Request Process

1. Ensure code follows project standards
2. Update documentation if needed
3. Add/update tests
4. Ensure all tests pass
5. Submit PR with clear description of changes

## License

This project is part of the everyday-python-scripts collection. Please refer to the parent repository for license information.

**Note**: This tool is for educational and personal use. Always respect website terms of service and robots.txt files when scraping. Ensure you have permission to scrape and use the content.
