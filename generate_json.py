#!/usr/bin/env python3
"""
Generate bookstores.json from the verified manual_entries.csv
"""

import csv
import json
from pathlib import Path

def generate_json(input_csv: str, output_json: str):
    """
    Read manual_entries.csv and generate bookstores.json
    """

    bookstores = []

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bookstores.append({
                'name': row['name'],
                'product_url': row['product_url'],
                'postal_code': row['postal_code'],
                'city': row['city']
            })

    # Write to JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(bookstores, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(bookstores)} bookstores in {output_json}")


if __name__ == '__main__':
    input_file = 'data/manual_entries.csv'
    output_file = 'data/bookstores.json'

    generate_json(input_file, output_file)
    print(f"\nDone! JSON file created at {output_file}")
