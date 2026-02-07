# Job Scraper

Scrape job listings from job board websites, filter them based on keywords, and save matching jobs to a CSV file with details. Supports multiple job boards, configurable selectors, keyword filtering, and rate limiting.

## Project Description

Job Scraper solves the problem of manually searching multiple job boards by automatically scraping listings, filtering them based on customizable keywords, and exporting results to CSV. It helps job seekers efficiently find relevant opportunities across multiple sources and saves time by automating the search and filtering process.

**Target Audience**: Job seekers, recruiters, and anyone who needs to monitor job listings from multiple sources and filter by specific criteria.

## Features

- Multi-job board support with configurable CSS selectors
- Keyword-based filtering (include and exclude keywords)
- Match any or all keywords option
- CSV export with job details (title, company, location, description, URL, source)
- Rate limiting to respect server resources
- Pagination support for multi-page results
- Comprehensive error handling and logging
- Configurable request timeouts and delays
- User-agent customization
- Extensible architecture for adding new job boards

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for web scraping
- Understanding of CSS selectors for configuring job board selectors

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/job-scraper
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

Edit `config.yaml` to configure job boards and filters:

```yaml
filters:
  keywords:
    - python
    - developer
  exclude_keywords:
    - intern

job_boards:
  - name: "Example Job Board"
    base_url: "https://example-jobs.com"
    search_url: "https://example-jobs.com/search?q=python"
    selectors:
      job_item: ".job-listing"
      title: ".job-title a"
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **output_file**: Path to save CSV file (default: `jobs.csv`)
- **filters**: Keyword filtering configuration
  - **keywords**: List of keywords to match
  - **exclude_keywords**: List of keywords to exclude
  - **match_any**: Match any keyword (true) or all keywords (false)
- **job_boards**: List of job board configurations
  - **name**: Display name for job board
  - **base_url**: Base URL of job board
  - **search_url**: Search URL (use `{page}` for pagination)
  - **max_pages**: Maximum pages to scrape
  - **selectors**: CSS selectors for extracting job data
- **rate_limiting**: Delay between requests
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `OUTPUT_FILE`: Override output CSV file path
- `KEYWORDS`: Comma-separated list of keywords (overrides config)

### Job Board Selectors

Each job board requires CSS selectors to extract job information:

- **job_item**: Selector for the container element of each job listing
- **title**: Selector for job title (should be inside job_item)
- **company**: Selector for company name
- **location**: Selector for job location
- **description**: Selector for job description
- **url**: Selector for job detail page URL (usually same as title link)

### Example Configuration

```yaml
filters:
  keywords:
    - python
    - software engineer
    - developer
  exclude_keywords:
    - intern
    - junior
  match_any: true

job_boards:
  - name: "Tech Jobs Board"
    base_url: "https://techjobs.example.com"
    search_url: "https://techjobs.example.com/search?q=python&page={page}"
    max_pages: 5
    selectors:
      job_item: "article.job-card"
      title: "h2.job-title a"
      company: ".company-name"
      location: ".location"
      description: ".job-summary"
      url: "h2.job-title a"
```

## Usage

### Basic Usage

Scrape jobs with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Specify output file (overrides config)
python src/main.py -o my_jobs.csv

# Skip keyword filtering, save all scraped jobs
python src/main.py --no-filter

# Combine options
python src/main.py -c config.yaml -o results.csv
```

### Common Use Cases

1. **Scrape Python Developer Jobs**:
   ```bash
   python src/main.py
   ```
   Configure keywords in `config.yaml` to include "python" and "developer".

2. **Scrape All Jobs Without Filtering**:
   ```bash
   python src/main.py --no-filter
   ```
   Useful for initial scraping to see what's available.

3. **Custom Output Location**:
   ```bash
   python src/main.py -o ~/Documents/jobs_python.csv
   ```

4. **Multiple Job Boards**:
   - Add multiple job board configurations to `config.yaml`
   - Each board will be scraped and results combined

5. **Finding Selectors**:
   - Use browser developer tools (F12) to inspect job listing HTML
   - Identify CSS selectors for each job field
   - Update `config.yaml` with correct selectors

## Project Structure

```
job-scraper/
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

- **src/main.py**: Core scraping logic, keyword filtering, and CSV export
- **config.yaml**: YAML configuration file with job boards and filters
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)
- **jobs.csv**: Generated CSV file with job listings (created when script runs)

## CSV Output Format

The generated CSV file contains the following columns:

- **title**: Job title
- **company**: Company name
- **location**: Job location
- **description**: Job description/summary
- **url**: URL to full job listing
- **source**: Name of job board where job was found

Example CSV row:

```csv
title,company,location,description,url,source
"Senior Python Developer","Tech Corp","San Francisco, CA","We are looking for...","https://example.com/job/123","Example Job Board"
```

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
- Job data extraction from HTML
- Keyword filtering logic
- CSV export functionality
- Error handling for network issues
- Configuration loading
- URL construction and pagination

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Configuration file not found`

**Solution**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option.

---

**Issue**: No jobs found or incorrect data extracted

**Solution**: 
- Verify CSS selectors in `config.yaml` are correct for the job board
- Use browser developer tools to inspect HTML structure
- Check that job board HTML structure hasn't changed
- Enable DEBUG logging to see detailed extraction process

---

**Issue**: `ConnectionError` or timeout errors

**Solution**:
- Check internet connection
- Increase `request_timeout` in `config.yaml`
- Increase `delay_seconds` in rate_limiting to be more respectful
- Some job boards may block automated requests; consider using proxies

---

**Issue**: Jobs not matching keywords

**Solution**:
- Check keyword spelling and case (matching is case-insensitive)
- Verify `match_any` setting matches your intent
- Review job descriptions to see what text is actually being searched
- Use `--no-filter` to see all scraped jobs first

---

**Issue**: Rate limiting or IP blocking

**Solution**:
- Increase `delay_seconds` in rate_limiting configuration
- Reduce `max_pages` to scrape fewer pages
- Some job boards have anti-scraping measures; respect their terms of service

### Error Messages

- **"Error fetching URL"**: Network issue or invalid URL; check internet connection and URL format
- **"No job item selector configured"**: Missing CSS selector in config; add `job_item` selector
- **"Error parsing job element"**: HTML structure changed or selector incorrect; update selectors
- **"No jobs to save"**: No jobs matched filters or scraping failed; check logs for details

## Legal and Ethical Considerations

- **Respect robots.txt**: Check job board's robots.txt file before scraping
- **Terms of Service**: Review and comply with each job board's terms of service
- **Rate Limiting**: Use appropriate delays between requests to avoid overloading servers
- **Personal Use**: This tool is intended for personal use; commercial use may require permission
- **Data Usage**: Use scraped data responsibly and in accordance with applicable laws

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

This project is provided as-is for educational and personal use. Users are responsible for ensuring compliance with job board terms of service and applicable laws.
