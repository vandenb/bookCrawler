# Example config.py
# Dit bestand laat zien hoe configuratie eruit kan zien
# Claude Code zal de daadwerkelijke versie maken

"""
Configuration for Bookstore Finder Crawler
"""

# Book details (pas deze aan voor andere boeken)
BOOK_CONFIG = {
    "title": "Zanger Ronald zingt de blues",
    "author": "Walter van den Berg",
    "isbn": "9789025459284",  # Optioneel, helpt bij verificatie
    
    # Alternatieve zoektermen (voor als de exacte titel niet werkt)
    "search_variations": [
        "Zanger Ronald zingt de blues",
        "Ronald zingt de blues",
        "Walter van den Berg Ronald",
    ]
}

# Crawler settings
CRAWLER_CONFIG = {
    # Rate limiting
    "delay_between_requests": 2.5,  # Seconden tussen requests naar zelfde domein
    "delay_between_bookstores": 3.0,  # Seconden tussen verschillende bookstores
    
    # Timeouts
    "request_timeout": 10,  # Seconden voor HTTP requests
    "max_retries": 2,  # Aantal retry pogingen bij failures
    
    # User-Agent (pas aan met je eigen contact info!)
    "user_agent": "BookstoreFinder/1.0 (+https://jouwwebsite.nl/bot; jouw@email.nl)",
    
    # Google search settings
    "google_search_enabled": True,
    "google_max_results": 5,  # Hoeveel Google resultaten te checken
    
    # Crawling limits (safety)
    "max_pages_per_site": 10,  # Max aantal pagina's om te crawlen per boekhandel
    "max_depth": 2,  # Max crawl depth vanaf homepage
}

# Postal code extraction settings
EXTRACTION_CONFIG = {
    # Waar te zoeken voor postcode (in volgorde van prioriteit)
    "search_locations": [
        "footer",
        "contact_page",
        "about_page",
        "address_tags",
        "entire_page"  # Laatste fallback
    ],
    
    # URL patronen voor contact pagina's
    "contact_url_patterns": [
        r"/contact",
        r"/neem-contact-op",
        r"/contacteer-ons",
        r"/over-ons",
        r"/about",
        r"/locatie",
        r"/route",
        r"/adres"
    ],
    
    # Nederlandse postcode regex
    "postal_code_regex": r"\b[1-9][0-9]{3}\s?[A-Z]{2}\b",
    
    # Common false positives om te filteren
    "postal_code_blacklist": [
        "0000AA",  # Dummy codes
        "1234AB",  # Test codes
    ]
}

# Database settings
DATABASE_CONFIG = {
    "db_path": "data/bookstores.db",
    "create_if_missing": True,
}

# Output settings
OUTPUT_CONFIG = {
    "json_path": "data/bookstores.json",
    "json_indent": 2,
    "include_failed_searches": False,  # Include bookstores waar niets gevonden is
    "sort_by": "postal_code",  # of "name", "city"
}

# Logging settings
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "log_file": "crawler.log",
    "log_format": "%(asctime)s - %(levelname)s - %(message)s",
    "console_output": True,
}

# Feature flags (voor testen / debugging)
FEATURE_FLAGS = {
    "use_google_search": True,  # False om direct crawling te forceren
    "check_robots_txt": True,  # False om robots.txt te negeren (niet aanbevolen!)
    "verify_book_page": True,  # False om verificatie over te slaan
    "extract_additional_data": False,  # True om ook emails, telefoon, etc. te extracten
}
