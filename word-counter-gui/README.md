# Word Counter GUI

A Python GUI application that analyzes text files for word frequency, character count, and reading time estimates. Built with tkinter for a simple, cross-platform interface.

## Features

- **Word counting**: Accurate word count analysis
- **Character counting**: Total characters and characters without spaces
- **Sentence and paragraph counting**: Text structure analysis
- **Word frequency analysis**: Top 10 most frequent words with counts
- **Reading time estimates**: Estimates for slow (150 wpm), average (200 wpm), and fast (250 wpm) reading speeds
- **File loading**: Open and analyze text files
- **Real-time updates**: Statistics update as you type
- **User-friendly interface**: Simple, intuitive GUI with clear statistics display

## Prerequisites

- Python 3.8 or higher
- tkinter (usually included with Python, may require separate installation on Linux)
- pip (Python package installer)

### Installing tkinter

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install python3-tkinter
```

**macOS:** tkinter is included with Python

**Windows:** tkinter is included with Python

## Installation

### Step 1: Navigate to Project Directory

```bash
cd word-counter-gui
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

### Step 4: Verify tkinter Installation

```bash
python3 -c "import tkinter; print('tkinter is available')"
```

## Configuration

### Configuration File (config.yaml)

The script supports configuration via a YAML file:

```yaml
average_reading_speed: 200
average_reading_speed_slow: 150
average_reading_speed_fast: 250
top_words_count: 10
```

## Usage

### Basic Usage

Launch the GUI application:

```bash
python src/main.py
```

### With Configuration File

```bash
python src/main.py --config config.yaml
```

### Command-Line Arguments

- `--config`: Path to configuration file (YAML)

## Using the Application

1. **Open File**: Click "Open File" to load a text file for analysis
2. **Type Text**: Type or paste text directly into the text area
3. **View Statistics**: Statistics update automatically as you type
4. **Clear**: Click "Clear" to reset the text area

### Statistics Provided

- **Word Count**: Total number of words
- **Character Count**: Total characters including spaces
- **Characters (no spaces)**: Total characters excluding spaces
- **Sentences**: Number of sentences
- **Paragraphs**: Number of paragraphs
- **Reading Time**: Estimated reading time at different speeds
- **Word Frequency**: Top 10 most frequent words with counts

## Project Structure

```
word-counter-gui/
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

- `src/main.py`: Core implementation with WordCounter and WordCounterGUI classes
- `config.yaml`: Configuration file with reading speed settings
- `tests/test_main.py`: Unit tests for all public functions
- `logs/`: Directory for log files (created automatically)

## Reading Time Calculation

Reading time is calculated based on average reading speeds:
- **Slow**: 150 words per minute
- **Average**: 200 words per minute (standard)
- **Fast**: 250 words per minute

The calculation: `reading_time = word_count / words_per_minute`

## Word Frequency Analysis

The application identifies the top 10 most frequent words in the text, showing:
- Word (lowercase)
- Count (number of occurrences)

Words are extracted using word boundaries, so punctuation is properly handled.

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
- Word counting accuracy
- Character counting
- Sentence and paragraph counting
- Word frequency calculation
- Reading time calculation
- Text analysis edge cases

## Troubleshooting

### Common Issues

**Issue: "tkinter is not available"**

Solution: Install tkinter for your Python installation. See Prerequisites section for installation instructions.

**Issue: "No module named 'tkinter'"**

Solution: On Linux, install python3-tk package. On other systems, ensure Python was installed with tkinter support.

**Issue: GUI window does not appear**

Solution: Check that you're running the script in an environment that supports GUI applications. Some headless servers may not support GUI applications.

**Issue: File encoding error**

Solution: The application tries UTF-8 first, then falls back to latin-1. If issues persist, check file encoding.

**Issue: Statistics not updating**

Solution: Ensure text is entered in the text area. Statistics update automatically on text changes.

### Error Messages

All errors are logged to both the console and `logs/counter.log`. Check the log file for detailed error information and stack traces.

### Log Files

Log files are stored in the `logs/` directory:
- `counter.log`: Main log file with all operations and errors

## Performance Considerations

- The application processes text in real-time as you type
- Large text files may take a moment to load
- Word frequency calculation is efficient for typical document sizes
- The GUI remains responsive during analysis

## Best Practices

1. **Use appropriate file encoding**: UTF-8 is preferred for text files
2. **Large files**: For very large files, consider breaking them into smaller sections
3. **Reading time**: Reading time estimates are approximate and vary by reader
4. **Word frequency**: Common words (the, a, an, etc.) will typically appear in frequency lists

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
