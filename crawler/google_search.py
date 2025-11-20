"""
Google site-search functionality to find book product pages.
Falls back to direct crawling if Google search is not available.
"""

import logging
import re
from typing import Optional, List
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup

from config import BOOK_CONFIG, CRAWLER_CONFIG, SEARCH_PATTERNS
from utils import make_request, is_likely_product_page

logger = logging.getLogger(__name__)


class ProductPageFinder:
    """
    Finds product pages for books on bookstore websites.
    Uses Google site-search as primary method, with direct crawling as fallback.
    """

    def __init__(self, user_agent: str, timeout: int = 10):
        self.user_agent = user_agent
        self.timeout = timeout
        self.use_google = CRAWLER_CONFIG["use_google_search"]

    def find_product_page(self, bookstore_name: str, bookstore_url: str) -> Optional[str]:
        """
        Find the product page for the configured book on a bookstore website.

        Args:
            bookstore_name: Name of the bookstore
            bookstore_url: URL of the bookstore website

        Returns:
            URL of the product page, or None if not found
        """
        logger.info(f"Searching for product page on {bookstore_name} ({bookstore_url})")

        # Method 1: Try known Libris/BLZ URL pattern first
        # Many Dutch bookstores use the same webshop software with predictable URLs
        product_url = self._try_known_url_patterns(bookstore_url)
        if product_url:
            logger.info(f"Found via known URL pattern: {product_url}")
            return product_url

        # Method 2: Try Google site-search
        if self.use_google:
            product_url = self._search_via_google(bookstore_url)
            if product_url:
                logger.info(f"Found via Google: {product_url}")
                return product_url
            else:
                logger.debug(f"Google search failed for {bookstore_url}")

        # Method 3: Try direct crawling as fallback
        logger.debug(f"Attempting direct crawl for {bookstore_url}")
        product_url = self._search_via_direct_crawl(bookstore_url)

        if product_url:
            logger.info(f"Found via direct crawl: {product_url}")
            return product_url

        logger.warning(f"Product page not found for {bookstore_name}")
        return None

    def _try_known_url_patterns(self, site_url: str) -> Optional[str]:
        """
        Try known URL patterns used by Libris/BLZ bookstore software.

        Many Dutch bookstores use the same webshop platform with predictable
        product page URLs.

        Args:
            site_url: URL of the bookstore website

        Returns:
            Product page URL or None
        """
        from urllib.parse import urlparse

        parsed = urlparse(site_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Known URL patterns for this book
        # Pattern used by Libris/BLZ webshops
        patterns = [
            "/a/walter-van-den-berg/zanger-ronald-zingt-de-blues/501634390#paperback-9789048853366",
            "/a/walter-van-den-berg/zanger-ronald-zingt-de-blues/501634390",
            "/boek/?authortitle=walter-van-den-berg/zanger-ronald-zingt-de-blues--9789048853366",
        ]

        for pattern in patterns:
            test_url = base_url + pattern
            logger.debug(f"Testing known URL pattern: {test_url}")

            response = make_request(test_url, self.user_agent, self.timeout)

            if response:
                # Verify it's actually the right book
                html_lower = response.text.lower()
                if 'zanger ronald' in html_lower or BOOK_CONFIG["isbn"] in response.text:
                    return test_url

        return None

    def _search_via_google(self, site_url: str) -> Optional[str]:
        """
        Search for the book using Google site-search.

        Args:
            site_url: URL of the site to search

        Returns:
            Product page URL or None
        """
        # Build search query
        book_title = BOOK_CONFIG["title"]
        book_author = BOOK_CONFIG["author"]

        # Extract domain from site URL
        from urllib.parse import urlparse
        domain = urlparse(site_url).netloc

        # Try different search patterns
        search_queries = [
            f'site:{domain} "{book_title}" "{book_author}"',
            f'site:{domain} "{book_title}"',
            f'site:{domain} {BOOK_CONFIG["isbn"]}',
        ]

        for query in search_queries:
            logger.debug(f"Google search: {query}")

            # Build Google search URL
            google_url = f"https://www.google.com/search?q={quote_plus(query)}"

            # Make request
            response = make_request(google_url, self.user_agent, self.timeout)

            if not response:
                logger.debug("Google search request failed")
                continue

            # Parse results
            soup = BeautifulSoup(response.text, 'lxml')

            # Find search result links
            # Google's HTML structure: results are in <div> with class 'g', links in <a>
            results = soup.find_all('div', class_='g')

            for result in results[:5]:  # Check first 5 results
                link_tag = result.find('a', href=True)
                if link_tag:
                    url = link_tag['href']

                    # Google sometimes wraps URLs, extract actual URL
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]

                    # Check if this looks like a product page
                    if domain in url and is_likely_product_page(url):
                        # Verify the page exists and contains book info
                        if self._verify_product_page(url):
                            return url

        return None

    def _search_via_direct_crawl(self, site_url: str) -> Optional[str]:
        """
        Search for the book by crawling the bookstore website directly.

        Args:
            site_url: URL of the bookstore website

        Returns:
            Product page URL or None
        """
        # Fetch homepage
        response = make_request(site_url, self.user_agent, self.timeout)

        if not response:
            logger.debug(f"Could not fetch homepage: {site_url}")
            return None

        soup = BeautifulSoup(response.text, 'lxml')

        # Strategy 1: Look for search box and construct search URL
        search_url = self._find_search_url(soup, site_url)
        if search_url:
            logger.debug(f"Found search URL: {search_url}")

            # Try searching
            search_response = make_request(search_url, self.user_agent, self.timeout)
            if search_response:
                result_url = self._extract_product_from_search_results(
                    search_response.text,
                    site_url
                )
                if result_url:
                    return result_url

        # Strategy 2: Look for direct links to the book
        # This works if the book is featured on homepage or in catalog
        book_title_lower = BOOK_CONFIG["title"].lower()
        book_author_lower = BOOK_CONFIG["author"].lower()

        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().lower()

            # Check if link text mentions the book
            if book_title_lower in text or 'zanger ronald' in text:
                full_url = urljoin(site_url, href)

                if is_likely_product_page(full_url):
                    # Verify it's the right book
                    if self._verify_product_page(full_url):
                        return full_url

        # Strategy 3: Look for catalog/books section and crawl one level deeper
        # (We'll keep this simple and not go too deep)
        catalog_links = self._find_catalog_links(soup, site_url)

        for catalog_url in catalog_links[:3]:  # Limit to avoid too many requests
            logger.debug(f"Checking catalog: {catalog_url}")

            catalog_response = make_request(catalog_url, self.user_agent, self.timeout)
            if catalog_response:
                result_url = self._extract_product_from_catalog(
                    catalog_response.text,
                    site_url
                )
                if result_url:
                    return result_url

        return None

    def _find_search_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        Try to construct a search URL for the book.

        Args:
            soup: BeautifulSoup object of homepage
            base_url: Base URL of the site

        Returns:
            Search URL or None
        """
        # Common search URL patterns in Dutch bookstores
        search_patterns = [
            '/zoeken',
            '/search',
            '/zoek',
            '/catalogsearch/result',
        ]

        # Try to find search form
        search_forms = soup.find_all('form')

        for form in search_forms:
            action = form.get('action', '')
            inputs = form.find_all('input')

            # Look for search-related forms
            for input_tag in inputs:
                name = input_tag.get('name', '').lower()
                if any(keyword in name for keyword in ['search', 'query', 'q', 'zoek']):
                    # Found search form!
                    search_path = action or '/search'
                    search_url = urljoin(base_url, search_path)

                    # Add book title as query parameter
                    book_title = BOOK_CONFIG["title"]
                    separator = '&' if '?' in search_url else '?'
                    search_url = f"{search_url}{separator}{name}={quote_plus(book_title)}"

                    return search_url

        # If no form found, try standard search paths
        for pattern in search_patterns:
            search_url = urljoin(base_url, pattern)
            search_url = f"{search_url}?q={quote_plus(BOOK_CONFIG['title'])}"
            # We'll return first pattern (could verify it exists, but skip for simplicity)
            return search_url

        return None

    def _extract_product_from_search_results(self, html: str, base_url: str) -> Optional[str]:
        """
        Extract product URL from search results page.
        """
        soup = BeautifulSoup(html, 'lxml')

        book_title_lower = BOOK_CONFIG["title"].lower()
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().lower()

            # Check if link mentions the book
            if 'zanger ronald' in text or book_title_lower in text:
                full_url = urljoin(base_url, href)

                if is_likely_product_page(full_url):
                    if self._verify_product_page(full_url):
                        return full_url

        return None

    def _find_catalog_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find links to catalog/books sections.
        """
        catalog_urls = []
        catalog_keywords = ['boeken', 'books', 'catalog', 'catalogus', 'assortiment', 'literatuur']

        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '').lower()
            text = link.get_text().lower()

            if any(keyword in href or keyword in text for keyword in catalog_keywords):
                full_url = urljoin(base_url, link['href'])
                if full_url not in catalog_urls:
                    catalog_urls.append(full_url)

        return catalog_urls

    def _extract_product_from_catalog(self, html: str, base_url: str) -> Optional[str]:
        """
        Extract product URL from catalog page.
        """
        # Same logic as search results
        return self._extract_product_from_search_results(html, base_url)

    def _verify_product_page(self, url: str) -> bool:
        """
        Verify that a URL actually contains the book we're looking for.

        Args:
            url: URL to verify

        Returns:
            True if page contains the book, False otherwise
        """
        response = make_request(url, self.user_agent, self.timeout)

        if not response:
            return False

        html_lower = response.text.lower()
        book_title_lower = BOOK_CONFIG["title"].lower()
        book_author_lower = BOOK_CONFIG["author"].lower()

        # Check if page contains book title and author
        has_title = book_title_lower in html_lower or 'zanger ronald' in html_lower
        has_author = book_author_lower in html_lower or 'walter van den berg' in html_lower

        # Also check for ISBN (strong signal)
        has_isbn = BOOK_CONFIG["isbn"] in response.text

        # Page should have at least title + author, or ISBN
        if (has_title and has_author) or has_isbn:
            logger.debug(f"Verified product page: {url}")
            return True

        logger.debug(f"Page does not contain expected book info: {url}")
        return False
