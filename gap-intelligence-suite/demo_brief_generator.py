"""
Demo Content Brief Generator v2.0
==================================
Combineert Gap Intelligence output met OpenAI API voor kwalitatieve content briefs.
Voegt DEMO-assortiment context toe en filtert irrelevante gaps eruit.

Gebruik:
    python demo_brief_generator.py                    # Top 10 relevante gaps
    python demo_brief_generator.py --top 20           # Top 20
    python demo_brief_generator.py --rank 5           # Alleen gap rank 5
    python demo_brief_generator.py --all              # Alle relevante gaps
    python demo_brief_generator.py --dry-run          # Test zonder API calls

Vereisten:
    pip install openai
    OPENAI_API_KEY environment variable (of hardcode hieronder)
"""

import json
import os
import re
import time
import argparse
from datetime import datetime
from pathlib import Path

# ==============================================
# CONFIGURATIE - pas paden aan indien nodig
# ==============================================

GAPS_FILE = Path("data/gaps_detected_gsc.json")
OUTPUT_DIR = Path("output/content_briefs_v2")

# API key - zet als environment variable of vul hier in
# Windows: setx OPENAI_API_KEY "sk-..."
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Vertraging tussen API calls (seconden) - voorkomt rate limiting
API_DELAY = 2

# ==============================================
# DEMO ASSORTIMENT CONTEXT
# Handmatig samengesteld uit categorieindeling excel.
# Dit voorkomt dat Claude verkeerde merken of producten noemt.
# ==============================================

DEMO_CONTEXT = {
    "bedrijfsomschrijving": (
        "DEMO (Demo Paint- en Verfhandel B.V.) is een professionele B2B groothandel "
        "in verf, coatings, oliën en toebehoren. Klanten zijn professionals: schilders, "
        "jachtbouwers, scheepvaartbedrijven, aannemers en industriële afnemers. "
        "DEMO verkoopt GEEN consumentenproducten van Gamma/Praxis/Hornbach-achtige merken."
    ),
    "hoofdcategorieen": [
        "Jachtbouw en Marine",
        "Schilders",
        "Afbouw",
        "Automotive",
        "Non-Paint (gereedschap, benodigdheden)",
        "Olie en vetten",
        "Binnenvaart",
    ],
    "merken_per_categorie": {
        "jachtbouw_marine": [
            "Hempel", "Jotun", "Epifanes", "International", "Aemme",
            "Hydrant", "Owatrol", "Werdol", "Touwen", "Nelf",
            "West Systems", "Gurit SP Epoxy", "De IJssel", "Yachtcare",
            "Sika", "Den Braven",
        ],
        "schilders": [
            "Wijzonol", "Nelf", "Nylo", "De Vos verf", "Relius", "Ekotex",
            "einZa", "Jotun", "Avis", "Trae Lyx", "Sika",
        ],
        "afbouw": [
            "Sika", "Den Braven", "Knauf", "Weber", "Mapei",
        ],
        "automotive": [
            "Finixa", "Hydrant", "Nelf", "Avis",
        ],
        "olie_vetten": [
            "Americol", "Shell", "Mobil", "Q8",
        ],
    },
    "niet_relevant": [
        # Producten/categorieën die DEMO NIET verkoopt of niet de core zijn
        "trappen", "ladders", "steigers", "schuurmachines", "accu gereedschap",
        "washi tape", "huishoudproducten", "consumentenmerken",
        "Sikkens", "Trimetal", "Sigma", "Little Greene", "Mathys",
        "Boonstoppel", "SPS", "gamma", "praxis", "hornbach",
    ],
    "relevante_onderwerpen": [
        # Onderwerpen waar DEMO wél sterk in is en content over zou moeten hebben
        "antifouling", "epoxy coating", "jachtlak", "primer", "grondverf",
        "muurverf", "buitenverf", "binnenverf", "lak waterbasis", "lak terpentine",
        "metaallak", "vloerlak", "douglas beits", "steigerhout beits",
        "blanke lak", "zijdeglans lak", "radiatorlak", "afbijtmiddel",
        "kwasten", "verfrollers", "schuurpapier", "spuitbussen",
        "sika kit", "epoxy", "polyester", "plamuur", "verdunning",
        "olie vetten", "scheepsverf", "binnenvaart coating",
    ],
}

# ==============================================
# DEMO RELEVANTIE SCORING
# Bepaalt of een gap relevant is voor DEMO
# ==============================================

RELEVANTIE_BOOST_TERMEN = [
    # Hoge relevantie - DEMO core producten
    "lak", "verf", "coating", "primer", "grondverf", "antifouling",
    "epoxy", "plamuur", "beits", "aflak", "muurverf", "vloerlak",
    "kit", "sika", "hempel", "jotun", "epifanes", "international",
    "wijzonol", "nelf", "kwast", "roller", "schuurpapier",
    "verdunning", "oplosmiddel", "afbijtmiddel", "spuitbus",
    "radiatorlak", "metaallak", "blanke lak", "zijdeglans",
    "douglas", "steigerhout", "voorstrijk", "sierpleister",
]

RELEVANTIE_PENALTY_TERMEN = [
    # Lage relevantie - niet DEMO core
    "trap", "ladder", "steiger", "schuurmachine", "accu",
    "washi tape", "sikkens", "trimetal", "sigma", "little greene",
    "mathys", "boonstoppel", "sps muurverf", "kleurenwaaier",
    "huishoud", "reformladder", "vlizotrap", "vouwladder",
    "telescoopladder", "werkbordes",
    # Gereedschap merken die DEMO niet verkoopt
    "makita", "bosch", "dewalt", "stanley", "hammerite",
    "repair care", "polyfilla", "zwaluw", "paintura", "lucamax",
    # Specifieke product-types die niet bij DEMO passen
    "bitset", "bouwstofzuiger", "stofzak", "modelleermes",
    "plamuur waterbasis",
]


def bereken_demo_relevantie(gap: dict) -> float:
    """
    Bereken hoe relevant een gap is voor DEMO (0-100).
    Hogere score = beter geschikt voor DEMO content.
    """
    titel = gap.get("title", "").lower()
    url = gap.get("competitor_url", "").lower()
    h2s = " ".join(gap.get("h2s_sample", [])).lower()
    tekst = f"{titel} {url} {h2s}"

    score = gap.get("priority_score", 50)

    # Boost voor relevante termen
    for term in RELEVANTIE_BOOST_TERMEN:
        if term in tekst:
            score += 8

    # Penalty voor irrelevante termen
    for term in RELEVANTIE_PENALTY_TERMEN:
        if term in tekst:
            score -= 25

    # Cap tussen 0 en 100
    return max(0, min(100, score))


def filter_en_sorteer_gaps(gaps: list, min_relevantie: float = 40) -> list:
    """
    Filter irrelevante gaps en sorteer op DEMO-relevantie.
    """
    gescoord = []
    for gap in gaps:
        demo_score = bereken_demo_relevantie(gap)
        if demo_score >= min_relevantie:
            gap_copy = dict(gap)
            gap_copy["demo_relevantie_score"] = round(demo_score, 1)
            gescoord.append(gap_copy)

    # Sorteer op DEMO relevantie (hoog naar laag)
    gescoord.sort(key=lambda x: x["demo_relevantie_score"], reverse=True)
    return gescoord



# ==============================================
# PRODUCTTYPE -> MERK MAPPING
# ==============================================

PRODUCTTYPE_MERKEN = {
    "roller": ["Finixa", "Nelf"],
    "kwast": ["Finixa", "Nelf"],
    "spuitbus": ["Hempel", "Jotun", "Nelf", "Epifanes", "Sika"],
    "schuurpapier": ["Finixa"],
    "antifouling": ["Hempel", "Jotun", "Epifanes", "International"],
    "bootlak": ["Epifanes", "Hempel", "Jotun", "International", "Aemme"],
    "jachtlak": ["Epifanes", "Hempel", "Jotun", "International"],
    "blanke lak": ["Epifanes", "Hempel", "Aemme", "Hydrant", "De Vos verf"],
    "epoxy": ["West Systems", "Gurit SP Epoxy", "De IJssel", "Hempel"],
    "muurverf": ["Wijzonol", "Nelf", "Nylo", "De Vos verf", "Jotun", "einZa"],
    "buitenverf": ["Wijzonol", "Nelf", "Nylo", "Jotun", "De Vos verf"],
    "binnenverf": ["Wijzonol", "Nelf", "Nylo", "De Vos verf", "Avis"],
    "vloerlak": ["Wijzonol", "Nelf", "Sika", "Jotun", "Trae Lyx"],
    "radiatorlak": ["Wijzonol", "Nelf", "Nylo"],
    "grondverf": ["Wijzonol", "Nelf", "Nylo", "Jotun", "Avis"],
    "primer": ["Wijzonol", "Nelf", "Jotun", "Avis", "Hempel"],
    "beits": ["Wijzonol", "Nelf", "Trae Lyx", "De Vos verf"],
    "lak": ["Wijzonol", "Nelf", "Nylo", "Jotun", "De Vos verf"],
    "metaallak": ["Jotun", "Hempel", "Nelf", "De IJssel"],
    "kit": ["Sika", "Den Braven"],
    "lijm": ["Sika", "Den Braven"],
    "olie": ["Americol", "Shell", "Mobil"],
    "vet": ["Americol"],
    "smeermiddel": ["Americol"],
}


def bepaal_relevante_merken(titel: str) -> str:
    """Bepaal welke merken relevant zijn op basis van producttitel."""
    titel_lower = titel.lower()
    gevonden = []
    for product_term, merken in PRODUCTTYPE_MERKEN.items():
        if product_term in titel_lower:
            gevonden.extend(merken)
    if gevonden:
        uniek = list(dict.fromkeys(gevonden))
        return f"Voor dit specifieke product zijn deze merken het meest relevant: {', '.join(uniek)}"
    else:
        return (
            "Gebruik alleen merken die logisch passen bij het product. "
            "Noem GEEN kit/lijm merken (Sika, Den Braven) bij verf of gereedschap."
        )

# ==============================================
# OPENAI API
# ==============================================

def genereer_brief_via_openai(gap: dict) -> dict:
    """
    Genereer een content brief via OpenAI API (gpt-4o).
    Returns dict met brief data.
    """
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    titel = gap.get("title", "")
    concurrent_url = gap.get("competitor_url", "")
    h2s = gap.get("h2s_sample", [])
    word_count = gap.get("word_count", 800)
    categorie = gap.get("category", "other")

    prompt = f"""Je bent een SEO content strategist voor DemoShop.example, een professionele B2B verf- en coatings groothandel in Nederland.

## DEMO BEDRIJFSCONTEXT
{DEMO_CONTEXT["bedrijfsomschrijving"]}

Hoofdcategorieën: {", ".join(DEMO_CONTEXT["hoofdcategorieen"])}

Merken die DEMO verkoopt (gebruik ALLEEN deze in je brief):
- Jachtbouw/Marine: {", ".join(DEMO_CONTEXT["merken_per_categorie"]["jachtbouw_marine"])}
- Schilders: {", ".join(DEMO_CONTEXT["merken_per_categorie"]["schilders"])}
- Overig: Sika, Den Braven, Finixa, Americol

{bepaal_relevante_merken(titel)}

## GAP INFORMATIE
Concurrent URL: {concurrent_url}
Concurrent paginatitel: {titel}
Concurrent H2-structuur (sample): {json.dumps(h2s, ensure_ascii=False)}
Concurrent woordenaantal: {word_count} woorden
Content type: {categorie}

## JOUW TAAK
Maak een gedetailleerde content brief voor DemoShop.example om deze gap te vullen.
De brief moet:
1. DEMO's B2B professionele doelgroep aanspreken (schilders, aannemers, jachtbouwers)
2. ALLEEN merken noemen die DEMO daadwerkelijk verkoopt (zie lijst hierboven)
3. Beter zijn dan de concurrent door meer diepgang en praktische expertise
4. Gevonden kunnen worden op dezelfde zoekterm als de concurrent

Geef je antwoord ALLEEN als JSON (geen markdown, geen uitleg erbuiten), in dit exacte formaat:
{{
  "suggested_h1": "...",
  "suggested_h2s": ["...", "...", "...", "...", "..."],
  "target_word_count": {max(int(word_count * 1.15), 800)},
  "meta_title": "...",
  "meta_description": "...",
  "content_angle": "...",
  "doelgroep": "...",
  "relevante_demo_merken": ["...", "..."],
  "key_topics": ["...", "...", "...", "...", "..."],
  "internal_link_suggesties": ["...", "...", "..."],
  "demo_unique_selling_points": ["...", "..."],
  "verwachte_zoekintentie": "informationeel of transactioneel"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        response_format={"type": "json_object"},  # Forceert JSON output
        temperature=0.4,  # Lager = consistenter en feitelijker
    )

    raw_text = response.choices[0].message.content.strip()

    # Strip markdown code fences voor de zekerheid
    raw_text = re.sub(r"^```json\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    return json.loads(raw_text)


# ==============================================
# BRIEF OPMAAK
# ==============================================

def maak_markdown_brief(gap: dict, claude_output: dict) -> str:
    """
    Genereer een markdown brief op basis van gap data en Claude output.
    """
    nu = datetime.now().strftime("%Y-%m-%d")
    rank = gap.get("rank", "?")
    demo_score = gap.get("demo_relevantie_score", "?")
    orig_score = gap.get("priority_score", "?")

    md = f"""# CONTENT BRIEF: {claude_output.get('suggested_h1', gap['title'])}

============================================================
**Gegenereerd:** {nu}
**Methode:** Claude Sonnet (DEMO-context aware)
**Gap Rank:** #{rank} | **Originele Score:** {orig_score}/100 | **DEMO Relevantie:** {demo_score}/100
============================================================

## 🎯 WAAROM DEZE CONTENT?

**Concurrent:** {gap.get('competitor_name', 'Competitor B')}
**Concurrent URL:** {gap.get('competitor_url', '')}
**Content Type:** {gap.get('category', '')}
**Zoekintentie:** {claude_output.get('verwachte_zoekintentie', 'informationeel')}

**Doelgroep:** {claude_output.get('doelgroep', 'Professionele schilders en aannemers')}

Door dit te maken kan DEMO:
- Traffic winnen van concurrent op deze zoekterm
- Autoriteit opbouwen bij de doelgroep
- Klanten beter informeren en naar het juiste product leiden

---

## 📝 CONTENT SPECIFICATIES

### H1 (Paginatitel)
```
{claude_output.get('suggested_h1', '')}
```

### H2 Structuur
"""
    for i, h2 in enumerate(claude_output.get("suggested_h2s", []), 1):
        md += f"{i}. {h2}\n"

    md += f"""
### Target Metrics
- **Woordenaantal:** {claude_output.get('target_word_count', 1000)}+ woorden
- **Aantal H2s:** {len(claude_output.get('suggested_h2s', []))}+
- **Afbeeldingen:** 2-3 (product foto's of toepassingsfoto's)

---

## 🔍 SEO OPTIMALISATIE

### Meta Title (max 60 tekens)
```
{claude_output.get('meta_title', '')}
```

### Meta Description (max 155 tekens)
```
{claude_output.get('meta_description', '')}
```

---

## 💡 CONTENT ANGLE

{claude_output.get('content_angle', '')}

---

## 🏷️ RELEVANTE DEMO MERKEN OM TE NOEMEN

{', '.join(claude_output.get('relevante_demo_merken', []))}

*(Gebruik ALLEEN deze merken - dit zijn de merken die DEMO daadwerkelijk verkoopt)*

---

## 🚀 DEMO UNIQUE SELLING POINTS OM TE VERWERKEN

"""
    for usp in claude_output.get("demo_unique_selling_points", []):
        md += f"- {usp}\n"

    md += """
---

## 📌 KEY TOPICS OM TE BEHANDELEN

"""
    for topic in claude_output.get("key_topics", []):
        md += f"- {topic}\n"

    md += """
---

## 🔗 INTERNAL LINKING SUGGESTIES

"""
    for link in claude_output.get("internal_link_suggesties", []):
        md += f"- {link}\n"

    md += f"""
---

## ✅ ACTION ITEMS

- [ ] Schrijf content van minimaal {claude_output.get('target_word_count', 1000)} woorden
- [ ] Gebruik H2 structuur zoals voorgesteld
- [ ] Voeg 2-3 afbeeldingen toe (product of toepassing)
- [ ] Verwerk relevante DEMO merken: {', '.join(claude_output.get('relevante_demo_merken', [])[:3])}
- [ ] Voeg interne links toe naar gerelateerde DEMO categorieën
- [ ] Optimaliseer meta title en description
- [ ] Upload naar CMS en submit via Google Search Console

---

## 📊 VERWACHTE IMPACT

**Concurrent heeft:** {gap.get('word_count', '?')} woorden, {gap.get('h2_count', '?')} H2s
**DEMO target:** {claude_output.get('target_word_count', 1000)}+ woorden, {len(claude_output.get('suggested_h2s', []))}+ H2s

Verwachting bij vergelijkbare of betere content:
- Ranking: Top 5-15 binnen 60-90 dagen
- Traffic: Afhankelijk van zoekvolume keyword

---

**GENERATED BY:** Demo Gap Intelligence v2.0 + GPT-4o (DEMO-context aware)
**BRIEF ID:** #{rank}
"""
    return md


def maak_json_brief(gap: dict, claude_output: dict) -> dict:
    """Combineer gap data en Claude output tot volledig JSON brief."""
    return {
        "gap_id": gap.get("rank"),
        "generated_at": datetime.now().isoformat(),
        "generation_method": "gpt-4o-demo-context",
        "demo_relevantie_score": gap.get("demo_relevantie_score"),
        "original_priority_score": gap.get("priority_score"),
        "competitor_url": gap.get("competitor_url"),
        "competitor_name": gap.get("competitor_name"),
        "competitor_title": gap.get("title"),
        "competitor_word_count": gap.get("word_count"),
        "competitor_h2s": gap.get("h2s_sample"),
        "content_type": gap.get("category"),
        **claude_output
    }


# ==============================================
# BESTANDSNAAM HELPER
# ==============================================

def maak_bestandsnaam(rank: int, titel: str) -> str:
    """Genereer een schone bestandsnaam."""
    clean = re.sub(r"[^\w\s-]", "", titel.lower())
    clean = re.sub(r"[\s_-]+", "_", clean)
    clean = clean[:60].strip("_")
    return f"{rank:03d}_{clean}"


# ==============================================
# MAIN
# ==============================================

def main():
    parser = argparse.ArgumentParser(description="Demo Content Brief Generator v2.0")
    parser.add_argument("--top", type=int, default=10, help="Aantal briefs (default: 10)")
    parser.add_argument("--rank", type=int, help="Genereer alleen brief voor specifieke rank")
    parser.add_argument("--all", action="store_true", help="Genereer alle relevante briefs")
    parser.add_argument("--min-relevantie", type=float, default=40,
                        help="Minimum DEMO relevantie score (default: 40)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Toon gefilterde gaps zonder API calls")
    args = parser.parse_args()

    # Check API key
    if not OPENAI_API_KEY and not args.dry_run:
        print("❌ OPENAI_API_KEY niet gevonden.")
        print("   Zet: setx OPENAI_API_KEY 'sk-...'  (Windows, herstart terminal daarna)")
        print("   Of voeg toe aan script bovenaan bij OPENAI_API_KEY = '...'")
        return

    # Laad gaps
    if not GAPS_FILE.exists():
        print(f"❌ Gaps bestand niet gevonden: {GAPS_FILE}")
        print("   Run eerst: python gap_intelligence.py detect")
        return

    with open(GAPS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    alle_gaps = data.get("gaps", [])
    print(f"\n📂 {len(alle_gaps)} gaps geladen uit {GAPS_FILE}")

    # Filter en sorteer op DEMO relevantie
    relevante_gaps = filter_en_sorteer_gaps(alle_gaps, min_relevantie=args.min_relevantie)
    print(f"✅ {len(relevante_gaps)} gaps na DEMO-relevantie filter (min: {args.min_relevantie})")

    # Selecteer welke gaps te verwerken
    if args.rank:
        te_verwerken = [g for g in relevante_gaps if g.get("rank") == args.rank]
        if not te_verwerken:
            print(f"❌ Rank {args.rank} niet gevonden na filtering.")
            return
    elif args.all:
        te_verwerken = relevante_gaps
    else:
        te_verwerken = relevante_gaps[:args.top]

    print(f"\n📋 Top gaps na filtering (DEMO relevantie score):")
    print(f"{'Rank':>5} | {'DEMO Score':>9} | {'Orig Score':>10} | Titel")
    print("-" * 75)
    for g in relevante_gaps[:15]:
        marker = " ◀" if g in te_verwerken else ""
        print(f"{g.get('rank', '?'):>5} | {g.get('demo_relevantie_score', 0):>9.1f} | "
              f"{g.get('priority_score', 0):>10.1f} | {g.get('title', '')[:45]}{marker}")

    if args.dry_run:
        print(f"\n🔍 Dry run - geen API calls. {len(te_verwerken)} briefs zouden worden gegenereerd.")
        return

    # Maak output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Genereer briefs
    print(f"\n🚀 Genereer {len(te_verwerken)} briefs via Claude API...\n")

    succes = 0
    fouten = 0

    for i, gap in enumerate(te_verwerken, 1):
        rank = gap.get("rank", i)
        titel = gap.get("title", "")
        print(f"[{i}/{len(te_verwerken)}] Rank #{rank}: {titel[:55]}...")

        try:
            # OpenAI API call
            claude_output = genereer_brief_via_openai(gap)

            # Genereer bestandsnaam
            bestandsnaam = maak_bestandsnaam(rank, claude_output.get("suggested_h1", titel))

            # Sla op als markdown
            md_path = OUTPUT_DIR / f"{bestandsnaam}.md"
            md_content = maak_markdown_brief(gap, claude_output)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            # Sla op als JSON
            json_path = OUTPUT_DIR / f"{bestandsnaam}.json"
            json_content = maak_json_brief(gap, claude_output)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_content, f, indent=2, ensure_ascii=False)

            print(f"   ✅ Opgeslagen: {md_path.name}")
            succes += 1

            # Vertraging tussen calls
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
Succesvol: {succes} briefs
Fouten:    {fouten}
Output:    {OUTPUT_DIR}/

Volgende stappen:
  1. Review briefs in {OUTPUT_DIR}/
  2. Pak top 3 voor uitwerking deze week
  3. Herschrijf/pas aan waar nodig
{'='*60}
""")


if __name__ == "__main__":
    main()