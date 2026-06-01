# GAP INTELLIGENCE SUITE v1.0

**DIY Competitor Analysis Tool voor DemoShop.example**  
*Geen Ahrefs/SEMrush nodig!*

---

## 📋 WAT DOET HET?

Gap Intelligence crawlt je concurrenten, detecteert content gaps, en genereert kant-en-klare content briefs.

### Features:
- ✅ **Competitor Crawling** → Extract alle pages van CompetitorA, Competitor B, etc.
- ✅ **Gap Detection** → Vind content die concurrent heeft maar DEMO niet
- ✅ **Auto Brief Generator** → Genereer actionable briefs met H2 structuur, meta tags, etc.
- ✅ **Priority Scoring** → Rank gaps op ROI potential
- ✅ **GPT-4 Integration** → Optioneel voor betere briefs

---

## 🚀 QUICK START

### 1. Installatie

```bash
cd "C:\Path\To\Projects"
mkdir "Gap Intelligence"
cd "Gap Intelligence"

# Plaats alle .py files hier
# - config_gaps.py
# - competitor_crawler.py
# - gap_detector.py
# - brief_generator.py
# - gap_intelligence.py

# Installeer dependencies
pip install requests beautifulsoup4 openai --break-system-packages
```

### 2. Configuratie

Open `config_gaps.py` en check:

```python
# Concurrenten (edit indien nodig)
COMPETITORS = {
    'CompetitorA': {
        'name': 'Competitor A',
        'domain': 'competitor-a.example',
        'sitemap_url': 'https://www.competitor-a.example/sitemap.xml',
        'priority': 1
    },
    # Add more competitors...
}

# OpenAI (optioneel, voor betere briefs)
# Set environment variable:
# os.environ['OPENAI_API_KEY'] = 'sk-...'
```

### 3. Run!

```bash
# Full workflow (eerste keer)
python gap_intelligence.py

# Of stap voor stap:
python gap_intelligence.py crawl   # ~5-10 min
python gap_intelligence.py detect  # ~1 min
python gap_intelligence.py brief   # ~2-3 min
```

---

## 📁 OUTPUT

### Na de run vind je:

```
Gap Intelligence/
├── data/
│   ├── competitors.json         # Crawled data
│   ├── demo_sitemap.json        # DEMO sitemap
│   └── gaps_detected.json      # Gap analysis
│
├── output/
│   ├── content_briefs/          # 📄 BRIEFS HIER!
│   │   ├── 001_epoxy_coating_vergelijking.md
│   │   ├── 001_epoxy_coating_vergelijking.json
│   │   ├── 002_2k_lakken_gids.md
│   │   └── ...
│   │
│   ├── gap_report.csv          # Excel export
│   └── gap_dashboard_data.json # Voor dashboard
│
└── logs/
    └── gap_intelligence.log    # Log file
```

---

## 📄 CONTENT BRIEF FORMAT

Elke brief bevat:

```markdown
# CONTENT BRIEF: 2K Lakken Vergelijking

## 🎯 WAAROM DEZE CONTENT?
- Concurrent: CompetitorA.nl
- Priority Score: 87.5/100
- Content Type: comparison

## 📝 CONTENT SPECIFICATIES
### H1
2K Lakken Vergelijking - Complete Gids 2026

### H2 Structuur
1. Wat zijn 2K lakken?
2. Voordelen van 2K lakken
3. Top 5 merken vergelijking
4. Toepassingen per oppervlak
5. Verwerkingstips

### Target Metrics
- Woordenaantal: 1400+ woorden
- Aantal H2s: 5+
- Afbeeldingen: 2-3+

## 🔍 SEO OPTIMALISATIE
Meta Title: 2K Lakken Vergelijking | Beste Merken 2026
Meta Description: Vergelijk 2K lakken merken en kies...

## 🔗 INTERNAL LINKING
Link naar:
1. /sika-2k-epoxy-coating
2. /international-schooner-gold
3. /lakken-categorie

## ✅ ACTION ITEMS
- [ ] Schrijf content van 1400+ woorden
- [ ] Gebruik H2 structuur zoals voorgesteld
- [ ] Voeg 2-3 afbeeldingen toe
- [ ] Link naar 3 gerelateerde DEMO pagina's
- [ ] Optimaliseer meta tags
- [ ] Upload naar CMS
```

---

## ⚙️ CONFIGURATIE OPTIES

### Concurrenten toevoegen

```python
# In config_gaps.py
COMPETITORS['NIEUW'] = {
    'name': 'Nieuwe Concurrent',
    'domain': 'concurrent.nl',
    'sitemap_url': 'https://concurrent.nl/sitemap.xml',
    'priority': 2  # 1 = hoogste prioriteit
}
```

### Blacklist termen

```python
# Filter irrelevante content
BLACKLIST_TERMS = [
    'gaming', 'consumer brand', 'irrelevant topic'
]
```

### Gap detection thresholds

```python
GAP_CONFIG = {
    'similarity_threshold': 0.8,  # 0-1, hoger = strenger
    'min_search_volume': 50,
}
```

### Brief generator settings

```python
BRIEF_CONFIG = {
    'use_gpt': True,  # Set False als geen OpenAI key
    'auto_generate_for_top_n': 20,  # Aantal briefs
    'target_word_count_multiplier': 1.1  # 10% langer dan concurrent
}
```

---

## 🔄 WEEKLY WORKFLOW

### Maandag ochtend (30 min):

```bash
# 1. Run gap detection (updates elke week)
python gap_intelligence.py

# 2. Review top 5 briefs
cd output/content_briefs
# Open 001_*.md, 002_*.md, etc.

# 3. Kies top 3 voor deze week
# 4. Assign aan team / jezelf
```

### Rest van de week:

```bash
# Content maken op basis van briefs
# Check action items in elke brief
```

---

## 🐛 TROUBLESHOOTING

### "Competitor data niet gevonden"

```bash
# Run eerst crawl step
python gap_intelligence.py crawl
```

### "Gaps file niet gevonden"

```bash
# Run detect step
python gap_intelligence.py detect
```

### "OpenAI API error"

```bash
# Disable GPT in config
# In config_gaps.py:
BRIEF_CONFIG['use_gpt'] = False
```

### Crawling duurt te lang

```python
# In config_gaps.py, verlaag:
CRAWLER_CONFIG['max_pages_per_site'] = 1000  # Was: 5000
```

### Te veel gaps gevonden

```python
# Verhoog similarity threshold
GAP_CONFIG['similarity_threshold'] = 0.9  # Was: 0.8

# Of verhoog min volume
GAP_CONFIG['min_search_volume'] = 100  # Was: 50
```

---

## 📊 PERFORMANCE

**Tijden (schatting):**
- Crawl: 5-10 min (3 concurrenten, ~300 pages each)
- Detect: 1-2 min
- Brief: 2-3 min (20 briefs)
- **Totaal: ~10-15 min**

**Output:**
- ~20-50 gaps gevonden (typisch)
- Top 20 briefs gegenereerd
- Ready to execute

---

## 🔮 VOLGENDE STAPPEN (Future)

### Optionele uitbreidingen:

1. **Dashboard Integration**
   - Voeg "Gap Intelligence" tab toe aan dashboard_v3.html
   - Live gap monitoring

2. **Automated Scheduling**
   - Windows Task Scheduler → run elke maandag
   - Email report met top 5 gaps

3. **SERP Analysis**
   - Scrape Google rankings voor gaps
   - Competitor position tracking

4. **Internal Link Optimizer**
   - Find orphan pages
   - Suggest link placements

5. **Revenue Attribution**
   - Link gaps to potential revenue
   - ROI forecasting per gap

---

## 🤝 SUPPORT

**Issues?**
- Check logs: `logs/gap_intelligence.log`
- Review config: `config_gaps.py`
- Test step-by-step: `python gap_intelligence.py crawl/detect/brief`

**Questions?**
- Deze tool is gebouwd specifiek voor DemoShop.example
- Aanpassingen mogelijk via config files

---

## 📝 CHANGELOG

### v1.0 (24-03-2026)
- ✅ Initial release
- ✅ Competitor crawling
- ✅ Gap detection
- ✅ Brief generation (template + GPT)
- ✅ Priority scoring

---

**Built with ❤️ for DemoShop.example**  
**No Ahrefs/SEMrush needed!**
