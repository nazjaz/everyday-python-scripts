# Excel Sheet Merger

A Python automation tool that processes Excel files by reading multiple sheets, merging data using configurable strategies, validating data integrity, and exporting the merged result to CSV format with comprehensive error handling.

## Features

- Read multiple sheets from Excel files (.xlsx, .xls, .xlsm)
- Flexible merging strategies: concatenation, union, intersection, and join
- Comprehensive data validation with configurable rules
- Data cleaning options (duplicate removal, empty row/column removal)
- Robust error handling with detailed logging
- Configurable CSV export options
- Support for environment variable overrides
- Detailed processing statistics and validation reports

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd excel-sheet-merger
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

## Configuration

### Configuration File

The tool uses a YAML configuration file (`config.yaml`) for settings. Key configuration sections:

- **files**: Input and output file paths
- **sheets**: Sheet selection (specific sheets or all sheets)
- **merging**: Merge strategy and options
- **validation**: Data validation rules
- **cleaning**: Data cleaning options
- **csv_export**: CSV export settings

### Environment Variables

You can override configuration using environment variables:

- `INPUT_FILE`: Path to input Excel file
- `OUTPUT_FILE`: Path to output CSV file

Create a `.env` file in the project root (see `.env.example` for template).

### Example Configuration

```yaml
files:
  input_file: "data/input.xlsx"
  output_file: "data/output.csv"

sheets:
  names: ["Sheet1", "Sheet2"]  # or null for all sheets

merging:
  strategy: concat  # Options: concat, union, intersection, join
  add_sheet_column: true
```

## Usage

### Command Line

Basic usage with configuration file:
```bash
python src/main.py
```

Specify custom configuration file:
```bash
python src/main.py -c custom_config.yaml
```

Override input/output files:
```bash
python src/main.py -i input.xlsx -o output.csv
```

### Merge Strategies

1. **concat**: Simple concatenation of all sheets (default)
   - Combines all rows from all sheets
   - Preserves all columns from each sheet

2. **union**: Union of all columns
   - Combines all unique columns from all sheets
   - Missing values filled with NaN

3. **intersection**: Only common columns
   - Only includes columns present in all sheets
   - Useful when sheets have consistent structure

4. **join**: Join on specified key columns
   - Requires `join.keys` configuration
   - Supports inner, left, right, and outer joins

### Example Use Cases

**Merge all sheets from an Excel file:**
```yaml
sheets:
  names: null  # Process all sheets
merging:
  strategy: concat
```

**Merge specific sheets with union strategy:**
```yaml
sheets:
  names: ["Sales", "Inventory", "Orders"]
merging:
  strategy: union
```

**Join sheets on a common key:**
```yaml
merging:
  strategy: join
  join:
    keys: ["id", "date"]
    type: inner
```

## Project Structure

```
excel-sheet-merger/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── API.md
└── logs/
    └── .gitkeep
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_main.py::test_load_excel_sheets
```

## Troubleshooting

### Common Issues

**File not found error:**
- Verify the input file path is correct
- Check file permissions
- Ensure file extension is supported (.xlsx, .xls, .xlsm)

**Sheet not found error:**
- Verify sheet names in configuration match actual sheet names
- Check for typos or case sensitivity
- Use `null` in `sheets.names` to process all sheets

**Memory errors with large files:**
- Process sheets individually by specifying sheet names
- Consider splitting large Excel files
- Increase system memory if possible

**Encoding issues in CSV export:**
- Adjust `csv_export.encoding` in configuration
- Use UTF-8 with BOM for Excel compatibility: `utf-8-sig`

**Validation errors:**
- Review validation rules in configuration
- Check required columns exist in all sheets
- Adjust validation settings as needed

### Error Messages

The tool provides detailed error messages in logs. Check `logs/excel_merger.log` for:
- File access errors
- Sheet loading failures
- Validation issues
- Merge strategy problems

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
