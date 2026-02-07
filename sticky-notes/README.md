# Sticky Notes Manager

A desktop application for creating and managing sticky notes with color coding and category organization. Store your notes locally in a SQLite database with an intuitive GUI interface.

## Project Description

Sticky Notes Manager solves the problem of organizing and managing notes on your desktop. It provides a centralized application for creating, editing, deleting, and organizing notes with color coding and categories, all stored in a local database for persistence.

**Target Audience**: Users who need a simple, local note-taking application with organization features and visual categorization.

## Features

- **GUI Interface**: User-friendly graphical interface built with tkinter
- **Note Management**: Create, edit, and delete notes easily
- **Color Coding**: Assign colors to notes for visual organization (10 predefined colors)
- **Category Organization**: Organize notes by categories (General, Work, Personal, etc.)
- **Note Preview**: Preview note content in the main window
- **Category Filtering**: Filter notes by category for easy navigation
- **Persistent Storage**: All notes saved to SQLite database
- **Auto-save**: Automatic saving of note changes
- **Search and Organization**: Quickly find notes by category or color

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- tkinter (usually included with Python, may need separate installation on Linux)

### Installing tkinter

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install python3-tk
```

**Linux (Fedora)**:
```bash
sudo dnf install python3-tkinter
```

**macOS/Windows**: Usually included with Python installation

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/sticky-notes
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

### Step 4: Configure Settings (Optional)

1. Copy the example environment file (if needed):
   ```bash
   cp .env.example .env
   ```

2. Edit `config.yaml` to customize colors, categories, or default settings:
   ```yaml
   colors:
     - name: "Yellow"
       code: "#FFEB3B"
   
   categories:
     - "General"
     - "Work"
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **database**: SQLite database file path
- **defaults**: Default note settings (size, font, color, category)
- **colors**: Available colors for notes (name and hex code)
- **categories**: Available categories for organizing notes
- **gui**: Window size and appearance settings
- **auto_save**: Auto-save interval settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_FILE`: Override database file path
- `AUTO_SAVE_INTERVAL`: Override auto-save interval in seconds

### Example Configuration

```yaml
defaults:
  default_color: "#FFEB3B"  # Yellow
  default_category: "General"

colors:
  - name: "Yellow"
    code: "#FFEB3B"
  - name: "Green"
    code: "#4CAF50"

categories:
  - "General"
  - "Work"
  - "Personal"
```

## Usage

### Basic Usage

Launch the application:

```bash
python src/main.py
```

The GUI window will open with:
- **Left Panel**: List of all notes with color coding
- **Right Panel**: Note preview area
- **Menu Bar**: File operations (New Note, Exit)
- **Buttons**: New Note, Edit, Delete

### Creating a Note

1. Click "New Note" button or use File → New Note
2. Enter note title and content
3. Select color from dropdown
4. Select category from dropdown
5. Click "Save"

### Editing a Note

1. Double-click a note in the list, or
2. Select a note and click "Edit" button
3. Modify title, content, color, or category
4. Click "Save"

### Deleting a Note

1. Select a note in the list
2. Click "Delete" button
3. Confirm deletion (note is permanently removed)

### Filtering Notes

1. Use the "Category" dropdown at the top of the note list
2. Select a category to filter, or "All" to show all notes
3. List updates automatically

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml
```

## Project Structure

```
sticky-notes/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── data/
│   └── sticky_notes.db     # SQLite database (created automatically)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: GUI application, note management, database operations
- **config.yaml**: YAML configuration file with colors, categories, and settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/sticky_notes.db**: SQLite database storing all notes
- **logs/sticky_notes.log**: Application log file with rotation

## Database Schema

The SQLite database contains one main table:

### notes
- `id`: Primary key (auto-increment)
- `title`: Note title
- `content`: Note content/text
- `color`: Color hex code
- `category`: Category name
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `position_x`: X position on screen (for future use)
- `position_y`: Y position on screen (for future use)
- `width`: Note width (for future use)
- `height`: Note height (for future use)

## Available Colors

Pre-configured colors (customizable in config.yaml):

- Yellow (#FFEB3B)
- Green (#4CAF50)
- Blue (#2196F3)
- Pink (#E91E63)
- Orange (#FF9800)
- Purple (#9C27B0)
- Red (#F44336)
- Cyan (#00BCD4)
- Lime (#CDDC39)
- Teal (#009688)

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Database operations (create, read, update, delete)
- Note saving and loading
- Category filtering
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named '_tkinter'`

**Solution**: Install tkinter for your system:
- Linux: `sudo apt-get install python3-tk` (Ubuntu/Debian) or `sudo dnf install python3-tkinter` (Fedora)
- macOS/Windows: Usually included, reinstall Python if missing

---

**Issue**: GUI window doesn't appear

**Solution**: 
- Check that tkinter is properly installed
- Verify Python version (3.8+)
- Check logs for error messages

---

**Issue**: Notes not saving

**Solution**: 
- Check database file path permissions
- Ensure data directory exists and is writable
- Check logs for database errors

---

**Issue**: Colors not displaying correctly

**Solution**: 
- Verify color codes in config.yaml are valid hex codes
- Check that color format is `#RRGGBB` (6 hex digits)

---

**Issue**: Application crashes on startup

**Solution**: 
- Check configuration file syntax (valid YAML)
- Verify all required configuration sections are present
- Check logs for specific error messages

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"Database error"**: Check database file permissions and disk space
- **"tkinter not available"**: Install tkinter package for your system

## Keyboard Shortcuts

- **Double-click note**: Edit note
- **Select note**: Show preview
- **Menu → New Note**: Create new note
- **Menu → Exit**: Close application

## Future Enhancements

Potential features for future versions:
- Desktop sticky note windows (floating notes)
- Search functionality
- Note tags/labels
- Export notes to text/PDF
- Note templates
- Reminder/alarm functionality
- Note encryption

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-mock pytest-cov`
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
