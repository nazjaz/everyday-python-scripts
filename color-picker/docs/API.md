# API Documentation

## ColorPicker Class

The main class for the color picker GUI application.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the ColorPicker with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.

**Side Effects:**
- Creates GUI window and widgets
- Loads saved palettes if available
- Sets up logging

#### `run() -> None`

Start the GUI application main loop. This method blocks until the window is closed.

#### `_hex_to_rgb(hex_color: str) -> tuple`

Convert hex color string to RGB tuple.

**Parameters:**
- `hex_color` (str): Hex color string (with or without # prefix).

**Returns:**
- `tuple`: Tuple of (R, G, B) values, each 0-255.

**Example:**
```python
rgb = picker._hex_to_rgb("#FF0000")
# Returns: (255, 0, 0)
```

#### `_rgb_to_hex(r: int, g: int, b: int) -> str`

Convert RGB values to hex color string.

**Parameters:**
- `r` (int): Red value (0-255).
- `g` (int): Green value (0-255).
- `b` (int): Blue value (0-255).

**Returns:**
- `str`: Hex color string with # prefix (e.g., "#FF0000").

**Example:**
```python
hex_color = picker._rgb_to_hex(255, 0, 0)
# Returns: "#FF0000"
```

#### `_update_color_display(hex_color: str) -> None`

Update the color display canvas and hex/RGB labels.

**Parameters:**
- `hex_color` (str): Hex color string to display.

**Side Effects:**
- Updates color preview canvas
- Updates hex code entry field
- Updates RGB label
- Sets `self.current_color`

#### `_pick_color() -> None`

Open system color picker dialog and update display with selected color.

**Side Effects:**
- Opens color chooser dialog
- Updates color display if color is selected
- Logs color selection

#### `_add_to_palette() -> None`

Add current color to the palette list.

**Side Effects:**
- Adds color entry to `self.palette`
- Updates palette display
- Shows warning if no color is selected

#### `_remove_from_palette() -> None`

Remove selected color from palette.

**Side Effects:**
- Removes color from `self.palette`
- Updates palette display
- Shows warning if no color is selected

#### `_clear_palette() -> None`

Clear all colors from the palette.

**Side Effects:**
- Clears `self.palette`
- Updates palette display
- Shows confirmation dialog

#### `_save_palette() -> None`

Save current palette to JSON file.

**Side Effects:**
- Prompts for palette name
- Saves palette to file specified in config
- Shows success/error message
- Logs save operation

#### `_load_palette() -> None`

Load a saved palette from JSON file.

**Side Effects:**
- Prompts for palette name
- Loads palette from file
- Updates `self.palette`
- Updates palette display
- Shows success/error message

### Attributes

#### `current_color: Optional[str]`

Currently selected color as hex string (e.g., "#FF0000"). None if no color is selected.

#### `palette: List[Dict[str, str]]`

List of color entries in the current palette. Each entry contains:
- `hex`: Hex color string
- `rgb`: RGB values as string (e.g., "(255, 0, 0)")

#### `palette_file: Path`

Path object pointing to the JSON file where palettes are saved/loaded.

#### `config: dict`

Configuration dictionary loaded from YAML file.

### GUI Components

The class creates and manages the following GUI components:

- `root`: Main Tk window
- `color_canvas`: Canvas widget displaying selected color
- `hex_entry`: Entry widget for hex code display/editing
- `rgb_label`: Label widget displaying RGB values
- `palette_listbox`: Listbox widget displaying palette colors

### Example Usage

```python
from src.main import ColorPicker

# Initialize with default config
app = ColorPicker()

# Or with custom config
app = ColorPicker(config_path="custom_config.yaml")

# Start the application (blocks until window closes)
app.run()
```

### Palette File Format

Palettes are saved in JSON format:

```json
{
  "palettes": {
    "palette_name": {
      "colors": [
        {
          "hex": "#FF0000",
          "rgb": "(255, 0, 0)"
        },
        {
          "hex": "#00FF00",
          "rgb": "(0, 255, 0)"
        }
      ]
    }
  },
  "default_palette": "palette_name"
}
```
