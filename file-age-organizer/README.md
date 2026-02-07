# File Age Organizer

A Python automation tool that organizes files by age into categories like New, Recent, Old, and Very-Old based on configurable time thresholds.

## Features

- Organize files by age into configurable categories
- Support for multiple age categories (New, Recent, Old, Very-Old)
- Configurable time thresholds (days, hours, or minutes)
- Move or copy files to category folders
- Recursive or non-recursive directory scanning
- Configurable exclusions (patterns, directories, extensions)
- Handle duplicate file names (skip, rename, or overwrite)
- Comprehensive error handling and logging
- Dry-run mode to preview operations
- Detailed reports with category distribution
- Statistics tracking

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd file-age-organizer
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

- **age_thresholds**: Age thresholds for each category (value and unit)
- **organizer**: Organization settings (directories, recursive, exclusions)
- **report**: Report generation settings
- **logging**: Logging configuration

### Default Categories

- **New**: Files modified within last 1 day
- **Recent**: Files modified within last 7 days
- **Old**: Files modified within last 30 days
- **Very-Old**: Files modified within last 365 days

### Customizing Age Thresholds

Edit `config.yaml` to customize thresholds:

```yaml
age_thresholds:
  New:
    value: 1
    unit: days
  Recent:
    value: 7
    unit: days
  Old:
    value: 30
    unit: days
  Very-Old:
    value: 365
    unit: days
```

You can use different units (days, hours, minutes) for each category.

### Environment Variables

You can override configuration using environment variables:

- `SOURCE_DIRECTORY`: Source directory (overrides config.yaml)
- `DESTINATION_DIRECTORY`: Destination directory (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Organize files with default configuration:**
```bash
python src/main.py
```

**Organize files from specific directory:**
```bash
python src/main.py --source /path/to/files
```

**Specify destination directory:**
```bash
python src/main.py --source /path/to/files --destination /path/to/organized
```

**Copy files instead of moving:**
```bash
python src/main.py --source /path/to/files --action copy
```

**Preview operations (dry-run):**
```bash
python src/main.py --source /path/to/files --dry-run
```

**Generate report:**
```bash
python src/main.py --source /path/to/files --output report.txt
```

### Use Cases

**Organize downloads folder by age:**
```bash
python src/main.py -s ~/Downloads -d ~/Downloads/by_age
```

**Copy files to organized structure:**
```bash
python src/main.py -s ./project -d ./organized -a copy
```

**Preview before organizing:**
```bash
python src/main.py -s ~/Documents --dry-run
```

## Project Structure

```
file-age-organizer/
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
- `config.yaml`: Configuration file with age thresholds
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory
- `organized/`: Default destination directory (created automatically)

## How It Works

1. **Scan Directory**: Finds all files in source directory
2. **Calculate Age**: Determines age of each file (time since last modification)
3. **Categorize**: Assigns files to categories based on age thresholds
4. **Organize**: Moves or copies files to category folders
5. **Report**: Generates detailed report with statistics

### Example Organization

**Before:**
```
~/Downloads/
  file1.txt (modified today)
  file2.pdf (modified 3 days ago)
  file3.jpg (modified 2 months ago)
  file4.zip (modified 1 year ago)
```

**After:**
```
~/Downloads/organized/
  New/
    file1.txt
  Recent/
    file2.pdf
  Old/
    file3.jpg
  Very-Old/
    file4.zip
```

## Age Threshold Configuration

### Threshold Units

Each category threshold can use different units:

- **days**: Age in days (e.g., 7 days)
- **hours**: Age in hours (e.g., 24 hours = 1 day)
- **minutes**: Age in minutes (e.g., 1440 minutes = 1 day)

### Example Configurations

**Fine-grained categories:**
```yaml
age_thresholds:
  Very-New:
    value: 1
    unit: hours
  New:
    value: 1
    unit: days
  Recent:
    value: 7
    unit: days
  Old:
    value: 30
    unit: days
  Very-Old:
    value: 365
    unit: days
```

**Short-term tracking:**
```yaml
age_thresholds:
  Today:
    value: 1
    unit: days
  This-Week:
    value: 7
    unit: days
  This-Month:
    value: 30
    unit: days
  Older:
    value: 365
    unit: days
```

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
pytest tests/test_main.py::test_organize_files
```

## Troubleshooting

### Common Issues

**Files not being organized:**
- Check that source directory exists and is readable
- Verify age thresholds are configured correctly
- Review exclusion rules in configuration
- Check logs for error messages

**Permission errors:**
- Ensure read permissions for source directory
- Ensure write permissions for destination directory
- Some system directories may require elevated privileges

**Files in wrong category:**
- Verify file modification times are correct
- Check age threshold configuration
- Review threshold units (days vs hours vs minutes)
- Ensure thresholds are ordered correctly

**Duplicate name handling:**
- Configure `handle_duplicate_names` in config
- Options: skip, rename, or overwrite
- Check logs for duplicate handling messages

### Error Messages

The tool provides detailed error messages in logs. Check `logs/file_age_organizer.log` for:
- File access errors
- Permission issues
- Organization errors
- Category assignment problems

### Best Practices

1. **Test with dry-run first**: Always use `--dry-run` to preview operations
2. **Backup important files**: Consider backing up before organizing
3. **Review exclusions**: Configure exclusions to avoid processing system files
4. **Customize thresholds**: Adjust age thresholds to match your needs
5. **Use copy mode**: Use `--action copy` to preserve originals during testing

## Security Considerations

- Be cautious when organizing system directories
- Review exclusion rules to avoid processing sensitive files
- Verify destination directory permissions
- Consider backing up before bulk operations
- Test with dry-run mode first

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
