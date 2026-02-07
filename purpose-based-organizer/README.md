# Purpose-Based File Organizer

A Python script that organizes files by purpose tags inferred from filenames, locations, and content analysis. Creates purpose-based folder hierarchies to help users organize files by their intended use rather than just file type.

## Features

- **Multi-Source Purpose Inference**: Infers file purposes from three sources:
  - **Filenames**: Analyzes keywords in filenames (e.g., "invoice", "resume", "homework")
  - **Locations**: Considers file location context (e.g., Downloads, Desktop, Projects)
  - **Content**: Analyzes text content for purpose indicators (for text-based files)
- **Intelligent Scoring**: Combines multiple sources with weighted scoring to determine primary purpose
- **Purpose-Based Organization**: Organizes files into purpose-based folder hierarchies:
  - Financial (invoices, receipts, tax documents)
  - Work (resumes, contracts, project files)
  - Personal (photos, diaries, personal documents)
  - Education (homework, assignments, certificates)
  - Health (medical records, prescriptions, insurance)
  - Travel (itineraries, bookings, tickets)
  - Legal (legal documents, licenses, permits)
- **Duplicate Detection**: Identifies duplicate files using MD5 hashing
- **Comprehensive Reporting**: Generates detailed reports showing purpose distribution and duplicate files
- **Dry Run Mode**: Test organization without actually moving files
- **Configurable**: Customizable purpose patterns, location contexts, and content keywords via YAML configuration
- **Safe Operation**: Handles filename conflicts and provides detailed logging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd purpose-based-organizer
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The script uses `config.yaml` for configuration. Key settings include:

### Organization Settings

- `base_folder`: Base directory where organized files will be placed (default: "organized")
- `unknown_folder`: Folder name for files with unknown purpose (default: "Unknown")
- `include_secondary_purposes`: Whether to create subfolders for secondary purposes (default: false)
- `skip_duplicates`: Whether to skip duplicate files during organization (default: false)

### Purpose Detection

- `min_score`: Minimum score threshold for purpose detection (default: 1)
- `patterns`: Custom purpose patterns with keywords and weights
- `location_contexts`: Custom location-based context mappings
- `content_keywords`: Custom content-based keyword mappings

### Example Configuration

```yaml
organization:
  base_folder: "organized"
  unknown_folder: "Unknown"
  include_secondary_purposes: false
  skip_duplicates: false

purpose_detection:
  min_score: 1
  patterns:
    "CustomPurpose":
      - {"keywords": ["custom", "specific"], "weight": 3}
  location_contexts:
    "CustomFolder": ["CustomPurpose"]
  content_keywords:
    "CustomPurpose": ["custom phrase", "specific term"]
```

## Usage

### Basic Usage

Scan and organize files in a directory:

```bash
python src/main.py /path/to/directory
```

### Command-Line Options

- `directory`: Directory to scan and organize (required)
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Simulate organization without moving files
- `-r, --report`: Output path for organization report (overrides config)

### Examples

**Dry run to preview organization**:
```bash
python src/main.py /path/to/files -d
```

**Organize files with custom config**:
```bash
python src/main.py /path/to/files -c custom_config.yaml
```

**Generate report to specific location**:
```bash
python src/main.py /path/to/files -r /path/to/report.txt
```

**Full example with all options**:
```bash
python src/main.py ~/Downloads -d -c config.yaml -r report.txt
```

## Project Structure

```
purpose-based-organizer/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── config.yaml            # Configuration file
├── .gitignore            # Git ignore patterns
├── src/
│   └── main.py           # Main application
├── tests/
│   └── test_main.py      # Unit tests
├── docs/
│   └── API.md            # API documentation
└── logs/
    └── .gitkeep          # Placeholder for logs
```

## How It Works

1. **Scanning**: Recursively scans the specified directory for files
2. **Purpose Inference**: For each file, analyzes three sources:
   - **Filename Analysis**: Checks for keywords in filename (weight: 3)
   - **Location Analysis**: Considers parent directory context (weight: 2)
   - **Content Analysis**: Analyzes text content for keywords (weight: 1)
3. **Scoring**: Combines scores from all sources to determine primary purpose
4. **Duplicate Detection**: Calculates MD5 hashes to identify duplicate files
5. **Organization**: Moves files to purpose-based folders:
   - Financial → organized/Financial/
   - Work → organized/Work/
   - Personal → organized/Personal/
   - Education → organized/Education/
   - Health → organized/Health/
   - Travel → organized/Travel/
   - Legal → organized/Legal/
6. **Reporting**: Generates a comprehensive report with statistics and findings

## Supported Purpose Categories

The script recognizes the following purpose categories by default:

- **Financial**: Invoices, bills, receipts, tax documents, bank statements
- **Work**: Resumes, CVs, contracts, project files, meeting notes
- **Personal**: Photos, diaries, personal documents
- **Education**: Homework, assignments, course materials, certificates
- **Health**: Medical records, prescriptions, insurance documents
- **Travel**: Itineraries, bookings, reservations, tickets
- **Legal**: Legal documents, licenses, permits, wills

Custom purpose categories can be added via configuration.

## Purpose Detection Examples

### Filename-Based Detection

- `invoice_2024.pdf` → Financial
- `resume_john_doe.pdf` → Work
- `homework_math.pdf` → Education
- `vacation_photos.jpg` → Personal/Travel

### Location-Based Detection

- Files in `Downloads/` → Temporary/Pending
- Files in `Desktop/` → Active/Current
- Files in `Projects/` → Work/Development

### Content-Based Detection

- Text files containing "invoice number" → Financial
- Text files containing "meeting agenda" → Work
- Text files containing "assignment" → Education

## Testing

Run the test suite using pytest:

```bash
pytest tests/test_main.py -v
```

For coverage report:

```bash
pytest tests/test_main.py --cov=src --cov-report=html
```

## Troubleshooting

### Files Not Categorized Correctly

1. Check if the file matches any purpose patterns in the configuration
2. Add custom patterns for your specific use case
3. Review the report to see detection scores and adjust thresholds

### Too Many Files in "Unknown"

1. Lower the `min_score` threshold in configuration
2. Add custom purpose patterns for your file types
3. Check if filenames contain recognizable keywords

### Duplicate Detection Issues

- Ensure files are readable (permissions)
- Large files may take time to hash
- Review duplicate files in the report

### Large Directory Scanning

For very large directories, scanning may take time. The script logs progress and provides statistics upon completion. Consider using dry-run mode first to preview operations.

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for all public functions and classes
4. Add unit tests for new features
5. Update documentation as needed

## License

This project is provided as-is for educational and personal use.
