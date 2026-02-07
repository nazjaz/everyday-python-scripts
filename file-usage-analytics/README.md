# File Usage Analytics

A Python automation tool that generates comprehensive file usage analytics including access patterns, modification trends, and storage growth over time with visualizations. This tool helps understand file system usage patterns and storage behavior.

## Project Title and Description

The File Usage Analytics tool scans directories and analyzes file usage patterns to generate insights about access patterns, modification trends, and storage growth. It creates visualizations and detailed reports to help users understand how their file systems are being used over time.

This tool solves the problem of understanding file system usage by providing detailed analytics and visual representations of access patterns, modification frequency, storage growth, and file type distributions.

**Target Audience**: System administrators, data analysts, developers, and anyone managing file systems who need insights into usage patterns and storage trends.

## Features

- Comprehensive file usage analysis including access patterns, modification trends, and storage growth
- Multiple visualization charts: access patterns by hour, modification trends over time, storage growth (daily and cumulative), file extension distribution, and size distribution
- Detailed analytics reports with statistics and insights
- Configurable scanning with skip patterns for excluding system directories
- Support for large directory structures with efficient scanning
- Time-based analysis of file creation, modification, and access patterns
- File type and size distribution analysis

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Read access to directories being analyzed
- Matplotlib and NumPy for visualization generation

## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/everyday-python-scripts/file-usage-analytics
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

The tool uses a YAML configuration file to define scanning settings, visualization options, and reporting preferences. The default configuration file is `config.yaml` in the project root.

#### Key Configuration Options

**Scanning Settings:**
- `scan.skip_patterns`: List of path patterns to skip during scanning (default: common system directories)

**Visualization Settings:**
- `visualizations.output_dir`: Directory where visualization charts are saved (default: "analytics_charts")

**Report Settings:**
- `report.output_file`: Path for analytics report (default: "analytics_report.txt")

**Logging Settings:**
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logging.file`: Path to log file (default: "logs/app.log")

### Example Configuration

```yaml
scan:
  skip_patterns:
    - ".git"
    - "__pycache__"
    - ".venv"
    - "node_modules"

visualizations:
  output_dir: "analytics_charts"

report:
  output_file: "analytics_report.txt"

logging:
  level: "INFO"
  file: "logs/app.log"
```

### Environment Variables

No environment variables are currently required. All configuration is managed through the `config.yaml` file.

## Usage

### Basic Usage

Analyze files in a directory:

```bash
python src/main.py /path/to/directory
```

### Generate Visualizations

Analyze and generate visualization charts:

```bash
python src/main.py /path/to/directory --visualizations
```

### Specify Custom Configuration

```bash
python src/main.py /path/to/directory -c custom_config.yaml
```

### Custom Output Directory

```bash
python src/main.py /path/to/directory --visualizations -o custom_charts_dir
```

### Custom Report Output

```bash
python src/main.py /path/to/directory -r custom_report.txt
```

### Combined Options

```bash
python src/main.py /path/to/directory -c config.yaml --visualizations -o charts -r report.txt
```

### Command-Line Arguments

- `directory`: (Required) Directory path to analyze
- `-c, --config`: Path to configuration file (default: config.yaml)
- `-v, --visualizations`: Generate visualization charts
- `-o, --output-dir`: Custom output directory for visualizations (overrides config)
- `-r, --report`: Custom output path for analytics report (overrides config)

### Common Use Cases

**Analyze Project Directory:**
1. Configure skip patterns in `config.yaml`
2. Run: `python src/main.py ~/projects --visualizations`
3. Review charts in `analytics_charts/` directory
4. Check report in `analytics_report.txt`

**Analyze Downloads Folder:**
```bash
python src/main.py ~/Downloads --visualizations
```

**Analyze with Custom Settings:**
1. Create custom `config.yaml` with your preferences
2. Run: `python src/main.py /path/to/files -c custom_config.yaml --visualizations`
3. Review generated analytics

## Project Structure

```
file-usage-analytics/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore               # Git ignore patterns
├── .env.example             # Environment variables template
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

- `src/main.py`: Contains the `FileUsageAnalytics` class and main logic
- `config.yaml`: Configuration file with scanning and visualization settings
- `requirements.txt`: Python package dependencies
- `tests/test_main.py`: Unit tests for the main module
- `analytics_charts/`: Directory created at runtime for visualization charts
- `logs/`: Directory for application log files

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
- File metadata collection
- Directory analysis functionality
- Visualization generation
- Report generation
- Error handling
- Path skipping logic

## Troubleshooting

### Common Issues

**No Analytics Data Available:**
- Ensure the directory path is correct and accessible
- Check that files exist in the directory
- Verify skip patterns aren't excluding all files
- Review logs for detailed error messages

**Permission Errors:**
- Ensure you have read access to source directory
- Check file ownership and permissions
- Some system files may require elevated permissions

**Visualization Generation Fails:**
- Verify matplotlib and numpy are installed correctly
- Check that output directory is writable
- Ensure sufficient disk space for chart generation

**Slow Performance:**
- Large directories may take time to analyze
- Consider excluding unnecessary subdirectories in skip patterns
- Review logs to identify bottlenecks

### Error Messages

**"Directory not found"**: The specified directory path doesn't exist. Verify the path is correct.

**"Path is not a directory"**: The specified path exists but is a file, not a directory.

**"No analytics data available"**: No files were found or analyzed. Check directory contents and skip patterns.

**"Permission denied"**: Insufficient permissions to access the directory or files. Check file permissions.

### Best Practices

1. **Start with small directories** to test configuration and understand output
2. **Configure skip patterns** to exclude system and development directories
3. **Review logs** to understand what's being analyzed
4. **Use visualizations** to get visual insights into usage patterns
5. **Regular analysis** helps track trends over time
6. **Backup important data** before running analysis on critical directories

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
