"""
Gap Intelligence Configuration
===============================
Alle instellingen voor concurrent analysis en gap detection.
"""
from pathlib import Path
import os

# ==============================================
# PATHS
# ==============================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'
BRIEFS_DIR = OUTPUT_DIR / 'content_briefs'

# Maak directories aan als ze niet bestaan
for dir_path in [DATA_DIR, OUTPUT_DIR, BRIEFS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Output files
COMPETITORS_FILE = DATA_DIR / 'competitors.json'
DEMO_SITEMAP_FILE = DATA_DIR / 'demo_sitemap.json'
GAPS_FILE = DATA_DIR / 'gaps_detected.json'
GAP_REPORT_CSV = OUTPUT_DIR / 'gap_report.csv'
DASHBOARD_DATA = OUTPUT_DIR / 'gap_dashboard_data.json'

# ==============================================
# GOOGLE APIS (gebruik bestaande credentials)
# ==============================================
SERVICE_ACCOUNT_FILE = r'C:\Path\To\Credentials\serviceaccount.example.json'
SPREADSHEET_ID = '1tZ893UCaO3UlV6TgzFdU-n0EYw0nJUHfAMq8bTCoFpI'
GSC_PROPERTY_URI = 'sc-domain:demo-shop.example'

# ==============================================
# CONCURRENTEN
# ==============================================
COMPETITORS = {
    'CompetitorA': {
        'name': 'Competitor A',
        'domain': 'competitor-a.example',
        'sitemap_url': 'https://www.competitor-a.example/sitemap_index.xml',
        'sitemap_alternatives': [
            'https://www.competitor-a.example/sitemap_index.xml',
            'https://www.competitor-a.example/sitemap.xml',
            'https://competitor-a.example/sitemap_index.xml',
            'https://competitor-a.example/sitemap.xml'
        ],
        'priority': 1  # 1 = hoogste prioriteit
    },
    'VWW': {
        'name': 'Competitor B',
        'domain': 'competitor-b.example', 
        'sitemap_url': 'https://www.competitor-b.example/sitemap_index.xml',
        'sitemap_alternatives': [
            'https://www.competitor-b.example/sitemap_index.xml',
            'https://www.competitor-b.example/sitemap.xml'
        ],
        'priority': 2
    },
    'SD': {
        'name': 'Competitor C',
        'domain': 'schilderdepot.nl',
        'sitemap_url': 'https://www.schilderdepot.nl/sitemap.xml',
        'sitemap_alternatives': [
            'https://www.schilderdepot.nl/sitemap.xml',
            'https://schilderdepot.nl/sitemap.xml'
        ],
        'priority': 3
    }
}

DEMO_SITEMAP_URL = 'https://demo-shop.example/sitemap_index.xml'  # Try index first
DEMO_SITEMAP_ALTERNATIVES = [
    'https://demo-shop.example/sitemap_index.xml',
    'https://demo-shop.example/sitemap.xml',
    'https://www.demo-shop.example/sitemap_index.xml',
    'https://www.demo-shop.example/sitemap.xml'
]

# ==============================================
# CRAWLER SETTINGS
# ==============================================
CRAWLER_CONFIG = {
    'user_agent': 'Mozilla/5.0 (compatible; DEMOBot/1.0; +https://demo-shop.example)',
    'max_pages_per_site': 5000,  # Limit om niet te veel te crawlen
    'request_delay': 0.5,  # Seconden tussen requests (be nice)
    'timeout': 10,  # Seconden per request
    'max_retries': 3,
    'respect_robots_txt': True
}

# Page categorization patterns (voor content type detection)
PAGE_CATEGORIES = {
    'product': {
        'url_patterns': ['/product/', '/p/', '/shop/'],
        'title_patterns': ['kopen', 'bestel', 'prijs']
    },
    'category': {
        'url_patterns': ['/categorie/', '/c/', '/shop/'],
        'title_patterns': ['overzicht', 'alle', 'collectie']
    },
    'comparison': {
        'url_patterns': ['/vergelijk', '/versus', '/compare'],
        'title_patterns': ['vergelijk', 'versus', 'vs', 'verschillen']
    },
    'guide': {
        'url_patterns': ['/gids/', '/guide/', '/handleiding/'],
        'title_patterns': ['gids', 'guide', 'handleiding', 'tips', 'advies']
    },
    'blog': {
        'url_patterns': ['/blog/', '/artikel/', '/nieuws/'],
        'title_patterns': ['blog', 'artikel', 'nieuws']
    }
}

# ==============================================
# GAP DETECTION SETTINGS
# ==============================================
GAP_CONFIG = {
    # Minimum metrics voor concurrent page om als "opportunity" te tellen
    'min_competitor_position': 10,  # Alleen als concurrent in top 10 rankt
    'min_search_volume': 50,  # Minimum zoekvolume (uit GSC of geschat)
    
    # Content similarity threshold (0-1, hoger = strenger)
    # 0.8 = alleen als 80%+ overlap, zie we het als "DEMO heeft dit al"
    'similarity_threshold': 0.8,
    
    # Priority scoring weights
    'priority_weights': {
        'competitor_position': 0.3,  # Hoe hoger concurrent, hoe belangrijker
        'search_volume': 0.4,  # Volume is koning
        'content_freshness': 0.1,  # Nieuwere concurrent content = hoger prio
        'demo_relevance': 0.2  # Hoe relevant is het voor DEMO assortiment
    }
}

# ==============================================
# CONTENT BRIEF GENERATOR SETTINGS
# ==============================================
BRIEF_CONFIG = {
    # OpenAI API (gebruik bestaande key als je die hebt)
    'use_gpt': True,  # Set False als je geen OpenAI key hebt
    'gpt_model': 'gpt-4o',
    
    # Template settings
    'target_word_count_multiplier': 1.1,  # 10% langer dan concurrent avg
    'min_h2_count': 4,
    'suggested_internal_links': 3,
    
    # Auto-brief generation triggers
    'auto_generate_for_top_n': 20,  # Genereer briefs voor top 20 gaps
}

# ==============================================
# DASHBOARD INTEGRATION
# ==============================================
DASHBOARD_CONFIG = {
    'dashboard_html_path': r'C:\Path\To\Projects\Pageviews update\dashboard_v3.html',
    'dashboard_data_path': r'C:\Path\To\Projects\Pageviews update\dashboard_data.json',
    'top_gaps_to_show': 20
}

# ==============================================
# LOGGING
# ==============================================
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'gap_intelligence.log'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR

# ==============================================
# BLACKLIST (filter noise)
# ==============================================
BLACKLIST_TERMS = [
    # Gaming spam (zoals in ML Keywords)
    'assetto corsa', 'competizione', 'demo game', 
    'ps4', 'ps5', 'xbox', 'nintendo',
    
    # Consumer brands (DEMO is professional)
    'gamma', 'praxis', 'karwei', 'hornbach',
    
    # Irrelevant categorieën
    'kleding', 'schoenen', 'meubels', 'electronica'
]

# Concurrent brands to exclude (niet relevant voor DEMO)
EXCLUDE_COMPETITOR_BRANDS = [
    'demo paint en verf',  # Te generiek/consumer
]

# ==============================================
# VALIDATION
# ==============================================
def validate_config():
    """Check of configuratie compleet en geldig is"""
    errors = []
    
    # Check service account
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        errors.append(f"Service account file niet gevonden: {SERVICE_ACCOUNT_FILE}")
    
    # Check competitors
    if not COMPETITORS:
        errors.append("Geen concurrenten geconfigureerd")
    
    # Check OpenAI key als GPT enabled
    if BRIEF_CONFIG['use_gpt']:
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            errors.append(
                "BRIEF_CONFIG['use_gpt'] is True maar OPENAI_API_KEY environment variable niet gevonden. "
                "Set deze via: os.environ['OPENAI_API_KEY'] = 'sk-...' of disable GPT briefs."
            )
    
    if errors:
        raise ValueError("Configuratie fouten:\n" + "\n".join(f"- {e}" for e in errors))
    
    return True


# ==============================================
# COLOR SCHEME (DEMO huisstijl - consistent met rest)
# ==============================================
class Colors:
    LIGHTBLUE = "#1875ad"
    DARKBLUE = "#103a5d"
    GREYBLUE = "#dde3ed"
    RED = "#e30617"
    ORANGE = "#e67e22"
    GREEN = "#10b981"
    YELLOW = "#f59e0b"
