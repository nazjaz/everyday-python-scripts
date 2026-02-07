# PDF Text Extractor

Extract text content from PDF files and save it to text files with the same name. Handles encrypted PDFs, multi-page PDFs, and includes comprehensive logging and error handling. Perfect for batch processing PDF documents and converting them to searchable text format.

## Project Description

PDF Text Extractor solves the problem of extracting text from multiple PDF files efficiently. It processes PDFs recursively, handles encrypted documents with password support, extracts text from all pages, and saves the content to organized text files. Ideal for document processing, text analysis, and creating searchable text archives from PDF collections.

**Target Audience**: Researchers, document managers, data analysts, and anyone who needs to extract and process text content from PDF files in bulk.

## Features

- Extract text from all pages of multi-page PDFs
- Handle encrypted PDFs with password support
- Recursive directory scanning
- Preserve directory structure in output
- Page separators for multi-page documents
- Skip encrypted PDFs option if password not available
- Comprehensive error handling and logging
- Dry-run mode to preview operations
- Support for various PDF formats
- Statistics tracking (files processed, pages extracted, errors)

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- PDF files to process

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/pdf-text-extractor
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

Edit `config.yaml` to set your source and destination directories:

```yaml
source_directory: ~/Documents/PDFs
destination_directory: ~/Documents/ExtractedText
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory containing PDF files to process
- **destination_directory**: Directory for extracted text files
- **pdf_password**: Password for encrypted PDFs (leave empty if not needed)
- **skip_encrypted**: Skip encrypted PDFs if password is not provided (default: `true`)
- **output_encoding**: Text file encoding (default: `utf-8`)
- **operations**: Operation settings
  - **create_destination**: Create destination directory if it doesn't exist
  - **recursive**: Scan subdirectories recursively
  - **preserve_structure**: Preserve directory structure in destination
  - **dry_run**: Preview mode without creating files
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `SOURCE_DIRECTORY`: Override source directory path
- `DESTINATION_DIRECTORY`: Override destination directory path
- `PDF_PASSWORD`: Override PDF password
- `DRY_RUN`: Enable dry run mode (`true`/`false`)

### Example Configuration

```yaml
source_directory: ~/Documents/PDFs
destination_directory: ~/Documents/ExtractedText
pdf_password: ""
skip_encrypted: true
output_encoding: utf-8

operations:
  create_destination: true
  recursive: true
  preserve_structure: true
  dry_run: false
```

## Usage

### Basic Usage

Extract text from PDFs with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Preview changes without creating text files (dry run)
python src/main.py --dry-run

# Specify password for encrypted PDFs
python src/main.py -p "your_password"

# Combine options
python src/main.py -c config.yaml --dry-run -p "password"
```

### Common Use Cases

1. **Preview Extraction (Recommended First Step)**:
   ```bash
   python src/main.py --dry-run
   ```
   See what would be extracted without creating files.

2. **Extract Text from All PDFs**:
   ```bash
   python src/main.py
   ```
   Processes all PDFs in source directory.

3. **Extract from Encrypted PDFs**:
   ```bash
   python src/main.py -p "your_password"
   ```
   Or set `pdf_password` in `config.yaml`.

4. **Process Specific Directory**:
   - Edit `source_directory` in `config.yaml`
   - Or set environment variable: `export SOURCE_DIRECTORY=/path/to/pdfs`

5. **Preserve Directory Structure**:
   - Set `preserve_structure: true` in config
   - Output files will maintain source directory hierarchy

## Project Structure

```
pdf-text-extractor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py         # Package initialization
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core extraction logic, PDF reading, and text file creation
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)

## Output Format

For multi-page PDFs, the extracted text includes page separators:

```
--- Page 1 ---
Text content from first page...

--- Page 2 ---
Text content from second page...

--- Page 3 ---
Text content from third page...
```

Single-page PDFs are extracted without page separators.

## Handling Encrypted PDFs

The script handles encrypted PDFs in the following ways:

1. **With Password**: If `pdf_password` is provided in config or via `-p` option, the script attempts to decrypt and extract text.

2. **Without Password**: If no password is provided and `skip_encrypted: true`, encrypted PDFs are skipped and logged.

3. **Failed Decryption**: If password is incorrect, the PDF is skipped and an error is logged.

## Limitations

- **Image-based PDFs**: PDFs that contain only images (scanned documents) will not extract text. These require OCR (Optical Character Recognition) which is not included in this script.

- **Complex Layouts**: PDFs with complex layouts, tables, or multi-column text may not extract perfectly.

- **Password Protection**: Encrypted PDFs require the correct password to extract text.

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- PDF text extraction
- Multi-page PDF handling
- Encrypted PDF handling
- File operations
- Error handling
- Directory structure preservation

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Source directory does not exist`

**Solution**: Ensure the source directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: No text extracted from PDF

**Solution**:
- PDF may be image-based (scanned document) - requires OCR
- PDF may have complex layout - text extraction may be incomplete
- Check logs for specific error messages
- Try opening PDF in a viewer to verify it contains selectable text

---

**Issue**: `PermissionError` when creating text files

**Solution**: Ensure you have write permissions to the destination directory. On Linux/Mac, you may need to adjust directory permissions.

---

**Issue**: Encrypted PDFs not being processed

**Solution**:
- Provide password via `-p` option or `pdf_password` in config
- Check that password is correct
- If `skip_encrypted: true`, encrypted PDFs without password will be skipped

---

**Issue**: Text extraction quality is poor

**Solution**:
- Some PDFs have poor text extraction quality due to formatting
- Complex layouts may not extract perfectly
- Consider using OCR tools for image-based PDFs
- Try different PDF libraries (pdfplumber, pdfminer) for better results

### Error Messages

- **"Error reading PDF"**: PDF file may be corrupted or in unsupported format
- **"PDF is encrypted"**: PDF requires password; provide via config or `-p` option
- **"No text extracted"**: PDF may be image-based or have no extractable text
- **"Error saving text"**: Check destination directory permissions and disk space

## Tips for Best Results

1. **Use Dry-Run First**: Always run with `--dry-run` to preview operations
2. **Check PDF Quality**: Verify PDFs contain selectable text (not just images)
3. **Handle Encrypted PDFs**: Provide passwords for encrypted documents
4. **Review Logs**: Check logs after processing to identify any issues
5. **Test with Sample**: Test with a small set of PDFs first
6. **Backup Originals**: Keep original PDFs as backup

## Alternative Libraries

If PyPDF2 doesn't provide satisfactory results, consider these alternatives:

- **pdfplumber**: Better for complex layouts and tables
- **pdfminer**: More control over extraction process
- **pymupdf (fitz)**: Fast and handles many PDF features

These can be integrated by modifying the `_extract_text_from_pdf` method.

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov pytest-mock`
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
