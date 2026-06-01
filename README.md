# Gap Intelligence Suite

> Zelfgebouwde SEO concurrentie-analyse tool die doet wat Ahrefs en SEMrush doen — maar dan specifiek gericht op jouw eigen data.

## Wat doet het?

Gap Intelligence crawlt concurrentpagina's, vergelijkt die met je eigen Google Search Console data en detecteert automatisch waar kansen liggen. Het werkt twee kanten op: je ziet waar concurrenten beter zichtbaar zijn dan jij én waar jij juist een voorsprong hebt waar je op moet letten.

De output is direct bruikbaar: kant-en-klare content briefs op basis van gedetecteerde gaps, prioriteitslijsten en een overzicht per concurrent.

**Geen Ahrefs. Geen SEMrush. Geen maandelijkse abonnementskosten.**

---

## Resultaten in de praktijk

- Concurrent had sterke pagina's rondom badkamers gedetecteerd via de gap analysis
- Direct gereageerd met meerdere nieuwe pagina's over schilderen, kitten en badkamerafwerking
- Gaps worden gesorteerd op prioriteit zodat het meest waardevolle werk altijd bovenaan staat
- Tweerichtingsanalyse: niet alleen gaps vinden maar ook eigen sterktes bewaken

---

## Architectuur

```
gap-intelligence-suite/
├── config_gaps.py              # Configuratie: eigen domein, concurrenten, GSC credentials
├── fetch_fov_urls.py           # Haalt eigen URLs op via Google Search Console API
├── competitor_crawler.py       # Crawlt concurrentpagina's met Playwright
├── gap_detector.py             # Vergelijkt eigen data met concurrentdata
├── gsc_gap_detector.py         # GSC-specifieke gap detectie op zoekwoord niveau
├── gap_intelligence.py         # Main orchestrator: draait de volledige pipeline
├── run_gap_analysis_v3.py      # Alternatieve runner met sitemap integratie
├── brief_generator.py          # Genereert content briefs op basis van gaps
├── fov_brief_generator.py      # Content Brief Generator v2.0 met AI integratie
├── fov_artikel_generator.py    # Genereert volledige artikel outlines
└── test_sitemaps.py            # Debug tool voor sitemap validatie
```

---

## Hoe werkt het?

### Stap 1 — Eigen data ophalen
De tool haalt via de Google Search Console API alle URLs, zoekwoorden en prestaties op voor jouw domein.

### Stap 2 — Concurrenten crawlen
Via Playwright worden concurrentpagina's gecrawld. De tool haalt pagina-structuur, koppen en zoekwoorddichtheid op.

### Stap 3 — Gap detectie
De gap detector vergelijkt beide datasets:
- Welke onderwerpen/zoekwoorden heeft de concurrent die jij niet hebt?
- Waar scoort de concurrent beter op dezelfde zoekwoorden?
- Waar heb jij een voorsprong die de concurrent kan inlopen?

### Stap 4 — Prioriteren
Gaps worden gesorteerd op potentieel zoekvolume en concurrentieverschil. De grootste kansen komen bovenaan.

### Stap 5 — Content briefs genereren
Op basis van de top-gaps genereert de tool direct bruikbare content briefs met suggested structure, zoekwoorden en aanpak.

---

## Installatie

```bash
git clone https://github.com/bastiaanvdh/gap-intelligence-suite
cd gap-intelligence-suite
pip install -r requirements.txt
```

Vereiste packages:
```
playwright
beautifulsoup4
google-auth
google-api-python-client
pandas
openai
```

---

## Configuratie

Kopieer `config_gaps_example.py` naar `config_gaps.py` en vul in:

```python
# Jouw domein
OWN_DOMAIN = "https://jouwdomein.nl"

# Google Search Console property
GSC_PROPERTY = "sc-domain:jouwdomein.nl"

# Pad naar GSC credentials JSON
CREDENTIALS_PATH = "credentials/gsc_credentials.json"

# Concurrenten om te analyseren
COMPETITORS = [
    "https://concurrent1.nl",
    "https://concurrent2.nl",
]

# OpenAI API key (voor brief generatie)
OPENAI_API_KEY = "sk-..."
```

---

## Gebruik

```bash
# Volledige pipeline draaien
python gap_intelligence.py

# Alleen gap detectie
python gap_detector.py

# Content briefs genereren op basis van bestaande gap analyse
python brief_generator.py

# Debug sitemaps
python test_sitemaps.py
```

---

## Output

De tool genereert:
- `gaps_report.xlsx` — volledig overzicht van alle gedetecteerde gaps met prioriteitsscore
- `competitor_analysis.xlsx` — per concurrent een breakdown van hun sterke pagina's
- `content_briefs/` — map met per gap een kant-en-klare content brief

---

## Tech stack

| Tool | Waarvoor |
|---|---|
| Python | Core taal |
| Playwright | Headless browser voor concurrent crawling |
| BeautifulSoup | HTML parsing |
| Google Search Console API | Eigen zoekwoorddata |
| Google Analytics API | Traffic data |
| scikit-learn | ML-componenten voor gap scoring |
| OpenAI API | Content brief generatie |
| Pandas | Data verwerking en export |

---

## Gebouwd door

Bastiaan van der Horst — [LinkedIn](https://www.linkedin.com/in/bastiaan-v-01846112a) · [Portfolio](https://bastiaanvdh.github.io/portfolio)
