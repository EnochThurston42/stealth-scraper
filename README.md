# StealthScraper 

A lightweight web scraping toolkit with session management, stealth headers, and multiple output formats.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![No Dependencies](https://img.shields.io/badge/dependencies-zero-orange)

## Features

- **Stealth mode** — Rotates real browser User-Agent strings and sends browser-like headers
- **Session management** — Cookie persistence across requests, save/load cookie jars
- **Rate limiting** — Configurable delay between requests to avoid getting blocked
- **Smart selectors** — Regex-based HTML and text extraction
- **Link extraction** — Automatically resolve relative URLs to absolute
- **Output formats** — Export to JSON, CSV, or Markdown
- **Zero dependencies** — Pure Python stdlib. No pip installs.

## Quick Start

```python
from stealth_scraper import ScraperSession, scrape

# One-shot scrape
page = scrape("https://example.com")
print(page.text[:500])

# Session with cookie persistence
session = ScraperSession(rate_limit=2.0, stealth=True)
page1 = session.get("https://example.com/login")
page2 = session.get("https://example.com/dashboard")
session.save_cookies("cookies.json")

# Extract and export
links = page1.find_links(base_url="https://example.com")
page1.to_markdown("output.md")
page1.to_json("output.json")
```

### CLI Usage

```bash
# Scrape a page
python stealth_scraper.py https://example.com

# Extract links
python stealth_scraper.py https://example.com --links

# Save as markdown
python stealth_scraper.py https://example.com -o page.md
```

## Architecture

```
StealthScraper
├── ScraperSession      # HTTP session with cookies, rate limiting, stealth
│   ├── get()           # Fetch URL with full session context
│   ├── save_cookies()  # Persist cookies to JSON
│   └── load_cookies()  # Load cookies from JSON
├── ScrapedPage         # Parsed result with extraction methods
│   ├── find_all()      # Regex search on raw HTML
│   ├── find_links()    # Extract and resolve all links
│   ├── find_text()     # Regex search on stripped text
│   ├── to_json()       # Export as JSON
│   ├── to_csv()        # Export as CSV
│   └── to_markdown()   # Export as Markdown
└── scrape()            # Quick one-shot function
```

## License

MIT
