"""
Gap Analysis v3 - With correct DEMO sitemap
===========================================
"""
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           GAP INTELLIGENCE v1.1                              ║
║           Competitor B vs DEMO                               ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    try:
        from competitor_crawler import CompetitorCrawler, SitemapCrawler
        from config_gaps_v2 import COMPETITORS_FILE, DEMO_SITEMAP_FILE, DEMO_SITEMAP_URL
        import json
        
        crawler = CompetitorCrawler()
        
        # Step 1: Fetch DEMO sitemap
        logger.info("STEP 1: Crawling DemoShop.example sitemap")
        logger.info("="*60)
        logger.info(f"URL: {DEMO_SITEMAP_URL}")
        
        sitemap_crawler = SitemapCrawler()
        demo_urls = sitemap_crawler.fetch_sitemap(DEMO_SITEMAP_URL)
        
        if not demo_urls:
            logger.error("❌ Could not fetch DEMO sitemap!")
            logger.info("Falling back to GSC...")
            from fetch_demo_urls import fetch_demo_urls_from_gsc
            demo_urls_list = fetch_demo_urls_from_gsc()
            logger.info(f"✓ Got {len(demo_urls_list)} URLs from GSC")
        else:
            logger.info(f"✓ Got {len(demo_urls)} URLs from sitemap")
            
            # Save DEMO data
            demo_data = {
                'domain': 'demo-shop.example',
                'source': 'sitemap',
                'crawled_at': datetime.now().isoformat(),
                'total_urls': len(demo_urls),
                'urls': demo_urls
            }
            
            with open(DEMO_SITEMAP_FILE, 'w', encoding='utf-8') as f:
                json.dump(demo_data, f, indent=2, ensure_ascii=False)
        
        # Step 2: Crawl Competitor B
        logger.info("\nSTEP 2: Crawling Competitor B")
        logger.info("="*60)
        
        vww_data = crawler.crawl_competitor('VWW')
        logger.info(f"✓ Got {vww_data['total_urls']} URLs, analyzed {vww_data['analyzed_pages']}")
        
        # Save competitor data
        results = {
            'crawl_date': datetime.now().isoformat(),
            'competitors': {'VWW': vww_data},
            'demo': None  # Already saved above
        }
        
        with open(COMPETITORS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Step 3: Detect gaps
        logger.info("\nSTEP 3: Detecting content gaps")
        logger.info("="*60)
        
        from gap_detector import detect_and_report
        gaps_data = detect_and_report()
        
        total_gaps = gaps_data['summary']['total']
        logger.info(f"✓ Found {total_gaps} gaps")
        
        # Step 4: Generate briefs
        if total_gaps > 0:
            logger.info("\nSTEP 4: Generating content briefs")
            logger.info("="*60)
            
            from brief_generator import BriefGenerator
            generator = BriefGenerator()
            
            # Generate top 10 (of minder als er minder gaps zijn)
            num_briefs = min(10, total_gaps)
            generator.generate_all_briefs(top_n=num_briefs)
            
            print(f"""
{'='*60}
✅ SUCCESS!
{'='*60}

Results:
  DEMO URLs: {len(demo_urls)}
  Competitor B URLs: {vww_data['total_urls']}
  Content gaps found: {total_gaps}
  Briefs generated: {num_briefs}

📂 Output:
  Briefs: output/content_briefs/
  Data: data/gaps_detected.json
  
📊 Gap summary:
  By competitor: {gaps_data['summary']['by_competitor']}
  By category: {gaps_data['summary']['by_category']}

Next steps:
  1. cd output/content_briefs
  2. Review top {min(5, num_briefs)} briefs
  3. Pick 1-3 to execute this week

{'='*60}
""")
        else:
            print(f"""
{'='*60}
⚠️  NO GAPS FOUND
{'='*60}

This could mean:
  - DEMO already has all content that Competitor B has
  - Similarity threshold too high (currently 0.7)
  - Different product focus between sites

Try:
  1. Lower similarity in config_gaps_v2.py (0.7 → 0.5)
  2. Add more competitors
  3. Check data/competitors.json for crawl results

{'='*60}
""")
        
    except Exception as e:
        logger.error(f"\n❌ Failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
