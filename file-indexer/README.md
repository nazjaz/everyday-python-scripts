# File Indexer

A Python command-line tool for generating searchable file indexes with comprehensive metadata. Index files across directory trees, extract metadata (size, modification date, type, path), and save to JSON format for fast searching and analysis.

## Features

- **Comprehensive Metadata Extraction**: Index files with size, modification date, creation date, file type, permissions, and full paths
- **Flexible Indexing**: Index single or multiple directories, with recursive or non-recursive options
- **Searchable Index**: Built-in search functionality to find files by name, path, or type
- **JSON Export**: Save indexes in JSON format for easy integration with other tools
- **Configurable Filtering**: Exclude files and directories by patterns, size limits, or hidden files
- **Hash Calculation**: Optional file hash calculation for integrity verification
- **Human-Readable Output**: File sizes displayed in human-readable format (KB, MB, GB)
- **Extensible**: Highly configurable through YAML configuration files

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Clone or Navigate to Project Directory

```bash
cd everyday-python-scripts/file-indexer
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

### Step 4: Configure Environment (Optional)

Copy `.env.example` to `.env` and modify if needed:

```bash
cp .env.example .env
```

Edit `.env` to set logging level or other environment variables.

### Step 5: Review Configuration

Edit `config.yaml` to customize indexing options, exclude patterns, and metadata settings.

## Configuration

The `config.yaml` file contains all configuration options:

### Index Directories

```yaml
index_directories:
  - .  # Current directory
  - /path/to/another/directory
```

### Indexing Options

```yaml
options:
  include_hidden: false      # Include hidden files
  include_empty: true         # Include zero-byte files
  min_file_size: 0           # Minimum file size (bytes)
  max_file_size: 0           # Maximum file size (bytes)
  calculate_hashes: false    # Calculate file hashes
  hash_algorithm: sha256     # Hash algorithm (md5, sha1, sha256)
  include_permissions: true   # Include file permissions
  include_owner: false       # Include owner information
  recursive: true            # Recursive indexing
```

### Metadata Selection

```yaml
metadata:
  size: true                 # File size
  modification_date: true    # Last modified date
  creation_date: true        # Creation date
  file_type: true            # File extension
  mime_type: false           # MIME type
  full_path: true            # Absolute path
  relative_path: false       # Relative path
```

### Exclude Patterns

```yaml
exclude_patterns:
  - '^\\.'        # Hidden files
  - '\\.tmp$'     # Temporary files
  - '\\.log$'     # Log files

exclude_directories:
  - '^\\.git$'
  - '^__pycache__$'
  - '^node_modules$'
```

## Usage

### Basic Indexing

Index the current directory (as configured in `config.yaml`):

```bash
python src/main.py index
```

### Index Specific Directories

```bash
python src/main.py index -d /path/to/dir1 /path/to/dir2
```

### Non-Recursive Indexing

```bash
python src/main.py index --no-recursive
```

### Custom Output File

```bash
python src/main.py index -o /path/to/output.json
```

### Search Index

Search for files in an existing index:

```bash
python src/main.py search -q "test"
```

### Case-Sensitive Search

```bash
python src/main.py search -q "Test" --case-sensitive
```

### Search Specific Index File

```bash
python src/main.py search -i /path/to/index.json -q "query"
```

### Complete Example

```bash
# Index multiple directories
python src/main.py index -d ~/Documents ~/Downloads -o ~/my_index.json

# Search the index
python src/main.py search -i ~/my_index.json -q "python"
```

## Project Structure

```
file-indexer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/                    # Additional documentation
├── logs/                    # Log files directory
└── data/                    # Index output directory
```

## Index JSON Format

The generated index file has the following structure:

```json
{
  "created_at": "2024-01-15T10:30:00",
  "total_files": 150,
  "directories_indexed": ["/path/to/directory"],
  "recursive": true,
  "files": [
    {
      "name": "example.txt",
      "full_path": "/path/to/directory/example.txt",
      "size": 1024,
      "size_human": "1.00 KB",
      "modified": "2024-01-15T09:00:00",
      "modified_timestamp": 1705316400.0,
      "created": "2024-01-14T08:00:00",
      "created_timestamp": 1705230000.0,
      "file_type": "txt",
      "extension": "txt",
      "permissions_octal": "644",
      "permissions_string": "-rw-r--r--"
    }
  ]
}
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with verbose output:

```bash
pytest tests/ -v
```

Run specific test:

```bash
pytest tests/test_main.py::TestFileIndexer::test_get_file_metadata
```

## Troubleshooting

### Error: Configuration file not found

Ensure `config.yaml` exists in the project root directory. You can specify a custom config file with `-c`:

```bash
python src/main.py index -c /path/to/config.yaml
```

### Error: Permission denied

If you encounter permission errors when indexing certain directories, ensure you have read permissions. You can exclude problematic directories in `config.yaml`.

### Large Index Files

For very large directory trees, consider:
- Using size limits (`min_file_size`, `max_file_size`)
- Excluding unnecessary file types
- Indexing directories separately and merging results

### Search Returns No Results

- Check that the index file exists and is valid JSON
- Verify search query matches file names or paths
- Try case-insensitive search (default)
- Check that search fields are configured in `config.yaml`

### Performance Issues

For large directory trees:
- Disable hash calculation if not needed
- Disable owner information if not needed
- Use non-recursive indexing for shallow directory structures
- Index during off-peak hours

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for all public functions and classes
4. Add unit tests for new features
5. Update README.md for user-facing changes

## License

This project is provided as-is for automation and utility purposes.
