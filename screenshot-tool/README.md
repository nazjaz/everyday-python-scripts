# Screenshot Tool

A Python GUI application for capturing screenshots, annotating them with drawing tools, text, and shapes, and saving them with timestamps. This tool provides an intuitive interface for creating and editing screenshots.

## Features

- **Screenshot Capture**: Capture full-screen screenshots with a single click
- **Image Loading**: Open and edit existing image files
- **Annotation Tools**:
  - Freehand drawing
  - Rectangle and circle shapes
  - Arrow annotations
  - Text annotations with customizable font size
- **Customizable Colors**: Choose any color for annotations
- **Adjustable Line Width**: Control the thickness of drawing tools
- **Timestamp Saving**: Automatically saves screenshots with timestamps
- **Multiple Save Options**: Save with default name or choose custom filename
- **Clean Interface**: Simple, intuitive GUI with toolbar and menu
- **Comprehensive Logging**: Detailed logging with rotation

## Prerequisites

- Python 3.8 or higher
- GUI support (X11 on Linux, native on macOS/Windows)
- Sufficient screen resolution for GUI display
- Write permissions for screenshot directory

## Installation

1. Clone or navigate to the project directory:
```bash
cd screenshot-tool
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
   - Set default screenshot directory
   - Configure timestamp format
   - Adjust default annotation settings

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **save.default_directory**: Directory for saving screenshots (default: ./screenshots)
- **save.timestamp_format**: Timestamp format for filenames (default: %Y%m%d_%H%M%S)
- **save.default_format**: Default file format (default: png)
- **annotation.default_color**: Default drawing color in hex format (default: #FF0000)
- **annotation.default_line_width**: Default line width for drawing (default: 3)
- **annotation.default_font_size**: Default font size for text (default: 20)

### Environment Variables

Optional environment variables can override configuration:

- `SCREENSHOT_DIRECTORY`: Override default screenshot directory path

## Usage

### Basic Usage

Launch the application:
```bash
python src/main.py
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config /path/to/custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
screenshot-tool/
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
├── logs/
│   └── .gitkeep             # Logs directory placeholder
└── screenshots/             # Generated screenshots directory
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

## How to Use

### Capturing Screenshots

1. Click "Capture Screenshot" button or use File > Capture Screenshot
2. The application window will hide briefly
3. A screenshot of your entire screen will be captured
4. The screenshot will appear in the canvas for annotation

### Opening Images

1. Click "Open Image" button or use File > Open Image
2. Select an image file from the file dialog
3. The image will be loaded into the canvas for annotation

### Annotating Screenshots

1. **Select Tool**: Choose from the toolbar:
   - **Select**: Default tool (no annotation)
   - **Draw**: Freehand drawing
   - **Rectangle**: Draw rectangles
   - **Circle**: Draw circles
   - **Arrow**: Draw arrows
   - **Text**: Add text annotations

2. **Choose Color**: Click the color button to select annotation color

3. **Adjust Width**: Use the width spinbox to set line thickness

4. **Draw**: Click and drag on the canvas to create annotations

5. **Add Text**: Select Text tool, click on canvas, enter text in dialog

6. **Clear**: Click "Clear" to remove all annotations

### Saving Screenshots

1. **Quick Save**: Click "Save" button to save with timestamp
   - Filename format: `screenshot_YYYYMMDD_HHMMSS.png`
   - Saved to default directory

2. **Save As**: Use File > Save As... to choose custom filename and location

## Toolbar Features

- **Capture Screenshot**: Capture full screen
- **Open Image**: Load existing image file
- **Tool Selection**: Radio buttons for different annotation tools
- **Color Picker**: Button showing current color (click to change)
- **Line Width**: Spinbox to adjust drawing thickness (1-20)
- **Clear**: Remove all annotations
- **Save**: Quick save with timestamp

## Menu Features

- **File > Capture Screenshot**: Capture screen
- **File > Open Image**: Load image file
- **File > Save**: Save with timestamp
- **File > Save As...**: Save with custom name
- **File > Exit**: Close application

## Troubleshooting

### Screenshot Not Capturing

If screenshots are not captured:
- Ensure you have screen capture permissions (macOS may require permission)
- Check that the mss library is installed correctly
- Verify your display is accessible
- Check logs for error messages

### GUI Not Displaying

If the GUI doesn't appear:
- Verify tkinter is installed (usually included with Python)
- Check that you have a display available (X11 on Linux)
- Try running with verbose logging to see errors

### Images Not Loading

If images fail to load:
- Verify the image file format is supported (PNG, JPEG, GIF, BMP)
- Check file permissions
- Ensure PIL/Pillow is installed correctly
- Review logs for specific error messages

### Annotations Not Saving

If annotations don't appear in saved images:
- Current implementation saves the original image
- Full annotation saving requires coordinate mapping (future enhancement)
- Annotations are visible in the GUI canvas

### Permission Errors

If you encounter permission errors:
- Ensure write permissions for screenshot directory
- Check file system permissions
- Verify sufficient disk space

## Platform-Specific Notes

### macOS

- May require screen recording permissions in System Preferences
- Grant permission when prompted or in System Preferences > Security & Privacy

### Linux

- Requires X11 display server
- May need to install tkinter separately: `sudo apt-get install python3-tk`

### Windows

- Should work out of the box with Python installation
- Ensure tkinter is included (usually is)

## Security Considerations

- Screenshots may contain sensitive information
- Be cautious when sharing screenshots
- Screenshots are saved locally by default
- Review screenshot directory contents regularly

## Performance Considerations

- Screenshot capture is fast but may briefly hide the window
- Large images may take time to load and display
- Multiple annotations may slow down canvas rendering
- Consider image size when working with very large screenshots

## Known Limitations

- Annotations are currently displayed on canvas but full coordinate mapping to saved image is a future enhancement
- Text annotations use system default fonts
- Limited to single monitor capture (primary monitor)
- No undo/redo functionality currently

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
