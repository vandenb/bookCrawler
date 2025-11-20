# Prompt voor Claude Code: Bookstore Finder Crawler (Fase 1)

## Opdracht
Bouw een Python-gebaseerde crawler die Nederlandse boekhandel-websites doorzoekt naar de verkooppagina van het boek "Zanger Ronald zingt de blues" van Walter van den Berg, en de locatiegegevens (postcode + plaatsnaam) van deze boekhandels extraheert.

## Belangrijkste Vereisten

### Input
- **CSV-bestand** (`data/bookstores.csv`) met minimaal deze kolommen:
  - `name`: naam van de boekhandel
  - `url`: homepage URL van de boekhandel
  - Optioneel: `category`, `notes`, etc.

Voorbeeld CSV:
```csv
name,url
Boekhandel Dominicanen,https://www.boekhandeldominicanen.nl
Athenaeum Boekhandel,https://www.athenaeum.nl
De Slegte,https://www.deslegte.com
```

### Zoekstrategie
1. **Primaire methode**: Google site-search
   - Query: `site:boekhandel.nl "Zanger Ronald zingt de blues"`
   - Parse Google resultaten om directe product page URL te vinden
   - BELANGRIJK: Check of Google dit toelaat (soms blokkeren ze automated searches)

2. **Fallback methode**: Direct crawlen
   - Als Google blokkeerd of geen resultaten geeft
   - Crawl homepage → zoek naar `/boeken/`, `/product/`, search-functie
   - Zoek naar pagina's die boektitel + auteur bevatten

### Data Extractie

**Van de product page:**
- Verificatie dat dit de juiste boekpagina is (check op titel + auteur)
- URL van de pagina (dit is de belangrijkste output!)

**Van de website (footer eerst, dan contact page):**
1. **Postcode** - Nederlands formaat:
   - 4 cijfers (eerste mag geen 0 zijn) + 2 letters (geen F, I, O, Q, U, Y)
   - Regex: `\b[1-9][0-9]{3}\s?[A-Z]{2}\b`
   - Normaliseer naar "1234AB" formaat (geen spaties voor database)

2. **Plaatsnaam**:
   - Meestal direct na of voor postcode
   - Vaak in `<address>` tags of class="address" elementen
   - Common patterns: "1234 AB Amsterdam", "Amsterdam, 1234 AB"

**Extractie-strategie:**
```
1. Zoek in footer (<footer>, class/id met "footer")
2. Als niet gevonden: zoek contact page (/contact, /over-ons, etc.)
3. Als niet gevonden: zoek in hele homepage
4. Laatste fallback: check <address> tags anywhere
```

### Output

**Twee formaten:**

1. **SQLite database** (`data/bookstores.db`)
   - Tabel `bookstores` met kolommen:
     - id (INTEGER PRIMARY KEY)
     - name (TEXT)
     - homepage_url (TEXT)
     - product_url (TEXT) - belangrijkste veld!
     - postal_code (TEXT)
     - city (TEXT)
     - search_method (TEXT) - "google" of "crawl"
     - found_at (TIMESTAMP)
     - last_updated (TIMESTAMP)
     - notes (TEXT) - voor errors/warnings

2. **JSON export** (`data/bookstores.json`)
   - Structuur zoals gespecificeerd in .clinerules
   - Alleen bookstores waar product_url gevonden is
   - Sorteer op postal_code voor efficiente frontend queries

### Ethisch Crawlen (VERPLICHT!)

**Implementeer deze safeguards:**
- robots.txt checker voor elk domein
- Rate limiting: 2-3 seconden tussen requests naar zelfde domein
- User-Agent: "BookstoreFinder/1.0 (+https://jouwwebsite.nl/bot; jouw@email.nl)"
- Timeout: max 10 seconden per request
- Max retries: 2 pogingen bij failures
- Error logging zonder crash

### Code Structuur

Maak een modulaire opzet:

```
crawler/
├── main.py                    # Entry point, orchestreert de crawl
├── config.py                  # Configuratie (boek details, settings)
├── models.py                  # Data models / database schema
├── google_search.py           # Google site-search implementatie
├── crawler.py                 # Direct crawl fallback methode
├── extractor.py               # Postcode & city extractie logic
├── database.py                # SQLite operations
├── utils.py                   # Helpers (rate limiting, robots.txt)
└── requirements.txt           # Dependencies
```

### Dependencies
Minimale set:
- requests
- beautifulsoup4
- lxml
- google (optioneel, als je een library gebruikt voor Google search)

### Gebruiksinstructies

De tool moet zo werken:
```bash
# Setup
cd crawler
python -m venv venv
source venv/bin/activate  # of `venv\Scripts\activate` op Windows
pip install -r requirements.txt

# Run
python main.py --input ../data/bookstores.csv --output ../data/bookstores.json

# Opties
python main.py --help
  --input CSV         Path naar input CSV met bookstore URLs
  --output JSON       Path voor output JSON file
  --db DATABASE       Path naar SQLite database (default: bookstores.db)
  --verbose          Extra logging
  --limit N          Test met eerste N bookstores
```

### Logging & Progress

Implementeer duidelijke output:
```
[14:30:01] Starting crawler voor "Zanger Ronald zingt de blues"
[14:30:01] Loaded 25 bookstores from CSV
[14:30:02] [1/25] Boekhandel Dominicanen...
[14:30:03]   ✓ Product page found via Google
[14:30:04]   ✓ Postal code: 6211HN, City: Maastricht
[14:30:05] [2/25] Athenaeum Boekhandel...
[14:30:06]   ✗ Product page not found
[14:30:07] [3/25] De Slegte...
[14:30:08]   ✓ Product page found via crawling
[14:30:09]   ✗ Postal code not found
...
[14:45:00] Completed! Results:
  - Bookstores processed: 25
  - Product pages found: 18 (72%)
  - Postal codes extracted: 15 (83% of found)
  - Saved to: bookstores.json
```

### Error Handling

Graceful degradation voor:
- Google blokkeert automated searches → fallback naar crawling
- Product page niet gevonden → log en skip
- Postcode niet gevonden → sla op met postal_code=NULL
- Contact page 404 → skip zonder crash
- Timeout/connection errors → log en continue

### Testing Checklist

Test met deze scenario's:
1. ✅ Boekhandel heeft het boek + duidelijke footer met postcode
2. ✅ Boekhandel heeft het boek + postcode alleen op contact page
3. ✅ Boekhandel heeft het boek NIET in assortiment
4. ✅ Moderne website met JavaScript-rendered content
5. ✅ Oude website met simpele HTML
6. ✅ robots.txt verbiedt crawling
7. ✅ Website is tijdelijk down (timeout)

###Voorbeeld Output JSON

```json
{
  "metadata": {
    "book_title": "Zanger Ronald zingt de blues",
    "author": "Walter van den Berg",
    "isbn": "9789025459284",
    "last_updated": "2024-11-16T14:30:00Z",
    "total_found": 18,
    "total_scanned": 25
  },
  "bookstores": [
    {
      "name": "Boekhandel Dominicanen",
      "product_url": "https://www.boekhandeldominicanen.nl/boek/zanger-ronald-zingt-de-blues-9789025459284",
      "postal_code": "6211HN",
      "city": "Maastricht",
      "search_method": "google",
      "crawled_at": "2024-11-16T14:30:04Z"
    },
    {
      "name": "De Slegte Amsterdam",
      "product_url": "https://www.deslegte.com/zanger-ronald-zingt-de-blues/",
      "postal_code": "1012AB",
      "city": "Amsterdam",
      "search_method": "crawl",
      "crawled_at": "2024-11-16T14:32:15Z"
    }
  ]
}
```

### Best Practices uit Onderzoek

Implementeer deze technieken uit het eerdere onderzoek:
- URL normalisatie met `urllib.parse.urljoin()` voor relatieve links
- BeautifulSoup met 'lxml' parser voor snelheid
- Postal code regex met word boundaries `\b` om false positives te voorkomen
- Per-domain rate limiting met `time.sleep()` en timestamp tracking
- robots.txt parsing met `urllib.robotparser.RobotFileParser`

### Volgende Stap (Fase 2)

Na succesvolle crawler-implementatie, bouw de JavaScript search widget die:
- De JSON inleest
- Fuzzy postal code matching doet (4 cijfers input → vind 1234XX en nabije codes)
- Resultaten toont met bookstore name, city, en link naar product page

## Vragen voor Verduidelijking

Als iets onduidelijk is tijdens implementatie:
1. Welk Google search mechanisme werkt het beste? (googlesearch-python library, requests naar google.nl, of iets anders?)
2. Hoe detecteren we of we de juiste boekpagina hebben? (alleen op titel? of ook ISBN check?)
3. Wat doen we met bookstores die meerdere locaties hebben?

## Start met Fase 1

Focus nu eerst op het bouwen van de crawler. Maak een robuuste, goed-gelogde implementatie die lokaal draait en handmatig gestart wordt. Simpel en betrouwbaar is belangrijker dan fancy features.
