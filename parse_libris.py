#!/usr/bin/env python3
"""
Parse libris-blz.txt and extract bookstore data to CSV format.
"""

import re
import csv
from pathlib import Path

def parse_libris_file(input_path: str, output_path: str):
    """
    Parse the libris-blz.txt file and write to CSV.

    The format is:
    LIBRIS-BOEKHANDEL or BLZ-BOEKHANDEL (header)
    Name
    Address
    Postal code City
    Phone
    Email (optional)
    URL
    """

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by headers
    # Pattern matches either LIBRIS-BOEKHANDEL or BLZ-BOEKHANDEL
    entries = re.split(r'(?:LIBRIS-BOEKHANDEL|BLZ-BOEKHANDEL)\n', content)

    bookstores = []

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        lines = [line.strip() for line in entry.split('\n') if line.strip()]

        if len(lines) < 4:
            print(f"Skipping incomplete entry: {lines}")
            continue

        # Parse the entry
        name = lines[0]

        # Find postal code line (format: 4 digits + space + 2 letters + space + city)
        postal_code = None
        city = None
        url = None

        for i, line in enumerate(lines):
            # Match Dutch postal code pattern (4 digits + 2 letters)
            postal_match = re.match(r'^(\d{4}\s*[A-Za-z]{2})\s+(.+)$', line)
            if postal_match:
                postal_code = postal_match.group(1).upper()
                # Normalize postal code format (add space if missing)
                if len(postal_code) == 6:
                    postal_code = postal_code[:4] + ' ' + postal_code[4:]
                city = postal_match.group(2)
            # Match Belgian postal code pattern (4 digits only)
            elif re.match(r'^(\d{4})\s+([A-Za-z].+)$', line):
                belgian_match = re.match(r'^(\d{4})\s+([A-Za-z].+)$', line)
                postal_code = belgian_match.group(1)
                city = belgian_match.group(2)

        # URL is typically the last line
        # It can start with www., libris.nl/, or end with .nl, .be, .com, .shop
        for line in reversed(lines):
            if re.match(r'^(?:www\.|libris\.nl|.*\.nl/?|.*\.be/?|.*\.com/?|.*\.shop/?)', line, re.IGNORECASE):
                url = line
                # Add https:// prefix if not present
                if not url.startswith('http'):
                    url = 'https://' + url
                break

        if name and postal_code and city and url:
            bookstores.append({
                'name': name,
                'url': url,
                'postal_code': postal_code,
                'city': city
            })
        else:
            print(f"Warning: Incomplete data for {name}: postal={postal_code}, city={city}, url={url}")

    # Write to CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'url', 'postal_code', 'city'])
        writer.writeheader()
        for store in bookstores:
            writer.writerow(store)

    print(f"Extracted {len(bookstores)} bookstores to {output_path}")
    return len(bookstores)


if __name__ == '__main__':
    input_file = 'libris-blz.txt'
    output_file = 'data/bookstores.csv'

    count = parse_libris_file(input_file, output_file)
    print(f"Done! {count} bookstores written to {output_file}")
