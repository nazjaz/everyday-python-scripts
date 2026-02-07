# Music Organizer

Organize music files by reading ID3 tags, creating folder structures like Artist/Album/Track, and renaming files with track numbers. Supports multiple audio formats (MP3, FLAC, OGG, M4A, etc.) and includes comprehensive logging and duplicate handling.

## Project Description

Music Organizer solves the problem of disorganized music collections by automatically reading ID3 metadata tags and reorganizing files into a consistent folder structure. It creates Artist/Album hierarchies, renames files with track numbers, and handles missing tags gracefully. Perfect for organizing large music libraries and maintaining consistent naming conventions.

**Target Audience**: Music enthusiasts, DJs, and anyone with large music collections who want to maintain organized folder structures based on metadata.

## Features

- ID3 tag reading for multiple audio formats (MP3, FLAC, OGG, M4A, AAC, WMA, WAV, Opus)
- Automatic folder structure creation (Artist/Album/)
- Track number-based file renaming (e.g., "01 - Song Title.mp3")
- Configurable folder structure and filename formats
- Default values for missing tags (Unknown Artist, Unknown Album, etc.)
- Duplicate handling (skip, rename, or overwrite)
- Recursive directory scanning
- Move or copy operation modes
- Preserve file timestamps
- Dry-run mode to preview changes
- Comprehensive logging with rotation
- Cross-platform support

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Music files with ID3 tags (or files will use default values)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/music-organizer
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
source_directory: ~/Music/Unorganized
destination_directory: ~/Music/Organized
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory containing unorganized music files
- **destination_directory**: Directory for organized music files
- **folder_structure**: Pattern for folder hierarchy (default: `Artist/Album`)
- **filename_format**: Pattern for file naming (default: `{track} - {title}{ext}`)
- **defaults**: Default values for missing tags
- **duplicate_handling**: How to handle duplicate filenames (skip, rename, overwrite)
- **operations**: Operation settings (recursive, method, preserve_timestamps, dry_run)
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory path
- `DESTINATION_DIRECTORY`: Override destination directory path
- `DRY_RUN`: Enable dry run mode (`true`/`false`)

### Folder Structure Patterns

Configure the `folder_structure` setting to customize directory organization:

- `Artist/Album` (default): Creates `Artist Name/Album Name/` structure
- `Artist/Album/Year`: Adds year subdirectory
- `Genre/Artist/Album`: Organizes by genre first (requires genre tag)

### Filename Format Patterns

Configure the `filename_format` setting to customize file naming:

- `{track} - {title}{ext}` (default): "01 - Song Title.mp3"
- `{track} {title}{ext}`: "01 Song Title.mp3" (no dash)
- `{title}{ext}`: "Song Title.mp3" (no track number)
- `{track:02d} - {artist} - {title}{ext}`: Custom format with zero-padded track

### Example Configuration

```yaml
source_directory: ~/Downloads/Music
destination_directory: ~/Music/Library

folder_structure: Artist/Album
filename_format: "{track} - {title}{ext}"

defaults:
  artist: "Unknown Artist"
  album: "Unknown Album"
  track: "00"

duplicate_handling: rename

operations:
  create_destination: true
  recursive: true
  method: move
  preserve_timestamps: true
  dry_run: false
```

## Usage

### Basic Usage

Organize music files with default configuration:

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

2. **Organize Music Collection**:
   ```bash
   python src/main.py
   ```
   Organizes all music files in source directory.

3. **Copy Instead of Move**:
   - Set `operations.method: copy` in `config.yaml`
   - Original files remain in source directory

4. **Custom Folder Structure**:
   - Edit `folder_structure` in `config.yaml`
   - Example: `Genre/Artist/Album` (requires genre tag)

5. **Handle Files Without Tags**:
   - Configure `defaults` in `config.yaml`
   - Files without tags will use default values

## Project Structure

```
music-organizer/
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

- **src/main.py**: Core organization logic, ID3 tag reading, and file operations
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Supported Audio Formats

The script supports the following audio formats:

- MP3 (ID3v1, ID3v2)
- FLAC (Vorbis comments)
- OGG (Vorbis comments)
- M4A (iTunes metadata)
- AAC
- WMA
- WAV
- Opus

## ID3 Tag Reading

The script reads the following tags from audio files:

- **Artist** (TPE1, ARTIST, ©ART)
- **Album** (TALB, ALBUM, ©alb)
- **Track Number** (TRCK, TRACKNUMBER, TRACK)
- **Title** (TIT2, TITLE, ©nam)

If tags are missing, default values from configuration are used.

## Example Output Structure

After organization, your music will be structured like:

```
Organized/
├── The Beatles/
│   ├── Abbey Road/
│   │   ├── 01 - Come Together.mp3
│   │   ├── 02 - Something.mp3
│   │   └── 03 - Maxwell's Silver Hammer.mp3
│   └── Sgt. Pepper's Lonely Hearts Club Band/
│       ├── 01 - Sgt. Pepper's Lonely Hearts Club Band.mp3
│       └── 02 - With a Little Help from My Friends.mp3
└── Pink Floyd/
    └── The Dark Side of the Moon/
        ├── 01 - Speak to Me.mp3
        └── 02 - Breathe.mp3
```

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
- ID3 tag reading from various formats
- Folder structure creation
- Filename formatting
- Duplicate handling
- File operations (move/copy)
- Error handling
- Default value handling

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Source directory does not exist`

**Solution**: Ensure the source directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: Files not being organized or tags not read

**Solution**:
- Verify files have ID3 tags (use a tag editor to check)
- Check that file format is supported
- Review logs for specific error messages
- Files without tags will use default values

---

**Issue**: `PermissionError` when moving files

**Solution**: Ensure you have write permissions to both source and destination directories. On Linux/Mac, you may need to adjust directory permissions.

---

**Issue**: Files organized incorrectly

**Solution**:
- Check ID3 tags in your music files (may need correction)
- Review folder structure and filename format in config
- Use `--dry-run` to preview before organizing
- Check logs for tag reading issues

---

**Issue**: Duplicate files

**Solution**:
- Configure `duplicate_handling` in config (skip, rename, or overwrite)
- Default is "rename" which adds a counter to duplicate filenames
- Review source directory for actual duplicates

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Source directory does not exist"**: Verify the path in `config.yaml` or environment variable
- **"Error reading tags"**: File may be corrupted or in unsupported format; check logs
- **"Error organizing file"**: Check file permissions and disk space

## Tips for Best Results

1. **Backup First**: Always backup your music collection before organizing
2. **Use Dry-Run**: Always run with `--dry-run` first to preview changes
3. **Fix Tags First**: Use a tag editor to fix incorrect or missing tags before organizing
4. **Start Small**: Test with a small subset of files first
5. **Review Logs**: Check logs after organizing to identify any issues
6. **Use Copy Mode**: Use `method: copy` initially to keep originals safe

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
