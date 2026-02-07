# File Category Organizer

A Python automation tool that organizes files by extension groups into categories like Media, Documents, Archives, Code, and Data with custom mappings.

## Features

- Organize files by extension groups into predefined categories
- Support for categories: Media, Documents, Archives, Code, Data, and Other
- Custom extension-to-category mappings
- Duplicate detection using file hashing
- Recursive or non-recursive directory processing
- Configurable exclusion patterns and extensions
- Handle duplicate file names (skip, rename, or overwrite)
- Comprehensive error handling and logging
- Dry-run mode to preview operations
- Detailed statistics and reporting

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd file-category-organizer
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Configuration File

The tool uses a YAML configuration file (`config.yaml`) for settings. Key configuration sections:

- **organizer**: Organization settings (directories, recursive, duplicate handling)
- **categories**: Default category mappings (extension groups)
- **custom_mappings**: Custom extension-to-category overrides
- **logging**: Logging configuration

### Default Categories

- **Media**: Images (jpg, png, gif, etc.), Videos (mp4, avi, mov, etc.), Audio (mp3, wav, flac, etc.)
- **Documents**: PDFs, Office documents (doc, xls, ppt), Text files, etc.
- **Archives**: ZIP, RAR, 7Z, TAR, GZ, etc.
- **Code**: Programming files (py, js, html, java, cpp, etc.)
- **Data**: CSV, TSV, databases, SQL files, etc.
- **Other**: Files that don't match any category

### Custom Mappings

Add custom mappings in `config.yaml`:

```yaml
custom_mappings:
  .custom: Documents
  .special: Media
  .myext: Code
```

### Environment Variables

You can override configuration using environment variables:

- `SOURCE_DIRECTORY`: Source directory (overrides config.yaml)
- `DESTINATION_DIRECTORY`: Destination directory (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Organize files with default configuration:**
```bash
python src/main.py
```

**Organize files from specific directory:**
```bash
python src/main.py --source /path/to/files
```

**Specify destination directory:**
```bash
python src/main.py --source /path/to/files --destination /path/to/organized
```

**Preview operations (dry-run):**
```bash
python src/main.py --source /path/to/files --dry-run
```

### Use Cases

**Organize downloads folder:**
```bash
python src/main.py -s ~/Downloads -d ~/Downloads/organized
```

**Organize project files:**
```bash
python src/main.py -s ./project -d ./project/organized
```

**Preview before organizing:**
```bash
python src/main.py -s ~/Downloads --dry-run
```

## Project Structure

```
file-category-organizer/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── API.md
└── logs/
    └── .gitkeep
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file with category mappings
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory
- `organized/`: Default destination directory (created automatically)

## How It Works

1. **Scan Source Directory**: Finds all files in source directory (recursively or not)
2. **Categorize by Extension**: Determines category based on file extension
3. **Check Exclusions**: Skips files matching exclusion patterns
4. **Duplicate Detection**: Optionally checks for duplicate files using MD5 hash
5. **Create Category Folders**: Creates category directories in destination
6. **Move Files**: Moves files to appropriate category folders
7. **Handle Conflicts**: Handles duplicate names based on configuration

### Example Organization

**Before:**
```
~/Downloads/
  photo.jpg
  document.pdf
  archive.zip
  script.py
  data.csv
```

**After:**
```
~/Downloads/organized/
  Media/
    photo.jpg
  Documents/
    document.pdf
  Archives/
    archive.zip
  Code/
    script.py
  Data/
    data.csv
```

## Configuration Options

### Organizer Settings

- `source_directory`: Directory containing files to organize
- `destination_directory`: Directory for organized files
- `recursive`: Process subdirectories (default: true)
- `overwrite_existing`: Overwrite existing files (default: false)
- `check_duplicates`: Check for duplicate files using hash (default: true)
- `handle_duplicates`: How to handle duplicates - skip, rename, or overwrite
- `handle_duplicate_names`: How to handle duplicate names - skip, rename, or overwrite

### Exclusion Settings

- `exclude.patterns`: Regex patterns for files/paths to exclude
- `exclude.extensions`: File extensions to exclude

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_main.py::test_organize_files
```

## Troubleshooting

### Common Issues

**Files not being organized:**
- Check that source directory exists and is readable
- Verify file extensions are in category mappings
- Review exclusion rules in configuration
- Check logs for error messages

**Permission errors:**
- Ensure read permissions for source directory
- Ensure write permissions for destination directory
- Some system directories may require elevated privileges

**Duplicate detection issues:**
- Large files may take time to hash
- Verify sufficient disk space
- Check file permissions

**Files in wrong category:**
- Review category mappings in config.yaml
- Check custom_mappings for overrides
- Verify file extensions are correct

### Error Messages

The tool provides detailed error messages in logs. Check `logs/file_organizer.log` for:
- File access errors
- Permission issues
- Duplicate detection problems
- Organization errors

### Best Practices

1. **Test with dry-run first**: Always use `--dry-run` to preview operations
2. **Backup important files**: Consider backing up before organizing
3. **Review exclusions**: Configure exclusions to avoid processing system files
4. **Check duplicates**: Enable duplicate detection to avoid unnecessary moves
5. **Custom mappings**: Use custom mappings for project-specific file types

## Security Considerations

- Be cautious when organizing system directories
- Review exclusion rules to avoid processing sensitive files
- Verify destination directory permissions
- Consider backing up before bulk operations
- Test with dry-run mode first

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
