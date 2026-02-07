# Password Generator

A Python GUI application for generating secure, customizable passwords. Create strong passwords with configurable length, character sets, and options for excluding similar or ambiguous characters. Includes clipboard integration for easy password copying.

## Features

- **Graphical User Interface**: Easy-to-use GUI built with tkinter
- **Customizable Length**: Adjustable password length from 4 to 128 characters
- **Character Set Selection**: Choose from lowercase, uppercase, digits, and symbols
- **Smart Exclusions**: Option to exclude similar-looking characters (0, O, l, I, 1) and ambiguous characters
- **Clipboard Integration**: One-click copy to clipboard functionality
- **Cryptographically Secure**: Uses `secrets` module for secure random number generation
- **Entropy Calculation**: Calculates password entropy for security assessment
- **CLI Mode**: Optional command-line interface for scripted password generation
- **Configurable**: Highly customizable through YAML configuration file

## Prerequisites

- Python 3.8 or higher
- tkinter (usually included with Python, but may need separate installation on Linux)
- pip (Python package installer)

### Installing tkinter

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install python3-tkinter
```

**macOS/Windows:**
tkinter is typically included with Python installations.

## Installation

### Step 1: Clone or Navigate to Project Directory

```bash
cd everyday-python-scripts/password-generator
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

### Step 4: Configure Environment (Optional)

Copy `.env.example` to `.env` and modify if needed:

```bash
cp .env.example .env
```

Edit `.env` to set logging level or other environment variables.

### Step 5: Review Configuration

Edit `config.yaml` to customize default password settings, character sets, and GUI appearance.

## Configuration

The `config.yaml` file contains all configuration options:

### Default Password Settings

```yaml
defaults:
  length: 16              # Default password length
  min_length: 4          # Minimum allowed length
  max_length: 128        # Maximum allowed length
  character_sets:
    lowercase: true       # Include lowercase letters
    uppercase: true       # Include uppercase letters
    digits: true         # Include digits
    symbols: true        # Include symbols
    exclude_similar: true    # Exclude similar characters
    exclude_ambiguous: false  # Exclude ambiguous characters
```

### Character Set Definitions

```yaml
characters:
  lowercase: "abcdefghijklmnopqrstuvwxyz"
  uppercase: "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  digits: "0123456789"
  symbols: "!@#$%^&*()_+-=[]{}|;:,.<>?"
  similar_chars: "0OIl1"      # Characters to exclude as similar
  ambiguous_chars: "{}[]()/\\'\"`~,;:.<>"  # Ambiguous characters
```

### GUI Settings

```yaml
gui:
  title: "Password Generator"
  window_width: 500
  window_height: 600
  font_family: "Arial"
  font_size: 10
```

### Security Settings

```yaml
security:
  use_secure_random: true    # Use cryptographically secure RNG
  min_entropy_bits: 40       # Minimum entropy for validation
```

## Usage

### GUI Mode (Default)

Launch the graphical interface:

```bash
python src/main.py
```

**Using the GUI:**

1. Adjust password length using the slider (4-128 characters)
2. Select character sets to include:
   - Lowercase letters (a-z)
   - Uppercase letters (A-Z)
   - Digits (0-9)
   - Symbols (!@#$%...)
3. Configure options:
   - Exclude similar characters (0, O, l, I, 1)
   - Exclude ambiguous characters ({, }, [, ], etc.)
4. Click "Generate Password" to create a new password
5. Click "Copy to Clipboard" to copy the password

### CLI Mode

Generate passwords from the command line:

```bash
# Generate with default settings
python src/main.py --cli

# Generate with custom length
python src/main.py --cli -l 32

# Generate without certain character sets
python src/main.py --cli -l 20 --no-symbols --no-digits

# Generate with all options
python src/main.py --cli -l 24
```

**CLI Options:**

- `--cli`: Enable CLI mode (non-GUI)
- `-l, --length`: Password length
- `--no-lowercase`: Exclude lowercase letters
- `--no-uppercase`: Exclude uppercase letters
- `--no-digits`: Exclude digits
- `--no-symbols`: Exclude symbols
- `-c, --config`: Path to custom configuration file

### Examples

**Generate a 20-character password with all character types:**
```bash
python src/main.py --cli -l 20
```

**Generate a 12-character alphanumeric password (no symbols):**
```bash
python src/main.py --cli -l 12 --no-symbols
```

**Generate a 16-character password with only lowercase and digits:**
```bash
python src/main.py --cli -l 16 --no-uppercase --no-symbols
```

## Project Structure

```
password-generator/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/                    # Additional documentation
└── logs/                    # Log files directory
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with verbose output:

```bash
pytest tests/ -v
```

Run specific test:

```bash
pytest tests/test_main.py::TestPasswordGenerator::test_generate_password_valid_length
```

## Security Considerations

- **Cryptographically Secure**: Uses Python's `secrets` module for secure random number generation
- **No Password Storage**: Passwords are never saved or logged (only generation events are logged)
- **Entropy Calculation**: Password entropy is calculated to assess security strength
- **Configurable Security**: Can enforce minimum entropy requirements

### Password Strength Guidelines

- **8-12 characters**: Minimum for low-security applications
- **16-20 characters**: Recommended for most applications
- **24+ characters**: Recommended for high-security applications
- **Use all character types**: Lowercase, uppercase, digits, and symbols for maximum security
- **Avoid similar characters**: Exclude 0, O, l, I, 1 to prevent confusion

## Troubleshooting

### Error: tkinter is not available

**Solution:** Install tkinter for your Python version:

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter

# macOS/Windows: Usually included with Python
```

### Error: No password to copy

**Solution:** Generate a password first by clicking "Generate Password" before copying.

### Error: At least one character set must be selected

**Solution:** Ensure at least one character set checkbox is selected (lowercase, uppercase, digits, or symbols).

### GUI Window Not Appearing

**Solution:**
- Check that tkinter is properly installed
- Verify Python version is 3.8 or higher
- Check logs in `logs/password_generator.log` for errors

### Clipboard Not Working

**Solution:**
- Ensure clipboard access permissions are granted (Linux may require additional packages)
- Try running with appropriate permissions
- Check system clipboard functionality

### Password Too Weak

**Solution:**
- Increase password length
- Enable all character sets (lowercase, uppercase, digits, symbols)
- Disable exclusions if possible
- Check entropy calculation in logs

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for all public functions and classes
4. Add unit tests for new features
5. Update README.md for user-facing changes
6. Test GUI on multiple platforms if possible

## License

This project is provided as-is for automation and utility purposes.
