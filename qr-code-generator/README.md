# QR Code Generator

A simple Python GUI application for generating QR codes from text, URLs, or contact information. Built with tkinter and qrcode, this tool provides an easy-to-use interface for creating QR codes that can be saved as image files.

## Project Title and Description

The QR Code Generator is a graphical user interface application that simplifies QR code creation. Users can generate QR codes from plain text, URLs, or contact information (vCard format). The application provides a preview of the generated QR code and allows users to save it in various image formats.

This tool solves the problem of quickly creating QR codes without needing to use online services or complex command-line tools. It's useful for creating QR codes for websites, contact information, or any text data that needs to be easily shareable.

**Target Audience**: General users, developers, marketers, and anyone who needs to create QR codes quickly and easily.

## Features

- Generate QR codes from text input
- Generate QR codes from URLs
- Generate QR codes from contact information (vCard format)
- Real-time QR code preview
- Save QR codes as PNG or JPEG images
- Configurable QR code settings (size, error correction, colors)
- Simple, intuitive GUI interface
- Multiple input types with dynamic interface
- Validation and error handling

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
cd /path/to/everyday-python-scripts/qr-code-generator
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
- `window.height`: Application window height in pixels (default: 700)

**QR Code Settings:**
- `qr_code.box_size`: Pixels per module (default: 10)
- `qr_code.border`: Border thickness in modules (default: 4)
- `qr_code.error_correction`: Error correction level - L, M, Q, or H (default: M)
- `qr_code.fill_color`: Foreground color (default: "black")
- `qr_code.back_color`: Background color (default: "white")

**Save Settings:**
- `save.default_directory`: Default directory for saving QR codes (default: ".")

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
window:
  width: 800
  height: 800

qr_code:
  box_size: 15
  border: 5
  error_correction: "H"
  fill_color: "blue"
  back_color: "white"

save:
  default_directory: "~/Downloads"

logging:
  level: "INFO"
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

1. **Select QR Code Type:**
   - Choose from "text", "url", or "contact" from the dropdown

2. **Enter Data:**
   - **Text/URL**: Enter text or URL in the text area
   - **Contact**: Fill in name, phone, email, and/or organization fields

3. **Generate QR Code:**
   - Click "Generate QR Code" button
   - Preview will appear in the canvas

4. **Save QR Code:**
   - Click "Save QR Code" button
   - Choose location and filename
   - Select format (PNG or JPEG)

### QR Code Types

**Text:**
- Enter any plain text
- Useful for short messages, notes, or data

**URL:**
- Enter a web URL (e.g., https://example.com)
- When scanned, opens the URL in a browser

**Contact:**
- Fill in contact information fields
- Generates vCard format QR code
- When scanned, adds contact to phone's address book
- At least one field (name, phone, or email) is required

### Common Use Cases

**Generate Website QR Code:**
1. Select "url" type
2. Enter website URL
3. Generate and save

**Create Contact QR Code:**
1. Select "contact" type
2. Fill in contact information
3. Generate and save
4. Share QR code for easy contact sharing

**Create Text QR Code:**
1. Select "text" type
2. Enter any text
3. Generate and save

## Project Structure

```
qr-code-generator/
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

- `src/main.py`: Contains the `QRCodeGenerator` class and GUI implementation
- `config.yaml`: Configuration file with window, QR code, and logging settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `logs/`: Directory for application log files

## Error Correction Levels

QR codes support different error correction levels:

- **L (Low)**: ~7% error correction - Smallest QR codes, less damage tolerance
- **M (Medium)**: ~15% error correction - Default, good balance
- **Q (Quartile)**: ~25% error correction - Better damage tolerance
- **H (High)**: ~30% error correction - Largest QR codes, best damage tolerance

Higher error correction creates larger QR codes but allows more damage before becoming unreadable.

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
- QR code generation for different types
- vCard formatting
- Error handling
- GUI component creation

## Troubleshooting

### Common Issues

**Application Won't Start:**
- Ensure Python 3.8+ is installed
- Verify tkinter is available: `python3 -c "import tkinter"`
- Install tkinter if missing (see Prerequisites)

**QR Code Not Generating:**
- Check that input is not empty
- For contact type, ensure at least one field is filled
- Review logs for error messages

**QR Code Not Displaying:**
- Check that PIL/Pillow is properly installed
- Verify image display canvas is visible
- Try regenerating the QR code

**Cannot Save QR Code:**
- Check file permissions in save directory
- Ensure disk space is available
- Verify file format is supported (PNG or JPEG)

### Error Messages

**"Configuration file not found"**: The config.yaml file is missing. Create it or use `-c` to specify a different path.

**"Invalid YAML in configuration file"**: The config.yaml file has syntax errors. Check YAML formatting.

**"Please enter text or URL"**: Text input is empty. Enter some text before generating.

**"Please fill in at least one contact field"**: Contact fields are empty. Fill in at least name, phone, or email.

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
