"""
Gap Intelligence Configuration - UPDATED
=========================================
Alleen werkende sitemaps enabled.
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

for dir_path in [DATA_DIR, OUTPUT_DIR, BRIEFS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

COMPETITORS_FILE = DATA_DIR / 'competitors.json'
DEMO_SITEMAP_FILE = DATA_DIR / 'demo_sitemap.json'
GAPS_FILE = DATA_DIR / 'gaps_detected.json'
GAP_REPORT_CSV = OUTPUT_DIR / 'gap_report.csv'
DASHBOARD_DATA = OUTPUT_DIR / 'gap_dashboard_data.json'

# ==============================================
# GOOGLE APIS
# ==============================================
SERVICE_ACCOUNT_FILE = r'C:\Path\To\Credentials\serviceaccount.example.json'
SPREADSHEET_ID = '1tZ893UCaO3UlV6TgzFdU-n0EYw0nJUHfAMq8bTCoFpI'
GSC_PROPERTY_URI = 'sc-domain:demo-shop.example'

# ==============================================
# CONCURRENTEN - ALLEEN WERKENDE!
# ==============================================
COMPETITORS = {
    'VWW': {
        'name': 'Competitor B',
        'domain': 'competitor-b.example', 
        'sitemap_url': 'https://www.competitor-b.example/sitemap.xml',
        'sitemap_alternatives': [
            'https://www.competitor-b.example/sitemap.xml'
        ],
        'priority': 1  # Nu de enige, dus prio 1
    }
    # CompetitorA en Competitor C uitgeschakeld - geen werkende sitemaps
    # Kun je later toevoegen als je hun URLs handmatig verzamelt
}

# DEMO Sitemap URL (uit Google Search Console)
DEMO_SITEMAP_URL = 'https://demo-shop.example/sitemap/44f96847-04f7687a8a323-2e7235834e5/sitemap.xml'

# Fallback: gebruik GSC API als sitemap faalt
USE_GSC_FOR_DEMO_URLS = False  # Set to True als sitemap niet werkt
DEMO_GSC_MAX_ROWS = 5000  # Max aantal URLs uit GSC

# ==============================================
# CRAWLER SETTINGS
# ==============================================
CRAWLER_CONFIG = {
    'user_agent': 'Mozilla/5.0 (compatible; DEMOBot/1.0; +https://demo-shop.example)',
    'max_pages_per_site': 5000,
    'request_delay': 0.5,
    'timeout': 10,
    'max_retries': 3,
    'respect_robots_txt': True
}

PAGE_CATEGORIES = {
    'product': {
        'url_patterns': ['/product/', '/p/', '/shop/', '/artikel/'],
        'title_patterns': ['kopen', 'bestel', 'prijs']
    },
    'category': {
        'url_patterns': ['/categorie/', '/c/', '/shop/', '/producten/'],
        'title_patterns': ['overzicht', 'alle', 'collectie']
    },
    'comparison': {
        'url_patterns': ['/vergelijk', '/versus', '/compare'],
        'title_patterns': ['vergelijk', 'versus', 'vs', 'verschillen']
    },
    'guide': {
        'url_patterns': ['/gids/', '/guide/', '/handleiding/', '/advies/'],
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
    'min_competitor_position': 10,
    'min_search_volume': 50,
    'similarity_threshold': 0.7,  # Verlaagd naar 0.7 (was 0.8) - meer gaps
    
    'priority_weights': {
        'competitor_position': 0.3,
        'search_volume': 0.4,
        'content_freshness': 0.1,
        'demo_relevance': 0.2
    }
}

# ==============================================
# CONTENT BRIEF GENERATOR SETTINGS
# ==============================================
BRIEF_CONFIG = {
    'use_gpt': False,  # Set to True als je OpenAI key hebt
    'gpt_model': 'gpt-4o',
    
    'target_word_count_multiplier': 1.1,
    'min_h2_count': 4,
    'suggested_internal_links': 3,
    
    'auto_generate_for_top_n': 20,
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
LOG_LEVEL = 'INFO'

# ==============================================
# BLACKLIST
# ==============================================
BLACKLIST_TERMS = [
    'assetto corsa', 'competizione', 'demo game', 
    'ps4', 'ps5', 'xbox', 'nintendo',
    'gamma', 'praxis', 'karwei', 'hornbach',
    'kleding', 'schoenen', 'meubels', 'electronica'
]

EXCLUDE_COMPETITOR_BRANDS = [
    'demo paint en verf',
]

# ==============================================
# VALIDATION
# ==============================================
def validate_config():
    """Check of configuratie compleet en geldig is"""
    errors = []
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        errors.append(f"Service account file niet gevonden: {SERVICE_ACCOUNT_FILE}")
    
    if not COMPETITORS:
        errors.append("Geen concurrenten geconfigureerd")
    
    if BRIEF_CONFIG['use_gpt']:
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            errors.append(
                "BRIEF_CONFIG['use_gpt'] is True maar OPENAI_API_KEY niet gevonden. "
                "Disable GPT of set API key."
            )
    
    if errors:
        raise ValueError("Configuratie fouten:\n" + "\n".join(f"- {e}" for e in errors))
    
    return True

# ==============================================
# COLORS (DEMO huisstijl)
# ==============================================
class Colors:
    LIGHTBLUE = "#1875ad"
    DARKBLUE = "#103a5d"
    GREYBLUE = "#dde3ed"
    RED = "#e30617"
    ORANGE = "#e67e22"
    GREEN = "#10b981"
    YELLOW = "#f59e0b"
