# Movie Watchlist

A command-line tool for scraping movie information from public databases (OMDB API), creating a local movie watchlist, and managing movies with ratings, genres, and release dates. Store your movie watchlist locally with comprehensive movie information.

## Project Description

Movie Watchlist solves the problem of managing a personal movie watchlist by providing an easy way to search for movies, add them to a local database, track watch status, and store ratings and notes. It helps users organize their movie viewing by maintaining a comprehensive local database with movie information, ratings from multiple sources, and personal tracking.

**Target Audience**: Movie enthusiasts who want to maintain a personal watchlist, track movies they've watched, and organize their movie viewing with ratings and notes.

## Features

- **Movie Search**: Search for movies by title using OMDB API
- **Movie Details**: Get comprehensive movie information including ratings, genres, cast, and plot
- **Local Database**: Store watchlist in SQLite database
- **Watch Status Tracking**: Track movies as to_watch, watching, watched, or dropped
- **Multiple Ratings**: Store ratings from IMDb, Metacritic, and Rotten Tomatoes
- **User Ratings**: Add personal ratings and notes for movies
- **Flexible Queries**: List movies by status, sort by various criteria
- **Comprehensive Information**: Store genre, director, actors, release date, runtime, and more
- **Persistent Storage**: All data stored locally in SQLite database

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- OMDB API key (free, get from http://www.omdbapi.com/apikey.aspx)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/movie-watchlist
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

### Step 4: Get OMDB API Key

1. Visit http://www.omdbapi.com/apikey.aspx
2. Request a free API key
3. Add it to `.env` file:

```bash
cp .env.example .env
# Edit .env and add your API key
OMDB_API_KEY=your_api_key_here
```

### Step 5: Configure Settings (Optional)

Edit `config.yaml` if you want to customize default settings:

```yaml
watchlist:
  default_status: to_watch
  auto_save_info: true
```

## Usage

### Basic Commands

**Search for movies**:
```bash
python src/main.py search --title "The Matrix"
```

**Add movie to watchlist**:
```bash
python src/main.py add --title "The Matrix" --year 1999
# Or by IMDb ID
python src/main.py add --imdb-id tt0133093
```

**List movies in watchlist**:
```bash
# List all movies
python src/main.py list

# List by status
python src/main.py list --status watched

# Sort by rating
python src/main.py list --sort rating
```

**Update movie status**:
```bash
python src/main.py update --imdb-id tt0133093 --status watched --rating 9
```

**Show movie details**:
```bash
python src/main.py show --title "The Matrix"
# Or
python src/main.py show --imdb-id tt0133093
```

**Remove movie from watchlist**:
```bash
python src/main.py remove --imdb-id tt0133093
```

### Command-Line Options

```bash
# Search with year filter
python src/main.py search --title "Matrix" --year 1999

# Add with custom status
python src/main.py add --title "The Matrix" --status watching

# Update with notes
python src/main.py update --imdb-id tt0133093 --status watched --rating 9 --notes "Great movie!"

# List with sorting
python src/main.py list --sort year --status to_watch

# Use custom configuration
python src/main.py list -c /path/to/config.yaml
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

#### OMDB API Settings

```yaml
omdb_api:
  base_url: "http://www.omdbapi.com/"
  api_key: null  # Set via environment variable or .env
  timeout: 10
```

#### Watchlist Options

```yaml
watchlist:
  default_status: to_watch  # Default status for new movies
  auto_save_info: true  # Auto-save movie information
  include_plot: true  # Include plot in movie details
```

#### Display Options

```yaml
display:
  movies_per_page: 20
  default_sort: title  # title, year, rating, added_date
  show_all_ratings: true  # Show all rating sources
```

### Environment Variables

Create a `.env` file (use `.env.example` as template):

- `OMDB_API_KEY`: Your OMDB API key (required)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Watchlist Statuses

- **to_watch**: Movies you want to watch
- **watching**: Movies you're currently watching
- **watched**: Movies you've completed
- **dropped**: Movies you've stopped watching

## Database Schema

The tool creates a SQLite database with the following key fields:

- `imdb_id`: Unique IMDb identifier
- `title`: Movie title
- `year`: Release year
- `genre`: Movie genres
- `director`: Director name
- `actors`: Main actors
- `released`: Release date
- `runtime`: Movie duration
- `imdb_rating`: IMDb rating (0-10)
- `metascore`: Metacritic score (0-100)
- `rotten_tomatoes`: Rotten Tomatoes score
- `status`: Watchlist status
- `user_rating`: Your personal rating (1-10)
- `notes`: Your personal notes
- `added_date`: When added to watchlist
- `watched_date`: When marked as watched

## Project Structure

```
movie-watchlist/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Application configuration
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── data/
│   └── movie_watchlist.db  # SQLite database
└── logs/
    └── movie_watchlist.log  # Application logs
```

## Example Workflow

1. **Search for a movie**:
   ```bash
   python src/main.py search --title "Inception"
   ```

2. **Add to watchlist**:
   ```bash
   python src/main.py add --title "Inception" --year 2010
   ```

3. **List your watchlist**:
   ```bash
   python src/main.py list --status to_watch
   ```

4. **Mark as watched**:
   ```bash
   python src/main.py update --imdb-id tt1375666 --status watched --rating 9
   ```

5. **View watched movies**:
   ```bash
   python src/main.py list --status watched --sort rating
   ```

## Querying the Database

You can query the database directly using SQLite:

```bash
sqlite3 data/movie_watchlist.db

# View all movies
SELECT title, year, status, imdb_rating FROM movies;

# View unwatched movies
SELECT title, year FROM movies WHERE status = 'to_watch';

# View top rated watched movies
SELECT title, year, user_rating FROM movies 
WHERE status = 'watched' AND user_rating IS NOT NULL 
ORDER BY user_rating DESC;
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Test Coverage

The test suite covers:
- Movie search functionality
- Movie details retrieval
- Database operations (add, get, update, remove)
- Status management
- Rating extraction
- Duplicate handling

## Troubleshooting

### API Key Issues

**Error: "OMDB API key is required"**
- Ensure API key is set in `.env` file
- Verify API key is correct
- Check API key is active on OMDB website

**Error: "Invalid API key"**
- Verify API key format
- Check API key hasn't expired
- Ensure no extra spaces in API key

### Movie Not Found

**Error: "Movie not found"**
- Verify movie title spelling
- Try searching with year
- Use IMDb ID if available
- Check movie exists on IMDb

### Database Issues

**Database locked**:
- Ensure only one instance is running
- Check file permissions
- Verify disk space available

**Data not saving**:
- Check database file permissions
- Verify disk space
- Check logs for errors

## Best Practices

1. **Use IMDb ID when possible**: More reliable than title search
2. **Add year for ambiguous titles**: Helps find correct movie
3. **Update status regularly**: Keep watchlist current
4. **Add personal ratings**: Track your own opinions
5. **Use notes**: Remember why you added a movie
6. **Backup database**: Regular backups preserve your watchlist

## API Rate Limits

OMDB API has rate limits:
- Free tier: 1,000 requests per day
- Be mindful of rate limits when searching
- Use IMDb ID when possible to reduce API calls

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guide
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with conventional commit format
7. Push and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

## License

This project is part of the everyday-python-scripts collection. See the main repository for license information.

## Disclaimer

This tool uses the OMDB API which is a third-party service. Movie information accuracy depends on the API data. The tool is for personal use only and should comply with OMDB API terms of service.
