# API Documentation

## CalculatorEngine Class

### Methods

#### `__init__()`

Initialize calculator engine.

**Attributes:**
- `memory`: Current memory value (float)
- `current_value`: Current display value (str)
- `previous_value`: Previous value for operations (float or None)
- `operation`: Current operation (str or None)
- `history`: List of calculation history entries

#### `input_digit(digit: str) -> str`

Input a digit.

**Parameters:**
- `digit`: Digit string (0-9)

**Returns:**
- Current display value

#### `input_decimal() -> str`

Input decimal point.

**Returns:**
- Current display value

#### `clear() -> str`

Clear current value, previous value, and operation.

**Returns:**
- Current display value ("0")

#### `clear_entry() -> str`

Clear current entry only (preserves operation and previous value).

**Returns:**
- Current display value ("0")

#### `set_operation(operation: str) -> Optional[str]`

Set operation to perform.

**Parameters:**
- `operation`: Operation symbol (+, -, *, /)

**Returns:**
- Current display value or None if operation should be performed

**Behavior:**
- If operation already set, performs calculation first
- Sets previous value to current value
- Resets current value to "0"

#### `calculate() -> Optional[str]`

Perform calculation.

**Returns:**
- Result as string or None if error (e.g., division by zero)

**Behavior:**
- Performs operation between previous and current values
- Adds calculation to history
- Resets operation and previous value
- Returns result as current value

#### `memory_add() -> None`

Add current value to memory.

#### `memory_subtract() -> None`

Subtract current value from memory.

#### `memory_recall() -> str`

Recall value from memory.

**Returns:**
- Memory value as string (also sets current value)

#### `memory_clear() -> None`

Clear memory (set to 0.0).

#### `get_history() -> List[Dict[str, str]]`

Get calculation history.

**Returns:**
- List of history entries, each containing:
  - `expression`: Calculation expression
  - `result`: Calculation result
  - `timestamp`: ISO format timestamp

#### `clear_history() -> None`

Clear calculation history.

## CalculatorGUI Class

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize calculator GUI.

**Parameters:**
- `config_path`: Path to configuration YAML file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML
- `ImportError`: If tkinter is not available

#### `run() -> None`

Run the calculator application (starts GUI main loop).

#### `_button_click(label: str) -> None`

Handle button click event.

**Parameters:**
- `label`: Button label (digit, operation, function)

#### `_show_history() -> None`

Show calculation history window.

#### `_clear_history() -> None`

Clear calculation history (called from history window).

#### `_load_history() -> None`

Load history from file.

#### `_save_history() -> None`

Save history to file.

#### `_on_closing() -> None`

Handle window closing event (saves history before exit).

## Configuration Structure

```yaml
gui:
  title: "Calculator"  # Window title
  window_size: "300x400"  # Window size (width x height)
  resizable_width: false  # Allow horizontal resizing
  resizable_height: false  # Allow vertical resizing

history:
  save_to_file: true  # Save history to file
  file: "data/calculator_history.json"  # History file path
  max_entries: 100  # Maximum history entries

logging:
  level: "INFO"  # Logging level
  file: "logs/calculator.log"  # Log file path
  max_bytes: 10485760  # Max log file size
  backup_count: 5  # Number of backup log files
```

## History File Format

History is stored in JSON format:

```json
{
  "history": [
    {
      "expression": "5.0 + 3.0",
      "result": "8.0",
      "timestamp": "2024-01-15T10:30:00.123456"
    }
  ],
  "saved_at": "2024-01-15T10:35:00.123456"
}
```

## Error Handling

The calculator handles the following errors:

- **Division by zero**: Returns `None` from `calculate()`, displays "Error"
- **Invalid operations**: Returns `None` from `calculate()`
- **Invalid input**: Validated at input level
- **File errors**: Logged but don't prevent calculator operation
