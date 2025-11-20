"""
Configuration for the Bookstore Finder crawler.
"""

# Book information - change this for different books
BOOK_CONFIG = {
    "title": "Zanger Ronald zingt de blues",
    "author": "Walter van den Berg",
    "isbn": "9789048853366",
}

# Crawler settings
CRAWLER_CONFIG = {
    # Delay between requests to same domain (seconds)
    # Set to 15s to respect libris.nl robots.txt crawl-delay
    "delay_between_requests": 15,

    # User-Agent header
    "user_agent": "BookstoreFinder/1.0 (contact: https://github.com/waltervandenberg/bookcrawler; Helping readers find independent bookstores)",

    # Request timeout (seconds)
    "request_timeout": 10,

    # Maximum retries for failed requests
    "max_retries": 2,

    # Respect robots.txt
    "respect_robots_txt": True,

    # Google search settings
    # Note: Google often shows consent pages, so direct crawling is more reliable
    "use_google_search": False,
    "google_delay": 5,  # Extra delay for Google to avoid rate limiting
}

# Search patterns for finding product pages
SEARCH_PATTERNS = {
    "dutch": [
        "{title}",
        "{title} {author}",
        "boek {title}",
        "ISBN {isbn}",
    ],
    "product_page_indicators": [
        "boek",
        "product",
        "artikel",
        "item",
        "/p/",
        "isbn",
    ],
}

# Postal code extraction patterns
POSTAL_CODE_CONFIG = {
    # Dutch postal code: 4 digits (1-9 first) + 2 letters (no F,I,O,Q,U,Y)
    "pattern": r"\b([1-9]\d{3})\s*([A-EGHJ-NPR-TV-Z]{2})\b",

    # Where to look for postal codes
    "search_locations": [
        "footer",
        "/contact",
        "/contacteer-ons",
        "/neem-contact-op",
        "/over-ons",
        "/vestigingen",
        "/winkels",
    ],

    # HTML elements that typically contain addresses
    "address_selectors": [
        "footer",
        ".footer",
        "#footer",
        ".contact",
        ".address",
        ".adres",
        "[itemtype*='PostalAddress']",
        "address",
    ],

    # Text patterns that indicate an address
    "address_indicators": [
        "adres:",
        "bezoekadres:",
        "winkeladres:",
        "vestiging:",
        "postbus:",
    ],
}

# Database and output settings
OUTPUT_CONFIG = {
    "database_path": "../data/bookstores.db",
    "json_output_path": "../data/bookstores.json",
    "log_file": "crawler.log",
}

# Logging settings
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
}
