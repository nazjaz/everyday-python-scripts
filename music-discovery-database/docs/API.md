# API Documentation

## MusicDiscoveryDatabase Class

The main class for scraping and managing public domain music discovery database.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the MusicDiscoveryDatabase with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.

**Side Effects:**
- Loads configuration
- Sets up logging
- Initializes SQLite database
- Creates database tables if they don't exist

#### `scrape_sources() -> None`

Scrape music from all configured sources.

**Side Effects:**
- Makes HTTP requests to configured sources
- Parses HTML content
- Adds artists and tracks to database
- Logs scraping progress

#### `_generate_recommendations() -> None`

Generate music recommendations based on genres and artists.

**Side Effects:**
- Analyzes tracks in database
- Calculates similarity scores
- Creates recommendation entries
- Logs recommendation generation

#### `get_statistics() -> Dict[str, Any]`

Get database statistics.

**Returns:**
- Dictionary containing:
  - `artists`: Number of artists
  - `tracks`: Number of tracks
  - `genres`: Number of genres
  - `recommendations`: Number of recommendations

#### `get_recommendations(track_title: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]`

Get music recommendations.

**Parameters:**
- `track_title` (Optional[str]): Track title to get recommendations for. If None, returns general recommendations.
- `limit` (int): Maximum number of recommendations to return.

**Returns:**
- List of recommendation dictionaries, each containing:
  - `similarity_score`: Similarity score (0.0-1.0)
  - `reason`: Reason for recommendation
  - `track`: Original track string
  - `recommended`: Recommended track string

#### `export_data(output_path: Optional[str] = None) -> str`

Export database data to JSON format.

**Parameters:**
- `output_path` (Optional[str]): Path to save JSON file. If None, uses default.

**Returns:**
- Path to saved JSON file.

**Raises:**
- `IOError`: If JSON file cannot be written.
- `PermissionError`: If output directory is not writable.

#### `_get_artist_id(artist_name: str, genre: Optional[str] = None) -> int`

Get or create artist ID.

**Parameters:**
- `artist_name` (str): Name of the artist.
- `genre` (Optional[str]): Optional genre for the artist.

**Returns:**
- Artist ID (integer).

#### `_get_genre_id(genre_name: str) -> int`

Get or create genre ID.

**Parameters:**
- `genre_name` (str): Name of the genre.

**Returns:**
- Genre ID (integer).

#### `_add_track(title: str, artist_name: str, genre: Optional[str] = None, duration: Optional[int] = None, url: Optional[str] = None, source: Optional[str] = None) -> int`

Add track to database.

**Parameters:**
- `title` (str): Track title.
- `artist_name` (str): Artist name.
- `genre` (Optional[str]): Optional genre.
- `duration` (Optional[int]): Optional duration in seconds.
- `url` (Optional[str]): Optional track URL.
- `source` (Optional[str]): Optional source identifier.

**Returns:**
- Track ID (integer).

### Attributes

#### `db_path: Path`

Path object pointing to the SQLite database file.

#### `config: dict`

Configuration dictionary loaded from YAML file.

#### `session: requests.Session`

HTTP session object for making requests.

#### `file_data: List[Dict[str, Any]]`

Not used in this class (inherited from file scanning patterns).

### Database Schema

#### artists Table
- `id`: INTEGER PRIMARY KEY
- `name`: TEXT UNIQUE NOT NULL
- `genre`: TEXT
- `bio`: TEXT
- `created_at`: TIMESTAMP

#### tracks Table
- `id`: INTEGER PRIMARY KEY
- `title`: TEXT NOT NULL
- `artist_id`: INTEGER (foreign key to artists.id)
- `genre`: TEXT
- `duration`: INTEGER
- `url`: TEXT
- `source`: TEXT
- `created_at`: TIMESTAMP

#### genres Table
- `id`: INTEGER PRIMARY KEY
- `name`: TEXT UNIQUE NOT NULL
- `description`: TEXT
- `created_at`: TIMESTAMP

#### recommendations Table
- `id`: INTEGER PRIMARY KEY
- `track_id`: INTEGER (foreign key to tracks.id)
- `recommended_track_id`: INTEGER (foreign key to tracks.id)
- `similarity_score`: REAL
- `reason`: TEXT
- `created_at`: TIMESTAMP

### Example Usage

```python
from src.main import MusicDiscoveryDatabase

# Initialize with default config
db = MusicDiscoveryDatabase()

# Or with custom config
db = MusicDiscoveryDatabase(config_path="custom_config.yaml")

# Scrape music from sources
db.scrape_sources()

# Generate recommendations
db._generate_recommendations()

# Get statistics
stats = db.get_statistics()
print(f"Tracks: {stats['tracks']}")

# Get recommendations
recommendations = db.get_recommendations(track_title="Beethoven", limit=5)
for rec in recommendations:
    print(f"{rec['recommended']} (score: {rec['similarity_score']})")

# Export data
db.export_data(output_path="music_data.json")
```

### JSON Export Format

The JSON export contains:

```json
{
  "exported_at": "2024-02-07T12:00:00",
  "statistics": {
    "artists": 10,
    "tracks": 50,
    "genres": 5,
    "recommendations": 100
  },
  "artists": [
    {
      "name": "Artist Name",
      "genre": "Classical",
      "bio": null
    }
  ],
  "tracks": [
    {
      "title": "Track Title",
      "artist": "Artist Name",
      "genre": "Classical",
      "duration": 180,
      "source": "musopen"
    }
  ],
  "genres": [
    {
      "name": "Classical",
      "description": null
    }
  ]
}
```
