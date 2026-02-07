# Calculator GUI

A simple calculator application with graphical user interface, supporting basic arithmetic operations, history tracking, and memory functions. This tool provides a clean, easy-to-use calculator for everyday calculations.

## Project Description

Calculator GUI solves the problem of needing a simple, reliable calculator application by providing a desktop GUI application with basic arithmetic operations, calculation history tracking, and memory functions. All calculations are logged and can be reviewed later.

**Target Audience**: General users, students, professionals, and anyone who needs a simple calculator application with history and memory features.

## Features

- **Basic Arithmetic Operations**: Addition (+), subtraction (-), multiplication (*), division (/)
- **Graphical User Interface**: Clean, intuitive GUI built with tkinter
- **History Tracking**: View and manage calculation history
- **Memory Functions**: Memory add (M+), memory subtract (M-), memory recall (MR), memory clear (MC)
- **Persistent History**: Save and load calculation history from file
- **Error Handling**: Graceful handling of division by zero and invalid operations
- **Clear Functions**: Clear (C) and Clear Entry (CE) buttons
- **Decimal Support**: Full decimal number support

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- tkinter (usually included with Python)
  - Linux: `sudo apt-get install python3-tk`
  - macOS: Included with Python
  - Windows: Included with Python

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/calculator-gui
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

### Step 4: Verify tkinter Installation

```bash
python3 -c "import tkinter; print('tkinter is available')"
```

If tkinter is not available, install it:
- **Linux**: `sudo apt-get install python3-tk`
- **macOS**: Should be included with Python
- **Windows**: Should be included with Python

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **gui**: Window title, size, and resizable options
- **history**: History file path and save settings
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `HISTORY_FILE`: Override history file path
- `SAVE_HISTORY`: Enable/disable history saving ("true" or "false")

### Example Configuration

```yaml
gui:
  title: "Calculator"
  window_size: "300x400"
  resizable_width: false
  resizable_height: false

history:
  save_to_file: true
  file: "data/calculator_history.json"
  max_entries: 100
```

## Usage

### Basic Usage

Run the calculator:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml
```

### Calculator Operations

#### Basic Operations

- **Digits (0-9)**: Input numbers
- **Decimal (.)**: Input decimal point
- **Operations (+, -, *, /)**: Perform arithmetic operations
- **Equals (=)**: Calculate result
- **Clear (C)**: Clear all (current value, previous value, operation)
- **Clear Entry (CE)**: Clear current entry only

#### Memory Functions

- **M+**: Add current value to memory
- **M-**: Subtract current value from memory
- **MR**: Recall value from memory
- **MC**: Clear memory

#### History

- **H**: Open history window to view previous calculations
- History window shows:
  - Calculation expressions
  - Results
  - Timestamps
  - Clear history button

### Example Calculations

1. **Simple Addition**:
   - Click: `5`, `+`, `3`, `=`
   - Result: `8`

2. **Multiplication**:
   - Click: `10`, `*`, `2.5`, `=`
   - Result: `25`

3. **Using Memory**:
   - Click: `10`, `M+` (add 10 to memory)
   - Click: `5`, `*`, `2`, `=` (calculate 5 * 2 = 10)
   - Click: `MR` (recall memory: 10)
   - Click: `+`, `5`, `=` (10 + 5 = 15)

4. **View History**:
   - Click: `H` button
   - View all previous calculations with timestamps

## Project Structure

```
calculator-gui/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation
├── data/
│   └── calculator_history.json  # Calculation history (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    └── calculator.log      # Application logs
```

### File Descriptions

- **src/main.py**: Calculator engine, GUI setup, and event handling
- **config.yaml**: YAML configuration file with GUI and history settings
- **tests/test_main.py**: Unit tests for calculator engine
- **data/calculator_history.json**: JSON file storing calculation history
- **logs/calculator.log**: Application log file with rotation

## Calculator Engine

The calculator engine (`CalculatorEngine`) provides:

- **State Management**: Tracks current value, previous value, and operation
- **Calculation Logic**: Performs arithmetic operations
- **Memory Management**: Stores and retrieves memory value
- **History Tracking**: Maintains list of previous calculations

## History System

### History Features

- **Automatic Tracking**: All calculations are automatically added to history
- **Persistent Storage**: History is saved to JSON file on exit
- **History Window**: View all calculations with expressions, results, and timestamps
- **Clear History**: Clear all history entries

### History File Format

History is stored in JSON format:

```json
{
  "history": [
    {
      "expression": "10 + 5",
      "result": "15",
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "saved_at": "2024-01-15T10:35:00"
}
```

## Memory Functions

The calculator supports four memory operations:

1. **M+ (Memory Add)**: Adds current display value to memory
2. **M- (Memory Subtract)**: Subtracts current display value from memory
3. **MR (Memory Recall)**: Recalls memory value to display
4. **MC (Memory Clear)**: Clears memory (sets to 0)

Memory persists during the session but is reset when the application closes.

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Calculator engine operations
- Memory functions
- History tracking
- Error handling (division by zero)
- Input validation

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'tkinter'`

**Solution**: 
- **Linux**: Install tkinter: `sudo apt-get install python3-tk`
- **macOS**: tkinter should be included with Python. If missing, reinstall Python.
- **Windows**: tkinter should be included with Python. If missing, reinstall Python.

---

**Issue**: GUI window doesn't appear

**Solution**: 
- Check that tkinter is properly installed
- Verify Python version (3.8+)
- Check logs for errors
- Try running with verbose logging

---

**Issue**: History not saving

**Solution**: 
- Check that `history.save_to_file` is `true` in config.yaml
- Verify write permissions for data directory
- Check logs for file write errors

---

**Issue**: Division by zero shows "Error"

**Solution**: This is expected behavior. The calculator prevents division by zero and displays "Error". Click C to clear and continue.

---

**Issue**: Calculator buttons not responding

**Solution**: 
- Check logs for errors
- Verify tkinter is working: `python3 -c "import tkinter; tkinter._test()"`
- Restart the application

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists or provide correct path with `-c` option
- **"tkinter not available"**: Install tkinter for your platform
- **"Calculation error"**: Invalid operation (e.g., division by zero)

## GUI Customization

You can customize the GUI appearance in `config.yaml`:

```yaml
gui:
  title: "My Calculator"  # Window title
  window_size: "350x450"  # Window size (width x height)
  resizable_width: true   # Allow horizontal resizing
  resizable_height: true  # Allow vertical resizing
```

## Keyboard Shortcuts

While the calculator is primarily mouse-operated, you can enhance it with keyboard support by modifying the code. Currently, all operations are performed via button clicks.

## Performance Considerations

- **History Size**: Large history files may slow down loading. Consider limiting history entries.
- **GUI Responsiveness**: The GUI remains responsive during calculations
- **Memory Usage**: Minimal memory footprint for calculator operations

## Security Considerations

- **History File**: History file contains calculation data - ensure appropriate file permissions
- **Input Validation**: All inputs are validated to prevent errors
- **Error Handling**: Division by zero and invalid operations are handled gracefully

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-mock pytest-cov`
5. Create a feature branch: `git checkout -b feature/your-feature`

### Code Style Guidelines

- Follow PEP 8 style guide
- Maximum line length: 88 characters (Black formatter)
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Run tests before committing: `pytest tests/`

### Pull Request Process

1. Ensure all tests pass
2. Update README.md if adding new features
3. Add tests for new functionality
4. Submit pull request with clear description

## License

This project is provided as-is for educational and personal use.
