# Markdown Processor

A Python automation script that processes markdown files by validating links, checking for broken references, and generating table of contents automatically. Useful for maintaining documentation, validating markdown files, and ensuring link integrity.

## Features

- **Link validation**: Validates internal file links, external HTTP/HTTPS links, and anchor links
- **Reference checking**: Checks for broken reference-style links
- **Table of contents generation**: Automatically generates TOC from headers
- **Multiple TOC placement options**: Place TOC at top, after first header, or disable
- **Configurable depth**: Control which header levels appear in TOC
- **Comprehensive reporting**: Detailed reports of all findings
- **File updates**: Optionally update files with generated TOC
- **Error handling**: Graceful handling of encoding issues and file errors

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Step 1: Navigate to Project Directory

```bash
cd markdown-processor
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

**Note**: The `requests` library is optional and only needed for external link validation. The script will work without it but won't validate external links.

## Configuration

### Configuration File (config.yaml)

The script supports configuration via a YAML file:

```yaml
base_path: null
validate_external_links: false
toc_placement: "top"
toc_min_depth: 2
toc_max_depth: 6
```

## Usage

### Basic Usage

Process a single markdown file:

```bash
python src/main.py document.md
```

### Multiple Files

Process multiple markdown files:

```bash
python src/main.py file1.md file2.md file3.md
```

### Validate External Links

Check external HTTP/HTTPS links:

```bash
python src/main.py document.md --validate-external
```

### Generate and Update TOC

Generate table of contents and update files:

```bash
python src/main.py document.md --update
```

### Custom TOC Placement

Place TOC after first header:

```bash
python src/main.py document.md --toc-placement after-first-header --update
```

### Control TOC Depth

Limit TOC to specific header levels:

```bash
python src/main.py document.md --toc-min-depth 2 --toc-max-depth 4 --update
```

### Save Report to File

Save processing report to a file:

```bash
python src/main.py document.md --output report.txt
```

### Use Configuration File

```bash
python src/main.py document.md --config config.yaml
```

### Command-Line Arguments

- `files`: Markdown files to process (required, one or more)
- `--base-path`: Base path for resolving relative links
- `--validate-external`: Validate external HTTP/HTTPS links
- `--toc-placement`: Where to place TOC - top, after-first-header, or none (default: top)
- `--toc-min-depth`: Minimum header depth for TOC (default: 2)
- `--toc-max-depth`: Maximum header depth for TOC (default: 6)
- `--update`: Update files with generated TOC
- `--output`: Output file path for report
- `--config`: Path to configuration file (YAML)

## Project Structure

```
markdown-processor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file template
├── .gitignore               # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py              # Main script implementation
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md               # API documentation (if applicable)
└── logs/
    └── .gitkeep             # Log directory placeholder
```

### File Descriptions

- `src/main.py`: Core implementation with MarkdownProcessor class and CLI interface
- `config.yaml`: Default configuration file with processing settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

## Link Validation

The script validates three types of links:

### Internal Links

File paths relative to the markdown file or base path:
- `[Link Text](./file.md)`
- `[Link Text](../other/file.md)`
- `[Link Text](file.md)`

### External Links

HTTP/HTTPS URLs (validation optional):
- `[Link Text](https://example.com)`
- `[Link Text](http://example.com/page)`

### Anchor Links

Links to headers within the same document:
- `[Link Text](#header-name)`
- `[Link Text](#section-title)`

### Reference Links

Reference-style links:
- `[Link Text][ref-label]`
- `[ref-label]: https://example.com`

## Table of Contents Generation

The script automatically generates a table of contents from headers in the markdown file.

### Example Input

```markdown
# Main Title

## Section One

### Subsection 1.1

## Section Two
```

### Generated TOC

```markdown
## Table of Contents

- [Section One](#section-one)
  - [Subsection 1.1](#subsection-11)
- [Section Two](#section-two)
```

### TOC Placement Options

- **top**: Place TOC at the beginning of the file
- **after-first-header**: Place TOC after the first header
- **none**: Do not generate TOC

## Output Format

The script provides a comprehensive report:

```
Markdown Processing Report
================================================================================

Files processed: 3
Links found: 15
  - External: 5
  - Internal: 8
Broken links: 2
References found: 3
Broken references: 1
TOC generated: 3

--------------------------------------------------------------------------------

File: /path/to/document.md
  Headers: 10
  Links: 5
  References: 2
  Broken Links:
    - [Broken Link](./nonexistent.md) (internal)
    - [External](https://broken-link.com) (external)
  Broken References:
    - [Missing Ref]: missing-reference
```

## Testing

### Run Tests

```bash
pytest tests/
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage and includes:
- Header extraction
- Link extraction and validation
- Reference checking
- TOC generation
- File updates
- Error handling

## Troubleshooting

### Common Issues

**Issue: "File does not exist"**

Solution: Verify file paths are correct. Use absolute paths or ensure relative paths are correct from the current working directory.

**Issue: "Encoding error"**

Solution: The script tries UTF-8 first, then falls back to latin-1. If issues persist, check file encoding.

**Issue: "External links not validated"**

Solution: Install the requests library: `pip install requests`. External link validation is optional.

**Issue: "TOC not generated"**

Solution: Verify that:
- File contains headers
- Headers are within the configured depth range (toc_min_depth to toc_max_depth)
- TOC placement is not set to "none"

**Issue: "Broken links reported incorrectly"**

Solution: Check that:
- Base path is set correctly for relative links
- File paths are relative to the markdown file or base path
- Anchor links match header slugs (generated from header text)

### Error Messages

All errors are logged to both the console and `logs/processor.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `processor.log`: Main log file with all operations and errors

## Best Practices

1. **Use consistent header structure**: Consistent header levels make TOC generation more effective
2. **Validate regularly**: Run validation regularly to catch broken links early
3. **Set appropriate base path**: Use `--base-path` when processing files from different directories
4. **Update files carefully**: Use `--update` only after reviewing the generated TOC
5. **Check external links periodically**: External link validation can be slow; use it selectively

## Limitations

- **JavaScript-rendered content**: The script cannot validate links in dynamically generated content
- **Complex markdown**: Some complex markdown features may not be fully supported
- **External link validation**: Requires network access and can be slow
- **Anchor matching**: Anchor links must match generated slugs exactly

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes following the code style guidelines
4. Write or update tests
5. Ensure all tests pass: `pytest tests/`
6. Commit your changes with conventional commit messages
7. Push to your branch and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable and function names
- Keep functions focused on a single responsibility

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Follow conventional commit message format
4. Request review from maintainers

## License

This project is provided as-is for educational and automation purposes.
