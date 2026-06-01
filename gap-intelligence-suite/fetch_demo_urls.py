"""
DEMO URL Fetcher via Google Search Console
==========================================
Haal DEMO URLs uit GSC API (geen sitemap nodig!)
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from google.oauth2 import service_account
from googleapiclient.discovery import build

from config_gaps_v2 import (
    SERVICE_ACCOUNT_FILE, GSC_PROPERTY_URI, 
    DEMO_SITEMAP_FILE, DEMO_GSC_MAX_ROWS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def fetch_demo_urls_from_gsc() -> List[str]:
    """
    Haal DEMO URLs uit Google Search Console.
    
    Returns:
        List van DEMO URLs
    """
    logger.info("\n" + "="*60)
    logger.info("FETCHING DEMO URLs FROM GOOGLE SEARCH CONSOLE")
    logger.info("="*60)
    
    # Authenticate
    logger.info("Authenticating with Google Search Console...")
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    service = build('searchconsole', 'v1', credentials=credentials)
    
    # Query laatste 3 maanden (URLs die traffic krijgen)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    logger.info(f"Fetching URLs from {start_date} to {end_date}")
    
    all_urls = []
    start_row = 0
    batch_size = 25000  # GSC max
    
    while True:
        request = {
            'startDate': str(start_date),
            'endDate': str(end_date),
            'dimensions': ['page'],
            'rowLimit': batch_size,
            'startRow': start_row
        }
        
        logger.info(f"  Fetching batch (start_row: {start_row})...")
        response = service.searchanalytics().query(
            siteUrl=GSC_PROPERTY_URI,
            body=request
        ).execute()
        
        rows = response.get('rows', [])
        if not rows:
            break
        
        for row in rows:
            url = row['keys'][0]
            all_urls.append(url)
        
        logger.info(f"    Got {len(rows)} URLs (total: {len(all_urls)})")
        
        # Check if we hit the limit
        if len(all_urls) >= DEMO_GSC_MAX_ROWS:
            logger.warning(f"  Reached limit of {DEMO_GSC_MAX_ROWS} URLs")
            break
        
        # Check if there are more results
        if len(rows) < batch_size:
            break
        
        start_row += batch_size
    
    logger.info(f"\n✓ Fetched {len(all_urls)} DEMO URLs from GSC")
    
    # Convert to sitemap-like format (for compatibility)
    sitemap_data = []
    for url in all_urls:
        sitemap_data.append({
            'url': url,
            'lastmod': str(end_date),
            'priority': None,
            'changefreq': None
        })
    
    # Save
    result = {
        'domain': 'demo-shop.example',
        'source': 'google_search_console',
        'crawled_at': datetime.now().isoformat(),
        'date_range': f"{start_date} to {end_date}",
        'total_urls': len(sitemap_data),
        'urls': sitemap_data
    }
    
    with open(DEMO_SITEMAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Saved to: {DEMO_SITEMAP_FILE}")
    
    return all_urls


if __name__ == '__main__':
    urls = fetch_demo_urls_from_gsc()
    print(f"\nFetched {len(urls)} URLs")
    print("\nFirst 10 URLs:")
    for url in urls[:10]:
        print(f"  - {url}")
