# API Documentation

## ArtGalleryDatabase Class

The main class for scraping public domain art collections and managing the gallery database.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the ArtGalleryDatabase with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.
- `ValueError`: If configuration file is empty.

**Side Effects:**
- Loads configuration
- Sets up logging
- Initializes SQLite database with required tables
- Creates images directory if it doesn't exist

#### `scrape_collections(sources: Optional[List[str]] = None, limit: int = 50, **kwargs: Any) -> None`

Scrape artworks from specified sources.

**Parameters:**
- `sources` (Optional[List[str]]): List of sources to scrape. If None, uses config defaults. Supported: "wikimedia", "metmuseum".
- `limit` (int): Maximum number of artworks per source. Default: 50.
- `**kwargs`: Additional source-specific parameters:
  - `category`: For Wikimedia Commons, filter by category
  - `department_id`: For Met Museum, filter by department ID

**Side Effects:**
- Scrapes artworks from specified sources
- Downloads images to images directory
- Saves artwork metadata to database
- Updates statistics
- Logs all operations

**Example:**
```python
gallery.scrape_collections(sources=["wikimedia"], limit=100, category="Paintings")
```

#### `search_artworks(query: Optional[str] = None, artist: Optional[str] = None, category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]`

Search artworks in database.

**Parameters:**
- `query` (Optional[str]): Text query to search in title, description, tags.
- `artist` (Optional[str]): Filter by artist name (partial match).
- `category` (Optional[str]): Filter by category (partial match).
- `limit` (int): Maximum number of results. Default: 100.

**Returns:**
- `List[Dict[str, Any]]`: List of artwork dictionaries matching search criteria.

**Search Logic:**
- Query searches across title, description, and tags fields
- Artist and category filters use partial matching (LIKE)
- All filters are combined with AND logic
- Results are ordered by creation date (newest first)

**Example:**
```python
results = gallery.search_artworks(query="landscape", artist="Monet", category="impressionism")
```

#### `get_artwork_by_id(artwork_id: int) -> Optional[Dict[str, Any]]`

Get artwork by database ID.

**Parameters:**
- `artwork_id` (int): Database ID of artwork.

**Returns:**
- `Optional[Dict[str, Any]]`: Artwork dictionary or None if not found.

**Example:**
```python
artwork = gallery.get_artwork_by_id(123)
if artwork:
    print(artwork["title"])
```

#### `get_statistics() -> Dict[str, Any]`

Get database statistics.

**Returns:**
- `Dict[str, Any]`: Dictionary with statistics:
  - `total_artworks`: Total number of artworks in database
  - `total_artists`: Number of unique artists
  - `total_categories`: Number of unique categories
  - `artworks_with_images`: Number of artworks with downloaded images
  - `scraping_stats`: Dictionary with scraping statistics

**Example:**
```python
stats = gallery.get_statistics()
print(f"Total artworks: {stats['total_artworks']}")
```

#### `_save_artwork(artwork: Dict[str, Any]) -> Optional[int]`

Save artwork to database. Internal method used during scraping.

**Parameters:**
- `artwork` (Dict[str, Any]): Artwork dictionary with metadata.

**Returns:**
- `Optional[int]`: Database ID of saved artwork or None if error.

**Artwork Dictionary Structure:**
```python
{
    "title": "Artwork Title",
    "artist": "Artist Name",
    "year": 2020,
    "medium": "Oil on canvas",
    "dimensions": "50x70 cm",
    "description": "Artwork description",
    "source_url": "https://example.com/source",
    "image_url": "https://example.com/image.jpg",
    "category": "painting",
    "tags": "landscape,impressionism"
}
```

#### `_download_image(image_url: str, artwork_id: str) -> Optional[Path]`

Download image from URL and save to images directory. Internal method.

**Parameters:**
- `image_url` (str): URL of image to download.
- `artwork_id` (str): Unique identifier for artwork.

**Returns:**
- `Optional[Path]`: Path to downloaded image or None if error.

**Side Effects:**
- Downloads image file
- Saves to images directory
- Skips download if file already exists

#### `_calculate_image_hash(image_path: Path) -> str`

Calculate MD5 hash of image file. Internal method.

**Parameters:**
- `image_path` (Path): Path to image file.

**Returns:**
- `str`: MD5 hash string.

**Raises:**
- `IOError`: If file cannot be read.

### Attributes

#### `db_path: Path`

Path to SQLite database file.

#### `images_dir: Path`

Path to directory where images are stored.

#### `config: dict`

Configuration dictionary loaded from YAML file.

#### `stats: Dict[str, Any]`

Dictionary containing scraping statistics:
- `artworks_scraped`: Number of artworks scraped
- `images_downloaded`: Number of images downloaded
- `errors`: Number of errors encountered

### Database Schema

The SQLite database contains the following table:

#### `artworks` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| title | TEXT | Artwork title |
| artist | TEXT | Artist name |
| year | INTEGER | Creation year |
| medium | TEXT | Art medium |
| dimensions | TEXT | Artwork dimensions |
| description | TEXT | Artwork description |
| source_url | TEXT | Original source URL |
| image_url | TEXT | Original image URL |
| image_path | TEXT | Local path to downloaded image |
| image_hash | TEXT | MD5 hash of image file |
| category | TEXT | Art category |
| tags | TEXT | Comma-separated tags |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |

**Indexes:**
- `idx_title`: Index on title column
- `idx_artist`: Index on artist column
- `idx_category`: Index on category column
- `idx_tags`: Index on tags column

### Example Usage

```python
from src.main import ArtGalleryDatabase

# Initialize with default config
gallery = ArtGalleryDatabase()

# Or with custom config
gallery = ArtGalleryDatabase(config_path="custom_config.yaml")

# Scrape artworks
gallery.scrape_collections(sources=["wikimedia", "metmuseum"], limit=50)

# Search artworks
results = gallery.search_artworks(query="landscape", limit=20)
for artwork in results:
    print(f"{artwork['title']} by {artwork.get('artist', 'Unknown')}")

# Get specific artwork
artwork = gallery.get_artwork_by_id(123)
if artwork:
    print(f"Title: {artwork['title']}")
    print(f"Image: {artwork.get('image_path', 'Not downloaded')}")

# Get statistics
stats = gallery.get_statistics()
print(f"Total artworks: {stats['total_artworks']}")
print(f"Total artists: {stats['total_artists']}")
```

### Data Sources

#### Wikimedia Commons

Scrapes public domain images from Wikimedia Commons using the MediaWiki API.

**Parameters:**
- `category`: Optional category filter (e.g., "Paintings", "Sculptures")

**Limitations:**
- Rate limiting may apply
- Some categories may have limited results

#### Metropolitan Museum of Art API

Scrapes public domain artworks from the Met Museum collection using their public API.

**Parameters:**
- `department_id`: Optional department ID filter

**Limitations:**
- Only public domain artworks are scraped
- API may have rate limits
- Some objects may not have images

### Error Handling

The class handles errors gracefully:
- Network errors during scraping are logged but don't stop the process
- Image download failures are logged and skipped
- Database errors are logged and re-raised
- Invalid configuration raises exceptions during initialization

### Performance Considerations

- Database operations use indexes for efficient searching
- Image downloads are cached (skipped if file exists)
- Request delays are configurable to respect rate limits
- Large collections may take time to scrape
