# File Organizer

Automatically organize downloaded files into categorized folders based on file extensions. This tool moves images to Pictures, documents to Documents, videos to Videos, and archives to Archives folders, with built-in duplicate detection and comprehensive logging.

## Project Description

File Organizer solves the problem of cluttered download directories by automatically categorizing and organizing files based on their extensions. It helps maintain an organized file structure, prevents duplicate files, and provides detailed logging of all operations.

**Target Audience**: Users who download many files and want to maintain an organized file system without manual sorting.

## Features

- Automatic file categorization by extension (images, documents, videos, archives)
- Duplicate detection using file hashing (MD5, SHA1, or SHA256)
- Comprehensive logging with rotation and multiple log levels
- Dry run mode to preview changes before execution
- Configurable destination directories and category mappings
- Preserves file timestamps during moves
- Handles name conflicts automatically
- Supports multiple duplicate handling strategies (skip, rename, move to duplicates folder)

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Write permissions to source and destination directories

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/file-organizer
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

2. Edit `config.yaml` to set your source and destination directories:
   ```yaml
   source_directory: ~/Downloads
   destination_base: ~/Organized
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory to monitor for files (default: `~/Downloads`)
- **destination_base**: Base directory for organized files (default: `~/Organized`)
- **categories**: File extension mappings to folder names
- **duplicate_detection**: Settings for duplicate file handling
- **logging**: Log file location and rotation settings
- **operations**: File operation preferences (dry run, preserve timestamps, etc.)

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory path
- `DESTINATION_BASE`: Override destination base directory
- `DRY_RUN`: Enable dry run mode (`true`/`false`)

### Example Configuration

```yaml
source_directory: ~/Downloads
destination_base: ~/Organized

categories:
  pictures:
    folder: Pictures
    extensions: [.jpg, .jpeg, .png, .gif, .webp]
  
  documents:
    folder: Documents
    extensions: [.pdf, .doc, .docx, .txt]

duplicate_detection:
  enabled: true
  method: hash
  hash_algorithm: sha256
  action: skip
```

## Usage

### Basic Usage

Run the organizer with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Preview changes without moving files (dry run)
python src/main.py --dry-run

# Combine options
python src/main.py -c config.yaml --dry-run
```

### Common Use Cases

1. **Organize Downloads Folder**:
   ```bash
   python src/main.py
   ```

2. **Preview Organization** (dry run):
   ```bash
   python src/main.py --dry-run
   ```

3. **Organize Custom Directory**:
   - Edit `config.yaml` to change `source_directory`
   - Or set environment variable: `export SOURCE_DIRECTORY=/path/to/files`

4. **Skip Duplicates**:
   - Configure `duplicate_detection.action: skip` in config.yaml
   - Duplicate files will be logged but not moved

## Project Structure

```
file-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── src/
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core file organization logic, duplicate detection, and logging
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- File categorization logic
- Duplicate detection
- File moving operations
- Dry run mode
- Error handling
- Name conflict resolution

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Source directory does not exist`

**Solution**: Ensure the source directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: `PermissionError` when moving files

**Solution**: Ensure you have write permissions to both source and destination directories. On Linux/Mac, you may need to use `sudo` or adjust directory permissions.

---

**Issue**: Files not being categorized

**Solution**: Check that file extensions are included in the appropriate category in `config.yaml`. Extensions are case-sensitive in the config but matching is case-insensitive.

---

**Issue**: Duplicate detection not working

**Solution**: 
- Verify `duplicate_detection.enabled: true` in config.yaml
- Check that hash algorithm is supported (md5, sha1, sha256)
- Ensure destination directories exist and are readable

---

**Issue**: Logs directory not found

**Solution**: The logs directory is created automatically. If issues persist, manually create `logs/` directory in the project root.

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Source directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Error moving file"**: Check file permissions and disk space

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov`
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
