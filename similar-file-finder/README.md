# Similar File Finder

A Python automation tool that finds files with similar names using various string similarity algorithms. This tool helps identify potential duplicates, related files, or files with naming inconsistencies by comparing filenames using algorithms like SequenceMatcher, Levenshtein distance, and Jaro-Winkler similarity.

## Project Title and Description

The Similar File Finder scans directories and compares filenames using string similarity algorithms to identify files with similar names. It supports multiple similarity algorithms and configurable thresholds, making it useful for finding duplicate files, related documents, or files with naming variations.

This tool solves the problem of identifying files with similar names that might be duplicates or related, helping users organize their file systems and identify potential naming issues.

**Target Audience**: System administrators, file organizers, developers, and anyone managing large file collections who need to identify similar or duplicate files.

## Features

- Multiple string similarity algorithms:
  - SequenceMatcher (difflib) - Fast and effective for general use
  - Levenshtein distance - Measures edit distance between strings
  - Jaro-Winkler - Optimized for names and short strings
- Configurable similarity threshold
- Compare by filename or full filename (with extension)
- Comprehensive reporting of similar file pairs
- Sorted results by similarity score
- Skip patterns for excluding system/development directories
- Detailed statistics and logging

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Read access to directories being scanned

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/similar-file-finder
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

### Step 4: Verify Installation

```bash
python src/main.py --help
```

## Configuration

### Configuration File (config.yaml)

The tool uses a YAML configuration file for settings. The default configuration file is `config.yaml` in the project root.

#### Key Configuration Options

**Similarity Settings:**
- `similarity.algorithm`: Algorithm to use
  - `"sequence"`: SequenceMatcher from difflib (default, fast and effective)
  - `"levenshtein"`: Levenshtein distance-based similarity
  - `"jaro_winkler"`: Jaro-Winkler similarity (good for names)
- `similarity.threshold`: Similarity threshold (0.0 to 1.0)
  - Files with similarity >= threshold will be reported
  - Default: 0.8 (80% similar)
- `similarity.compare_by`: What to compare
  - `"name"`: Filename without extension (default)
  - `"full_name"`: Full filename with extension

**Scan Settings:**
- `scan.skip_patterns`: List of path patterns to skip during scanning
  - Default includes: .git, __pycache__, .venv, node_modules, etc.

**Report Settings:**
- `report.output_file`: Path for report output (default: "similar_files_report.txt")

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
similarity:
  algorithm: "jaro_winkler"
  threshold: 0.85
  compare_by: "full_name"

scan:
  skip_patterns:
    - ".git"
    - "backup"

report:
  output_file: "my_similar_files.txt"

logging:
  level: "DEBUG"
  file: "logs/app.log"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Find similar files in a directory:

```bash
python src/main.py /path/to/directory
```

### Specify Custom Configuration

```bash
python src/main.py /path/to/directory -c custom_config.yaml
```

### Custom Output Path

```bash
python src/main.py /path/to/directory -o custom_report.txt
```

### Combined Options

```bash
python src/main.py /path/to/directory -c config.yaml -o report.txt
```

### Command-Line Arguments

- `directory`: (Required) Directory path to scan for similar files
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-o, --output`: Custom output path for report

### Common Use Cases

**Find Potential Duplicates:**
1. Set threshold to 0.9 or higher for strict matching
2. Run: `python src/main.py ~/Downloads`
3. Review report for duplicate candidates

**Find Related Files:**
1. Set threshold to 0.7-0.8 for broader matching
2. Use to find files with similar naming patterns
3. Useful for organizing related documents

**Compare Full Filenames:**
1. Set `compare_by: "full_name"` in config
2. Useful when extensions might differ but names are similar

**Use Different Algorithms:**
- SequenceMatcher: Good general-purpose algorithm (default)
- Levenshtein: Better for detecting typos and small variations
- Jaro-Winkler: Optimized for names and short strings

## Project Structure

```
similar-file-finder/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation
└── logs/
    └── .gitkeep             # Placeholder for logs directory
```

### File Descriptions

- `src/main.py`: Contains the `SimilarFileFinder` class and main logic
- `config.yaml`: Configuration file with similarity, scan, and logging settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `logs/`: Directory for application log files

## Similarity Algorithms

### SequenceMatcher (Default)

- Uses Python's `difflib.SequenceMatcher`
- Fast and effective for general use
- Good at finding common subsequences
- Returns ratio between 0.0 and 1.0

### Levenshtein Distance

- Measures minimum number of single-character edits needed
- Good for detecting typos and small variations
- Calculates edit distance, then converts to similarity ratio
- More computationally intensive than SequenceMatcher

### Jaro-Winkler

- Optimized for names and short strings
- Gives higher weight to common prefixes
- Good for matching person names, file names
- Returns similarity between 0.0 and 1.0

## Testing

### Run Tests

```bash
python -m pytest tests/
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage, testing:
- Configuration loading and validation
- String similarity algorithms
- File scanning logic
- Similar file detection
- Report generation
- Error handling

## Troubleshooting

### Common Issues

**Too Many Similar Files Found:**
- Increase the similarity threshold in config.yaml
- Try a different algorithm
- Use `compare_by: "name"` instead of `"full_name"`

**Not Finding Similar Files:**
- Decrease the similarity threshold
- Try a different algorithm (Jaro-Winkler is more lenient)
- Check that files actually have similar names

**Permission Errors:**
- Ensure you have read permissions for the directory
- Some system directories may require elevated permissions
- The tool will log warnings and continue scanning other files

**Large Directory Scanning Takes Time:**
- This is expected for large directory trees
- The algorithm compares all pairs of files (O(n²) complexity)
- Progress is logged to the console and log file
- Consider scanning subdirectories separately

### Error Messages

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

**"Configuration file is empty"**: The config.yaml file exists but has no content. Restore from example.

### Best Practices

1. **Start with default settings** and adjust threshold based on results
2. **Use appropriate algorithm** for your use case:
   - General purpose: SequenceMatcher
   - Typo detection: Levenshtein
   - Name matching: Jaro-Winkler
3. **Adjust threshold** based on needs:
   - 0.9+: Very strict (likely duplicates)
   - 0.7-0.9: Moderate (related files)
   - 0.5-0.7: Lenient (loosely related)
4. **Review reports carefully** - similarity doesn't guarantee duplicates
5. **Use skip patterns** to exclude system and development directories

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guidelines
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Include docstrings for all public functions and classes
- Use meaningful variable names
- Write tests for all new functionality

### Pull Request Process

1. Ensure code follows project standards
2. Update documentation if needed
3. Add/update tests
4. Ensure all tests pass
5. Submit PR with clear description of changes

## License

This project is part of the everyday-python-scripts collection. Please refer to the parent repository for license information.
