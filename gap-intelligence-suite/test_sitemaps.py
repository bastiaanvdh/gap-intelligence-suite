"""
Sitemap Tester - Debug tool
============================
Test sitemap URLs om te zien welke werken.
"""
import requests
from competitor_crawler import SitemapCrawler

def test_sitemap(url):
    """Test een sitemap URL"""
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print('='*60)
    
    # Try direct request first
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        # Show first 200 chars
        content = response.content[:200]
        print(f"\nFirst 200 bytes:")
        print(content)
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return
    
    # Now try with crawler
    print(f"\n--- Testing with SitemapCrawler ---")
    crawler = SitemapCrawler()
    urls = crawler.fetch_sitemap(url)
    print(f"✓ Extracted {len(urls)} URLs")
    
    if urls:
        print(f"\nFirst 3 URLs:")
        for url_data in urls[:3]:
            print(f"  - {url_data.get('url', 'N/A')}")


if __name__ == '__main__':
    # Test DEMO first
    test_sitemap('https://demo-shop.example/sitemap_index.xml')
    test_sitemap('https://www.demo-shop.example/sitemap_index.xml')
    test_sitemap('https://demo-shop.example/sitemap.xml')
    
    # Test competitors
    test_sitemap('https://www.competitor-a.example/sitemap_index.xml')
    test_sitemap('https://www.competitor-b.example/sitemap.xml')
