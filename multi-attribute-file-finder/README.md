# Multi-Attribute File Finder

A Python automation tool for finding files matching multiple attribute combinations. This script allows you to search for files based on combinations of size, age, type, and other attributes, such as large old files, small new files, or executable documents.

## Features

- **Multi-Attribute Matching**: Combine multiple file attributes in a single search
- **Predefined Combinations**: Common combinations like "large old files", "small new files", "executable documents"
- **Flexible Attribute Criteria**:
  - **Size**: By bytes, size categories (tiny, small, medium, large, very_large)
  - **Age**: By modification/creation date, days ago, or age categories (new, recent, old, very_old)
  - **Type**: By extension, file type categories, or executable status
  - **Filename**: By glob patterns, regex, or contains matching
- **Multiple Output Formats**: Text, JSON, or CSV output
- **Combination-Based Results**: Groups results by matching combinations
- **Comprehensive Logging**: Detailed logging with rotation

## Prerequisites

- Python 3.8 or higher
- Read permissions to search directories
- Sufficient memory for analyzing large directory trees

## Installation

1. Clone or navigate to the project directory:
```bash
cd multi-attribute-file-finder
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

5. Review and customize `config.yaml` with your attribute combinations:
   - Predefined combinations are included
   - Add custom combinations as needed
   - Configure search directory and output format

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **search.directory**: Directory to search (default: current directory)
- **search.exclude_directories**: Directories to exclude (glob patterns)
- **combinations**: List of attribute combinations to search for
- **output.format**: Output format - text, json, or csv (default: text)

### Predefined Combinations

The configuration includes several predefined combinations:

1. **large_old_files**: Files >10 MB, modified >90 days ago
2. **small_new_files**: Files <1 MB, modified within last 7 days
3. **executable_documents**: Document files that are executable
4. **large_recent_images**: Image files >5 MB, modified within last 30 days
5. **old_code_files**: Code files modified >180 days ago
6. **small_old_archives**: Archive files <1 MB, modified >365 days ago

### Creating Custom Combinations

Add custom combinations to `config.yaml`:

```yaml
combinations:
  - name: "my_custom_combination"
    size:
      min_bytes: 1048576  # 1 MB
      max_bytes: 10485760  # 10 MB
    age:
      modified:
        days_ago_max: 30
    type:
      categories: ["image", "video"]
```

### Environment Variables

Optional environment variables can override configuration:

- `SEARCH_DIRECTORY`: Override search directory path

## Usage

### Basic Usage

Search with default configuration:
```bash
python src/main.py
```

### Custom Search Directory

Search in a specific directory:
```bash
python src/main.py --directory /path/to/search
```

### Output to File

Save results to a file:
```bash
python src/main.py --output results.txt
```

### JSON Format

Generate results in JSON format:
```bash
python src/main.py --format json --output results.json
```

### CSV Format

Generate results in CSV format:
```bash
python src/main.py --format csv --output results.csv
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --directory`: Directory to search (overrides config)
- `-o, --output`: Output file path (default: stdout)
- `-f, --format`: Output format - text, json, or csv (overrides config)
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
multi-attribute-file-finder/
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

1. **Configuration Loading**: Loads attribute combinations from `config.yaml`.

2. **File Discovery**: Recursively scans the search directory for files, excluding system directories.

3. **Attribute Matching**: For each file, checks against all defined combinations:
   - **Size Matching**: Checks file size against size criteria
   - **Age Matching**: Checks modification/creation dates against age criteria
   - **Type Matching**: Checks file type, extension, and executable status
   - **Filename Matching**: Checks filename against patterns

4. **Combination Matching**: Files that match all criteria in a combination are added to that combination's results.

5. **Result Grouping**: Results are grouped by combination name.

6. **Output Formatting**: Formats results in requested format (text, JSON, or CSV).

## Attribute Criteria

### Size Criteria

- **min_bytes**: Minimum file size in bytes
- **max_bytes**: Maximum file size in bytes
- **categories**: Size categories (tiny, small, medium, large, very_large)

### Age Criteria

- **modified.days_ago_min**: Minimum days since modification
- **modified.days_ago_max**: Maximum days since modification
- **modified.after**: Modified after date (ISO format or "30 days ago")
- **modified.before**: Modified before date
- **created**: Same options for creation date
- **categories**: Age categories (new, recent, moderate, old, very_old)

### Type Criteria

- **extensions**: List of file extensions to match
- **exclude_extensions**: List of extensions to exclude
- **categories**: File type categories (image, document, video, audio, code, archive, executable)
- **executable**: Boolean to require executable files

### Filename Criteria

- **glob**: Glob patterns (e.g., "*.txt", "file_*")
- **regex**: Regular expression patterns
- **contains**: Substring matches (case-insensitive)

## Example Combinations

### Large Old Files
```yaml
- name: "large_old_files"
  size:
    categories: ["large", "very_large"]
    min_bytes: 10485760  # 10 MB
  age:
    modified:
      days_ago_min: 90
```

### Small New Files
```yaml
- name: "small_new_files"
  size:
    categories: ["tiny", "small"]
    max_bytes: 1048576  # 1 MB
  age:
    modified:
      days_ago_max: 7
```

### Executable Documents
```yaml
- name: "executable_documents"
  type:
    categories: ["document"]
    executable: true
```

## Troubleshooting

### No Results Found

If no results are found:
- Check that combinations are not too restrictive
- Verify search directory path is correct
- Try adjusting attribute criteria
- Review logs for analysis details

### Too Many Results

If too many results are found:
- Make combinations more specific
- Add additional criteria to narrow results
- Use exclude patterns to filter unwanted files

### Performance Issues

If search is slow:
- Reduce search scope (smaller directory)
- Exclude more directories from search
- Limit number of combinations
- Check logs for performance bottlenecks

### Permission Errors

If you encounter permission errors:
- Ensure read access to search directory
- Check file and directory permissions
- Some files may be skipped with warnings

## Use Cases

### Finding Large Old Files for Cleanup
```yaml
- name: "cleanup_candidates"
  size:
    min_bytes: 104857600  # 100 MB
  age:
    modified:
      days_ago_min: 365  # 1 year old
```

### Finding Recent Small Files
```yaml
- name: "recent_small_files"
  size:
    max_bytes: 1048576  # 1 MB
  age:
    modified:
      days_ago_max: 7
```

### Finding Executable Documents (Security)
```yaml
- name: "suspicious_executables"
  type:
    categories: ["document"]
    executable: true
```

## Security Considerations

- The script only reads file metadata, never file contents
- Executable detection checks file permissions
- No sensitive file contents are accessed
- The script respects file permissions and skips inaccessible files

## Performance Considerations

- Processing time increases with number of files and combinations
- Multiple combinations are checked for each file
- Consider reducing number of combinations for very large directories
- Use filtering to reduce search space

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
