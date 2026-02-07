# Document Organizer

Organize document files by type into folders like PDFs, Word-Documents, Spreadsheets, and Presentations based on file extensions and MIME types. Automatically categorizes documents and maintains an organized file structure.

## Project Description

Document Organizer solves the problem of cluttered document directories by automatically categorizing files based on their type. It uses both file extensions and MIME type detection to accurately identify document types, then organizes them into appropriate folders. Perfect for maintaining organized document collections and quickly finding files by category.

**Target Audience**: Users with large document collections, office workers, students, and anyone who needs to maintain organized document folders.

## Features

- **Multi-Method Detection**: Uses both file extensions and MIME types for accurate categorization
- **Document Categories**: Organizes into PDFs, Word-Documents, Spreadsheets, and Presentations
- **MIME Type Support**: Detects file types even when extensions are missing or incorrect
- **Duplicate Handling**: Options to skip, rename, or overwrite duplicate files
- **Recursive Scanning**: Processes files in subdirectories
- **Move or Copy**: Choose to move or copy files during organization
- **Preserve Timestamps**: Maintains original file modification times
- **Dry-Run Mode**: Preview operations before executing
- **Comprehensive Logging**: Detailed logs of all operations
- **Exclusion Patterns**: Skip specific files or patterns

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Write permissions to source and destination directories
- (Optional) python-magic library for enhanced MIME type detection

### Optional: Enhanced MIME Type Detection

For more accurate MIME type detection, install `python-magic`:

**Linux**:
```bash
sudo apt-get install libmagic1  # Ubuntu/Debian
sudo yum install file-devel      # CentOS/RHEL
pip install python-magic
```

**macOS**:
```bash
brew install libmagic
pip install python-magic
```

**Windows**:
```bash
# Download and install file.exe from http://gnuwin32.sourceforge.net/packages/file.htm
pip install python-magic-bin
```

Note: The script works without python-magic, using extension-based detection as fallback.

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/document-organizer
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

Edit `config.yaml` to set your source and destination directories:

```yaml
source_directory: ~/Documents/Unorganized
destination_directory: ~/Documents/Organized
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory containing documents to organize
- **destination_directory**: Base directory for organized documents
- **categories**: Document type categories and their folder mappings
  - **pdfs**: PDF files
  - **word_documents**: Word, RTF, ODT files
  - **spreadsheets**: Excel, ODS, CSV files
  - **presentations**: PowerPoint, ODP files
- **duplicate_handling**: How to handle duplicate filenames (skip, rename, overwrite)
- **exclusions**: Patterns and extensions to exclude
- **operations**: Operation settings (recursive, method, preserve_timestamps, dry_run)
- **logging**: Log file location and rotation settings

### Category Configuration

Each category includes:
- **folder**: Destination folder name
- **extensions**: List of file extensions for this category
- **mime_types**: List of MIME types for this category

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory path
- `DESTINATION_DIRECTORY`: Override destination directory path
- `DRY_RUN`: Enable dry run mode (`true`/`false`)

### Example Configuration

```yaml
source_directory: ~/Downloads/Documents
destination_directory: ~/Documents/Organized

categories:
  pdfs:
    folder: PDFs
    extensions: [.pdf]
    mime_types: [application/pdf]

  word_documents:
    folder: Word-Documents
    extensions: [.doc, .docx, .rtf]
    mime_types:
      - application/msword
      - application/vnd.openxmlformats-officedocument.wordprocessingml.document

duplicate_handling: rename

operations:
  recursive: true
  method: move
  preserve_timestamps: true
  dry_run: false
```

## Usage

### Basic Usage

Organize documents with default configuration:

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

1. **Preview Organization (Recommended First Step)**:
   ```bash
   python src/main.py --dry-run
   ```
   See what would be organized without making changes.

2. **Organize Documents**:
   ```bash
   python src/main.py
   ```
   Organizes all documents in source directory.

3. **Copy Instead of Move**:
   - Set `operations.method: copy` in `config.yaml`
   - Original files remain in source directory

4. **Organize Specific Directory**:
   - Edit `source_directory` in `config.yaml`
   - Or set environment variable: `export SOURCE_DIRECTORY=/path/to/documents`

5. **Handle Duplicates**:
   - Configure `duplicate_handling` in config (skip, rename, or overwrite)
   - Default is "rename" which adds a counter to duplicate filenames

## Project Structure

```
document-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py         # Package initialization
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core organization logic, MIME type detection, and file operations
- **config.yaml**: YAML configuration file with categories and settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Document Categories

The script organizes documents into four main categories:

1. **PDFs**: PDF documents (.pdf)
2. **Word-Documents**: Word, RTF, ODT files (.doc, .docx, .rtf, .odt)
3. **Spreadsheets**: Excel, ODS, CSV files (.xls, .xlsx, .ods, .csv)
4. **Presentations**: PowerPoint, ODP files (.ppt, .pptx, .odp)

## MIME Type Detection

The script uses a two-tier approach for file type detection:

1. **Extension-Based**: First checks file extension against configured extensions
2. **MIME Type**: If python-magic is available, reads file content for accurate detection

This ensures accurate categorization even when:
- File extensions are missing
- File extensions are incorrect
- Files have non-standard extensions

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Document category detection (extension and MIME type)
- File organization operations
- Duplicate handling
- Exclusion logic
- Error handling
- File operations (move/copy)

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Source directory does not exist`

**Solution**: Ensure the source directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: Files not being categorized correctly

**Solution**:
- Check that file extensions are included in appropriate category in `config.yaml`
- Verify MIME types are configured correctly
- Install python-magic for more accurate MIME type detection
- Review logs for specific categorization issues

---

**Issue**: `PermissionError` when moving files

**Solution**: Ensure you have write permissions to both source and destination directories. On Linux/Mac, you may need to adjust directory permissions.

---

**Issue**: MIME type detection not working

**Solution**:
- Install python-magic library (see Prerequisites)
- Install system dependencies (libmagic) if needed
- Script will fall back to extension-based detection if python-magic is unavailable

---

**Issue**: Files with wrong extensions not detected

**Solution**: Install python-magic for content-based MIME type detection, which can identify files even with incorrect extensions.

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Source directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Error organizing file"**: Check file permissions and disk space
- **"No category found"**: File extension and MIME type don't match any configured category

## Tips for Best Results

1. **Use Dry-Run First**: Always run with `--dry-run` to preview operations
2. **Install python-magic**: For more accurate file type detection
3. **Review Categories**: Customize categories in config to match your document types
4. **Check Exclusions**: Configure exclusions to skip unwanted files
5. **Backup Important Files**: Always backup important documents before organizing
6. **Review Logs**: Check logs after organizing to identify any issues

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov pytest-mock`
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
