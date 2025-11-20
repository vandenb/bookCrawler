"""
Extractor for postal codes and location information from bookstore websites.
"""

import re
import logging
from typing import Optional, Tuple, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

from config import POSTAL_CODE_CONFIG
from utils import make_request, clean_text

logger = logging.getLogger(__name__)


class LocationExtractor:
    """
    Extracts postal codes and city names from bookstore websites.
    """

    def __init__(self, user_agent: str, timeout: int = 10):
        self.user_agent = user_agent
        self.timeout = timeout

        # Compile postal code regex once
        self.postal_code_pattern = re.compile(
            POSTAL_CODE_CONFIG["pattern"],
            re.IGNORECASE
        )

    def extract_location(self, base_url: str, html_content: str = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract postal code and city from a bookstore website.

        Args:
            base_url: Base URL of the bookstore
            html_content: Optional HTML content to search (if None, will fetch)

        Returns:
            Tuple of (postal_code, city) or (None, None) if not found
        """
        # First, try to extract from provided HTML (usually homepage)
        if html_content:
            result = self._extract_from_html(html_content, base_url)
            if result[0]:
                return result

        # If not found, try contact pages
        contact_urls = self._get_contact_page_urls(base_url, html_content)

        for contact_url in contact_urls:
            logger.debug(f"Trying contact page: {contact_url}")

            response = make_request(
                contact_url,
                self.user_agent,
                self.timeout
            )

            if response:
                result = self._extract_from_html(response.text, base_url)
                if result[0]:
                    logger.info(f"Found location on contact page: {contact_url}")
                    return result

        logger.warning(f"Could not extract postal code for {base_url}")
        return None, None

    def _extract_from_html(self, html_content: str, base_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract postal code and city from HTML content.

        Args:
            html_content: HTML content to search
            base_url: Base URL (for logging)

        Returns:
            Tuple of (postal_code, city) or (None, None)
        """
        soup = BeautifulSoup(html_content, 'lxml')

        # First, try structured address elements
        result = self._extract_from_address_elements(soup)
        if result[0]:
            return result

        # Then try footer
        result = self._extract_from_footer(soup)
        if result[0]:
            return result

        # Finally, search entire page as fallback
        result = self._extract_from_full_text(soup)
        if result[0]:
            return result

        return None, None

    def _extract_from_address_elements(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """
        Try to extract from structured address elements (schema.org, address tags, etc.)
        """
        # Try address-specific selectors
        for selector in POSTAL_CODE_CONFIG["address_selectors"]:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(separator=" ", strip=True)
                    result = self._extract_postal_code_and_city(text)
                    if result[0]:
                        logger.debug(f"Found postal code in {selector}")
                        return result
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")

        return None, None

    def _extract_from_footer(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """
        Try to extract from footer elements.
        """
        footers = soup.find_all(['footer', 'div'], class_=re.compile('footer', re.I))

        for footer in footers:
            text = footer.get_text(separator=" ", strip=True)
            result = self._extract_postal_code_and_city(text)
            if result[0]:
                logger.debug("Found postal code in footer")
                return result

        return None, None

    def _extract_from_full_text(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """
        Last resort: search entire page text.
        """
        # Get all text, preserving some structure
        text = soup.get_text(separator="\n", strip=True)
        result = self._extract_postal_code_and_city(text)
        if result[0]:
            logger.debug("Found postal code in full text search")
        return result

    def _extract_postal_code_and_city(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract postal code and city from a text string.

        Dutch postal codes: 4 digits + 2 letters (e.g., "1012 AB")
        City name usually comes before the postal code.

        Args:
            text: Text to search

        Returns:
            Tuple of (postal_code, city)
        """
        matches = self.postal_code_pattern.finditer(text)

        for match in matches:
            postal_code = f"{match.group(1)} {match.group(2).upper()}"

            # Try to extract city name (usually before postal code)
            # Get context around the match
            start_pos = max(0, match.start() - 100)
            end_pos = min(len(text), match.end() + 20)
            context = text[start_pos:end_pos]

            # Extract city (word(s) before postal code)
            city = self._extract_city_from_context(context, match.group(0))

            if city:
                logger.debug(f"Extracted: {postal_code}, {city}")
                return postal_code, city
            else:
                # Return postal code even without city
                logger.debug(f"Extracted postal code without city: {postal_code}")
                return postal_code, None

        return None, None

    def _extract_city_from_context(self, context: str, postal_code_match: str) -> Optional[str]:
        """
        Extract city name from context around postal code.

        Args:
            context: Text context around postal code
            postal_code_match: The matched postal code string

        Returns:
            City name or None
        """
        # Split by postal code
        before_postal = context.split(postal_code_match)[0]

        # Common patterns before postal code in Dutch addresses:
        # "Streetname 123, 1234 AB Amsterdam" -> want "Amsterdam" (after postal)
        # "Amsterdam, Streetname 123, 1234 AB" -> want "Amsterdam" (before postal)
        # "1234 AB Amsterdam" -> want "Amsterdam" (after postal)

        # Check if city is after postal code
        after_postal = context.split(postal_code_match)[-1] if postal_code_match in context else ""
        after_words = after_postal.strip().split()
        if after_words:
            # First word(s) after postal code might be city
            city_candidate = after_words[0].strip('.,;:')
            if self._is_valid_city_name(city_candidate):
                return city_candidate

        # Otherwise, look for city before postal code
        # Split by common delimiters
        parts = re.split(r'[,\n\r]', before_postal)

        if parts:
            # Take last part before postal code
            last_part = parts[-1].strip()

            # Extract potential city name (capitalized word(s))
            words = last_part.split()

            # Look for capitalized words (city names are capitalized)
            city_words = []
            for word in reversed(words):
                word = word.strip('.,;:')
                if word and word[0].isupper() and len(word) > 2:
                    city_words.insert(0, word)
                else:
                    break

            if city_words:
                city = " ".join(city_words[:3])  # Max 3 words
                if self._is_valid_city_name(city):
                    return city

        return None

    def _is_valid_city_name(self, name: str) -> bool:
        """
        Validate if a string looks like a city name.

        Args:
            name: Potential city name

        Returns:
            True if valid, False otherwise
        """
        if not name or len(name) < 3:
            return False

        # Should start with capital letter
        if not name[0].isupper():
            return False

        # Shouldn't be a common non-city word
        exclude_words = {
            'Nederland', 'Netherlands', 'Tel', 'Telefoon', 'Email', 'Mail',
            'Website', 'Openingstijden', 'Bezoekadres', 'Postadres',
            'Straat', 'Postbus', 'KVK', 'BTW', 'IBAN'
        }

        if name in exclude_words:
            return False

        return True

    def _get_contact_page_urls(self, base_url: str, html_content: str = None) -> List[str]:
        """
        Find potential contact page URLs.

        Args:
            base_url: Base URL of the website
            html_content: Optional HTML content to search for contact links

        Returns:
            List of potential contact page URLs
        """
        contact_urls = []

        # Standard contact page paths
        standard_paths = POSTAL_CODE_CONFIG["search_locations"]

        for path in standard_paths:
            url = urljoin(base_url, path)
            contact_urls.append(url)

        # If we have HTML, look for contact links
        if html_content:
            soup = BeautifulSoup(html_content, 'lxml')
            links = soup.find_all('a', href=True)

            contact_keywords = ['contact', 'over-ons', 'about', 'vestiging', 'winkel', 'locatie']

            for link in links:
                href = link.get('href', '')
                text = link.get_text().lower()

                if any(keyword in href.lower() or keyword in text for keyword in contact_keywords):
                    full_url = urljoin(base_url, href)
                    if full_url not in contact_urls:
                        contact_urls.append(full_url)

        # Limit to avoid too many requests
        return contact_urls[:5]
