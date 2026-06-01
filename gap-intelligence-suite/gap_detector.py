"""
Gap Detector
============
Analyseer verschillen tussen concurrent content en DEMO content.
Identificeer opportunities zonder externe tools (DIY Ahrefs).
"""
import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict
import re

from config_gaps import (
    COMPETITORS_FILE, DEMO_SITEMAP_FILE, GAPS_FILE,
    GAP_CONFIG, COMPETITORS, BLACKLIST_TERMS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLMatcher:
    """Match URLs tussen concurrent en DEMO op basis van content similarity"""
    
    @staticmethod
    def extract_slug(url: str) -> str:
        """
        Extract meaningful slug from URL.
        
        Examples:
            https://competitor-a.example/producten/epoxy-coating-2k -> epoxy-coating-2k
            https://demo-shop.example/sika-epoxy-primer-2k -> epoxy-primer-2k
        """
        # Remove domain
        parts = url.split('/')
        # Take last non-empty part
        slug = [p for p in parts if p and p not in ['http:', 'https:']][-1] if parts else ''
        # Remove query params
        slug = slug.split('?')[0]
        # Clean up
        slug = slug.lower().strip()
        return slug
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text voor similarity matching"""
        # Lowercase
        text = text.lower()
        # Remove special chars
        text = re.sub(r'[^\w\s-]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    @staticmethod
    def similarity_score(text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)"""
        text1_norm = URLMatcher.normalize_text(text1)
        text2_norm = URLMatcher.normalize_text(text2)
        return SequenceMatcher(None, text1_norm, text2_norm).ratio()
    
    @staticmethod
    def has_similar_content(comp_page: Dict, demo_urls: List[str], threshold: float = 0.8) -> bool:
        """
        Check of DEMO een vergelijkbare page heeft.
        
        Args:
            comp_page: Competitor page data
            demo_urls: List van DEMO URLs
            threshold: Similarity threshold (0-1)
        
        Returns:
            True als DEMO vergelijkbare content heeft
        """
        comp_title = comp_page.get('title', '')
        comp_slug = URLMatcher.extract_slug(comp_page['url'])
        
        for demo_url in demo_urls:
            demo_slug = URLMatcher.extract_slug(demo_url)
            
            # Check slug similarity
            if URLMatcher.similarity_score(comp_slug, demo_slug) >= threshold:
                return True
            
            # Check title similarity (if available)
            # Note: DEMO urls don't have titles in sitemap, so skip for now
            # We kunnen later DEMO pages ook analyseren als dat nodig is
        
        return False


class GapDetector:
    """Detect content gaps tussen concurrenten en DEMO"""
    
    def __init__(self):
        self.competitors_data = self._load_competitors()
        self.demo_data = self._load_demo()
    
    def _load_competitors(self) -> Dict:
        """Load competitor crawl data"""
        try:
            with open(COMPETITORS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Competitor data niet gevonden: {COMPETITORS_FILE}")
            logger.error("Run eerst: python competitor_crawler.py")
            raise
    
    def _load_demo(self) -> Dict:
        """Load DEMO sitemap data"""
        try:
            with open(DEMO_SITEMAP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"DEMO sitemap niet gevonden: {DEMO_SITEMAP_FILE}")
            logger.error("Run eerst: python competitor_crawler.py")
            raise
    
    def detect_gaps(self) -> Dict:
        """
        Main gap detection logic.
        
        Returns:
            Dict met detected gaps per type
        """
        logger.info(f"\n{'='*60}")
        logger.info("GAP DETECTION STARTING")
        logger.info(f"{'='*60}")
        
        demo_urls = [url_data['url'] for url_data in self.demo_data.get('urls', [])]
        logger.info(f"DEMO URLs in sitemap: {len(demo_urls)}")
        
        all_gaps = []
        
        # Analyseer elke concurrent
        for comp_key, comp_data in self.competitors_data.get('competitors', {}).items():
            logger.info(f"\nAnalyzing gaps vs {comp_data['name']}...")
            
            comp_gaps = self._detect_competitor_gaps(
                comp_data,
                demo_urls,
                comp_key
            )
            
            all_gaps.extend(comp_gaps)
            logger.info(f"  Found {len(comp_gaps)} gaps")
        
        # Score en rank gaps
        logger.info(f"\nScoring {len(all_gaps)} total gaps...")
        scored_gaps = self._score_gaps(all_gaps)
        
        # Group by category
        gaps_by_category = self._group_by_category(scored_gaps)
        
        # Prepare output
        result = {
            'detection_date': datetime.now().isoformat(),
            'total_gaps': len(scored_gaps),
            'gaps': scored_gaps,
            'gaps_by_category': gaps_by_category,
            'summary': self._generate_summary(scored_gaps)
        }
        
        # Save
        with open(GAPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"\n✓ Gaps saved to: {GAPS_FILE}")
        
        return result
    
    def _detect_competitor_gaps(
        self,
        comp_data: Dict,
        demo_urls: List[str],
        comp_key: str
    ) -> List[Dict]:
        """Detect gaps voor één concurrent"""
        gaps = []
        
        analyzed_pages = comp_data.get('analyzed_pages_data', [])
        
        for page in analyzed_pages:
            # Skip als DEMO vergelijkbare content heeft
            if URLMatcher.has_similar_content(
                page,
                demo_urls,
                threshold=GAP_CONFIG['similarity_threshold']
            ):
                continue
            
            # Skip als blacklisted
            if self._is_blacklisted(page):
                continue
            
            # Dit is een gap!
            gap = {
                'competitor': comp_key,
                'competitor_name': comp_data['name'],
                'competitor_url': page['url'],
                'title': page.get('title', ''),
                'category': page.get('category', 'other'),
                'word_count': page.get('word_count', 0),
                'h2_count': len(page.get('h2s', [])),
                'h2s_sample': page.get('h2s', [])[:5],  # First 5 H2s
                'detected_at': datetime.now().isoformat()
            }
            
            gaps.append(gap)
        
        return gaps
    
    def _is_blacklisted(self, page: Dict) -> bool:
        """Check if page bevat blacklisted terms"""
        text_to_check = ' '.join([
            page.get('title', ''),
            page.get('url', ''),
            page.get('meta_description', '')
        ]).lower()
        
        return any(term in text_to_check for term in BLACKLIST_TERMS)
    
    def _score_gaps(self, gaps: List[Dict]) -> List[Dict]:
        """
        Score gaps op priority.
        
        Scoring factors:
        - Competitor priority (CompetitorA > Competitor B > etc)
        - Content type (comparison/guide > product)
        - Content quality (word count, H2 structure)
        """
        weights = GAP_CONFIG['priority_weights']
        
        for gap in gaps:
            score = 0
            
            # Competitor priority
            comp_priority = COMPETITORS[gap['competitor']]['priority']
            # Invert: priority 1 = highest
            comp_score = (10 - comp_priority) / 10
            score += comp_score * weights['competitor_position'] * 100
            
            # Content type bonus
            category = gap['category']
            category_scores = {
                'comparison': 1.0,
                'guide': 0.9,
                'category': 0.7,
                'product': 0.5,
                'blog': 0.6,
                'other': 0.3
            }
            score += category_scores.get(category, 0.3) * weights['demo_relevance'] * 100
            
            # Content quality (word count as proxy)
            word_count = gap.get('word_count', 0)
            if word_count > 0:
                # Normalize: 1000+ words = max score
                quality_score = min(word_count / 1000, 1.0)
                score += quality_score * weights['search_volume'] * 100
            
            gap['priority_score'] = round(score, 2)
        
        # Sort by score (descending)
        gaps.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Add rank
        for i, gap in enumerate(gaps, 1):
            gap['rank'] = i
        
        return gaps
    
    def _group_by_category(self, gaps: List[Dict]) -> Dict:
        """Group gaps by content category"""
        grouped = defaultdict(list)
        
        for gap in gaps:
            category = gap['category']
            grouped[category].append(gap)
        
        return dict(grouped)
    
    def _generate_summary(self, gaps: List[Dict]) -> Dict:
        """Generate summary statistics"""
        if not gaps:
            return {
                'total': 0,
                'by_competitor': {},
                'by_category': {},
                'avg_word_count': 0,
                'top_priority': None
            }
        
        summary = {
            'total': len(gaps),
            'by_competitor': defaultdict(int),
            'by_category': defaultdict(int),
            'avg_word_count': 0,
            'top_priority': gaps[0] if gaps else None
        }
        
        total_words = 0
        for gap in gaps:
            summary['by_competitor'][gap['competitor_name']] += 1
            summary['by_category'][gap['category']] += 1
            total_words += gap.get('word_count', 0)
        
        if gaps:
            summary['avg_word_count'] = round(total_words / len(gaps), 0)
        
        # Convert defaultdicts to regular dicts
        summary['by_competitor'] = dict(summary['by_competitor'])
        summary['by_category'] = dict(summary['by_category'])
        
        return summary


def detect_and_report():
    """Main function: detect gaps en genereer report"""
    detector = GapDetector()
    result = detector.detect_gaps()
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("GAP DETECTION SUMMARY")
    logger.info(f"{'='*60}")
    
    summary = result['summary']
    logger.info(f"Total gaps found: {summary['total']}")
    
    logger.info(f"\nBy competitor:")
    for comp, count in summary['by_competitor'].items():
        logger.info(f"  {comp}: {count}")
    
    logger.info(f"\nBy category:")
    for cat, count in summary['by_category'].items():
        logger.info(f"  {cat}: {count}")
    
    logger.info(f"\nAvg content length: {summary['avg_word_count']} words")
    
    if summary['top_priority']:
        top = summary['top_priority']
        logger.info(f"\nTop priority gap:")
        logger.info(f"  Title: {top['title']}")
        logger.info(f"  Competitor: {top['competitor_name']}")
        logger.info(f"  Category: {top['category']}")
        logger.info(f"  Score: {top['priority_score']}")
    
    logger.info(f"\n{'='*60}")
    logger.info("✓ DETECTION COMPLETE")
    logger.info(f"{'='*60}")
    
    return result


if __name__ == '__main__':
    detect_and_report()
