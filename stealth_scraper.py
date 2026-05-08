#!/usr/bin/env python3
"""StealthScraper - Web scraping toolkit with session management and stealth headers."""
import json
import re
import csv
import time
import random
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin, urlparse


BROWSER_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

STEALTH_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class ScraperSession:
    """HTTP session with cookie persistence, stealth headers, and rate limiting."""
    
    def __init__(self, rate_limit: float = 1.0, stealth: bool = True):
        self.cookies = {}
        self.rate_limit = rate_limit
        self.stealth = stealth
        self._last_request = 0
        self.history = []
    
    def _build_headers(self, extra: dict = None) -> dict:
        headers = {}
        if self.stealth:
            headers.update(STEALTH_HEADERS)
            headers["User-Agent"] = random.choice(BROWSER_USER_AGENTS)
            if self.cookies:
                headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if extra:
            headers.update(extra)
        return headers
    
    def _rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
    
    def _update_cookies(self, resp):
        for header in resp.headers.get_all("Set-Cookie", []):
            parts = header.split(";")[0].split("=", 1)
            if len(parts) == 2:
                self.cookies[parts[0].strip()] = parts[1].strip()
    
    def get(self, url: str, headers: dict = None, timeout: int = 15) -> "ScrapedPage":
        self._rate_limit()
        req = Request(url, headers=self._build_headers(headers))
        self._last_request = time.time()
        
        try:
            resp = urlopen(req, timeout=timeout)
            self._update_cookies(resp)
            page = ScrapedPage(url, resp.read().decode("utf-8", errors="replace"), resp.status)
        except HTTPError as e:
            page = ScrapedPage(url, e.read().decode("utf-8", errors="replace"), e.code)
        except URLError as e:
            page = ScrapedPage(url, "", 0, error=str(e))
        
        self.history.append({"url": url, "status": page.status, "time": time.strftime("%H:%M:%S")})
        return page
    
    def save_cookies(self, path: str):
        Path(path).write_text(json.dumps(self.cookies, indent=2))
    
    def load_cookies(self, path: str):
        if Path(path).exists():
            self.cookies = json.loads(Path(path).read_text())


class ScrapedPage:
    """Parsed web page with CSS-like selectors and output formatters."""
    
    def __init__(self, url: str, html: str, status: int, error: str = None):
        self.url = url
        self.html = html
        self.status = status
        self.error = error
        self.text = re.sub(r"<[^>]+>", " ", html)
        self.text = re.sub(r"\s+", " ", self.text).strip()
    
    def find_all(self, pattern: str) -> list:
        """Find all matches of a regex pattern in the HTML."""
        return re.findall(pattern, self.html)
    
    def find_links(self, base_url: str = None) -> list:
        """Extract all links from the page."""
        links = re.findall(r'href=["\']([^"\']+)["\']', self.html)
        if base_url:
            links = [urljoin(base_url, link) for link in links]
        return list(set(links))
    
    def find_text(self, pattern: str) -> list:
        """Find all text matches in the stripped text content."""
        return re.findall(pattern, self.text)
    
    def to_json(self, path: str, data: dict = None):
        """Save page data as JSON."""
        output = data or {"url": self.url, "status": self.status, "text": self.text[:5000]}
        Path(path).write_text(json.dumps(output, indent=2, ensure_ascii=False))
    
    def to_csv(self, path: str, rows: list, headers: list):
        """Save extracted data as CSV."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
    
    def to_markdown(self, path: str):
        """Save page text content as Markdown."""
        content = f"# {self._extract_title()}\n\nSource: {self.url}\n\n{self.text}"
        Path(path).write_text(content, encoding="utf-8")
    
    def _extract_title(self) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", self.html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else urlparse(self.url).netloc


def scrape(url: str, stealth: bool = True, rate_limit: float = 1.0) -> ScrapedPage:
    """Quick one-shot scrape of a URL."""
    session = ScraperSession(rate_limit=rate_limit, stealth=stealth)
    return session.get(url)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="StealthScraper - web scraping toolkit")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("-o", "--output", help="Output file (json/csv/md)")
    parser.add_argument("--no-stealth", action="store_true")
    parser.add_argument("--rate-limit", type=float, default=1.0)
    parser.add_argument("--links", action="store_true", help="Extract links")
    args = parser.parse_args()
    
    page = scrape(args.url, stealth=not args.no_stealth, rate_limit=args.rate_limit)
    print(f"Status: {page.status}")
    print(f"Text length: {len(page.text)} chars")
    
    if args.links:
        links = page.find_links(base_url=args.url)
        print(f"Links found: {len(links)}")
        for link in sorted(links)[:20]:
            print(f"  {link}")
    
    if args.output:
        ext = Path(args.output).suffix
        if ext == ".json":
            page.to_json(args.output)
        elif ext == ".md":
            page.to_markdown(args.output)
        print(f"Saved to {args.output}")
