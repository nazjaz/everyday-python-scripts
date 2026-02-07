# API Documentation

## ScientificPaperDatabase Class

The main class for scraping and managing scientific paper database.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the ScientificPaperDatabase with configuration.

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

Scrape papers from all configured sources.

**Side Effects:**
- Makes HTTP requests to configured sources
- Parses XML/HTML content
- Adds papers to database
- Logs scraping progress

#### `search_papers(title: Optional[str] = None, author: Optional[str] = None, subject: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]`

Search papers in database.

**Parameters:**
- `title` (Optional[str]): Search term for title.
- `author` (Optional[str]): Author name to search for.
- `subject` (Optional[str]): Subject to filter by.
- `date_from` (Optional[str]): Start date (YYYY-MM-DD).
- `date_to` (Optional[str]): End date (YYYY-MM-DD).
- `limit` (int): Maximum number of results.

**Returns:**
- List of paper dictionaries, each containing:
  - `id`: Paper ID
  - `title`: Paper title
  - `authors`: Comma-separated author names
  - `subject`: Subject/category
  - `publication_date`: Publication date
  - `abstract`: Paper abstract
  - `url`: Paper URL
  - `source`: Source identifier
  - `pdf_url`: PDF download URL

#### `get_statistics() -> Dict[str, Any]`

Get database statistics.

**Returns:**
- Dictionary containing:
  - `papers`: Number of papers
  - `authors`: Number of authors
  - `subjects`: Number of subjects
  - `subjects_used`: Number of subjects actually used

#### `organize_by_subject() -> Dict[str, int]`

Get paper count by subject.

**Returns:**
- Dictionary mapping subject names to paper counts.

#### `organize_by_author(limit: int = 20) -> Dict[str, int]`

Get paper count by author.

**Parameters:**
- `limit` (int): Maximum number of authors to return.

**Returns:**
- Dictionary mapping author names to paper counts.

#### `organize_by_date(year: Optional[int] = None) -> Dict[str, int]`

Get paper count by publication date.

**Parameters:**
- `year` (Optional[int]): Optional year to filter by.

**Returns:**
- Dictionary mapping dates to paper counts.

#### `_add_paper(title: str, authors: List[str], subject: Optional[str] = None, publication_date: Optional[str] = None, abstract: Optional[str] = None, url: Optional[str] = None, source: Optional[str] = None, pdf_url: Optional[str] = None) -> Optional[int]`

Add paper to database.

**Parameters:**
- `title` (str): Paper title.
- `authors` (List[str]): List of author names.
- `subject` (Optional[str]): Subject/category.
- `publication_date` (Optional[str]): Publication date (YYYY-MM-DD).
- `abstract` (Optional[str]): Paper abstract.
- `url` (Optional[str]): Paper URL.
- `source` (Optional[str]): Source identifier.
- `pdf_url` (Optional[str]): PDF download URL.

**Returns:**
- Paper ID if added, None if duplicate.

### Attributes

#### `db_path: Path`

Path object pointing to the SQLite database file.

#### `config: dict`

Configuration dictionary loaded from YAML file.

#### `session: requests.Session`

HTTP session object for making requests.

### Database Schema

#### papers Table
- `id`: INTEGER PRIMARY KEY
- `title`: TEXT NOT NULL
- `authors`: TEXT (comma-separated)
- `subject`: TEXT
- `publication_date`: DATE
- `abstract`: TEXT
- `url`: TEXT
- `source`: TEXT
- `pdf_url`: TEXT
- `created_at`: TIMESTAMP

#### authors Table
- `id`: INTEGER PRIMARY KEY
- `name`: TEXT UNIQUE NOT NULL
- `affiliation`: TEXT
- `created_at`: TIMESTAMP

#### subjects Table
- `id`: INTEGER PRIMARY KEY
- `name`: TEXT UNIQUE NOT NULL
- `description`: TEXT
- `created_at`: TIMESTAMP

#### paper_authors Table
- `paper_id`: INTEGER (foreign key to papers.id)
- `author_id`: INTEGER (foreign key to authors.id)
- PRIMARY KEY (paper_id, author_id)

### Example Usage

```python
from src.main import ScientificPaperDatabase

# Initialize with default config
db = ScientificPaperDatabase()

# Or with custom config
db = ScientificPaperDatabase(config_path="custom_config.yaml")

# Scrape papers from sources
db.scrape_sources()

# Search papers
papers = db.search_papers(title="neural network", subject="cs.AI")
for paper in papers:
    print(f"{paper['title']} by {paper['authors']}")

# Get statistics
stats = db.get_statistics()
print(f"Total papers: {stats['papers']}")

# Organize by subject
by_subject = db.organize_by_subject()
for subject, count in by_subject.items():
    print(f"{subject}: {count} papers")
```

### arXiv Integration

The tool integrates with arXiv's public API:
- Uses arXiv API for structured data access
- Respects rate limits
- Extracts comprehensive metadata
- Provides PDF download links

### Search Capabilities

Search supports:
- **Title search**: Partial matching on paper titles
- **Author search**: Finds papers by author name
- **Subject filter**: Filters by subject/category
- **Date range**: Filter by publication date
- **Combined queries**: Multiple criteria can be combined
