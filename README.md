# BookCrawler - Boekhandel Finder

Een tool die lezers helpt om lokale boekhandels te vinden waar ze "Zanger Ronald zingt de blues" van Walter van den Berg kunnen kopen, in plaats van standaard naar bol.com te gaan.

**Status**: De widget is live! 223 geverifieerde boekhandels beschikbaar.

## 🎯 Doel

- Bezoekers van je website naar onafhankelijke boekhandels leiden
- Goodwill opbouwen bij boekhandelaren (belangrijk voor fysieke placement)
- Een gebruiksvriendelijke tool bieden die lokale aankoopopties toont

## 📦 Wat zit er in dit project?

Het project bestaat uit twee hoofdcomponenten:

### Fase 1: Data Verzameling ✅
- Parsing van libris-blz.txt (236 boekhandels)
- Automatische URL generatie met bekende patronen
- HTML verificatie tool voor handmatige controle
- Finale dataset: 223 geverifieerde boekhandels

### Fase 2: JavaScript Zoekwidget ✅
Een frontend widget die:
- Bezoekers hun postcode laat invoeren (4 cijfers)
- De dichtstbijzijnde boekhandels toont (op absolute numerieke afstand)
- Directe links geeft naar de productpagina
- Zowel standalone als embeddable versie

## 🚀 Quick Start

### Optie 1: Widget gebruiken (meest waarschijnlijk wat je wilt)

**Standalone pagina:**
Open `widget/bookstore-finder.html` in je browser.

**Embedden op je website:**
```html
<div id="bookstore-widget"></div>
<script src="/widget/bookstore-finder-embed.js"></script>
<script>
    BookstoreFinder.init({
        container: '#bookstore-widget',
        dataUrl: '/data/bookstores.json'
    });
</script>
```

Upload naar je server:
- `/data/bookstores.json`
- `/widget/bookstore-finder-embed.js`

### Optie 2: Data regenereren (als je de data wilt updaten)

```bash
# 1. Parse libris-blz.txt
python3 parse_libris.py

# 2. Genereer URL patterns en HTML verificatie
python3 generate_manual_entries.py

# 3. Open verify_urls.html en controleer alle links handmatig

# 4. Genereer JSON
python3 generate_json.py
```

## 📊 Data Flow

```
libris-blz.txt              Scripts                   Output
┌─────────────┐            ┌──────────────┐          ┌─────────────┐
│ 236 stores  │  ──────>   │ parse_libris │  ──────> │ bookstores  │
│ (raw text)  │            │              │          │ .csv        │
└─────────────┘            └──────────────┘          └─────────────┘
                                  │                         │
                                  v                         v
                           ┌──────────────┐          ┌─────────────┐
                           │ generate_    │  ──────> │ manual_     │
                           │ manual_      │          │ entries.csv │
                           │ entries      │          │ + HTML      │
                           └──────────────┘          └─────────────┘
                                                            │
                              Handmatige verificatie <──────┘
                                                            │
                                                            v
                                                     ┌─────────────┐
                                                     │ 223 verified│
                                                     │ stores      │
                                                     └─────────────┘
                                                            │
                                                            v
                           ┌──────────────┐          ┌─────────────┐
                           │ generate_    │  ──────> │ bookstores  │
                           │ json         │          │ .json       │
                           └──────────────┘          └─────────────┘
                                                            │
                                                            v
                                                     ┌─────────────┐
                                                     │   Widget    │
                                                     │  (browser)  │
                                                     └─────────────┘
```

## 🔧 Configuratie

Alle instellingen zitten in `crawler/config.py`:

```python
BOOK_CONFIG = {
    "title": "Zanger Ronald zingt de blues",
    "author": "Walter van den Berg",
    "isbn": "9789025459284"
}

CRAWLER_CONFIG = {
    "delay_between_requests": 2.5,
    "user_agent": "BookstoreFinder/1.0 (+je-website.nl)",
    # ... meer settings
}
```

Zie `example-config.py` voor alle opties.

## 📁 Project Structuur

```
BookCrawler/
├── README.md                        # Dit bestand
├── .gitignore                       # Git ignore regels
│
├── crawler/                         # Crawler code (niet gebruikt, maar bewaard)
│   ├── config.py                    # Configuratie
│   ├── google_search.py             # Google search functionaliteit
│   └── utils.py                     # Utility functies
│
├── data/                            # Data folder
│   ├── libris-blz.txt               # Input: originele lijst
│   ├── bookstores.csv               # Parsed data (236 stores)
│   ├── manual_entries.csv           # Handmatig geverifieerd (223 stores)
│   ├── bookstores.json              # Finale JSON voor widget ⭐
│   └── verify_urls.html             # HTML verificatie tool
│
├── widget/                          # JavaScript widget
│   ├── bookstore-finder.html        # Standalone pagina
│   ├── bookstore-finder-embed.js    # Embeddable versie ⭐
│   └── embed-example.html           # Voorbeeld
│
├── parse_libris.py                  # Script 1: Parse libris-blz.txt
├── generate_manual_entries.py       # Script 2: Genereer URLs + HTML
├── generate_json.py                 # Script 3: CSV → JSON
└── carwlindex.php                   # Je website met geïntegreerde widget
```

⭐ = Belangrijkste bestanden voor productie gebruik

## 🎯 Success Criteria

### Crawler slaagt als:
- ✅ Vindt productpagina's voor 60%+ van input bookstores
- ✅ Extraheert postcodes voor 80%+ van gevonden pagina's
- ✅ Draait zonder crashes bij diverse website-structuren
- ✅ Produceert valide JSON voor frontend

### Frontend slaagt als:
- ✅ Geeft resultaten voor meeste 4-cijferige postcode inputs
- ✅ Toont minimaal 1 boekhandel voor grote steden
- ✅ Degradeert gracefully bij geen resultaten
- ✅ Werkt snel en op mobile devices

## 🛡️ Ethisch Crawlen

De crawler respecteert het web door:
- ✅ robots.txt te checken en respecteren
- ✅ Rate limiting (2-3 sec tussen requests)
- ✅ Duidelijke User-Agent met contactinfo
- ✅ Graceful error handling (geen eindloze retries)
- ✅ Logging van alle activiteit

## 🐛 Troubleshooting

### Google blokkeert automated searches
**Oplossing:** Gebruik de fallback crawl-methode, of voeg langere delays toe (5-10 sec)

### Postcode niet gevonden
**Oorzaken:** 
- Boekhandel heeft meerdere vestigingen (geen centrale postcode)
- Online-only retailer zonder fysieke locatie
**Oplossing:** Handmatig controleren en CSV aanvullen

### Product page niet gevonden
**Oorzaken:**
- Boek tijdelijk uitverkocht
- JavaScript-rendered content (crawler ziet het niet)
**Oplossing:** Run met `--verbose` om te debuggen, overweeg browser automation

Zie QUICK-START.md sectie "Veelvoorkomende Issues" voor meer.

## 📖 Gebruik

### Basis gebruik
```bash
python main.py --input ../data/bookstores.csv
```

### Met opties
```bash
python main.py \
  --input ../data/bookstores.csv \
  --output ../data/bookstores.json \
  --db ../data/bookstores.db \
  --verbose \
  --limit 10
```

### Help
```bash
python main.py --help
```

## 📈 Uitbreidingsmogelijkheden

Toekomstige features (niet in initiële build):
- Automatische maandelijkse runs via cron
- Email notificaties bij nieuwe boekhandels
- Voorraad-beschikbaarheid checking
- Prijsvergelijking
- Admin dashboard voor bookstore management

## 🤝 Voor Boekhandelaren

Als je een boekhandelaar bent en wilt dat je winkel in deze tool verschijnt:
1. Zorg dat "Zanger Ronald zingt de blues" in je online assortiment staat
2. Zet duidelijke contactgegevens (met postcode) in je website footer
3. Contact de auteur via [je-email@adres.nl]

## 🔍 Hoe de widget werkt

**Sorteerlogica:**
De widget sorteert boekhandels op absolute numerieke afstand van de ingevoerde postcode.

Bijvoorbeeld voor postcode **5041**:
- Gianotten (5038) = afstand 3
- Een winkel in 5044 = afstand 3
- Buitelaar (5051) = afstand 10

Dus 5038 en 5044 zijn beide even "dichtbij" en komen voor 5051.

**Technisch:**
```javascript
const diff = Math.abs(userPostcode - storePostcode);
// Sorteer op diff, dan alfabetisch op stad
```

## 📝 Licentie

© 2025 Walter van den Berg

Dit project is gebouwd voor persoonlijk gebruik voor het promoten van "Zanger Ronald zingt de blues".

## ✉️ Contact

- Website: [waltervandenberg.nl](https://waltervandenberg.nl)
- Email: walter@vandenb.com

---

**Built with ❤️ and Claude Code**
