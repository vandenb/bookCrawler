# Boekhandel Finder

Een postcode-gebaseerde zoektool die lezers helpt lokale boekhandels te vinden waar ze "Zanger Ronald zingt de blues" kunnen kopen.

**Status**: Live met 223 geverifieerde boekhandels in Nederland.

## 🎯 Over dit project

**Eerlijk verhaal**: Dit heet "BookCrawler" maar is geen traditionele web crawler geworden. In plaats daarvan is het een **semi-geautomatiseerde data collection tool** met veel handmatige verificatie.

**Waarom geen echte crawler?**
- Google Search geblokkeerd door Cloudflare (403 Forbidden)
- Direct crawling te complex door verschillende website-structuren
- Robots.txt delays (15s) maakten het onpraktisch traag

**Wat werkte wel:**
- Nederlandse boekhandels gebruiken Libris/BLZ platform met **één URL-patroon**
- Pattern matching + handmatige verificatie = 223 werkende links
- Pragmatische aanpak: "fuck it, we doen het handmatig met slimme tooling"

## 📦 Wat dit project biedt

### 1. Data Collection Tools ✅
- Parser voor Libris bookstore lijst
- URL generator met bekende patronen
- HTML verificatie tool voor handmatige controle
- Workflow die **echt werkt** (90% handwerk, 10% automation)

### 2. JavaScript Zoekwidget ✅
Fully functional widget:
- Postcode search (eerste 4 cijfers)
- Absolute numerieke afstand berekening
- Direct links naar product pagina's
- Standalone + embeddable versies

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

### Optie 2: Eigen dataset maken (voor een ander boek)

**Realistisch tijdsinvestering**: 2-4 uur werk, afhankelijk van aantal winkels.

```bash
# 1. Parse libris-blz.txt (of andere source)
python3 parse_libris.py

# 2. Genereer URL patterns
# PAS AAN: url_pattern in generate_manual_entries.py met jouw boek
python3 generate_manual_entries.py

# 3. HANDMATIG: Open data/verify_urls.html
#    Klik alle 200+ links, corrigeer fouten in manual_entries.csv
#    Dit is het echte werk - plan hier 1-2 uur voor in

# 4. Genereer JSON voor widget
python3 generate_json.py
```

**Pro tip**: Als je boek NIET op Libris/BLZ staat, moet je een eigen lijst maken. Automatisch crawlen werkt waarschijnlijk niet (zie boven waarom).

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

## 📁 Project Structuur

```
BookCrawler/
├── README.md                        # Dit bestand
├── .gitignore
│
├── data/                            # Data folder
│   ├── libris-blz.txt               # Input: originele lijst van Libris
│   ├── bookstores.csv               # Parsed (236 stores)
│   ├── manual_entries.csv           # ✓ Handmatig geverifieerd (223)
│   ├── bookstores.json              # ⭐ Finale data voor widget
│   └── verify_urls.html             # Verificatie tool (zelf genereren)
│
├── widget/                          # ⭐ JavaScript widget (production ready)
│   ├── bookstore-finder.html        # Standalone pagina
│   ├── bookstore-finder-embed.js    # Embeddable versie
│   └── embed-example.html           # Gebruik voorbeeld
│
├── parse_libris.py                  # Script 1: Parse input
├── generate_manual_entries.py       # Script 2: URLs + HTML tool
├── generate_json.py                 # Script 3: CSV → JSON
│
└── crawler/                         # Legacy crawler code
    └── ...                          # (niet nodig voor deze workflow)
```

**Wat je écht nodig hebt voor een nieuw boek:**
1. Een lijst met boekhandel URLs (zoals libris-blz.txt)
2. Het URL-patroon van je boek (bijv. `/a/auteur/titel/id`)
3. 2-4 uur tijd voor handmatige verificatie
4. De drie Python scripts (parse, generate, convert)

## ⚙️ Aanpassen voor jouw boek

**In `generate_manual_entries.py` (regel 19):**
```python
# Pas dit aan naar jouw boek URL
url_pattern = "/a/walter-van-den-berg/zanger-ronald-zingt-de-blues/501634390"
```

Hoe vind je dit patroon?
1. Zoek je boek op een Libris boekhandel (bijv. athenaeum.nl)
2. Kopieer het URL gedeelte NA de domeinnaam
3. Test op 2-3 andere Libris winkels of het werkt

## 💡 Wat ik geleerd heb

**Voor toekomstige gebruikers van dit project:**

1. **Web crawling is moeilijk in 2024**
   - Bot detection is overal (Cloudflare, reCAPTCHA)
   - Robots.txt delays maken het traag
   - JavaScript-rendered content is lastig zonder browser automation

2. **Pattern matching werkt beter dan je denkt**
   - Als je domein één platform gebruikt (zoals Libris), zoek het patroon
   - Test het patroon op 5-10 sites
   - Genereer URLs en verifieer handmatig

3. **Handmatig werk is OK**
   - 2 uur handmatige verificatie vs 20 uur crawler debuggen
   - Je krijgt 100% accurate data
   - Je leert de uitzonderingen kennen

4. **Tooling > Automation**
   - Een HTML verificatie pagina met checkboxes = goud waard
   - CSV editing is snel en overzichtelijk
   - Python scripts voor repetitieve taken

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
