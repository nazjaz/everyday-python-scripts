# API Documentation

## IntelligentFileOrganizer Class

The main class for intelligent file organization using content analysis, filename patterns, and directory context.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the IntelligentFileOrganizer with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.
- `ValueError`: If no categories are defined.

**Side Effects:**
- Loads configuration
- Sets up logging
- Loads category definitions

#### `scan_directory(directory: str) -> None`

Scan directory and extract tags from files.

**Parameters:**
- `directory` (str): Path to directory to scan.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Scans directory recursively
- Extracts tags from filenames, directories, and content
- Populates `file_tags` dictionary
- Updates statistics
- Logs all operations

#### `organize_files(source_dir: str, dry_run: bool = False) -> None`

Organize files into category-based folders.

**Parameters:**
- `source_dir` (str): Source directory containing files.
- `dry_run` (bool): If True, simulate organization without moving files.

**Side Effects:**
- Determines categories for files
- Creates category folders
- Moves files to appropriate folders
- Updates statistics
- Logs all operations

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate organization report.

**Parameters:**
- `output_path` (Optional[str]): Path to save report file. If None, uses default from config.

**Returns:**
- `str`: Report content as string.

**Raises:**
- `IOError`: If report file cannot be written.
- `PermissionError`: If output directory is not writable.

#### `_extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]`

Extract keywords from text content.

**Parameters:**
- `text` (str): Text content to analyze.
- `max_keywords` (int): Maximum number of keywords to extract.

**Returns:**
- `List[str]`: List of extracted keywords (most frequent first).

#### `_extract_tags_from_filename(file_path: Path) -> List[str]`

Extract category tags from filename.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `List[str]`: List of matching category names.

#### `_extract_tags_from_directory(file_path: Path) -> List[str]`

Extract category tags from directory context.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `List[str]`: List of matching category names based on parent directories.

#### `_extract_tags_from_content(file_path: Path) -> List[str]`

Extract category tags from file content.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `List[str]`: List of matching category names based on content analysis.

**Note:** Only analyzes text files with extensions in `text_extensions` config.

#### `_extract_all_tags(file_path: Path) -> List[str]`

Extract all tags from filename, directory, and content.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- `List[str]`: List of all extracted tags (duplicates removed).

#### `_determine_category(file_path: Path, tags: List[str]) -> Optional[str]`

Determine primary category from tags.

**Parameters:**
- `file_path` (Path): Path to file (used for context).
- `tags` (List[str]): List of category tags.

**Returns:**
- Primary category name (most frequent tag) or None if no tags.

### Attributes

#### `file_tags: Dict[str, List[str]]`

Dictionary mapping file paths (as strings) to lists of extracted category tags.

#### `categories: Dict[str, Dict[str, Any]]`

Dictionary mapping category names to their definitions. Each category definition contains:
- `folder`: Destination folder name
- `keywords`: List of keywords for filename matching
- `patterns`: List of regex patterns for filename matching
- `directory_keywords`: List of keywords for directory matching
- `content_keywords`: List of keywords for content matching

#### `stats: Dict[str, Any]`

Dictionary containing operation statistics:
- `files_scanned`: Total number of files scanned
- `files_organized`: Number of files successfully organized
- `tags_extracted`: Total number of tags extracted
- `errors`: Number of errors encountered

#### `config: dict`

Configuration dictionary loaded from YAML file.

### Example Usage

```python
from src.main import IntelligentFileOrganizer

# Initialize with default config
organizer = IntelligentFileOrganizer()

# Or with custom config
organizer = IntelligentFileOrganizer(config_path="custom_config.yaml")

# Scan directory
organizer.scan_directory("/path/to/directory")

# Organize files (dry run first)
organizer.organize_files("/path/to/directory", dry_run=True)

# Actually organize files
organizer.organize_files("/path/to/directory", dry_run=False)

# Generate report
organizer.generate_report()

# Access results
print(f"Scanned {organizer.stats['files_scanned']} files")
print(f"Extracted {organizer.stats['tags_extracted']} tags")
for file_path, tags in list(organizer.file_tags.items())[:5]:
    print(f"{file_path}: {tags}")
```

### Category Definition Structure

Categories are defined in the configuration file with the following structure:

```yaml
categories:
  category_name:
    folder: "DestinationFolder"
    keywords:
      - "keyword1"
      - "keyword2"
    patterns:
      - ".*\\.ext$"
    directory_keywords:
      - "dir_keyword"
    content_keywords:
      - "content_keyword"
```

### Tag Extraction Priority

Tags are extracted from multiple sources and combined:
1. **Filename tags**: Based on keywords and patterns in filename
2. **Directory tags**: Based on keywords in parent directory names
3. **Content tags**: Based on keywords extracted from file content

The primary category is determined by the most frequent tag across all sources.
