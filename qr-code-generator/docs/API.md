# API Documentation

## QRCodeGenerator Class

The main class for the QR code generator GUI application.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the QRCodeGenerator with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.

**Side Effects:**
- Loads configuration
- Sets up logging
- Creates GUI window and widgets

#### `run() -> None`

Start the GUI application main loop. This method blocks until the window is closed.

#### `_generate_qr_code() -> None`

Generate QR code from input based on selected type.

**Side Effects:**
- Reads input from GUI widgets
- Creates QR code image
- Displays QR code on canvas
- Updates status label
- Shows error messages if generation fails

**QR Code Types:**
- `text`: Plain text input
- `url`: URL input
- `contact`: Contact information (vCard format)

#### `_save_qr_code() -> None`

Save current QR code to file.

**Side Effects:**
- Opens file save dialog
- Saves QR code image to selected file
- Updates status label
- Shows error messages if save fails

#### `_format_vcard() -> str`

Format contact information as vCard.

**Returns:**
- `str`: vCard formatted string.

**vCard Format:**
```
BEGIN:VCARD
VERSION:3.0
FN:Name
N:Name;;;;
TEL:Phone
EMAIL:Email
ORG:Organization
END:VCARD
```

#### `_on_type_change(*args: Any) -> None`

Handle QR code type change event.

**Side Effects:**
- Shows/hides appropriate input widgets
- Updates GUI layout

#### `_show_text_input() -> None`

Show text input widget, hide contact input.

**Side Effects:**
- Updates GUI layout

#### `_show_contact_input() -> None`

Show contact input widgets, hide text input.

**Side Effects:**
- Updates GUI layout

### Attributes

#### `current_qr_image: Optional[Image.Image]`

Currently generated QR code image (PIL Image object). None if no QR code has been generated.

#### `config: dict`

Configuration dictionary loaded from YAML file.

#### `root: Tk`

Main Tkinter window object.

#### GUI Components

The class creates and manages the following GUI components:

- `qr_type`: StringVar for QR code type selection
- `text_entry`: Text widget for text/URL input
- `name_entry`: Entry widget for contact name
- `phone_entry`: Entry widget for contact phone
- `email_entry`: Entry widget for contact email
- `org_entry`: Entry widget for contact organization
- `qr_canvas`: Canvas widget for QR code display
- `status_label`: Label widget for status messages

### Example Usage

```python
from src.main import QRCodeGenerator

# Initialize with default config
app = QRCodeGenerator()

# Or with custom config
app = QRCodeGenerator(config_path="custom_config.yaml")

# Start the application (blocks until window closes)
app.run()
```

### QR Code Configuration

QR codes are configured through the config file:

```yaml
qr_code:
  box_size: 10        # Pixels per module
  border: 4           # Border thickness
  error_correction: "M"  # L, M, Q, or H
  fill_color: "black"
  back_color: "white"
```

### Error Correction Levels

- **L (Low)**: ~7% error correction
- **M (Medium)**: ~15% error correction (default)
- **Q (Quartile)**: ~25% error correction
- **H (High)**: ~30% error correction

Higher levels create larger QR codes but allow more damage before becoming unreadable.

### Supported File Formats

When saving QR codes, the following formats are supported:
- PNG (recommended, lossless)
- JPEG (lossy compression)

### vCard Format

Contact information is formatted as vCard 3.0, which is a standard format for electronic business cards. When scanned, compatible QR code readers will add the contact to the device's address book.
