"""
Competitor Content Crawler
===========================
Crawl concurrent sitemaps en websites, extract content structure.
Dit is onze DIY alternatief voor Ahrefs/SEMrush.
"""
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional
import json
import time
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import re

from config_gaps import (
    COMPETITORS, DEMO_SITEMAP_URL, COMPETITORS_FILE, DEMO_SITEMAP_FILE,
    CRAWLER_CONFIG, PAGE_CATEGORIES, BLACKLIST_TERMS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SitemapCrawler:
    """Crawl sitemaps en extract URL + metadata"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': CRAWLER_CONFIG['user_agent']
        })
    
    def fetch_sitemap(self, sitemap_url: str) -> List[Dict]:
        """
        Haal sitemap op en parse URLs.
        
        Returns:
            List van dicts met keys: url, lastmod, priority, changefreq
        """
        logger.info(f"Fetching sitemap: {sitemap_url}")
        
        try:
            response = self.session.get(
                sitemap_url,
                timeout=CRAWLER_CONFIG['timeout']
            )
            response.raise_for_status()
            
            content = response.content
            
            # Check if gzipped (common for sitemaps)
            if sitemap_url.endswith('.gz') or content[:2] == b'\x1f\x8b':
                import gzip
                try:
                    content = gzip.decompress(content)
                    logger.info("  Decompressed gzipped sitemap")
                except Exception as e:
                    logger.warning(f"  Failed to decompress: {e}")
                    # Try without decompression
            
            # Parse XML with error recovery
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.warning(f"  XML parse error: {e}")
                # Try to fix common issues
                content_str = content.decode('utf-8', errors='ignore')
                # Remove problematic characters
                content_str = content_str.replace('&', '&amp;')
                try:
                    root = ET.fromstring(content_str.encode('utf-8'))
                except:
                    logger.error(f"  Could not parse sitemap even after cleanup")
                    return []
            
            # Handle sitemap index (sitemap van sitemaps)
            if 'sitemapindex' in root.tag:
                logger.info("  Sitemap index detected, fetching child sitemaps...")
                return self._parse_sitemap_index(root)
            else:
                return self._parse_sitemap(root)
                
        except Exception as e:
            logger.error(f"Error fetching sitemap {sitemap_url}: {e}")
            return []
    
    def _parse_sitemap_index(self, root: ET.Element) -> List[Dict]:
        """Parse sitemap index en fetch alle child sitemaps"""
        all_urls = []
        
        # Extract namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for sitemap in root.findall('ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace)
            if loc is not None:
                child_urls = self.fetch_sitemap(loc.text)
                all_urls.extend(child_urls)
                time.sleep(CRAWLER_CONFIG['request_delay'])
        
        return all_urls
    
    def _parse_sitemap(self, root: ET.Element) -> List[Dict]:
        """Parse reguliere sitemap"""
        urls = []
        
        # Extract namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for url_elem in root.findall('ns:url', namespace):
            loc = url_elem.find('ns:loc', namespace)
            if loc is None:
                continue
            
            url_data = {
                'url': loc.text,
                'lastmod': None,
                'priority': None,
                'changefreq': None
            }
            
            # Optional fields
            lastmod = url_elem.find('ns:lastmod', namespace)
            if lastmod is not None:
                url_data['lastmod'] = lastmod.text
            
            priority = url_elem.find('ns:priority', namespace)
            if priority is not None:
                url_data['priority'] = float(priority.text)
            
            changefreq = url_elem.find('ns:changefreq', namespace)
            if changefreq is not None:
                url_data['changefreq'] = changefreq.text
            
            urls.append(url_data)
        
        logger.info(f"  Found {len(urls)} URLs")
        return urls


class ContentAnalyzer:
    """Analyseer page content en extract metadata"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': CRAWLER_CONFIG['user_agent']
        })
    
    def analyze_page(self, url: str) -> Optional[Dict]:
        """
        Fetch en analyseer een single page.
        
        Returns:
            Dict met: title, description, h1, h2s, word_count, category
        """
        try:
            response = self.session.get(url, timeout=CRAWLER_CONFIG['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            data = {
                'url': url,
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'h1': self._extract_h1(soup),
                'h2s': self._extract_h2s(soup),
                'word_count': self._count_words(soup),
                'category': self._categorize_page(url, soup),
                'crawled_at': datetime.now().isoformat()
            }
            
            return data
            
        except Exception as e:
            logger.warning(f"Could not analyze {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else ''
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta = soup.find('meta', {'name': 'description'})
        return meta.get('content', '') if meta else ''
    
    def _extract_h1(self, soup: BeautifulSoup) -> str:
        """Extract H1"""
        h1 = soup.find('h1')
        return h1.get_text(strip=True) if h1 else ''
    
    def _extract_h2s(self, soup: BeautifulSoup) -> List[str]:
        """Extract all H2s"""
        return [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
    
    def _count_words(self, soup: BeautifulSoup) -> int:
        """Count words in main content"""
        # Remove script/style tags
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        text = soup.get_text()
        words = re.findall(r'\w+', text)
        return len(words)
    
    def _categorize_page(self, url: str, soup: BeautifulSoup) -> str:
        """
        Categorize page type (product, category, guide, etc.)
        """
        title = self._extract_title(soup).lower()
        
        for category, patterns in PAGE_CATEGORIES.items():
            # Check URL patterns
            if any(pattern in url.lower() for pattern in patterns['url_patterns']):
                return category
            
            # Check title patterns
            if any(pattern in title for pattern in patterns['title_patterns']):
                return category
        
        return 'other'


class CompetitorCrawler:
    """Main crawler orchestrator"""
    
    def __init__(self):
        self.sitemap_crawler = SitemapCrawler()
        self.content_analyzer = ContentAnalyzer()
    
    def crawl_competitor(self, competitor_key: str) -> Dict:
        """
        Crawl een concurrent volledig.
        
        Returns:
            Dict met alle pages + metadata
        """
        comp = COMPETITORS[competitor_key]
        logger.info(f"\n{'='*60}")
        logger.info(f"Crawling competitor: {comp['name']} ({comp['domain']})")
        logger.info(f"{'='*60}")
        
        # Step 1: Fetch sitemap - try alternatives
        sitemap_urls = []
        
        alternatives = comp.get('sitemap_alternatives', [comp['sitemap_url']])
        for url in alternatives:
            logger.info(f"Trying: {url}")
            urls = self.sitemap_crawler.fetch_sitemap(url)
            if urls:
                sitemap_urls = urls
                logger.info(f"✓ Success! Found {len(urls)} URLs")
                break
            time.sleep(1)  # Be nice between retries
        
        if not sitemap_urls:
            logger.warning(f"Could not fetch sitemap for {comp['name']}")
            logger.warning("All alternatives failed:")
            for url in alternatives:
                logger.warning(f"  - {url}")
        
        # Filter blacklisted URLs
        sitemap_urls = self._filter_blacklist(sitemap_urls)
        
        # Limit if too many
        if len(sitemap_urls) > CRAWLER_CONFIG['max_pages_per_site']:
            logger.warning(f"  Limiting to {CRAWLER_CONFIG['max_pages_per_site']} pages")
            sitemap_urls = sitemap_urls[:CRAWLER_CONFIG['max_pages_per_site']]
        
        # Step 2: Analyze subset of pages (not all - te veel!)
        # We analyseren alleen de "belangrijke" pages (hoge priority of recent)
        pages_to_analyze = self._select_pages_to_analyze(sitemap_urls, max_pages=100)
        
        logger.info(f"  Analyzing {len(pages_to_analyze)} high-priority pages...")
        
        analyzed_pages = []
        for i, page_url in enumerate(pages_to_analyze, 1):
            if i % 10 == 0:
                logger.info(f"    Progress: {i}/{len(pages_to_analyze)}")
            
            page_data = self.content_analyzer.analyze_page(page_url)
            if page_data:
                analyzed_pages.append(page_data)
            
            time.sleep(CRAWLER_CONFIG['request_delay'])
        
        result = {
            'competitor': competitor_key,
            'name': comp['name'],
            'domain': comp['domain'],
            'crawled_at': datetime.now().isoformat(),
            'total_urls': len(sitemap_urls),
            'analyzed_pages': len(analyzed_pages),
            'sitemap_urls': sitemap_urls,  # Alle URLs (zonder detail)
            'analyzed_pages_data': analyzed_pages  # Subset met detail
        }
        
        logger.info(f"✓ Completed: {len(analyzed_pages)} pages analyzed")
        return result
    
    def crawl_demo_site(self) -> Dict:
        """Crawl DemoShop.example sitemap (onze eigen site)"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Crawling DemoShop.example")
        logger.info(f"{'='*60}")
        
        from config_gaps import DEMO_SITEMAP_ALTERNATIVES
        
        sitemap_urls = []
        
        # Try alternative URLs
        for url in DEMO_SITEMAP_ALTERNATIVES:
            logger.info(f"Trying: {url}")
            urls = self.sitemap_crawler.fetch_sitemap(url)
            if urls:
                sitemap_urls = urls
                logger.info(f"✓ Success! Found {len(urls)} URLs")
                break
        
        if not sitemap_urls:
            logger.warning("Could not fetch DEMO sitemap from any known URL")
            logger.warning("Alternatives tried:")
            for url in DEMO_SITEMAP_ALTERNATIVES:
                logger.warning(f"  - {url}")
        
        result = {
            'domain': 'demo-shop.example',
            'crawled_at': datetime.now().isoformat(),
            'total_urls': len(sitemap_urls),
            'urls': sitemap_urls
        }
        
        logger.info(f"✓ Found {len(sitemap_urls)} DEMO pages")
        return result
    
    def _filter_blacklist(self, urls: List[Dict]) -> List[Dict]:
        """Filter URLs die blacklisted terms bevatten"""
        filtered = []
        for url_data in urls:
            url_lower = url_data['url'].lower()
            if not any(term in url_lower for term in BLACKLIST_TERMS):
                filtered.append(url_data)
        
        removed = len(urls) - len(filtered)
        if removed > 0:
            logger.info(f"  Filtered {removed} blacklisted URLs")
        
        return filtered
    
    def _select_pages_to_analyze(self, sitemap_urls: List[Dict], max_pages: int = 100) -> List[str]:
        """
        Selecteer de belangrijkste pages om te analyseren.
        Prioriteer op: priority score, recency, URL patterns
        """
        # Sort by priority (descending) en lastmod (newest first)
        scored = []
        for url_data in sitemap_urls:
            score = 0
            
            # Priority from sitemap
            if url_data.get('priority'):
                score += url_data['priority'] * 100
            
            # Recency (pages met lastmod krijgen bonus)
            if url_data.get('lastmod'):
                try:
                    # Parse date en geef bonus voor recente pages
                    lastmod_date = datetime.fromisoformat(url_data['lastmod'].replace('Z', '+00:00'))
                    days_old = (datetime.now() - lastmod_date.replace(tzinfo=None)).days
                    recency_score = max(0, 100 - days_old / 10)  # Max 100, min 0
                    score += recency_score
                except:
                    pass
            
            # URL pattern bonuses (favor certain page types)
            url = url_data['url'].lower()
            if '/product/' in url or '/p/' in url:
                score += 50
            elif '/categorie/' in url or '/c/' in url:
                score += 30
            elif '/vergelijk' in url or '/gids' in url:
                score += 40
            
            scored.append((score, url_data['url']))
        
        # Sort by score (descending) en take top N
        scored.sort(reverse=True, key=lambda x: x[0])
        selected = [url for score, url in scored[:max_pages]]
        
        return selected


def crawl_all_competitors() -> Dict:
    """Main function: crawl alle concurrenten + DEMO"""
    crawler = CompetitorCrawler()
    
    results = {
        'crawl_date': datetime.now().isoformat(),
        'competitors': {},
        'demo': None
    }
    
    # Crawl competitors
    for comp_key in COMPETITORS.keys():
        try:
            comp_data = crawler.crawl_competitor(comp_key)
            results['competitors'][comp_key] = comp_data
            
            # Save intermediate result (in case of crash)
            with open(COMPETITORS_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Failed to crawl {comp_key}: {e}")
    
    # Crawl DEMO
    try:
        demo_data = crawler.crawl_demo_site()
        results['demo'] = demo_data
    except Exception as e:
        logger.error(f"Failed to crawl DEMO: {e}")
    
    # Save final results
    logger.info(f"\n{'='*60}")
    logger.info("SAVING RESULTS")
    logger.info(f"{'='*60}")
    
    with open(COMPETITORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Saved to: {COMPETITORS_FILE}")
    
    # Save DEMO sitemap separately
    if results['demo']:
        with open(DEMO_SITEMAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(results['demo'], f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved DEMO sitemap to: {DEMO_SITEMAP_FILE}")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("CRAWL SUMMARY")
    logger.info(f"{'='*60}")
    for comp_key, comp_data in results['competitors'].items():
        logger.info(
            f"  {comp_data['name']}: "
            f"{comp_data['total_urls']} URLs, "
            f"{comp_data['analyzed_pages']} analyzed"
        )
    if results['demo']:
        logger.info(f"  DemoShop.example: {results['demo']['total_urls']} URLs")
    
    return results


if __name__ == '__main__':
    crawl_all_competitors()
