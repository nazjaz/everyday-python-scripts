# Music Discovery Database

A Python automation tool that scrapes public domain music information from various sources, stores it in a local SQLite database, and generates music recommendations based on genres and artists. This tool helps discover and organize public domain music while building a personalized music discovery database.

## Project Title and Description

The Music Discovery Database scrapes public domain music information from legitimate sources like Musopen and other public domain archives. It stores artist information, track details, genres, and generates recommendations based on similarity. The tool creates a local database that can be queried, exported, and used for music discovery.

This tool solves the problem of discovering and organizing public domain music by automatically collecting information from multiple sources and creating a searchable, recommendation-enabled database.

**Target Audience**: Music enthusiasts, researchers, developers, and anyone interested in discovering and organizing public domain music.

## Features

- Web scraping from public domain music sources
- SQLite database for local storage
- Artist information tracking (name, genre, bio)
- Track information (title, artist, genre, duration, source)
- Genre categorization and management
- Automatic recommendation generation based on genre and artist similarity
- Database statistics and reporting
- JSON export functionality
- Configurable scraping sources
- Rate limiting and respectful scraping practices
- Comprehensive logging

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection for web scraping
- (Optional) API keys for services that require authentication

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/music-discovery-database
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
- `database.file`: SQLite database file path (default: "music_database.db")

**Scraper Settings:**
- `scraper.user_agent`: User agent string for HTTP requests
- `scraper.delay`: Delay between requests in seconds (default: 2)
- `scraper.timeout`: Request timeout in seconds (default: 10)

**Source Configuration:**
- `sources.musopen.enabled`: Enable/disable Musopen scraping
- `sources.musopen.max_pages`: Maximum pages to scrape
- `sources.freesound.enabled`: Enable/disable Freesound scraping
- `sources.freesound.api_key`: API key for Freesound (if required)

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
database:
  file: "my_music_database.db"

scraper:
  user_agent: "MyMusicBot/1.0"
  delay: 3
  timeout: 15

sources:
  musopen:
    enabled: true
    max_pages: 10

logging:
  level: "INFO"
  file: "logs/app.log"
```

### Environment Variables

API keys and sensitive information can be stored in a `.env` file:

```
FREESOUND_API_KEY=your_api_key_here
```

## Usage

### Scrape Music from Sources

```bash
python src/main.py --scrape
```

### Generate Recommendations

```bash
python src/main.py --recommendations
```

### View Database Statistics

```bash
python src/main.py --stats
```

### Get Recommendations for a Track

```bash
python src/main.py --recommend "Beethoven"
```

### Export Database to JSON

```bash
python src/main.py --export music_data.json
```

### Combined Operations

```bash
# Scrape, generate recommendations, and show stats
python src/main.py --scrape --recommendations --stats

# Full workflow with custom config
python src/main.py -c custom_config.yaml --scrape --recommendations --export data.json
```

### Command-Line Arguments

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-s, --scrape`: Scrape music from configured sources
- `-r, --recommendations`: Generate recommendations
- `--stats`: Show database statistics
- `--recommend TRACK`: Get recommendations for a track title
- `-e, --export PATH`: Export data to JSON file

### Common Use Cases

**Initial Setup:**
1. Configure sources in `config.yaml`
2. Run: `python src/main.py --scrape`
3. Generate recommendations: `python src/main.py --recommendations`
4. View stats: `python src/main.py --stats`

**Regular Updates:**
```bash
# Scrape new music and update recommendations
python src/main.py --scrape --recommendations
```

**Discover Similar Music:**
```bash
# Find recommendations for a specific track
python src/main.py --recommend "Moonlight Sonata"
```

**Backup Database:**
```bash
# Export to JSON for backup
python src/main.py --export backup_$(date +%Y%m%d).json
```

## Project Structure

```
music-discovery-database/
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

- `src/main.py`: Contains the `MusicDiscoveryDatabase` class and main logic
- `config.yaml`: Configuration file with database, scraper, and source settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `music_database.db`: SQLite database file (created at runtime)
- `logs/`: Directory for application log files

## Database Schema

The SQLite database contains the following tables:

- **artists**: Artist information (name, genre, bio)
- **tracks**: Track information (title, artist_id, genre, duration, url, source)
- **genres**: Genre information (name, description)
- **recommendations**: Track recommendations (track_id, recommended_track_id, similarity_score, reason)

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
- Artist and track management
- Recommendation generation
- Data export
- Error handling

## Troubleshooting

### Common Issues

**Scraping Fails:**
- Check internet connection
- Verify source URLs are accessible
- Review rate limiting settings
- Check logs for specific error messages

**Database Errors:**
- Ensure write permissions in project directory
- Check disk space availability
- Verify database file isn't locked by another process

**No Data Scraped:**
- Verify sources are enabled in config.yaml
- Check that source websites haven't changed structure
- Review logs for parsing errors
- Adjust CSS selectors if website structure changed

**Recommendations Empty:**
- Ensure tracks have been scraped first
- Verify tracks have genre or artist information
- Run `--recommendations` after scraping

### Error Messages

**"Configuration file not found"**: The config.yaml file is missing. Create it or use `-c` to specify a different path.

**"Invalid YAML in configuration file"**: The config.yaml file has syntax errors. Check YAML formatting.

**"Database locked"**: Another process is using the database. Close other instances or wait.

**"Connection timeout"**: Network issues or source website is slow. Increase timeout in config.

### Best Practices

1. **Respect rate limits**: Use appropriate delays between requests
2. **Check terms of service**: Ensure scraping is allowed by source websites
3. **Regular backups**: Export database regularly using `--export`
4. **Monitor logs**: Review logs for errors and warnings
5. **Update selectors**: Website structures change; update CSS selectors as needed

## Legal and Ethical Considerations

- **Respect robots.txt**: Check and follow robots.txt files from source websites
- **Rate limiting**: Use appropriate delays to avoid overloading servers
- **Terms of service**: Ensure compliance with website terms of service
- **Public domain only**: Only scrape public domain or freely available content
- **Attribution**: Maintain proper attribution for scraped content

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

**Note**: This tool is for educational and personal use. Always respect website terms of service and robots.txt files when scraping.
