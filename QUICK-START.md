# Quick Start Guide: Bookstore Finder met Claude Code

## Wat heb je gekregen?

Je hebt nu 3 bestanden:

1. **`.clinerules`** - Context-bestand voor Claude Code met alle projectinformatie
2. **`claude-code-prompt.md`** - Gedetailleerde prompt voor Fase 1 (de crawler)
3. **`bookstores-template.csv`** - Voorbeeld CSV met Nederlandse boekhandel URLs

## Hoe te gebruiken met Claude Code

### Stap 1: Project opzetten

```bash
# Maak een nieuwe project folder
mkdir bookstore-finder
cd bookstore-finder

# Maak de benodigde subfolders
mkdir crawler
mkdir data
mkdir frontend  # voor later (Fase 2)

# Kopieer de .clinerules naar de project root
cp /path/to/.clinerules ./

# Kopieer de template CSV naar data/
cp /path/to/bookstores-template.csv data/bookstores.csv
```

### Stap 2: CSV vullen met jouw boekhandels

Bewerk `data/bookstores.csv` en voeg je lijst van Nederlandse boekhandels toe:

```csv
name,url
Boekhandel A,https://www.boekhandela.nl
Boekhandel B,https://www.boekhandelb.nl
...
```

Tips voor het vinden van boekhandels:
- Bekende ketens: Bruna, Athenaeum, Paagman, Polare, etc.
- Lokale boekhandels in jouw regio
- Google Maps: zoek op "boekhandel" in verschillende steden
- Websites zoals boekhandels.nl hebben soms lijsten

### Stap 3: Claude Code starten

```bash
# Zorg dat je in de bookstore-finder folder bent
cd bookstore-finder

# Start Claude Code
claude-code
```

Claude Code zal automatisch de `.clinerules` inlezen en context hebben over je project.

### Stap 4: De prompt geven aan Claude Code

Open `claude-code-prompt.md` en kopieer de hele inhoud. Geef dit aan Claude Code met eventueel deze toevoeging:

```
Ik wil graag dat je Fase 1 van dit project bouwt: de Python crawler.

Lees het prompt-bestand en bouw:
1. De complete folder structuur (crawler/ met alle modules)
2. Alle Python bestanden volgens de specificaties
3. Een werkende implementatie die mijn CSV inleest
4. Requirements.txt met de juiste dependencies
5. Duidelijke logging zodat ik kan zien wat er gebeurt

Start met het bouwen van de core modules en test met een paar bookstores uit mijn CSV.

Belangrijk: 
- Hou het simpel en robuust
- Google search als primaire methode, crawlen als fallback
- Goede error handling (geen crashes bij problemen)
- Ethisch crawlen (robots.txt, rate limiting)
```

### Stap 5: Testen en itereren

Zodra Claude Code de eerste versie heeft gebouwd:

```bash
# Installeer dependencies
cd crawler
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Test met een kleine set (bijv. eerste 5 bookstores)
python main.py --input ../data/bookstores.csv --limit 5 --verbose

# Als dat werkt, run de volledige lijst
python main.py --input ../data/bookstores.csv --output ../data/bookstores.json
```

### Stap 6: Resultaten controleren

Check de outputs:
- `data/bookstores.db` - SQLite database met alle data
- `data/bookstores.json` - JSON voor de frontend
- `crawler.log` - Logbestand met details

Je kunt de database inspecteren met:
```bash
sqlite3 data/bookstores.db
sqlite> SELECT name, postal_code, city FROM bookstores WHERE product_url IS NOT NULL;
sqlite> .quit
```

## Veelvoorkomende Issues en Oplossingen

### Google blokkeert de searches
**Probleem:** Google detecteert automated queries en blokkeert je IP

**Oplossingen:**
1. Gebruik de fallback crawl-methode voor alle sites
2. Voeg langere delays toe tussen Google queries (5-10 sec)
3. Gebruik een Google Custom Search API key (betaald, maar betrouwbaar)
4. Vraag Claude Code om een CAPTCHA-solving strategie (mogelijk met browser automation)

### Postcode niet gevonden
**Probleem:** Website heeft wel het boek, maar geen zichtbare postcode

**Oplossingen:**
- Check of de boekhandel meerdere vestigingen heeft (vaak geen centrale postcode)
- Sommige online-only retailers hebben geen fysieke locatie
- Handmatig deze gevallen nakijken en CSV aanvullen met bekende data

### Product page niet gevonden
**Probleem:** Boekhandel heeft het boek waarschijnlijk, maar crawler vindt de pagina niet

**Mogelijke oorzaken:**
- Boek is uitverkocht/niet meer op voorraad
- Zoekfunctie werkt anders dan verwacht
- JavaScript-rendering (pagina laadt content dynamisch)

**Debug tips:**
- Run met `--verbose` om te zien wat de crawler doet
- Test handmatig: zoek zelf op de website naar het boek
- Vraag Claude Code om browser automation toe te voegen (Playwright) voor JS-heavy sites

### Rate limiting / IP geblokkeerd
**Probleem:** Website blokkeert je na te veel requests

**Oplossingen:**
- Verhoog de delay in `config.py` naar 5-10 seconden
- Run de crawler in batches met pauzes ertussen
- Vraag Claude Code om rotating proxies toe te voegen (advanced)

## Fase 2: Frontend Widget

Zodra Fase 1 werkt en je een goede `bookstores.json` hebt:

1. Host de JSON ergens:
   - GitHub Pages (gratis, makkelijk)
   - Je eigen webserver
   - CDN zoals jsdelivr

2. Vraag Claude Code om de frontend te bouwen:
```
Nu Fase 1 af is en ik een werkende bookstores.json heb, 
wil ik Fase 2: de JavaScript zoektool voor mijn website.

Bouw een eenvoudige widget die:
- De JSON inleest van [jouw-url]/bookstores.json
- Een invoerveld toont voor 4-cijferige postcode
- Fuzzy matching doet (zoekt nabije postcodes tot min. 1 resultaat)
- Een lijst toont met boekhandels (naam, stad, link naar product page)
- Werkt zonder build-stap (vanilla JS)
- Mobile-friendly is

Maak het als een standalone HTML+JS bestand dat ik op mijn site kan embedden.
```

## Tips voor Optimaal Gebruik Claude Code

1. **Iteratief werken**: Laat Claude Code eerst de basis bouwen, test het, en vraag dan om verbeteringen

2. **Specifiek zijn**: Als iets niet werkt, geef concrete voorbeelden:
   - "De crawler werkt niet voor boekhandelvandervelde.nl, kan je debuggen?"
   - "De postcode extractie mist postcodes in de footer, kan je de regex verbeteren?"

3. **Testen met kleine sets**: Gebruik `--limit 5` tijdens development om snel te itereren

4. **Logging is je vriend**: De `--verbose` flag helpt enorm bij debuggen

5. **Modular vragen stellen**: Vraag niet alles tegelijk, maar:
   - "Bouw eerst de Google search module"
   - "Nu de crawler module"
   - "Nu de extractor"
   - etc.

## Verwachte Timeline

**Week 1: Basis crawler**
- Claude Code bouwt de structuur
- Je test met 5-10 bookstores
- Finetunen van extractie-regels

**Week 2: Volledige crawl**
- Run op je complete CSV
- Fix edge cases
- Optimaliseer success rate

**Week 3: Frontend**
- Claude Code bouwt de zoektool
- Integreer op je website
- Testen met verschillende postcodes

**Week 4: Polish**
- Verbeteringen op basis van gebruik
- Documentatie
- Mogelijk automatisering voor maandelijkse runs

## Ondersteuning

Als je ergens vastloopt:
1. Check de logs in `crawler.log`
2. Test handmatig wat de crawler probeert te doen
3. Vraag Claude Code om specifieke debugging help
4. Pas de .clinerules aan als requirements veranderen

## Volgende Stappen

Start nu met:
1. ✅ Project folder aanmaken
2. ✅ CSV vullen met bookstore URLs
3. ✅ Claude Code starten met de prompt
4. ✅ Eerste test run met --limit 5

Succes! 📚
