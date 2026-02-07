# Context-Aware File Organizer

A Python automation tool for organizing files by analyzing context clues from parent directories, filenames, and nearby files. This script creates intelligent, context-aware organization by understanding the semantic context of files rather than just their types or extensions.

## Features

- **Parent Directory Analysis**: Analyzes directory names in the file path for context clues
- **Filename Analysis**: Extracts keywords and patterns from filenames to understand context
- **Nearby Files Analysis**: Examines files in the same directory to infer context
- **Confidence Scoring**: Assigns confidence scores to organization decisions
- **Context Categories**: Organizes into semantic categories (work, personal, financial, education, etc.)
- **Duplicate Detection**: Uses content hashing to detect and skip duplicate files
- **Weighted Analysis**: Configurable weights for different context sources
- **Low Confidence Handling**: Files with low confidence are placed in "uncertain" subdirectories
- **Comprehensive Logging**: Detailed logging with rotation

## Prerequisites

- Python 3.8 or higher
- Write permissions to source and destination directories
- Sufficient disk space for file organization

## Installation

1. Clone or navigate to the project directory:
```bash
cd context-aware-organizer
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

4. Copy and configure the environment file (optional):
```bash
cp .env.example .env
# Edit .env with your settings if needed
```

5. Review and customize `config.yaml` with your settings:
   - Configure context keywords for your use case
   - Adjust analysis weights
   - Set minimum confidence threshold
   - Configure source and destination directories

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory to organize (default: current directory)
- **organization.destination_directory**: Where to save organized files (default: ./organized)
- **organization.min_confidence**: Minimum confidence score to organize (default: 0.3)
- **organization.check_duplicates**: Enable duplicate detection (default: true)
- **analysis.weights**: Weights for different context sources:
  - **parent_directories**: Weight for directory analysis (default: 0.4)
  - **filename**: Weight for filename analysis (default: 0.4)
  - **nearby_files**: Weight for nearby files analysis (default: 0.2)
- **context_keywords**: Keywords mapping to context categories

### Context Categories

Files are organized into semantic categories based on context analysis:

- **work**: Work-related files (job, office, business, project)
- **personal**: Personal files (home, family, private, photos)
- **financial**: Financial documents (bank, tax, invoice, receipt)
- **education**: Educational content (school, course, study, notes)
- **health**: Health-related files (medical, doctor, prescription)
- **travel**: Travel documents (trip, flight, hotel, itinerary)
- **project**: Project files (code, development, repository)
- **documents**: Legal documents (contract, agreement, certificate)
- **media**: Media files (photo, video, audio, music)
- **temporary**: Temporary files (temp, download, cache, draft)
- **miscellaneous**: Files that don't match any category

### Environment Variables

Optional environment variables can override configuration:

- `SOURCE_DIRECTORY`: Override source directory path
- `DESTINATION_DIRECTORY`: Override destination directory path

## Usage

### Basic Usage

Organize files with default configuration:
```bash
python src/main.py
```

### Dry Run

Preview what would be organized without making changes:
```bash
python src/main.py --dry-run
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config /path/to/custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Perform a dry run without making changes
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
context-aware-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── .gitkeep             # Documentation directory placeholder
└── logs/
    └── .gitkeep             # Logs directory placeholder
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## How It Works

1. **Context Analysis**: For each file, the script analyzes:
   - **Parent Directories**: Examines directory names in the file path for keywords
   - **Filename**: Extracts keywords and patterns from the filename
   - **Nearby Files**: Analyzes files in the same directory to infer context

2. **Context Scoring**: Each context source provides scores for different categories:
   - Parent directories: Higher weight for closer directories
   - Filename: Direct keyword matching
   - Nearby files: Type distribution and common keywords

3. **Weighted Combination**: Scores are combined using configurable weights:
   - Default: 40% parent directories, 40% filename, 20% nearby files
   - Weights can be adjusted in configuration

4. **Category Assignment**: The category with the highest combined score is selected.

5. **Confidence Handling**: 
   - Files with high confidence are organized normally
   - Files with low confidence (< min_confidence) are placed in "uncertain" subdirectories

6. **Organization**: Files are moved to `destination/category/` or `destination/category/uncertain/`

7. **Duplicate Detection**: Content hashing prevents duplicate files from being organized multiple times.

## Example Scenarios

### Scenario 1: Work Project Files
- **Path**: `/Users/john/work/project-alpha/report.pdf`
- **Analysis**:
  - Parent: "work" and "project" keywords → work category
  - Filename: "report" → work category
  - Nearby: Other project files → project category
- **Result**: Organized to `organized/work/` (high confidence)

### Scenario 2: Personal Photos
- **Path**: `/Users/john/Downloads/vacation_2024.jpg`
- **Analysis**:
  - Parent: "Downloads" → temporary category (low weight)
  - Filename: "vacation" → travel/personal category
  - Nearby: Mix of file types → less clear context
- **Result**: Organized to `organized/personal/` (medium confidence)

### Scenario 3: Financial Documents
- **Path**: `/Users/john/Documents/tax_2023.pdf`
- **Analysis**:
  - Parent: "Documents" → documents category
  - Filename: "tax" → financial category
  - Nearby: Other PDFs → documents category
- **Result**: Organized to `organized/financial/` (high confidence)

## Troubleshooting

### Files Not Being Organized

If files are not being organized:
- Check minimum confidence threshold (may be too high)
- Verify context keywords match your file naming conventions
- Review logs for confidence scores
- Files with very low confidence may be skipped

### Incorrect Categorization

If files are categorized incorrectly:
- Add more specific keywords to context_keywords in config.yaml
- Adjust weights to emphasize the most reliable context source
- Review parent directory names - they heavily influence categorization
- Check nearby files - they provide context clues

### Low Confidence Scores

If many files have low confidence:
- Add more keywords to context_keywords
- Adjust analysis weights
- Lower min_confidence threshold
- Files will be placed in "uncertain" subdirectories

### Duplicate Detection Issues

If duplicates are not detected:
- Ensure check_duplicates is enabled in config
- Hashes are stored per category directory
- Same content in different categories will be saved separately

### Performance Issues

If organization is slow:
- Content hashing for duplicates can be slow for large files
- Consider disabling duplicate checking if not needed
- Processing time increases with number of files

## Customization

### Adding Custom Context Categories

Add new categories to `context_keywords` in config.yaml:

```yaml
context_keywords:
  custom_category:
    - "keyword1"
    - "keyword2"
    - "keyword3"
```

### Adjusting Analysis Weights

Modify weights in `analysis.weights` to emphasize different context sources:

```yaml
analysis:
  weights:
    parent_directories: 0.5  # Emphasize directory names
    filename: 0.3
    nearby_files: 0.2
```

### Changing Confidence Threshold

Adjust `min_confidence` to control organization sensitivity:

```yaml
organization:
  min_confidence: 0.2  # Lower threshold = more files organized
```

## Security Considerations

- The script performs file move operations
- Always use `--dry-run` first to preview changes
- Ensure backups are in place before organizing important files
- Duplicate detection reads file contents but does not modify them
- The script does not process files outside the specified source directory

## Performance Considerations

- Context analysis processes each file individually
- Nearby file analysis examines up to 20 files per directory
- Duplicate detection can be slow for large files
- Consider processing during off-peak hours for large directories

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
