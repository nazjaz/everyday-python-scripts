# Barcode Generator API Documentation

## BarcodeGeneratorApp Class

Main GUI application class for generating barcodes.

### Methods

#### `__init__(config_path: str = "config.yaml") -> None`

Initialize BarcodeGeneratorApp with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Default: "config.yaml"

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

**Example:**
```python
app = BarcodeGeneratorApp(config_path="config.yaml")
app.run()
```

#### `run() -> None`

Start the GUI application. This method enters the tkinter main loop and blocks until the window is closed.

**Example:**
```python
app = BarcodeGeneratorApp()
app.run()
```

#### `generate_barcode() -> None`

Generate barcode from input code. Reads code from the input field, validates it for the selected format, generates the barcode image, and displays it in the preview area.

**Raises:**
- Shows warning dialog if code is empty
- Shows error dialog if code is invalid for selected format
- Shows error dialog if barcode generation fails

**Example:**
```python
# Called internally by GUI button click
app.generate_barcode()
```

#### `save_barcode() -> None`

Save generated barcode to file. Opens a file dialog for the user to select save location and format (PNG or JPEG).

**Raises:**
- Shows warning dialog if no barcode has been generated
- Shows error dialog if file save fails

**Example:**
```python
# Called internally by GUI button click
app.save_barcode()
```

#### `clear_preview() -> None`

Clear barcode preview and reset input fields. Removes the displayed barcode image and clears the code input field.

**Example:**
```python
# Called internally by GUI button click
app.clear_preview()
```

### Internal Methods

#### `_validate_code(code: str, format_name: str) -> bool`

Validate code for selected barcode format.

**Parameters:**
- `code` (str): Code/identifier to validate
- `format_name` (str): Name of barcode format

**Returns:**
- `bool`: True if code is valid, False otherwise

**Validation Rules:**
- EAN-13: Exactly 13 numeric digits
- EAN-8: Exactly 8 numeric digits
- Code39: Uppercase letters, numbers, and special characters (-. $/%+)
- Code128: ASCII characters (0-127)

**Example:**
```python
is_valid = app._validate_code("1234567890123", "EAN-13")
```

#### `_load_config(config_path: str) -> dict`

Load configuration from YAML file.

**Parameters:**
- `config_path` (str): Path to configuration file

**Returns:**
- `dict`: Dictionary containing configuration settings

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML

#### `_setup_logging() -> None`

Configure logging based on configuration settings. Sets up file and console logging handlers.

#### `_load_supported_formats() -> Dict[str, Any]`

Load supported barcode formats from configuration.

**Returns:**
- `Dict[str, Any]`: Dictionary mapping format names to barcode classes

**Default Formats:**
- EAN-13
- EAN-8
- Code128
- Code39

Additional formats can be loaded from configuration.

#### `_setup_window() -> None`

Configure main window properties. Sets title, size, and centers window on screen.

#### `_create_widgets() -> None`

Create and arrange GUI widgets. Sets up input fields, preview area, buttons, and status bar.

### Attributes

#### `config: dict`

Configuration dictionary loaded from YAML file.

#### `supported_formats: Dict[str, Any]`

Dictionary mapping format names to barcode classes.

#### `root: Tk`

Main tkinter window object.

#### `current_barcode_image: Optional[Image.Image]`

Currently generated barcode image (PIL Image object). None if no barcode has been generated.

#### `format_var: StringVar`

Tkinter variable storing selected barcode format.

#### `code_entry: Entry`

Tkinter entry widget for code input.

#### `preview_label: Label`

Tkinter label widget for displaying barcode preview.

#### `status_var: StringVar`

Tkinter variable storing status bar text.

## Usage Example

```python
from src.main import BarcodeGeneratorApp

# Initialize and run application
app = BarcodeGeneratorApp(config_path="config.yaml")
app.run()
```

## GUI Components

### Input Section
- **Format Dropdown**: Select barcode format (EAN-13, EAN-8, Code128, Code39)
- **Code Entry**: Input field for product code or identifier
- **Generate Button**: Generate barcode from input

### Preview Section
- **Preview Area**: Displays generated barcode image
- Updates automatically when barcode is generated

### Actions Section
- **Save Button**: Save barcode to file (PNG or JPEG)
- **Clear Button**: Clear preview and reset form

### Status Bar
- Displays current status and error messages
- Updates during barcode generation and saving

## Barcode Format Details

### EAN-13
- **Class**: `EAN13` from `barcode` module
- **Length**: 13 digits
- **Characters**: Numeric (0-9)
- **Use Case**: Retail products, books

### EAN-8
- **Class**: `EAN8` from `barcode` module
- **Length**: 8 digits
- **Characters**: Numeric (0-9)
- **Use Case**: Small retail items

### Code128
- **Class**: `Code128` from `barcode` module
- **Length**: Variable
- **Characters**: ASCII (0-127)
- **Use Case**: Shipping, inventory

### Code39
- **Class**: `Code39` from `barcode` module
- **Length**: Variable
- **Characters**: Uppercase letters, numbers, special characters
- **Use Case**: Industrial, identification
