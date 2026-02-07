# CSV Processor

Process CSV files by removing duplicate rows, standardizing date formats, cleaning data inconsistencies, and generating detailed validation reports. This tool helps ensure data quality and consistency in CSV datasets.

## Project Description

CSV Processor solves the problem of cleaning and validating CSV data files. It automatically removes duplicates, standardizes date formats across different input formats, cleans common data inconsistencies, and provides comprehensive validation reports to help identify data quality issues.

**Target Audience**: Data analysts, data engineers, and anyone working with CSV files who needs to ensure data quality and consistency.

## Features

- **Duplicate Removal**: Remove duplicate rows based on all columns or specific columns
- **Date Standardization**: Automatically detect and convert various date formats to a standard format
- **Data Cleaning**: Trim whitespace, normalize spaces, remove quotes, handle empty rows/columns
- **Data Validation**: Check for missing values, validate data types, verify value ranges
- **Detailed Reports**: Generate comprehensive validation reports with statistics and error details
- **Auto-detection**: Automatically detect date columns and data types
- **Flexible Configuration**: YAML-based configuration with extensive customization options

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- CSV files to process

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/everyday-python-scripts/csv-processor
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

### Step 4: Configure Settings

1. Copy the example environment file (if needed):
   ```bash
   cp .env.example .env
   ```

2. Edit `config.yaml` to set input and output file paths:
   ```yaml
   files:
     input_file: /path/to/input.csv
     output_file: /path/to/output.csv
   ```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **files**: Input, output, and report file paths
- **duplicate_removal**: Settings for removing duplicate rows
- **date_standardization**: Date format detection and conversion
- **data_cleaning**: Data cleaning operations and options
- **validation**: Data validation rules and checks
- **reporting**: Report content and format options

### Environment Variables

Optional environment variables can override config.yaml settings:

- `INPUT_FILE`: Override input CSV file path
- `OUTPUT_FILE`: Override output CSV file path

### Example Configuration

```yaml
files:
  input_file: data/input.csv
  output_file: data/output.csv
  report_file: logs/validation_report.txt

duplicate_removal:
  enabled: true
  method: all_columns
  keep: first

date_standardization:
  enabled: true
  target_format: "%Y-%m-%d"
  date_columns: []  # Auto-detect

data_cleaning:
  enabled: true
  trim_whitespace: true
  normalize_whitespace: true
```

## Usage

### Basic Usage

Process CSV file with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Override input file
python src/main.py -i /path/to/input.csv

# Override output file
python src/main.py -o /path/to/output.csv

# Combine options
python src/main.py -c config.yaml -i input.csv -o output.csv
```

### Common Use Cases

1. **Remove Duplicates**:
   ```yaml
   duplicate_removal:
     enabled: true
     method: all_columns
   ```

2. **Standardize Dates**:
   ```yaml
   date_standardization:
     enabled: true
     target_format: "%Y-%m-%d"
     date_columns: ["date", "created_at"]  # Or leave empty for auto-detect
   ```

3. **Clean Data**:
   ```yaml
   data_cleaning:
     trim_whitespace: true
     remove_empty_rows: true
     normalize_whitespace: true
   ```

4. **Validate Data**:
   ```yaml
   validation:
     required_columns: ["id", "name"]
     unique_columns: ["email"]
     check_value_ranges: true
     value_ranges:
       age: {min: 0, max: 120}
   ```

## Project Structure

```
csv-processor/
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
│   └── API.md              # API documentation (if applicable)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    ├── csv_processor.log   # Application logs
    └── validation_report.txt  # Validation report
```

### File Descriptions

- **src/main.py**: Core CSV processing logic, duplicate removal, date standardization, cleaning, and validation
- **config.yaml**: YAML configuration file with all processing settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/csv_processor.log**: Application log file with rotation
- **logs/validation_report.txt**: Detailed validation and processing report

## Supported Date Formats

The processor can automatically detect and convert various date formats:

- `YYYY-MM-DD` (2024-02-07)
- `MM/DD/YYYY` (02/07/2024)
- `DD/MM/YYYY` (07/02/2024)
- `YYYY/MM/DD` (2024/02/07)
- `DD-MM-YYYY` (07-02-2024)
- `MM-DD-YYYY` (02-07-2024)
- `YYYY-MM-DD HH:MM:SS` (with time)
- `YYYY-MM-DDTHH:MM:SS` (ISO format)
- `January 1, 2024` (full month name)
- `1 January 2024` (alternative format)
- `Jan 1, 2024` (abbreviated month)

## Validation Report

The validation report includes:

- **Processing Summary**: Overall statistics (rows processed, duplicates removed, etc.)
- **Column Statistics**: Data types, null counts, min/max values for numeric columns
- **Duplicate Details**: List of duplicate rows found
- **Invalid Dates**: List of date values that couldn't be parsed
- **Validation Errors**: Detailed list of validation failures
- **Cleaning Summary**: Summary of data cleaning operations performed

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
- CSV file loading
- Duplicate removal
- Date standardization
- Data cleaning
- Data validation
- Report generation
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'pandas'`

**Solution**: Install dependencies: `pip install -r requirements.txt`

---

**Issue**: Dates not being standardized

**Solution**: 
- Check that `date_standardization.enabled: true` in config.yaml
- Verify date columns are specified or auto-detection is working
- Check that input date formats match the formats in `input_formats` list

---

**Issue**: Duplicates not being removed

**Solution**: 
- Verify `duplicate_removal.enabled: true` in config.yaml
- Check that `method` is set correctly (all_columns, specific_columns, etc.)
- If using `specific_columns`, ensure column names are correct

---

**Issue**: Validation report not generated

**Solution**: 
- Check that `report_file` path in config.yaml is valid
- Ensure logs directory exists and is writable
- Check file permissions

---

**Issue**: Memory error with large CSV files

**Solution**: 
- Process files in chunks (modify code to use `chunksize` parameter in `pd.read_csv`)
- Increase available memory
- Consider processing subsets of data

### Error Messages

- **"Input file not specified"**: Set `files.input_file` in config.yaml or use `-i` option
- **"CSV file not found"**: Verify input file path is correct
- **"CSV file is empty"**: Input file has no data rows
- **"Required column not found"**: Column specified in validation doesn't exist in CSV

## Performance Considerations

- **Large Files**: For CSV files with millions of rows, processing may take time
- **Memory Usage**: Entire CSV is loaded into memory (pandas DataFrame)
- **Date Detection**: Auto-detection scans sample rows, which may take time for large files
- **Recommendations**: 
  - Process files in batches if memory is limited
  - Specify date columns explicitly to avoid auto-detection overhead
  - Use specific columns for duplicate detection to improve performance

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
