"""
Utility functions for the Bookstore Finder crawler.
Handles robots.txt checking, rate limiting, and common operations.
"""

import time
import logging
import ssl
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
from typing import Optional, Dict
from datetime import datetime, timedelta
import urllib3
import urllib.request

# Disable SSL warnings (for development/testing)
# Note: In production, you should fix SSL certificate issues properly
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter to ensure we don't overwhelm servers.
    Tracks last request time per domain.
    """

    def __init__(self, delay_seconds: float = 2.5):
        self.delay_seconds = delay_seconds
        self.last_request_time: Dict[str, datetime] = {}

    def wait_if_needed(self, url: str) -> None:
        """
        Wait if we've made a request to this domain too recently.
        """
        domain = urlparse(url).netloc

        if domain in self.last_request_time:
            elapsed = datetime.now() - self.last_request_time[domain]
            required_delay = timedelta(seconds=self.delay_seconds)

            if elapsed < required_delay:
                sleep_time = (required_delay - elapsed).total_seconds()
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)

        self.last_request_time[domain] = datetime.now()


class RobotsChecker:
    """
    Checks robots.txt to ensure we're allowed to crawl.
    Caches robots.txt parsers per domain.
    """

    def __init__(self, user_agent: str):
        self.user_agent = user_agent
        self.parsers: Dict[str, RobotFileParser] = {}
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def can_fetch(self, url: str) -> bool:
        """
        Check if we're allowed to fetch this URL according to robots.txt.
        Returns True if allowed, False if disallowed.
        """
        parsed = urlparse(url)
        domain = parsed.netloc

        # Get or create parser for this domain
        if domain not in self.parsers:
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)

            try:
                # Fetch robots.txt manually with SSL verification disabled
                req = urllib.request.Request(robots_url, headers={'User-Agent': self.user_agent})
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=10) as response:
                    robots_content = response.read().decode('utf-8', errors='ignore')
                    parser.parse(robots_content.splitlines())
                self.parsers[domain] = parser
                logger.debug(f"Successfully read robots.txt for {domain}")
            except Exception as e:
                logger.debug(f"Could not read robots.txt for {domain}: {e}")
                # If we can't read robots.txt, we'll be conservative and allow
                # (common practice when robots.txt doesn't exist)
                return True

        # Check if we can fetch
        try:
            can_fetch = self.parsers[domain].can_fetch(self.user_agent, url)
            if not can_fetch:
                logger.info(f"robots.txt disallows fetching: {url}")
            return can_fetch
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # On error, be conservative and allow
            return True


def make_request(
    url: str,
    user_agent: str,
    timeout: int = 10,
    max_retries: int = 2,
) -> Optional[requests.Response]:
    """
    Make an HTTP GET request with retries and error handling.

    Args:
        url: URL to fetch
        user_agent: User-Agent header value
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        Response object if successful, None if failed
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Requesting {url} (attempt {attempt + 1}/{max_retries + 1})")
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)

            # Check for successful status code
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                logger.info(f"404 Not Found: {url}")
                return None
            elif response.status_code == 403:
                logger.warning(f"403 Forbidden: {url}")
                return None
            elif response.status_code >= 500:
                logger.warning(f"Server error {response.status_code}: {url}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return None
            else:
                logger.warning(f"Unexpected status {response.status_code}: {url}")
                return None

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}: {url}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            return None

        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error on attempt {attempt + 1}: {url}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            return None

    return None


def normalize_url(url: str, base_url: str = None) -> str:
    """
    Normalize a URL (handle relative URLs, ensure scheme, etc.)

    Args:
        url: URL to normalize
        base_url: Base URL for resolving relative URLs

    Returns:
        Normalized absolute URL
    """
    # If URL is relative and we have a base, make it absolute
    if base_url and not url.startswith(("http://", "https://")):
        url = urljoin(base_url, url)

    # Ensure https if no scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def get_domain(url: str) -> str:
    """
    Extract domain from URL.

    Args:
        url: URL to extract domain from

    Returns:
        Domain name (e.g., 'example.com')
    """
    return urlparse(url).netloc


def is_likely_product_page(url: str, html_content: str = None) -> bool:
    """
    Heuristic check if URL looks like a product page.

    Args:
        url: URL to check
        html_content: Optional HTML content to analyze

    Returns:
        True if likely a product page, False otherwise
    """
    url_lower = url.lower()

    # URL-based indicators
    product_indicators = [
        "/product/",
        "/boek/",
        "/boeken/",
        "/artikel/",
        "/item/",
        "/p/",
        "isbn",
        "zanger-ronald",
    ]

    for indicator in product_indicators:
        if indicator in url_lower:
            return True

    # If we have HTML content, check for product-specific elements
    if html_content:
        content_lower = html_content.lower()
        if "in winkelwagen" in content_lower or "add to cart" in content_lower:
            return True
        if "zanger ronald" in content_lower and ("kopen" in content_lower or "bestellen" in content_lower):
            return True

    return False


def clean_text(text: str) -> str:
    """
    Clean and normalize text (remove extra whitespace, etc.)

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Replace multiple whitespace with single space
    text = " ".join(text.split())

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
