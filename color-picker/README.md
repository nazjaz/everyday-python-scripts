# Color Picker

A simple Python GUI application for color selection, hex code viewing, and color palette management. Built with tkinter, this tool allows users to pick colors, view their hex and RGB values, and save/load color palettes for design projects.

## Project Title and Description

The Color Picker is a graphical user interface application that simplifies color selection and palette management. Users can select colors using a system color picker, view hex codes and RGB values, build custom color palettes, and save/load palettes for later use.

This tool solves the problem of quickly selecting colors, viewing their codes, and organizing color collections for design work, web development, or any project requiring color management.

**Target Audience**: Designers, web developers, artists, and anyone who needs to work with colors and color palettes.

## Features

- Interactive color picker using system color chooser
- Real-time hex code display and editing
- RGB value display for selected colors
- Visual color preview canvas
- Build custom color palettes
- Save multiple named palettes to JSON files
- Load previously saved palettes
- Remove individual colors from palette
- Clear entire palette
- Double-click palette colors to select them
- Persistent palette storage
- Comprehensive logging

## Prerequisites

- Python 3.8 or higher
- pip package manager
- tkinter (usually included with Python, but may need separate installation on Linux)

### Installing tkinter on Linux

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/color-picker
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

### Step 4: Verify Installation

```bash
python src/main.py --help
```

## Configuration

### Configuration File (config.yaml)

The tool uses a YAML configuration file for settings. The default configuration file is `config.yaml` in the project root.

#### Key Configuration Options

**Window Settings:**
- `window.width`: Application window width in pixels (default: 600)
- `window.height`: Application window height in pixels (default: 500)

**Palette Settings:**
- `palette.save_file`: Path to JSON file for saving/loading palettes (default: "palettes.json")

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
window:
  width: 800
  height: 600

palette:
  save_file: "my_palettes.json"

logging:
  level: "DEBUG"
  file: "logs/app.log"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Start the application:

```bash
python src/main.py
```

### Specify Custom Configuration

```bash
python src/main.py -c custom_config.yaml
```

### Command-Line Arguments

- `-c, --config`: Path to configuration file (default: config.yaml)

### Using the Application

1. **Pick a Color:**
   - Click the "Pick Color" button to open the system color picker
   - Select a color and click OK
   - The color will be displayed in the preview canvas

2. **View Color Information:**
   - Hex code is displayed in the text field
   - RGB values are shown below the hex code
   - You can manually edit the hex code to change the color

3. **Add to Palette:**
   - Select a color
   - Click "Add to Palette" to add it to your current palette
   - Colors appear in the palette listbox

4. **Select from Palette:**
   - Double-click any color in the palette to select it
   - The color will be displayed in the preview area

5. **Remove Colors:**
   - Select a color in the palette listbox
   - Click "Remove Selected" to remove it

6. **Clear Palette:**
   - Click "Clear Palette" to remove all colors
   - Confirmation dialog will appear

7. **Save Palette:**
   - Build your color palette
   - Click "Save Palette"
   - Enter a name for your palette
   - The palette will be saved to a JSON file

8. **Load Palette:**
   - Click "Load Palette"
   - Enter the name of a previously saved palette
   - The palette will be loaded and displayed

### Common Use Cases

**Creating a Design Palette:**
1. Pick colors for your design project
2. Add each color to the palette
3. Save the palette with a descriptive name (e.g., "Website Theme")
4. Load it later when needed

**Quick Color Reference:**
1. Use the color picker to find a color
2. Copy the hex code for use in CSS, HTML, or design tools
3. View RGB values for other applications

**Color Exploration:**
1. Manually enter hex codes to preview colors
2. Build a collection of interesting colors
3. Save palettes for different projects

## Project Structure

```
color-picker/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation
└── logs/
    └── .gitkeep             # Placeholder for logs directory
```

### File Descriptions

- `src/main.py`: Contains the `ColorPicker` class and GUI implementation
- `config.yaml`: Configuration file with window, palette, and logging settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `palettes.json`: JSON file storing saved color palettes (created at runtime)
- `logs/`: Directory for application log files

## Testing

### Run Tests

```bash
python -m pytest tests/
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage, testing:
- Configuration loading and validation
- Color conversion functions (hex to RGB, RGB to hex)
- Palette management operations
- File I/O operations
- Error handling

## Troubleshooting

### Common Issues

**Application Won't Start:**
- Ensure Python 3.8+ is installed
- Verify tkinter is available: `python3 -c "import tkinter"`
- Install tkinter if missing (see Prerequisites)

**Color Picker Dialog Doesn't Appear:**
- Check system permissions
- Verify display server is running (Linux)
- Try running from terminal to see error messages

**Palettes Not Saving:**
- Check file permissions in the project directory
- Verify disk space is available
- Check logs for error messages

**Colors Not Displaying Correctly:**
- Verify hex code format (should be #RRGGBB)
- Check that RGB values are within 0-255 range
- Ensure color values are valid

### Error Messages

**"Configuration file not found"**: The config.yaml file is missing. Create it or use `-c` to specify a different path.

**"Invalid YAML in configuration file"**: The config.yaml file has syntax errors. Check YAML formatting.

**"No saved palettes found"**: No palettes have been saved yet. Create and save a palette first.

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guidelines
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Include docstrings for all public functions and classes
- Use meaningful variable names
- Write tests for all new functionality

### Pull Request Process

1. Ensure code follows project standards
2. Update documentation if needed
3. Add/update tests
4. Ensure all tests pass
5. Submit PR with clear description of changes

## License

This project is part of the everyday-python-scripts collection. Please refer to the parent repository for license information.
