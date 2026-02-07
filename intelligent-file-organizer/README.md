# Intelligent File Organizer

A Python automation tool that organizes files by extracting category tags from content analysis, filename patterns, and directory context. This intelligent categorization system uses multiple analysis methods to automatically categorize and organize files into appropriate folders.

## Project Title and Description

The Intelligent File Organizer analyzes files using three methods: content analysis (for text files), filename pattern matching, and directory context analysis. It extracts category tags from these sources and organizes files into category-based folder structures. This provides intelligent, context-aware file organization beyond simple extension-based categorization.

This tool solves the problem of organizing files intelligently by understanding their content and context, not just their file extensions. It's useful for managing large file collections where files may have inconsistent naming or need content-based categorization.

**Target Audience**: System administrators, content managers, developers, and anyone managing large file collections who need intelligent, context-aware file organization.

## Features

- **Multi-source tag extraction:**
  - Filename analysis (keywords and patterns)
  - Directory context analysis (parent directory names)
  - Content analysis (text file keyword extraction)
- **Intelligent categorization:** Combines multiple tag sources for accurate categorization
- **Configurable categories:** Define custom categories with keywords, patterns, and rules
- **Content analysis:** Analyzes text files to extract relevant keywords
- **Pattern matching:** Supports regex patterns for filename matching
- **Directory context:** Uses parent directory names as categorization hints
- **Dry-run mode:** Test organization without moving files
- **Comprehensive reporting:** Detailed reports with tag extraction examples
- **Skip patterns:** Exclude system/development directories

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Read access to directories being scanned
- Write access for file organization

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/intelligent-file-organizer
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

The tool uses a YAML configuration file to define categories and analysis settings. The default configuration file is `config.yaml` in the project root.

#### Key Configuration Options

**Organization Settings:**
- `organization.base_folder`: Base folder where organized files are placed (default: "organized")

**Analysis Settings:**
- `analysis.use_filename`: Enable filename analysis (default: true)
- `analysis.use_directory`: Enable directory context analysis (default: true)
- `analysis.use_content`: Enable content analysis (default: true)
- `analysis.max_content_size`: Maximum bytes to read from files (default: 100000)
- `analysis.text_extensions`: List of text file extensions to analyze

**Category Definitions:**
Each category can have:
- `folder`: Destination folder name
- `keywords`: List of keywords to match in filenames
- `patterns`: List of regex patterns for filename matching
- `directory_keywords`: Keywords to match in parent directory names
- `content_keywords`: Keywords to match in file content

**Scan Settings:**
- `scan.skip_patterns`: List of path patterns to skip

**Report Settings:**
- `report.output_file`: Path for organization report

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file

### Example Configuration

```yaml
organization:
  base_folder: "organized"

analysis:
  use_filename: true
  use_directory: true
  use_content: true
  max_content_size: 50000

categories:
  projects:
    folder: "Projects"
    keywords:
      - "project"
      - "task"
    directory_keywords:
      - "projects"
      - "work"
    content_keywords:
      - "project"
      - "milestone"
      - "deadline"

scan:
  skip_patterns:
    - ".git"
    - "backup"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Organize files in a directory:

```bash
python src/main.py /path/to/directory
```

### Dry Run Mode

Test organization without moving files:

```bash
python src/main.py /path/to/directory --dry-run
```

### Specify Custom Configuration

```bash
python src/main.py /path/to/directory -c custom_config.yaml
```

### Custom Report Output

```bash
python src/main.py /path/to/directory -r custom_report.txt
```

### Combined Options

```bash
python src/main.py /path/to/directory -c config.yaml --dry-run -r report.txt
```

### Command-Line Arguments

- `directory`: (Required) Directory path to scan and organize
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Simulate organization without moving files
- `-r, --report`: Custom output path for organization report

### Common Use Cases

**Organize Downloads Folder:**
```bash
python src/main.py ~/Downloads
```

**Test Before Organizing:**
1. Run with `--dry-run` first
2. Review logs and report
3. Adjust category definitions if needed
4. Run without `--dry-run` to actually organize

**Custom Categories:**
1. Edit `config.yaml` to add custom categories
2. Define keywords, patterns, and content keywords
3. Run organization

**Content-Based Organization:**
1. Enable `use_content: true` in config
2. Add `content_keywords` to category definitions
3. Tool will analyze text files and extract keywords

## Project Structure

```
intelligent-file-organizer/
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

- `src/main.py`: Contains the `IntelligentFileOrganizer` class and main logic
- `config.yaml`: Configuration file with categories and analysis settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `organized/`: Directory created at runtime for organized files
- `logs/`: Directory for application log files

## Tag Extraction Methods

### Filename Analysis

- Matches keywords in filenames (case-insensitive)
- Supports regex patterns for flexible matching
- Fast and efficient for most files

### Directory Context

- Analyzes parent directory names
- Uses directory keywords from category definitions
- Helps categorize files based on their location

### Content Analysis

- Extracts keywords from text file content
- Filters stop words and common terms
- Frequency-based keyword extraction
- Only analyzes configured text file extensions

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
- Tag extraction from filenames
- Tag extraction from directories
- Tag extraction from content
- Category determination
- File organization
- Error handling

## Troubleshooting

### Common Issues

**Files Not Being Categorized:**
- Check that categories have appropriate keywords/patterns
- Verify analysis methods are enabled (filename, directory, content)
- Review logs for tag extraction details
- Adjust category definitions to match your files

**Too Many Files in One Category:**
- Make category keywords more specific
- Add more categories to split files
- Adjust content keywords for better matching

**Content Analysis Not Working:**
- Verify file extensions are in `text_extensions` list
- Check that `use_content` is enabled
- Ensure files are readable text files
- Review `max_content_size` setting

**Permission Errors:**
- Ensure read access to source directory
- Ensure write access to destination
- Check file ownership and permissions

### Error Messages

**"No categories defined"**: The config.yaml file doesn't have any categories. Add at least one category definition.

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

### Best Practices

1. **Start with dry-run** to see what would be organized
2. **Review category definitions** to match your file types
3. **Enable all analysis methods** for best results
4. **Add custom categories** for your specific use cases
5. **Test with small directories** first
6. **Review logs** to understand tag extraction
7. **Backup important files** before organizing

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
