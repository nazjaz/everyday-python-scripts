# Barcode Generator

A Python GUI application for generating barcodes in various formats from product codes or identifiers. Supports multiple barcode formats including EAN-13, EAN-8, Code128, Code39, and more.

## Features

- **Graphical User Interface**: Simple and intuitive GUI built with tkinter
- **Multiple Barcode Formats**: Supports various barcode formats:
  - EAN-13 (13-digit European Article Number)
  - EAN-8 (8-digit European Article Number)
  - Code128 (high-density alphanumeric)
  - Code39 (alphanumeric with special characters)
  - Additional formats can be added via configuration
- **Real-Time Preview**: Preview generated barcodes before saving
- **Code Validation**: Validates input codes according to format requirements
- **Image Export**: Save barcodes as PNG or JPEG images
- **Configurable**: Customizable barcode appearance and writer options via YAML configuration
- **Error Handling**: Comprehensive error handling with user-friendly messages

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Tkinter (usually included with Python, but may need separate installation on Linux)

### Linux Tkinter Installation

If tkinter is not available, install it:

```bash
# Debian/Ubuntu
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd barcode-generator
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The script uses `config.yaml` for configuration. Key settings include:

### Barcode Settings

- `additional_formats`: List of additional barcode formats to load
- `writer_options`: Options for barcode image generation:
  - `module_width`: Width of each bar/space
  - `module_height`: Height of bars
  - `quiet_zone`: Empty space on sides
  - `font_size`: Font size for text below barcode
  - `text_distance`: Distance of text from barcode
  - `background`: Background color
  - `foreground`: Foreground color
  - `center_text`: Whether to center text below barcode
  - `write_text`: Whether to write text below barcode

### Example Configuration

```yaml
barcode:
  additional_formats: ["ISBN10", "ISBN13"]
  writer_options:
    module_width: 0.5
    module_height: 15.0
    quiet_zone: 6.5
    font_size: 10
    background: "white"
    foreground: "black"
    center_text: true
    write_text: true
```

## Usage

### Basic Usage

Run the application:

```bash
python src/main.py
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)

### Examples

**Run with default configuration**:
```bash
python src/main.py
```

**Run with custom configuration**:
```bash
python src/main.py -c custom_config.yaml
```

### Using the GUI

1. **Select Format**: Choose the barcode format from the dropdown menu
2. **Enter Code**: Type the product code or identifier in the input field
3. **Generate**: Click "Generate Barcode" or press Enter
4. **Preview**: View the generated barcode in the preview area
5. **Save**: Click "Save Barcode" to save the barcode as an image file
6. **Clear**: Click "Clear" to reset the form

## Project Structure

```
barcode-generator/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── config.yaml            # Configuration file
├── .gitignore            # Git ignore patterns
├── src/
│   └── main.py           # Main application
├── tests/
│   └── test_main.py      # Unit tests
├── docs/
│   └── API.md            # API documentation
└── logs/
    └── .gitkeep          # Placeholder for logs
```

## Supported Barcode Formats

### EAN-13
- **Description**: 13-digit European Article Number
- **Code Requirements**: Exactly 13 numeric digits
- **Example**: `1234567890123`
- **Use Case**: Retail products, books (ISBN-13)

### EAN-8
- **Description**: 8-digit European Article Number
- **Code Requirements**: Exactly 8 numeric digits
- **Example**: `12345670`
- **Use Case**: Small retail items

### Code128
- **Description**: High-density alphanumeric barcode
- **Code Requirements**: ASCII characters (0-127)
- **Example**: `ABC123`, `Test-456`
- **Use Case**: Shipping labels, inventory management

### Code39
- **Description**: Alphanumeric barcode with special characters
- **Code Requirements**: Uppercase letters, numbers, and special characters (-. $/%+)
- **Example**: `ABC-123`, `TEST-456`
- **Use Case**: Industrial applications, identification

### Additional Formats

Additional formats can be added via configuration. Supported formats include:
- ISBN10, ISBN13
- UPC, UPC-A, UPC-E
- I2of5, MSI
- And more (check python-barcode documentation)

## Code Format Requirements

### EAN-13
- Must be exactly 13 digits
- All characters must be numeric (0-9)

### EAN-8
- Must be exactly 8 digits
- All characters must be numeric (0-9)

### Code39
- Must contain only uppercase letters, numbers, and special characters: `-. $/%+`
- No lowercase letters allowed

### Code128
- Can contain any ASCII characters (0-127)
- Supports both uppercase and lowercase letters

## Testing

Run the test suite using pytest:

```bash
pytest tests/test_main.py -v
```

For coverage report:

```bash
pytest tests/test_main.py --cov=src --cov-report=html
```

## Troubleshooting

### "No module named 'tkinter'"

Install tkinter for your Python version:
- Linux: `sudo apt-get install python3-tk` (or equivalent)
- macOS: Usually included with Python
- Windows: Usually included with Python

### "Invalid Code" Error

Ensure your code matches the format requirements:
- EAN-13: Exactly 13 numeric digits
- EAN-8: Exactly 8 numeric digits
- Code39: Uppercase letters, numbers, and allowed special characters only
- Code128: ASCII characters only

### Barcode Not Displaying

- Check that the code is valid for the selected format
- Verify that all dependencies are installed correctly
- Check the logs for error messages

### Image Save Fails

- Ensure you have write permissions in the target directory
- Check available disk space
- Verify the file path is valid

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for all public functions and classes
4. Add unit tests for new features
5. Update documentation as needed

## License

This project is provided as-is for educational and personal use.
