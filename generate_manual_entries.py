#!/usr/bin/env python3
"""
Generate prefilled manual_entries.csv with all bookstores using the known URL pattern.
Also generates an HTML file with clickable links for manual verification.
"""

import csv
from pathlib import Path
from urllib.parse import urlparse

def generate_manual_entries(input_csv: str, output_csv: str, html_output: str):
    """
    Read bookstores.csv and generate:
    1. manual_entries.csv with prefilled URLs
    2. HTML file with clickable links
    """

    # URL pattern for the book
    url_pattern = "/a/walter-van-den-berg/zanger-ronald-zingt-de-blues/501634390"

    # Read bookstores
    bookstores = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bookstores.append(row)

    # Generate manual entries with constructed URLs
    entries = []
    for store in bookstores:
        # Use the full store URL as base (including path like /boekholtboekhandels)
        store_url = store['url']

        # Remove trailing slash if present
        base_url = store_url.rstrip('/')

        # Construct the product URL by appending the pattern
        product_url = base_url + url_pattern

        entries.append({
            'name': store['name'],
            'product_url': product_url,
            'postal_code': store['postal_code'],
            'city': store['city']
        })

    # Write to manual_entries.csv
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'product_url', 'postal_code', 'city'])
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)

    print(f"Generated {len(entries)} entries in {output_csv}")

    # Generate HTML file with clickable links
    html_content = """<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boekhandel URL Verificatie - Zanger Ronald zingt de blues</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        .info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .store {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .store-name {
            font-weight: bold;
            font-size: 1.1em;
            color: #1976d2;
        }
        .store-location {
            color: #666;
            font-size: 0.9em;
            margin: 5px 0;
        }
        .store-link {
            word-break: break-all;
        }
        .store-link a {
            color: #1976d2;
            text-decoration: none;
        }
        .store-link a:hover {
            text-decoration: underline;
        }
        .store-link a:visited {
            color: #7b1fa2;
        }
        .checkbox {
            margin-top: 8px;
        }
        .checkbox label {
            cursor: pointer;
            user-select: none;
        }
        .stats {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>
    <h1>Boekhandel URL Verificatie</h1>
    <div class="info">
        <strong>Boek:</strong> Zanger Ronald zingt de blues - Walter van den Berg<br>
        <strong>ISBN:</strong> 9789048853366<br>
        <strong>Aantal boekhandels:</strong> """ + str(len(entries)) + """<br><br>
        <em>Klik op elke link om te controleren of de pagina werkt. Vink af als de URL correct is.</em>
    </div>

    <div class="stats" id="stats">
        Gecontroleerd: <span id="checked-count">0</span> / """ + str(len(entries)) + """
    </div>

    <div id="stores">
"""

    for i, entry in enumerate(entries):
        html_content += f"""        <div class="store">
            <div class="store-name">{entry['name']}</div>
            <div class="store-location">{entry['postal_code']} {entry['city']}</div>
            <div class="store-link">
                <a href="{entry['product_url']}" target="_blank">{entry['product_url']}</a>
            </div>
            <div class="checkbox">
                <label>
                    <input type="checkbox" onchange="updateCount()"> URL werkt correct
                </label>
            </div>
        </div>
"""

    html_content += """    </div>

    <script>
        function updateCount() {
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            const checked = Array.from(checkboxes).filter(cb => cb.checked).length;
            document.getElementById('checked-count').textContent = checked;
        }
    </script>
</body>
</html>
"""

    with open(html_output, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated HTML verification page: {html_output}")


if __name__ == '__main__':
    input_file = 'data/bookstores.csv'
    output_file = 'data/manual_entries.csv'
    html_file = 'data/verify_urls.html'

    generate_manual_entries(input_file, output_file, html_file)
    print("\nDone! Open verify_urls.html in your browser to check the URLs.")
