"""
DEMO Artikel Generator v1.0
===========================
Genereert volledige kennisbank HTML-artikelen vanuit content briefs.
Output is direct plakbaar in het DEMO CMS tekstvak.

Gebruik:
    python demo_artikel_generator.py --brief output/content_briefs_v2/002_beglazingskit.json
    python demo_artikel_generator.py --brief output/content_briefs_v2/003_roestwerende_primer.json
    python demo_artikel_generator.py --batch output/content_briefs_v2/ --top 5

Vereisten:
    pip install openai
    OPENAI_API_KEY environment variable

Output:
    output/artikelen/<bestandsnaam>.html  (direct in CMS plakbaar)
"""

import json
import os
import re
import time
import argparse
from datetime import datetime
from pathlib import Path

# ==============================================
# CONFIGURATIE
# ==============================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
BRIEFS_DIR = Path("output/content_briefs_v2")
OUTPUT_DIR = Path("output/artikelen")
API_DELAY = 3  # Seconden tussen calls

# ==============================================
# DEMO STIJLGIDS VOOR DE PROMPT
# Beschrijft exact de HTML-structuur die gegenereerd moet worden
# ==============================================

DEMO_STIJLGIDS = """
Je genereert een volledig HTML kennisbankartikel voor DemoShop.example in hun vaste huisstijl.
DEMO is een professionele B2B verf- en coatings groothandel. Toon: direct, praktisch, vakkundig.
Doelgroep: schilders, aannemers, jachtbouwers, industriële afnemers.

## VERPLICHTE HTML STRUCTUUR

Het artikel bestaat uit deze vaste secties in deze volgorde:

### 1. CSS (altijd exact deze CSS, niet aanpassen)
Begin met deze CSS block:
```
<style>
  :root {
    --demo-dark: #103a5d;
    --demo-blue: #1875ad;
    --demo-light: #e9f5fc;
    --demo-border: #c9e3f5;
    --demo-accent: #e30617;
    --text-primary: #1a1a1a;
    --text-muted: #5a6a7a;
    --bg-warm: #fafbfc;
    --bg-card: #ffffff;
  }
  .kb-article { max-width: 100%; margin: 0 auto; padding-left: 12%; padding-right: 12%; font-family: Arial, sans-serif; line-height: 1.7; color: var(--text-primary); }
  @media (max-width: 768px) { .kb-article { padding-left: 5%; padding-right: 5%; } }
  .kb-hero { margin: 0 0 30px 0; }
  .kb-hero-img { width: 100%; height: 240px; object-fit: cover; border-radius: 12px; background: #e9f5fc; display: block; }
  .kb-hero-content { text-align: center; padding: 24px 0 0; }
  .kb-hero h1 { color: var(--demo-dark); font-size: clamp(1.75rem, 4vw, 2.25rem); font-weight: 700; margin: 0 0 12px; line-height: 1.2; }
  .kb-hero-subtitle { color: var(--text-muted); font-size: 1.05rem; margin: 0; }
  .kb-meta { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 32px; justify-content: center; }
  .kb-tag { background: var(--demo-light); border: 1px solid var(--demo-border); color: var(--demo-dark); border-radius: 50px; padding: 6px 14px; font-size: 0.85rem; font-weight: 500; }
  .kb-tldr { background: linear-gradient(135deg, var(--demo-dark) 0%, var(--demo-blue) 100%); color: #fff; border-radius: 12px; padding: 24px 28px; margin-bottom: 40px; }
  .kb-tldr, .kb-tldr * { color: #ffffff !important; }
  .kb-tldr a { color: #ffffff !important; text-decoration: underline; }
  .kb-tldr-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.8; margin-bottom: 8px; }
  .kb-tldr h2 { color: #ffffff !important; font-size: 1.15rem; font-weight: 600; margin: 0 0 12px; }
  .kb-tldr p { margin: 0; line-height: 1.6; color: #ffffff !important; }
  .kb-toc { background: var(--bg-warm); border: 1px solid #e5e9ed; border-radius: 10px; padding: 20px 24px; margin-bottom: 40px; }
  .kb-toc-title { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin: 0 0 12px; }
  .kb-toc ol { margin: 0; padding-left: 20px; }
  .kb-toc li { margin-bottom: 6px; }
  .kb-toc a { color: var(--demo-blue); text-decoration: none; font-weight: 500; }
  .kb-article h2 { color: var(--demo-dark); font-size: 1.5rem; font-weight: 700; margin: 48px 0 20px; padding-bottom: 10px; border-bottom: 2px solid var(--demo-light); }
  .kb-article h3 { color: var(--demo-dark); font-size: 1.15rem; font-weight: 600; margin: 32px 0 12px; }
  .kb-article h4 { color: var(--demo-blue); font-size: 1rem; font-weight: 600; margin: 24px 0 8px; }
  .kb-keuze-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 32px 0; }
  @media (max-width: 768px) { .kb-keuze-grid { grid-template-columns: 1fr; } }
  .kb-keuze-card { background: #fff; border: 1px solid #e5e9ed; border-radius: 12px; overflow: hidden; }
  .kb-keuze-header { background: var(--demo-dark); color: #fff; padding: 16px 20px; display: flex; align-items: center; gap: 12px; }
  .kb-keuze-icon { font-size: 1.4rem; }
  .kb-keuze-vraag { font-weight: 600; font-size: 1.05rem; }
  .kb-keuze-opties { padding: 8px; }
  .kb-keuze-optie { display: flex; flex-direction: column; gap: 4px; padding: 14px 16px; border-radius: 8px; margin-bottom: 4px; background: var(--bg-warm); }
  .kb-keuze-optie:last-child { margin-bottom: 0; }
  .kb-keuze-label { font-weight: 600; color: var(--demo-dark); font-size: 0.95rem; }
  .kb-keuze-antwoord { color: var(--text-muted); font-size: 0.9rem; }
  .kb-keuze-antwoord a { color: var(--demo-blue); font-weight: 500; }
  .kb-keuze-warning { background: #fff8e1; border-left: 3px solid #ffa000; }
  .kb-keuze-warning .kb-keuze-label { color: #e65100; }
  .kb-keuze-success { background: #e8f5e9; border-left: 3px solid #4caf50; }
  .kb-keuze-success .kb-keuze-label { color: #2e7d32; }
  .kb-keuze-danger { background: #ffebee; border-left: 3px solid #e53935; }
  .kb-keuze-danger .kb-keuze-label { color: #c62828; }
  .kb-table-wrap { overflow-x: auto; margin: 24px 0; border-radius: 10px; border: 1px solid #e5e9ed; }
  .kb-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
  .kb-table th { background: var(--demo-dark); color: #fff; padding: 14px 16px; text-align: left; font-weight: 600; }
  .kb-table th:first-child { border-radius: 9px 0 0 0; }
  .kb-table th:last-child { border-radius: 0 9px 0 0; }
  .kb-table td { padding: 12px 16px; border-bottom: 1px solid #eee; vertical-align: top; }
  .kb-table tr:last-child td { border-bottom: none; }
  .kb-table tr:nth-child(even) { background: var(--bg-warm); }
  .kb-steps { counter-reset: step-counter; display: flex; flex-direction: column; gap: 16px; margin: 24px 0; }
  .kb-step { display: flex; gap: 16px; padding: 20px; background: #fff; border: 1px solid #e5e9ed; border-radius: 10px; }
  .kb-step::before { counter-increment: step-counter; content: counter(step-counter); flex-shrink: 0; width: 36px; height: 36px; background: var(--demo-blue); color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; }
  .kb-step-content h4 { margin: 0 0 8px; color: var(--demo-dark); font-size: 1.05rem; }
  .kb-step-content p { margin: 0; color: var(--text-muted); }
  .kb-info { background: var(--demo-light); border-left: 4px solid var(--demo-blue); border-radius: 0 10px 10px 0; padding: 18px 22px; margin: 24px 0; }
  .kb-info-title { font-weight: 700; color: var(--demo-dark); margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
  .kb-info p { margin: 0; color: #3a4a5a; }
  .kb-warning { background: #fff8e1; border-left: 4px solid #ffa000; border-radius: 0 10px 10px 0; padding: 18px 22px; margin: 24px 0; }
  .kb-warning-title { font-weight: 700; color: #e65100; margin-bottom: 8px; }
  .kb-warning p { margin: 0; color: #5d4037; }
  .kb-danger { background: #ffebee; border-left: 4px solid #e53935; border-radius: 0 10px 10px 0; padding: 18px 22px; margin: 24px 0; }
  .kb-danger-title { font-weight: 700; color: #c62828; margin-bottom: 8px; }
  .kb-danger p { margin: 0; color: #b71c1c; }
  .kb-products { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin: 24px 0; }
  .kb-product { background: #fff; border: 1px solid #e5e9ed; border-radius: 12px; overflow: hidden; }
  .kb-product-img-placeholder { width: 100%; height: 160px; background: #e9f5fc; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 0.85rem; border-bottom: 1px solid #f0f0f0; }
  .kb-product-body { padding: 20px; }
  .kb-product-badge { display: inline-block; background: var(--demo-light); color: var(--demo-dark); font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 4px 10px; border-radius: 4px; margin-bottom: 10px; }
  .kb-product h4 { margin: 0 0 8px; font-size: 1.05rem; color: var(--demo-dark); }
  .kb-product p { font-size: 0.88rem; color: var(--text-muted); margin: 0 0 16px; }
  .kb-product-btn { display: inline-block; background: var(--demo-dark); color: #ffffff !important; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 0.88rem; }
  .kb-faq { margin: 40px 0; }
  .kb-faq-item { border-bottom: 1px solid #e5e9ed; }
  .kb-faq-item:first-child { border-top: 1px solid #e5e9ed; }
  .kb-faq-q { width: 100%; background: none; border: none; padding: 18px 40px 18px 0; text-align: left; font-size: 1rem; font-weight: 600; color: var(--demo-dark); cursor: pointer; position: relative; font-family: inherit; }
  .kb-faq-q::after { content: '+'; position: absolute; right: 0; top: 50%; transform: translateY(-50%); font-size: 1.5rem; color: var(--demo-blue); }
  .kb-faq-item.open .kb-faq-q::after { content: '−'; }
  .kb-faq-a { display: none; padding: 0 0 18px; color: var(--text-muted); line-height: 1.6; }
  .kb-faq-item.open .kb-faq-a { display: block; }
  .kb-cta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 48px 0 32px; }
  @media (max-width: 600px) { .kb-cta-grid { grid-template-columns: 1fr; } }
  .kb-cta-box { padding: 28px; border-radius: 12px; text-align: center; }
  .kb-cta-box, .kb-cta-box * { color: #ffffff !important; }
  .kb-cta-box h3 { margin: 0 0 12px; font-size: 1.1rem; }
  .kb-cta-box p { font-size: 0.9rem; margin: 0 0 16px; opacity: 0.9; }
  .kb-cta-primary { background: var(--demo-blue); }
  .kb-cta-secondary { background: var(--demo-dark); }
  .kb-cta-btn { display: inline-block; padding: 10px 24px; border: 2px solid #fff; border-radius: 6px; color: #ffffff !important; text-decoration: none; font-weight: 600; }
  .kb-article a { color: var(--demo-blue); }
  .kb-summary { background: var(--demo-light); border-radius: 12px; padding: 24px 28px; margin: 40px 0; }
  .kb-summary h3 { margin-top: 0; color: var(--demo-dark); }
  .kb-summary p { margin: 0 0 10px; color: #1a3a4a; }
  .kb-summary p:last-child { margin-bottom: 0; }
</style>
```

### 2. ARTIKEL BODY

Na de CSS, genereer de artikel body. Gebruik EXACT deze structuur en class-namen:

**Hero sectie:**
```html
<div class="kb-article">
  <div class="kb-hero">
    <!-- AFBEELDING PLACEHOLDER - later vervangen door redactie -->
    <div class="kb-hero-img" style="background: #e9f5fc; height: 240px; border-radius: 12px;"></div>
    <div class="kb-hero-content">
      <h1>[H1 HIER]</h1>
      <p class="kb-hero-subtitle">[SUBTITLE HIER]</p>
    </div>
  </div>
```

**Meta tags** (leestijd schatten op basis van woordenaantal, categorie uit brief):
```html
  <div class="kb-meta">
    <span class="kb-tag">🕒 [X-Y min]</span>
    <span class="kb-tag">🔧 [CATEGORIE]</span>
    <span class="kb-tag">🎨 [ONDERWERP]</span>
  </div>
```

**TL;DR box** (samenvatting in max 4 bulletpoints met vette koppen):
```html
  <div class="kb-tldr">
    <div class="kb-tldr-label">In het kort</div>
    <h2>[H1 TITEL]</h2>
    <p><strong>Wat is het:</strong> ... <br><strong>Wanneer gebruiken:</strong> ... <br><strong>Merken bij DEMO:</strong> ... <br><strong>Let op:</strong> ...</p>
  </div>
```

**Disclaimer:**
```html
  <div class="kb-info">
    <div class="kb-info-title">ℹ️ Disclaimer</div>
    <p>Deze informatie is bedoeld als praktische keuzehulp. Op basis van geleverde informatie kunnen geen rechten worden ontleend. Volg altijd de technische datasheet (TDS) van het product dat je gebruikt.</p>
  </div>
```

**Inhoudsopgave** (gebaseerd op H2-structuur van het artikel):
```html
  <nav class="kb-toc">
    <p class="kb-toc-title">In dit artikel</p>
    <ol>
      <li><a href="#sectie-1">Sectienaam 1</a></li>
      ...
    </ol>
  </nav>
```

**Introductie** (2-3 alinea's, concreet en praktisch, geen blabla):

**H2 secties** — gebruik een mix van deze componenten per sectie:

*Keuzegrid* (voor vergelijkingen, voor/nadelen, wanneer wat gebruiken):
```html
  <div class="kb-keuze-grid">
    <div class="kb-keuze-card">
      <div class="kb-keuze-header">
        <span class="kb-keuze-icon">🎨</span>
        <span class="kb-keuze-vraag">Vraag of situatie</span>
      </div>
      <div class="kb-keuze-opties">
        <div class="kb-keuze-optie kb-keuze-success">
          <span class="kb-keuze-label">Optie of eigenschap</span>
          <span class="kb-keuze-antwoord">Uitleg</span>
        </div>
        <div class="kb-keuze-optie kb-keuze-warning">...</div>
        <div class="kb-keuze-optie kb-keuze-danger">...</div>
        <div class="kb-keuze-optie">...</div>
      </div>
    </div>
  </div>
```

*Vergelijkingstabel* (voor specificaties, eigenschappen, merkvergelijking):
```html
  <div class="kb-table-wrap">
    <table class="kb-table">
      <thead><tr><th>...</th></tr></thead>
      <tbody><tr><td>...</td></tr></tbody>
    </table>
  </div>
```

*Stappenplan* (voor how-to secties):
```html
  <div class="kb-steps">
    <div class="kb-step">
      <div class="kb-step-content">
        <h4>Stap titel</h4>
        <p>Uitleg</p>
      </div>
    </div>
  </div>
```

*Info/warning/danger boxes* (gebruik spaarzaam, max 1-2 per artikel):
```html
  <div class="kb-info"><div class="kb-info-title">💡 Pro tip</div><p>...</p></div>
  <div class="kb-warning"><div class="kb-warning-title">⚠️ Let op</div><p>...</p></div>
  <div class="kb-danger"><div class="kb-danger-title">🚨 Gevaar</div><p>...</p></div>
```

**Productkaarten sectie** (altijd 2-4 producten, met placeholder afbeelding):
```html
  <h2 id="producten">Aanbevolen producten bij DEMO</h2>
  <div class="kb-products">
    <div class="kb-product">
      <div class="kb-product-img-placeholder">📷 Afbeelding toevoegen</div>
      <div class="kb-product-body">
        <span class="kb-product-badge">CATEGORIE</span>
        <h4>Productnaam</h4>
        <p>Korte productbeschrijving.</p>
        <a href="https://demo-shop.example/search?query=ZOEKTERM" class="kb-product-btn">Bekijk producten</a>
      </div>
    </div>
  </div>
```

**FAQ sectie** (minimaal 5 vragen, praktisch en direct):
```html
  <h2 id="faq">Veelgestelde vragen</h2>
  <div class="kb-faq">
    <div class="kb-faq-item">
      <button class="kb-faq-q">Vraag?</button>
      <div class="kb-faq-a"><strong>Direct antwoord.</strong> Verdere uitleg...</div>
    </div>
  </div>
```

**Samenvatting:**
```html
  <div class="kb-summary">
    <h3>Samenvatting: [ONDERWERP]</h3>
    <p><strong>Punt 1:</strong> ...</p>
    <p><strong>Punt 2:</strong> ...</p>
  </div>
```

**CTA grid** (altijd afsluiten met twee CTA's):
```html
  <div class="kb-cta-grid">
    <div class="kb-cta-box kb-cta-primary">
      <h3>Bekijk ons [PRODUCTCATEGORIE] assortiment</h3>
      <p>Korte beschrijving</p>
      <a href="https://demo-shop.example/search?query=ZOEKTERM" class="kb-cta-btn">Naar assortiment</a>
    </div>
    <div class="kb-cta-box kb-cta-secondary">
      <h3>Advies nodig?</h3>
      <p>Onze specialisten helpen je graag</p>
      <a href="mailto:verkoop@demo-shop.example" class="kb-cta-btn">Mail ons</a>
    </div>
  </div>
</div>
```

**JavaScript** (altijd exact dit aan het einde):
```html
<script>
document.querySelectorAll('.kb-faq-q').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.parentElement;
    const wasOpen = item.classList.contains('open');
    document.querySelectorAll('.kb-faq-item').forEach(i => i.classList.remove('open'));
    if (!wasOpen) { item.classList.add('open'); }
  });
});
</script>
```

## INTERNE LINKS
Verwerk interne links door de hele tekst. Gebruik dit formaat:
- Productzoekopdrachten: `<a href="https://demo-shop.example/search?query=ZOEKTERM">ANKERTEKST</a>`
- Categoriepagina's: `<a href="https://demo-shop.example/CATEGORIE">ANKERTEKST</a>`
- Link op relevante termen: merk-namen, productnamen, technieken

## TOON EN STIJL
- Direct en praktisch. Schrijf als een vakman die een collega helpt, niet als een marketeer.
- Concrete getallen waar mogelijk: droogtijden, verdunningspercentages, korrelgroottes, etc.
- Noem ALLEEN de DEMO-merken die in de brief staan als relevant.
- Alinea's max 3-4 zinnen.
- Geen opsommingen buiten de HTML-componenten.

## VERBODEN WOORDEN EN ZINNEN
Gebruik deze woorden en frasen NOOIT — ze klinken als AI-tekst en niet als een vakman:
- "essentieel", "cruciaal", "onmisbaar", "van groot belang"
- "speciaal ontworpen voor", "speciaal ontwikkeld voor", "speciaal gemaakt voor"
- "optimaal resultaat", "optimale prestaties", "optimale bescherming"
- "hoogwaardige kwaliteit", "topkwaliteit", "premium kwaliteit"
- "uitstekende eigenschappen", "uitstekende prestaties"
- "perfect voor", "ideaal voor" (gebruik in plaats daarvan: "geschikt voor" of gewoon beschrijven wat het doet)
- "zorgt voor een strakke afwerking" (te generiek)
- "biedt bescherming" (zeg WAT voor bescherming, HOE LANG, WAARTEGEN)
- "is een essentieel product" — begin nooit zo
- "In dit artikel" als openingszin van een alinea
- "Zoals eerder vermeld", "Zoals hierboven beschreven"
- Zinnen die beginnen met "Het is belangrijk dat..."
- "professionele resultaten" als loze belofte zonder specificatie

Gebruik in plaats daarvan:
- Specifieke, meetbare claims: "droogt in 2-4 uur", "overschilderbaar na 24u bij 20°C"
- Actieve zinnen: "Sika beglazingskit hecht op glas, aluminium en PVC"
- Vergelijkingen: "anders dan siliconen kit, is dit product overschilderbaar"
- Vakmanstaal: wat een ervaren schilder of aannemer zou zeggen
"""


# ==============================================
# ARTIKEL GENERATOR
# ==============================================

def genereer_artikel(brief: dict) -> str:
    """
    Genereer een volledig HTML artikel via OpenAI API.
    Returns HTML string.
    """
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Extraheer brief-data
    h1 = brief.get("suggested_h1", brief.get("title", ""))
    h2s = brief.get("suggested_h2s", [])
    merken = brief.get("relevante_demo_merken", [])
    doelgroep = brief.get("doelgroep", "professionele schilders en aannemers")
    content_angle = brief.get("content_angle", "")
    key_topics = brief.get("key_topics", [])
    meta_title = brief.get("meta_title", h1)
    meta_desc = brief.get("meta_description", "")
    zoekintentie = brief.get("verwachte_zoekintentie", "informationeel")
    word_count = brief.get("target_word_count", 900)
    internal_links = brief.get("internal_link_suggesties", [])
    usps = brief.get("demo_unique_selling_points", [])

    # Bouw de prompt
    prompt = f"""
{DEMO_STIJLGIDS}

## BRIEF VOOR DIT ARTIKEL

**H1:** {h1}
**H2 structuur:** {json.dumps(h2s, ensure_ascii=False)}
**Doelgroep:** {doelgroep}
**Content angle:** {content_angle}
**Relevante DEMO merken (ALLEEN deze noemen):** {', '.join(merken)}
**Key topics te behandelen:** {json.dumps(key_topics, ensure_ascii=False)}
**Zoekintentie:** {zoekintentie}
**Target woordenaantal:** {word_count}+
**DEMO USPs te verwerken:** {json.dumps(usps, ensure_ascii=False)}
**Interne link suggesties:** {json.dumps(internal_links, ensure_ascii=False)}
**Meta title:** {meta_title}
**Meta description:** {meta_desc}

## INSTRUCTIE

Genereer nu het VOLLEDIGE HTML artikel in één keer. Volg de stijlgids exact.
Gebruik de H2 structuur uit de brief als leidraad maar pas aan waar inhoudelijk logisch.

VERPLICHT in elk artikel:
- Minimaal 2 keuzegrids met elk 3-4 opties (success/warning/danger kleuren gebruiken)
- Minimaal 1 vergelijkingstabel
- Minimaal 1 stappenplan met 5+ stappen
- Minimaal 1 info of warning box
- Minimaal 4 productkaarten met placeholder afbeeldingen
- Minimaal 5 FAQ vragen met uitgebreide antwoorden
- Minimaal 5 interne links naar demo-shop.example/search?query=... door de tekst
- Samenvatting box aan het einde
- CTA grid als afsluiting
- JavaScript FAQ accordion

Minimum {word_count} woorden aan leesbare tekst (exclusief HTML tags en CSS).
Het artikel moet VOLLEDIG compleet zijn — niet afbreken voordat alle secties er zijn.

Geef ALLEEN de HTML terug, geen uitleg of markdown omheen.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000,
        temperature=0.3,
    )

    html = response.choices[0].message.content.strip()

    # Verwijder eventuele markdown code fences
    html = re.sub(r'^```html\s*', '', html)
    html = re.sub(r'\s*```$', '', html)

    return html


# ==============================================
# BESTAND OPSLAAN
# ==============================================

def sla_artikel_op(html: str, brief: dict, brief_pad: Path) -> Path:
    """Sla het gegenereerde artikel op als HTML bestand."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Genereer bestandsnaam op basis van brief bestandsnaam
    bestandsnaam = brief_pad.stem + ".html"
    output_pad = OUTPUT_DIR / bestandsnaam

    # Voeg metadata commentaar toe bovenaan
    meta_commentaar = f"""<!-- 
  DEMO Kennisbank Artikel
  Gegenereerd: {datetime.now().strftime('%Y-%m-%d %H:%M')}
  Brief: {brief_pad.name}
  H1: {brief.get('suggested_h1', '')}
  Merken: {', '.join(brief.get('relevante_demo_merken', []))}
  
  TODO voor redactie:
  1. Voeg hero afbeelding toe (vervang div.kb-hero-img placeholder)
  2. Voeg productafbeeldingen toe (vervang div.kb-product-img-placeholder)
  3. Controleer interne links op juiste URLs
  4. Controleer technische details (droogtijden, verdunningspercentages)
  5. Submit URL via Google Search Console na publicatie
-->
"""

    with open(output_pad, "w", encoding="utf-8") as f:
        f.write(meta_commentaar + "\n" + html)

    return output_pad


# ==============================================
# BRIEF LADEN
# ==============================================

def laad_brief(pad: Path) -> dict:
    """Laad een brief JSON bestand."""
    with open(pad, encoding="utf-8") as f:
        return json.load(f)


def vind_briefs(briefs_dir: Path, top: int = None) -> list:
    """Vind alle brief JSON bestanden, gesorteerd op DEMO relevantie score."""
    bestanden = list(briefs_dir.glob("*.json"))

    # Laad scores voor sortering
    gescoord = []
    for bestand in bestanden:
        try:
            brief = laad_brief(bestand)
            score = brief.get("demo_relevantie_score", 0)
            gescoord.append((score, bestand))
        except Exception:
            continue

    # Sorteer op score (hoog naar laag)
    gescoord.sort(key=lambda x: x[0], reverse=True)

    bestanden_gesorteerd = [b for _, b in gescoord]

    if top:
        return bestanden_gesorteerd[:top]
    return bestanden_gesorteerd


# ==============================================
# MAIN
# ==============================================

def main():
    parser = argparse.ArgumentParser(
        description="DEMO Artikel Generator — brief naar HTML artikel"
    )
    parser.add_argument("--brief", type=str,
                        help="Pad naar één brief JSON bestand")
    parser.add_argument("--batch", type=str,
                        help="Map met briefs voor batch verwerking")
    parser.add_argument("--top", type=int, default=5,
                        help="Aantal briefs in batch modus (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Toon welke briefs verwerkt worden zonder API calls")
    args = parser.parse_args()

    if not OPENAI_API_KEY and not args.dry_run:
        print("❌ OPENAI_API_KEY niet gevonden.")
        print("   Zet: setx OPENAI_API_KEY 'sk-...'")
        return

    print("""
╔══════════════════════════════════════════════════════════════╗
║           DEMO ARTIKEL GENERATOR v1.0                         ║
║           Brief → Volledig HTML Kennisbank Artikel           ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Bepaal welke briefs te verwerken
    if args.brief:
        brief_pad = Path(args.brief)
        if not brief_pad.exists():
            print(f"❌ Brief niet gevonden: {brief_pad}")
            return
        te_verwerken = [brief_pad]

    elif args.batch:
        briefs_dir = Path(args.batch)
        if not briefs_dir.exists():
            print(f"❌ Map niet gevonden: {briefs_dir}")
            return
        te_verwerken = vind_briefs(briefs_dir, top=args.top)
        print(f"📂 {len(te_verwerken)} briefs gevonden in {briefs_dir}")

    else:
        # Default: gebruik BRIEFS_DIR
        te_verwerken = vind_briefs(BRIEFS_DIR, top=args.top)
        print(f"📂 {len(te_verwerken)} briefs gevonden in {BRIEFS_DIR}")

    if not te_verwerken:
        print("Geen briefs gevonden.")
        return

    # Preview
    print(f"\n📋 Te verwerken:")
    for pad in te_verwerken:
        try:
            brief = laad_brief(pad)
            print(f"  • {pad.name[:50]:50s} | {brief.get('suggested_h1', '')[:45]}")
        except Exception:
            print(f"  • {pad.name}")

    if args.dry_run:
        print(f"\n🔍 Dry run — {len(te_verwerken)} artikelen zouden gegenereerd worden.")
        print(f"   Output map: {OUTPUT_DIR}/")
        return

    # Genereer artikelen
    print(f"\n🚀 Genereer {len(te_verwerken)} artikelen...\n")

    succes = 0
    fouten = 0

    for i, brief_pad in enumerate(te_verwerken, 1):
        try:
            brief = laad_brief(brief_pad)
            h1 = brief.get("suggested_h1", brief_pad.stem)

            print(f"[{i}/{len(te_verwerken)}] {h1[:55]}...")
            print(f"   ⏳ Genereren... (±45 seconden)")

            start = time.time()
            html = genereer_artikel(brief)
            duur = int(time.time() - start)
            print(f"   ⏱  Klaar in {duur}s")
            output_pad = sla_artikel_op(html, brief, brief_pad)

            print(f"   ✅ Opgeslagen: {output_pad.name}")
            succes += 1

            if i < len(te_verwerken):
                time.sleep(API_DELAY)

        except Exception as e:
            print(f"   ❌ Fout: {e}")
            fouten += 1
            continue

    # Samenvatting
    print(f"""
{'='*60}
✅ KLAAR
{'='*60}
Succesvol: {succes} artikelen
Fouten:    {fouten}
Output:    {OUTPUT_DIR}/

Checklist voor publicatie:
  □ Voeg hero afbeelding toe
  □ Voeg productafbeeldingen toe
  □ Controleer technische details
  □ Publiceer in CMS
  □ Submit via Google Search Console
{'='*60}
""")


if __name__ == "__main__":
    main()