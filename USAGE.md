# BookCrawler - Gebruiksaanwijzing

Deze tool helpt je om boekhandel-data te verzamelen voor "Zanger Ronald zingt de blues".

## Snelstart

### 1. Installatie

```bash
# Ga naar de crawler folder
cd crawler

# Maak een virtual environment aan
python3 -m venv venv

# Activeer de virtual environment
source venv/bin/activate

# Installeer dependencies
pip install -r requirements.txt
```

### 2. Eerste test (aanbevolen!)

Test de crawler eerst met een paar boekhandels:

```bash
# Test met de eerste 3 boekhandels
python main.py --input ../data/bookstores.csv --limit 3 --verbose
```

Dit laat je zien:
- Of de crawler werkt
- Welke boekhandels succesvol zijn
- Waar eventuele problemen zitten

### 3. Volledige run

Als de test goed gaat, draai dan de volledige lijst:

```bash
# Draai alle boekhandels
python main.py --input ../data/bookstores.csv --output ../data/bookstores.json
```

Dit kan 30-60 minuten duren voor 50 boekhandels (vanwege rate limiting).

### 4. Bekijk resultaten

```bash
# Bekijk statistieken
python main.py --input ../data/bookstores.csv --stats-only

# Bekijk de JSON output
cat ../data/bookstores.json | python3 -m json.tool | head -50
```

## Belangrijke opties

```bash
# Alleen statistieken tonen (geen crawl)
python main.py --input ../data/bookstores.csv --stats-only

# Limiteer aantal boekhandels (handig voor testen)
python main.py --input ../data/bookstores.csv --limit 5

# Verbose output (toont alle details)
python main.py --input ../data/bookstores.csv --verbose

# Custom output locatie
python main.py --input ../data/bookstores.csv --output /pad/naar/output.json

# Robots.txt negeren (niet aanbevolen!)
python main.py --input ../data/bookstores.csv --no-robots
```

## Je eigen boekhandels toevoegen

Bewerk [data/bookstores.csv](data/bookstores.csv):

```csv
name,url
Mijn Favoriete Boekhandel,https://www.voorbeeld.nl
Nog een Boekhandel,https://www.andervoorbeeld.nl
```

Formaat:
- **name**: Naam van de boekhandel
- **url**: Homepage URL (moet beginnen met `https://` of `http://`)

## Configuratie aanpassen

Bewerk [crawler/config.py](crawler/config.py) als je:

- Een ander boek wilt zoeken (verander `BOOK_CONFIG`)
- Rate limiting wilt aanpassen (verander `delay_between_requests`)
- User-Agent wilt wijzigen (verander `user_agent`)

Voorbeeld:

```python
BOOK_CONFIG = {
    "title": "Jouw Boektitel",
    "author": "Jouw Naam",
    "isbn": "9789012345678",
}
```

## Veelgestelde vragen

### De crawler vindt weinig postcodes

Dat is normaal. Veel boekhandels hebben hun adresgegevens niet (goed) op hun website staan, of gebruiken JavaScript. Een success rate van 60-70% is acceptabel.

**Oplossing**: Postcodes handmatig opzoeken en toevoegen aan de database.

### Sommige websites geven 403 Forbidden

Sommige websites hebben anti-bot bescherming (zoals Athenaeum). Dit is lastig te omzeilen zonder complexe tools.

**Oplossing**: Deze boekhandels overslaan, of handmatig de productpagina opzoeken.

### De crawler is erg traag

Dat is bewust! We respecteren websites met:
- 2.5 seconden tussen requests naar dezelfde website
- 5 seconden tussen verschillende boekhandels
- Robots.txt checking

**Dit is ethisch en netjes**. Maak het niet sneller.

### Google search werkt niet

Google geeft vaak "consent" pagina's in plaats van zoekresultaten. Daarom hebben we Google search standaard uitgezet en gebruiken we direct crawling.

**Dit is normaal** en werkt prima.

### SSL certificate errors

Op Mac kan dit voorkomen. We hebben SSL verificatie uitgezet voor development, maar dit is niet ideaal voor productie.

**Workaround**: De code heeft `verify=False` in requests, wat werkt maar niet veilig is.

## Output formaat

De crawler maakt twee bestanden:

### 1. SQLite Database ([data/bookstores.db](data/bookstores.db))

Lokale opslag van alle data, inclusief failed attempts. Handig voor debugging.

### 2. JSON export ([data/bookstores.json](data/bookstores.json))

Voor je website. Formaat:

```json
{
  "metadata": {
    "book_title": "Zanger Ronald zingt de blues",
    "book_author": "Walter van den Berg",
    "book_isbn": "9789048853366",
    "last_updated": "2025-11-16T14:30:00",
    "total_bookstores": 30
  },
  "bookstores": [
    {
      "name": "Boekhandel Voorbeeld",
      "product_url": "https://example.com/boek/...",
      "postal_code": "1234 AB",
      "city": "Amsterdam",
      "crawled_at": "2025-11-16T14:25:00"
    }
  ]
}
```

## Logs

Alle activiteit wordt gelogd naar [crawler/crawler.log](crawler/crawler.log).

```bash
# Bekijk laatste 50 regels
tail -50 crawler/crawler.log

# Volg logs real-time
tail -f crawler/crawler.log
```

## Problemen oplossen

### "ModuleNotFoundError: No module named 'requests'"

Je virtual environment is niet geactiveerd.

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "FileNotFoundError: ../data/bookstores.csv"

Je zit niet in de juiste folder.

```bash
cd crawler
python main.py --input ../data/bookstores.csv
```

### Crawler crasht

Check de logs:

```bash
tail -100 crawler.log
```

Start opnieuw met verbose mode:

```bash
python main.py --input ../data/bookstores.csv --limit 1 --verbose
```

## Volgende stap: Fase 2 (Frontend widget)

Als je tevreden bent met de data, ga dan naar Fase 2: de zoekwidget voor je website.

Zie [README.md](README.md) voor meer informatie.

## Hulp nodig?

- Check [README.md](README.md) voor project overzicht
- Bekijk [QUICK-START.md](QUICK-START.md) voor gedetailleerde instructies
- Kijk in [crawler.log](crawler/crawler.log) voor error details

---

**Veel succes met het promoten van je boek!** 📚
