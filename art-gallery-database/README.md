# Art Gallery Database

A Python automation tool that scrapes public domain art collections and creates a local art gallery database with searchable metadata and image organization. This tool helps build a personal collection of public domain artworks with full-text search capabilities.

## Project Title and Description

The Art Gallery Database tool scrapes public domain art collections from sources like Wikimedia Commons and the Metropolitan Museum of Art API, downloads images, and stores metadata in a local SQLite database. It provides search functionality to find artworks by title, artist, category, or tags.

This tool solves the problem of building a local, searchable collection of public domain artworks by automating the process of discovering, downloading, and organizing art with comprehensive metadata.

**Target Audience**: Art enthusiasts, researchers, educators, developers, and anyone interested in building a personal collection of public domain artworks with search capabilities.

## Features

- Scrapes public domain art from multiple sources (Wikimedia Commons, Met Museum API)
- Downloads and organizes images into local directory structure
- SQLite database with searchable metadata (title, artist, year, medium, dimensions, description, tags)
- Full-text search across title, description, and tags
- Filter by artist, category, or custom queries
- Duplicate detection using image hashing
- Comprehensive logging of all operations
- Database statistics and reporting
- Configurable scraping limits and sources

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection for scraping
- Write access for database and image storage

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/art-gallery-database
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

The tool uses a YAML configuration file to define database settings, image storage, and scraping preferences. The default configuration file is `config.yaml` in the project root.

#### Key Configuration Options

**Database Settings:**
- `database.path`: SQLite database file path (default: "art_gallery.db")

**Images Settings:**
- `images.directory`: Directory to store downloaded images (default: "images")

**Scraping Settings:**
- `scraping.sources`: List of sources to scrape (wikimedia, metmuseum)
- `scraping.default_limit`: Default number of artworks per source (default: 50)
- `scraping.request_delay`: Delay between requests in seconds (default: 0.2)

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
database:
  path: "art_gallery.db"

images:
  directory: "images"

scraping:
  sources:
    - "wikimedia"
    - "metmuseum"
  default_limit: 50
  request_delay: 0.2

logging:
  level: "INFO"
  file: "logs/app.log"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Scrape Art Collections

Scrape artworks from default sources:

```bash
python src/main.py --scrape
```

Scrape from specific sources with custom limit:

```bash
python src/main.py --scrape --sources wikimedia metmuseum --limit 100
```

### Search Artworks

Search by query:

```bash
python src/main.py --search "landscape"
```

Search by artist:

```bash
python src/main.py --search --artist "Van Gogh"
```

Search by category:

```bash
python src/main.py --search --category "portrait"
```

Combined search:

```bash
python src/main.py --search "sunset" --artist "Monet" --category "impressionism"
```

### View Statistics

```bash
python src/main.py --stats
```

### Combined Operations

```bash
python src/main.py --scrape --limit 50 && python src/main.py --stats
```

### Command-Line Arguments

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-s, --scrape`: Scrape art collections
- `--sources`: Sources to scrape (wikimedia, metmuseum)
- `--limit`: Maximum artworks per source (default: 50)
- `--search`: Search query for artworks
- `--artist`: Filter search by artist
- `--category`: Filter search by category
- `--stats`: Show database statistics

### Common Use Cases

**Build Initial Collection:**
1. Configure sources in `config.yaml`
2. Run: `python src/main.py --scrape --limit 100`
3. Wait for scraping to complete
4. Check statistics: `python src/main.py --stats`

**Search for Specific Artworks:**
1. Search by keyword: `python src/main.py --search "renaissance"`
2. Search by artist: `python src/main.py --search --artist "Leonardo"`
3. Combine filters for precise results

**Maintain Collection:**
1. Periodically run scraping to add new artworks
2. Use search to find specific pieces
3. Review statistics to track collection growth

## Project Structure

```
art-gallery-database/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── .env.example             # Environment variables template
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation
├── logs/
│   └── .gitkeep             # Placeholder for logs directory
├── images/                  # Downloaded images (created at runtime)
└── art_gallery.db           # SQLite database (created at runtime)
```

### File Descriptions

- `src/main.py`: Contains the `ArtGalleryDatabase` class and main logic
- `config.yaml`: Configuration file with database and scraping settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `art_gallery.db`: SQLite database storing artwork metadata
- `images/`: Directory containing downloaded artwork images
- `logs/`: Directory for application log files

## Database Schema

The SQLite database contains an `artworks` table with the following fields:

- `id`: Primary key (auto-increment)
- `title`: Artwork title
- `artist`: Artist name
- `year`: Creation year
- `medium`: Art medium (e.g., "Oil on canvas")
- `dimensions`: Artwork dimensions
- `description`: Artwork description
- `source_url`: Original source URL
- `image_url`: Original image URL
- `image_path`: Local path to downloaded image
- `image_hash`: MD5 hash of image file (for duplicate detection)
- `category`: Art category
- `tags`: Comma-separated tags
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

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
- Configuration loading and validation
- Database initialization and schema
- Artwork saving and retrieval
- Search functionality
- Image downloading and hashing
- Error handling
- Statistics generation

## Troubleshooting

### Common Issues

**No Artworks Scraped:**
- Check internet connection
- Verify source APIs are accessible
- Review logs for detailed error messages
- Some sources may have rate limiting

**Database Errors:**
- Ensure write permissions for database directory
- Check disk space availability
- Verify database file isn't locked by another process

**Image Download Failures:**
- Check internet connection
- Verify image URLs are accessible
- Some images may be very large or unavailable
- Review logs for specific error messages

**Search Returns No Results:**
- Ensure artworks have been scraped first
- Try broader search terms
- Check that database contains data: `python src/main.py --stats`

### Error Messages

**"Configuration file not found"**: The config.yaml file doesn't exist. Create it or specify path with `-c` option.

**"Database error"**: SQLite database operation failed. Check permissions and disk space.

**"Failed to download image"**: Image download failed. Check URL and network connection.

**"No artworks found"**: Source API returned no results. Try different sources or check API status.

### Best Practices

1. **Start with small limits** to test configuration and understand output
2. **Respect rate limits** by using appropriate request delays
3. **Regular backups** of database and images directory
4. **Monitor disk space** as images can be large
5. **Use search features** to find specific artworks efficiently
6. **Review logs** to understand scraping behavior and errors
7. **Periodic updates** to add new artworks to collection

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

## Data Sources

This tool scrapes public domain artworks from:

- **Wikimedia Commons**: Public domain images from Wikimedia Commons
- **Metropolitan Museum of Art API**: Public domain artworks from the Met Museum collection

All scraped content is in the public domain and free to use. Please respect the terms of service of each source.
