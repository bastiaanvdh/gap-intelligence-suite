"""
GSC Gap Detector v1.0
======================
Detecteert content gaps op basis van Google Search Console data.
Geen sitemap-crawling nodig — werkt puur op zoekwoorden waarbij
DEMO impressies heeft maar slecht rankt (positie > 10).

Dit is een betere methode dan sitemap-vergelijking omdat:
- Gebaseerd op echte Google-data, niet op wat concurrent publiceert
- Direct gekoppeld aan zoekvolume en traffic-potentieel
- Werkt voor elke concurrent, ook als sitemap geblokkeerd is

Output: gaps_detected_gsc.json (zelfde formaat als bestaande gaps_detected.json)
Zodat demo_brief_generator.py er direct op aansluit.

Gebruik:
    python gsc_gap_detector.py
    python gsc_gap_detector.py --days 90    # Langere periode
    python gsc_gap_detector.py --min-pos 15 # Ruimere positie-drempel
    python gsc_gap_detector.py --preview    # Toon gaps zonder op te slaan

Vereisten:
    pip install google-auth google-api-python-client
    Service account JSON met Search Console toegang
"""

import json
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ==============================================
# CONFIGURATIE
# ==============================================

SERVICE_ACCOUNT_FILE = r"C:\Path\To\Projects\Pageviews update\Bron\serviceaccount.example.json"
GSC_PROPERTY = "sc-domain:demo-shop.example"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Output — zelfde map als bestaande Gap Intelligence
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "gaps_detected_gsc.json"

# ==============================================
# GAP DETECTIE INSTELLINGEN
# ==============================================

# Zoekwoorden met positie HOGER dan dit = kans (slecht rankend)
MIN_POSITIE_VOOR_GAP = 10

# Minimum impressies — onder dit is het zoekvolume te laag
MIN_IMPRESSIES = 50

# Minimum woordlengte zoekwoord (filter te korte queries)
MIN_WOORDEN = 2

# Dagen terug voor GSC data
DEFAULT_DAYS_BACK = 90

# Maximum aantal gaps in output
MAX_GAPS = 150

# ==============================================
# DEMO RELEVANTIE (zelfde logica als demo_brief_generator)
# ==============================================

RELEVANTIE_BOOST = [
    "lak", "verf", "coating", "primer", "grondverf", "antifouling",
    "epoxy", "plamuur", "beits", "aflak", "muurverf", "vloerlak",
    "kit", "sika", "hempel", "jotun", "epifanes", "international",
    "wijzonol", "nelf", "kwast", "roller", "schuurpapier",
    "verdunning", "oplosmiddel", "afbijtmiddel", "spuitbus",
    "radiatorlak", "metaallak", "blanke lak", "zijdeglans",
    "douglas", "steigerhout", "voorstrijk", "sierpleister",
    "jachtbouw", "scheepvaart", "binnenvaart", "marine",
    "olie", "vet", "smeermiddel", "roestwerend",
]

RELEVANTIE_PENALTY = [
    "trap", "ladder", "steiger", "schuurmachine", "accu gereedschap",
    "washi", "sikkens", "trimetal", "sigma", "little greene",
    "mathys", "boonstoppel", "gamma", "praxis", "hornbach",
    "kleding", "schoenen", "meubels", "electronica",
    "vakantie", "reis", "hotel", "restaurant",
]

# ==============================================
# CONTENT TYPE DETECTIE
# Op basis van zoekwoordpatronen
# ==============================================

def detecteer_content_type(query: str) -> str:
    """Bepaal content type op basis van zoekwoord."""
    q = query.lower()

    informatief = ["wat is", "hoe", "waarom", "verschil", "wanneer",
                   "welke", "tips", "advies", "uitleg", "soorten"]
    transactioneel = ["kopen", "bestellen", "prijs", "goedkoop",
                      "aanbieding", "shop", "bestel"]
    vergelijking = ["vs", "versus", "vergelijk", "verschil tussen",
                    "of ", "beter"]

    for term in vergelijking:
        if term in q:
            return "comparison"
    for term in transactioneel:
        if term in q:
            return "product"
    for term in informatief:
        if term in q:
            return "guide"

    return "other"


def bereken_demo_relevantie(query: str) -> float:
    """Bereken DEMO relevantiescore voor een zoekwoord (0-100)."""
    q = query.lower()
    score = 50.0

    for term in RELEVANTIE_BOOST:
        if term in q:
            score += 8

    for term in RELEVANTIE_PENALTY:
        if term in q:
            score -= 25

    return max(0, min(100, score))


def bereken_prioriteit(impressies: int, positie: float,
                       demo_score: float, clicks: int) -> float:
    """
    Bereken prioriteitsscore voor een gap.

    Factoren:
    - Impressies (zoekvolume proxy): 40%
    - Positie (hoe slechter = hoe groter de kans): 30%
    - DEMO relevantie: 20%
    - CTR potentieel (clicks vs impressies): 10%
    """
    # Impressie score (log-scaled, max bij 10.000+)
    import math
    impressie_score = min(100, 35 * math.log10(impressies + 1))

    # Positie score: positie 11-20 = hoge kans, 50+ = te ver weg
    if positie <= 20:
        positie_score = 100 - (positie - 10) * 5
    elif positie <= 50:
        positie_score = 50 - (positie - 20) * 1.5
    else:
        positie_score = 5
    positie_score = max(0, min(100, positie_score))

    # CTR potentieel
    ctr_score = 0
    if impressies > 0:
        huidige_ctr = clicks / impressies
        # Verwachte CTR op positie 1 is ~32%, op positie 10 is ~2%
        verwachte_ctr_p1 = 0.32
        ctr_gap = verwachte_ctr_p1 - huidige_ctr
        ctr_score = min(100, ctr_gap * 300)

    score = (
        impressie_score * 0.40 +
        positie_score * 0.30 +
        demo_score * 0.20 +
        ctr_score * 0.10
    )

    return round(score, 2)


def genereer_h2_suggesties(query: str, content_type: str) -> list:
    """
    Genereer basis H2-suggesties op basis van zoekwoord en content type.
    Dit zijn placeholders — demo_brief_generator.py overschrijft deze
    met GPT-gegenereerde H2s.
    """
    q = query.lower().strip()

    if content_type == "guide":
        return [
            f"Wat is {q}?",
            f"Waarvoor gebruik je {q}?",
            f"Hoe breng je {q} aan?",
            f"Welke merken {q} biedt DEMO aan?",
            f"Tips voor professioneel gebruik van {q}",
        ]
    elif content_type == "product":
        return [
            f"Waarom kiezen voor professionele {q}?",
            f"Hoe kies je de juiste {q}?",
            f"Technische specificaties van {q}",
            f"Topmerken {q} bij DEMO",
            f"Onderhoud en gebruik van {q}",
        ]
    elif content_type == "comparison":
        return [
            f"Wat zijn de verschillen?",
            f"Wanneer kies je welke optie?",
            f"Technische vergelijking",
            f"Aanbeveling voor professionals",
        ]
    else:
        return [
            f"Wat is {q}?",
            f"Toepassingen van {q}",
            f"Voordelen voor professionals",
            f"DEMO's aanbod van {q}",
        ]


# ==============================================
# GSC DATA OPHALEN
# ==============================================

def haal_gsc_data_op(days_back: int = DEFAULT_DAYS_BACK) -> list:
    """
    Haal zoekwoorddata op uit Google Search Console.
    Returnt lijst met dicts: query, clicks, impressions, ctr, position.
    """
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    print(f"\n{'='*60}")
    print("STAP 1: GSC data ophalen")
    print(f"{'='*60}")
    print(f"Property: {GSC_PROPERTY}")
    print(f"Periode: laatste {days_back} dagen")

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("searchconsole", "v1", credentials=credentials)

    eind_datum = datetime.now().date()
    start_datum = eind_datum - timedelta(days=days_back)

    body = {
        "startDate": str(start_datum),
        "endDate": str(eind_datum),
        "dimensions": ["query"],
        "rowLimit": 25000,
        "dataState": "all",
    }

    print(f"Data ophalen van {start_datum} t/m {eind_datum}...")
    response = service.searchanalytics().query(
        siteUrl=GSC_PROPERTY, body=body
    ).execute()

    rows = []
    for row in response.get("rows", []):
        rows.append({
            "query": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0.0),
            "position": row.get("position", 0.0),
        })

    print(f"✅ {len(rows):,} zoekwoorden opgehaald")
    return rows


# ==============================================
# GAP DETECTIE
# ==============================================

def reinig_query(query: str) -> str:
    """
    Verwijder vervuilde SERP-metadata uit GSC query strings.
    GSC levert soms queries mee met trailing metadata zoals:
    'welke roller voor muurverf,blog,i|t,4,organic,https://...'
    """
    vervuiling_patronen = [
        r',\s*(blog|product|guide|article|organic|sponsored|featured)',
        r',\s*i\|t,',
        r',\s*i,-,',
        r',best\s+converting',
        r',https?://',
    ]
    for patroon in vervuiling_patronen:
        query = re.split(patroon, query, flags=re.IGNORECASE)[0]
    return query.strip()


def detecteer_gaps(gsc_rows: list, min_positie: float,
                   min_impressies: int) -> list:
    """
    Detecteer gaps op basis van GSC data.

    Een 'gap' is een zoekwoord waarbij:
    1. DEMO impressies heeft (het woord is relevant)
    2. De positie slecht is (> min_positie)
    3. Voldoende impressies voor traffic-potentieel
    4. DEMO-relevant genoeg
    """
    print(f"\n{'='*60}")
    print("STAP 2: Gaps detecteren")
    print(f"{'='*60}")
    print(f"Criteria: positie > {min_positie}, impressies >= {min_impressies}")

    gaps = []
    gefilterd = defaultdict(int)

    for row in gsc_rows:
        query = reinig_query(row["query"].strip())
        positie = row["position"]
        impressies = row["impressions"]
        clicks = row["clicks"]

        # Filter: positie moet slecht genoeg zijn
        if positie <= min_positie:
            gefilterd["goede_positie"] += 1
            continue

        # Filter: minimum impressies
        if impressies < min_impressies:
            gefilterd["te_weinig_impressies"] += 1
            continue

        # Filter: minimum woordlengte
        if len(query.split()) < MIN_WOORDEN:
            gefilterd["te_kort"] += 1
            continue

        # Filter: DEMO relevantie
        demo_score = bereken_demo_relevantie(query)
        if demo_score < 35:
            gefilterd["niet_relevant"] += 1
            continue

        # Content type
        content_type = detecteer_content_type(query)

        # Prioriteit score
        prioriteit = bereken_prioriteit(impressies, positie, demo_score, clicks)

        # H2 suggesties (placeholders)
        h2s = genereer_h2_suggesties(query, content_type)

        gaps.append({
            "query": query,
            "clicks": clicks,
            "impressions": impressies,
            "ctr": round(row["ctr"], 4),
            "position": round(positie, 1),
            "demo_relevantie_score": round(demo_score, 1),
            "priority_score": prioriteit,
            "content_type": content_type,
            "h2s_sample": h2s[:4],
            "detected_at": datetime.now().isoformat(),
        })

    # Sorteer op prioriteit
    gaps.sort(key=lambda x: x["priority_score"], reverse=True)

    # Voeg rank toe
    for i, gap in enumerate(gaps, 1):
        gap["rank"] = i

    print(f"\nFilter resultaten:")
    print(f"  Al goed rankend (pos ≤ {min_positie}): {gefilterd['goede_positie']:,}")
    print(f"  Te weinig impressies: {gefilterd['te_weinig_impressies']:,}")
    print(f"  Zoekwoord te kort: {gefilterd['te_kort']:,}")
    print(f"  Niet DEMO-relevant: {gefilterd['niet_relevant']:,}")
    print(f"\n✅ {len(gaps)} gaps gevonden")

    return gaps[:MAX_GAPS]


# ==============================================
# OUTPUT FORMAAT
# Zelfde als gaps_detected.json zodat demo_brief_generator.py
# er direct op aansluit
# ==============================================

def converteer_naar_gap_formaat(gaps: list) -> dict:
    """
    Converteer naar het formaat van gaps_detected.json
    zodat demo_brief_generator.py er direct op werkt.
    """
    geconverteerde_gaps = []

    for gap in gaps:
        query = gap["query"]

        geconverteerde_gaps.append({
            # Standaard gap velden (zelfde als sitemap-gebaseerde gaps)
            "competitor": "GSC",
            "competitor_name": f"Google positie {gap['position']:.0f}",
            "competitor_url": f"https://www.google.nl/search?q={query.replace(' ', '+')}",
            "title": query.capitalize(),
            "category": gap["content_type"],
            "word_count": 800,  # Target — we hebben geen concurrent word count
            "h2_count": 4,
            "h2s_sample": gap["h2s_sample"],
            "detected_at": gap["detected_at"],
            "priority_score": gap["priority_score"],
            "rank": gap["rank"],

            # Extra GSC-specifieke velden
            "gsc_query": query,
            "gsc_clicks": gap["clicks"],
            "gsc_impressions": gap["impressions"],
            "gsc_ctr": gap["ctr"],
            "gsc_position": gap["position"],
            "demo_relevantie_score": gap["demo_relevantie_score"],
            "source": "gsc",
        })

    # Samenvatting
    by_category = defaultdict(int)
    for gap in geconverteerde_gaps:
        by_category[gap["category"]] += 1

    return {
        "detection_date": datetime.now().isoformat(),
        "source": "google_search_console",
        "total_gaps": len(geconverteerde_gaps),
        "gaps": geconverteerde_gaps,
        "gaps_by_category": dict(by_category),
        "summary": {
            "total": len(geconverteerde_gaps),
            "by_category": dict(by_category),
            "by_competitor": {"GSC (slechte posities)": len(geconverteerde_gaps)},
            "avg_impressions": round(
                sum(g["gsc_impressions"] for g in geconverteerde_gaps) /
                max(len(geconverteerde_gaps), 1), 0
            ),
            "avg_position": round(
                sum(g["gsc_position"] for g in geconverteerde_gaps) /
                max(len(geconverteerde_gaps), 1), 1
            ),
        },
    }


# ==============================================
# MAIN
# ==============================================

def main():
    parser = argparse.ArgumentParser(
        description="GSC Gap Detector — vindt content gaps zonder sitemap-crawling"
    )
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS_BACK,
                        help=f"Dagen terug voor GSC data (default: {DEFAULT_DAYS_BACK})")
    parser.add_argument("--min-pos", type=float, default=MIN_POSITIE_VOOR_GAP,
                        help=f"Minimum positie voor gap (default: {MIN_POSITIE_VOOR_GAP})")
    parser.add_argument("--min-impressies", type=int, default=MIN_IMPRESSIES,
                        help=f"Minimum impressies (default: {MIN_IMPRESSIES})")
    parser.add_argument("--preview", action="store_true",
                        help="Toon top 20 gaps zonder op te slaan")
    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║           GSC GAP DETECTOR v1.0                              ║
║           DemoShop.example — Gaps via Search Console                   ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Stap 1: GSC data ophalen
    try:
        gsc_rows = haal_gsc_data_op(days_back=args.days)
    except Exception as e:
        print(f"\n❌ Fout bij ophalen GSC data: {e}")
        print("   Check service account bestand en GSC property URL.")
        return

    # Stap 2: Gaps detecteren
    gaps = detecteer_gaps(
        gsc_rows,
        min_positie=args.min_pos,
        min_impressies=args.min_impressies,
    )

    if not gaps:
        print("\n⚠️  Geen gaps gevonden. Probeer --min-pos hoger of --min-impressies lager.")
        return

    # Preview modus
    if args.preview:
        print(f"\n📋 Top 20 gaps (preview — niet opgeslagen):")
        print(f"{'Rank':>5} | {'Score':>6} | {'Pos':>5} | {'Impr':>6} | {'Type':>10} | Zoekwoord")
        print("-" * 80)
        for gap in gaps[:20]:
            print(
                f"{gap['rank']:>5} | {gap['priority_score']:>6.1f} | "
                f"{gap['gsc_position']:>5.1f} | {gap['gsc_impressions']:>6} | "
                f"{gap['content_type']:>10} | {gap['gsc_query'][:40]}"
            )
        print(f"\nGebruik zonder --preview om op te slaan naar {OUTPUT_FILE}")
        return

    # Stap 3: Converteren en opslaan
    print(f"\n{'='*60}")
    print("STAP 3: Opslaan")
    print(f"{'='*60}")

    output_data = converteer_naar_gap_formaat(gaps)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Opgeslagen: {OUTPUT_FILE}")

    # Samenvatting
    print(f"""
{'='*60}
SAMENVATTING
{'='*60}
Totaal gaps gevonden:  {output_data['total_gaps']}
Gemiddelde positie:    {output_data['summary']['avg_position']}
Gemiddelde impressies: {output_data['summary']['avg_impressions']:.0f}

Per content type:""")

    for cat, count in output_data["gaps_by_category"].items():
        print(f"  {cat:15s}: {count}")

    print(f"""
Top 10 gaps:
{'Rank':>5} | {'Score':>6} | {'Pos':>5} | {'Impr':>6} | Zoekwoord
{'-'*65}""")

    for gap in output_data["gaps"][:10]:
        print(
            f"{gap['rank']:>5} | {gap['priority_score']:>6.1f} | "
            f"{gap['gsc_position']:>5.1f} | {gap['gsc_impressions']:>6} | "
            f"{gap['gsc_query'][:40]}"
        )

    print(f"""
{'='*60}
VOLGENDE STAP
{'='*60}
Gebruik demo_brief_generator.py met dit bestand:

  Pas in demo_brief_generator.py aan:
    GAPS_FILE = Path("data/gaps_detected_gsc.json")

  Dan:
    python demo_brief_generator.py --dry-run
    python demo_brief_generator.py --top 10
{'='*60}
""")


if __name__ == "__main__":
    main()