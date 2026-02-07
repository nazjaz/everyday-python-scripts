# Duplicate Structure Finder

A Python automation tool for identifying duplicate directory structures with similar file arrangements. This script helps consolidate redundant folder hierarchies by finding directories that have similar folder structures, file types, and arrangements.

## Features

- **Structure Analysis**: Analyzes directory hierarchies, file counts, and arrangements
- **Similarity Calculation**: Calculates similarity scores between directory structures
- **Multiple Comparison Metrics**: Compares file counts, subdirectory counts, extensions, names, and depth
- **Structure Hashing**: Uses hash-based comparison for exact structure matches
- **Similarity Thresholds**: Configurable thresholds for identifying duplicates
- **Detailed Reports**: Generates comprehensive reports with recommendations
- **Recursive Analysis**: Analyzes nested directory structures
- **Filtering**: Excludes system directories and files from analysis
- **Comprehensive Logging**: Detailed logging with rotation

## Prerequisites

- Python 3.8 or higher
- Read permissions to search directories
- Sufficient memory for analyzing large directory trees

## Installation

1. Clone or navigate to the project directory:
```bash
cd duplicate-structure-finder
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
   - Set search directory
   - Configure similarity threshold
   - Adjust filtering options

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **search.directory**: Directory to search for duplicates (default: current directory)
- **search.include_root**: Whether to include root directory in analysis (default: false)
- **comparison.similarity_threshold**: Minimum similarity to consider duplicates (default: 0.8)
- **comparison.min_file_count**: Minimum files required to analyze directory (default: 1)
- **comparison.min_subdirectory_count**: Minimum subdirectories required (default: 0)
- **analysis.max_depth**: Maximum depth to analyze (0 = unlimited)
- **analysis.include_sizes**: Include file sizes in comparison (default: true)
- **filtering.exclude_directories**: Directories to exclude from analysis
- **filtering.exclude_files**: File patterns to exclude
- **filtering.exclude_extensions**: File extensions to exclude

### Environment Variables

Optional environment variables can override configuration:

- `SEARCH_DIRECTORY`: Override search directory path

## Usage

### Basic Usage

Search for duplicate structures with default configuration:
```bash
python src/main.py
```

### Custom Search Directory

Search in a specific directory:
```bash
python src/main.py --directory /path/to/search
```

### Output to File

Save report to a file:
```bash
python src/main.py --output report.txt
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
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
duplicate-structure-finder/
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

1. **Directory Discovery**: Recursively finds all directories in the search path, excluding system directories.

2. **Structure Analysis**: For each directory, analyzes:
   - File count and file names
   - File extensions
   - Subdirectory count and names
   - Directory depth
   - Total size

3. **Structure Hashing**: Creates a hash representing the directory structure based on:
   - File and subdirectory counts
   - Depth
   - File extensions
   - Subdirectory names

4. **Similarity Calculation**: Compares directory structures using multiple metrics:
   - **File Count Similarity** (20% weight): Ratio of file counts
   - **Subdirectory Count Similarity** (20% weight): Ratio of subdirectory counts
   - **Extension Similarity** (30% weight): Common file extensions
   - **Subdirectory Name Similarity** (20% weight): Common subdirectory names
   - **Depth Similarity** (10% weight): Directory depth comparison

5. **Duplicate Identification**: Identifies pairs with similarity above the threshold.

6. **Report Generation**: Generates a detailed report with:
   - Summary statistics
   - Detailed findings for each duplicate pair
   - Recommendations for consolidation

## Similarity Scoring

The similarity score ranges from 0.0 to 1.0:
- **1.0**: Identical structures (same hash)
- **0.9-1.0**: Very similar structures (high confidence for consolidation)
- **0.8-0.9**: Similar structures (good candidates for review)
- **0.7-0.8**: Moderately similar (may be worth reviewing)
- **< 0.7**: Different structures

## Example Scenarios

### Scenario 1: Project Backups
- **Directory 1**: `/projects/myproject_backup_2023/`
- **Directory 2**: `/projects/myproject_backup_2024/`
- **Similarity**: High (same structure, different dates)
- **Recommendation**: Review and consolidate if backups are redundant

### Scenario 2: Duplicate Project Folders
- **Directory 1**: `/work/project-alpha/`
- **Directory 2**: `/work/project-alpha-copy/`
- **Similarity**: Very High (nearly identical)
- **Recommendation**: Strong candidate for consolidation

### Scenario 3: Similar Templates
- **Directory 1**: `/templates/template_v1/`
- **Directory 2**: `/templates/template_v2/`
- **Similarity**: Medium-High (similar but evolved)
- **Recommendation**: Review to determine if consolidation is appropriate

## Troubleshooting

### No Duplicates Found

If no duplicates are found:
- Lower the similarity threshold (try 0.7 or 0.6)
- Check that directories are not excluded by filters
- Verify search directory contains multiple directories
- Review logs for analysis details

### Too Many False Positives

If too many false positives are found:
- Increase the similarity threshold (try 0.9)
- Add more specific exclusion patterns
- Review similarity calculation weights in code

### Performance Issues

If analysis is slow:
- Set max_depth to limit recursion depth
- Exclude more directories from analysis
- Process smaller directory trees separately
- Check logs for performance bottlenecks

### Permission Errors

If you encounter permission errors:
- Ensure read access to search directory
- Check file and directory permissions
- Some directories may be skipped with warnings

## Use Cases

### Consolidating Project Backups
Find duplicate project structures to identify redundant backups:
```bash
python src/main.py --directory /projects --output backup_analysis.txt
```

### Finding Duplicate Templates
Identify similar template directories:
```bash
python src/main.py --directory /templates --output template_duplicates.txt
```

### Organizing Workspace
Find duplicate folder structures in workspace:
```bash
python src/main.py --directory ~/workspace --output workspace_duplicates.txt
```

## Security Considerations

- The script only reads directory structures, never modifies files
- No sensitive file contents are read
- Directory paths are logged but can be filtered
- The script respects file permissions and skips inaccessible directories

## Performance Considerations

- Processing time increases with number of directories
- Deep directory trees take longer to analyze
- Similarity calculation is O(n²) for n directories
- Consider analyzing subdirectories separately for very large trees

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
