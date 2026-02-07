# Text Editor GUI

A Python GUI text editor featuring syntax highlighting, find and replace functionality, and multiple file tabs. Built with tkinter for a simple, cross-platform text editing experience.

## Features

- **Multiple File Tabs**: Open and edit multiple files simultaneously in tabbed interface
- **Syntax Highlighting**: Automatic syntax highlighting for:
  - Python (.py, .pyw)
  - JavaScript (.js, .jsx)
  - HTML (.html, .htm)
  - CSS (.css)
  - JSON (.json)
- **Find and Replace**: 
  - Find text with highlighting
  - Replace all occurrences
  - Keyboard shortcuts (Ctrl+F, Ctrl+H)
- **File Operations**:
  - New file
  - Open file
  - Save file
  - Save as
- **Edit Features**:
  - Undo/Redo support
  - Text wrapping
  - Line numbers (via scrollbar)
- **Keyboard Shortcuts**:
  - Ctrl+N: New file
  - Ctrl+O: Open file
  - Ctrl+S: Save file
  - Ctrl+Shift+S: Save as
  - Ctrl+F: Find
  - Ctrl+H: Replace
  - Ctrl+Z: Undo
  - Ctrl+Y: Redo
- **Status Indicators**: Shows modified status with asterisk (*) in tab name
- **Unsaved Changes Warning**: Prompts before closing with unsaved changes

## Prerequisites

- Python 3.8 or higher
- tkinter (usually included with Python)
- Display server (X11 on Linux, native on Windows/macOS)

## Installation

1. Clone or navigate to the project directory:
```bash
cd text-editor-gui
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

4. Copy and configure the environment file (optional):
```bash
cp .env.example .env
# Edit .env with your settings if needed
```

5. Review and customize `config.yaml` with your settings:
   - Window title and geometry
   - Syntax highlighting colors
   - Editor preferences

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **editor.title**: Window title (default: "Text Editor")
- **editor.geometry**: Initial window size (default: "800x600")
- **syntax_highlighting.tags**: Color configuration for syntax highlighting:
  - keyword_color: Color for keywords (default: blue)
  - string_color: Color for strings (default: green)
  - comment_color: Color for comments (default: gray)
  - number_color: Color for numbers (default: red)

### Environment Variables

Optional environment variables can override configuration:

- `EDITOR_TITLE`: Override window title
- `EDITOR_GEOMETRY`: Override window geometry

## Usage

### Basic Usage

Launch the editor:
```bash
python src/main.py
```

### Open Files

Open files from command line:
```bash
python src/main.py file1.txt file2.py
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config custom-config.yaml
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `files`: Optional list of files to open

## Project Structure

```
text-editor-gui/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── .gitkeep             # Documentation directory placeholder
└── logs/
    └── .gitkeep             # Logs directory placeholder
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

Note: GUI tests may require a display server or headless mode.

## How It Works

1. **Application Initialization**:
   - Creates main window with menu bar, toolbar, and status bar
   - Sets up notebook widget for tabs
   - Configures keyboard shortcuts

2. **Tab Management**:
   - Each file opens in a new tab
   - Tabs show filename and modification status
   - Multiple tabs can be open simultaneously

3. **Syntax Highlighting**:
   - Detects file type from extension
   - Applies appropriate syntax rules
   - Uses regex patterns to identify keywords, strings, comments, numbers
   - Colors text using tkinter tags

4. **Find and Replace**:
   - Find dialog searches text and highlights matches
   - Replace dialog replaces all occurrences
   - Supports keyboard shortcuts

5. **File Operations**:
   - New: Creates empty tab
   - Open: Opens file in new tab
   - Save: Saves current tab
   - Save As: Saves with new filename

## Syntax Highlighting

### Supported Languages

- **Python**: Keywords, strings, comments, numbers
- **JavaScript**: Keywords, strings, comments, numbers
- **HTML**: Tags, attributes, comments
- **CSS**: Properties, values, comments
- **JSON**: Keys, values, numbers, booleans

### Customization

Add custom syntax highlighting by modifying the `SyntaxHighlighter` class:

```python
def _highlight_custom(self, content: str) -> None:
    """Highlight custom language syntax."""
    # Add your patterns here
    self._apply_tag(r"pattern", "tag_name", content)
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New file |
| Ctrl+O | Open file |
| Ctrl+S | Save file |
| Ctrl+Shift+S | Save as |
| Ctrl+F | Find |
| Ctrl+H | Replace |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |

## Menu Structure

### File Menu
- New (Ctrl+N)
- Open (Ctrl+O)
- Save (Ctrl+S)
- Save As (Ctrl+Shift+S)
- Exit

### Edit Menu
- Find (Ctrl+F)
- Replace (Ctrl+H)
- Undo (Ctrl+Z)
- Redo (Ctrl+Y)

## Toolbar

Quick access buttons for:
- New file
- Open file
- Save file
- Find
- Replace

## Troubleshooting

### GUI Not Displaying

If the GUI doesn't display:
- Ensure you have a display server (X11 on Linux)
- Check that tkinter is installed: `python3 -m tkinter`
- Verify Python version (3.8+)

### Syntax Highlighting Not Working

If syntax highlighting doesn't work:
- Check file extension matches supported types
- Verify configuration file syntax
- Review logs for errors

### Files Not Saving

If files aren't saving:
- Check file permissions
- Ensure directory exists
- Review error messages in status bar
- Check logs for details

### Performance Issues

If editor is slow:
- Reduce number of open tabs
- Close large files
- Check system resources
- Review syntax highlighting patterns

## Platform-Specific Notes

### Linux
- Requires X11 display server
- May need to install `python3-tk` package
- Test with: `python3 -m tkinter`

### macOS
- tkinter usually included with Python
- May need to install Python via Homebrew if not included

### Windows
- tkinter included with standard Python installation
- Should work out of the box

## Limitations

- Syntax highlighting is basic (not full parser)
- No code folding
- No line numbers in gutter (can be added)
- Limited to text files
- No plugin system

## Future Enhancements

Potential improvements:
- Line numbers
- Code folding
- Auto-completion
- Multiple themes
- Plugin system
- More language support
- Split view
- Print functionality

## Security Considerations

- File operations use standard file system permissions
- No network access or external connections
- All file operations are local
- User is responsible for file permissions

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
