"""
Content Brief Generator
========================
Genereer actionable content briefs voor gedetecteerde gaps.
Gebruikt GPT-4 (optioneel) of template-based generation.
"""
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import os

from config_gaps import (
    GAPS_FILE, BRIEFS_DIR, BRIEF_CONFIG,
    DEMO_SITEMAP_FILE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI import (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not installed. Briefs will be template-based only.")


class BriefGenerator:
    """Generate content briefs from gaps"""
    
    def __init__(self):
        self.gaps_data = self._load_gaps()
        self.use_gpt = BRIEF_CONFIG['use_gpt'] and OPENAI_AVAILABLE
        
        if self.use_gpt:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                logger.warning("OPENAI_API_KEY not found. Falling back to template-based briefs.")
                self.use_gpt = False
    
    def _load_gaps(self) -> Dict:
        """Load detected gaps"""
        try:
            with open(GAPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Gaps file niet gevonden: {GAPS_FILE}")
            logger.error("Run eerst: python gap_detector.py")
            raise
    
    def generate_all_briefs(self, top_n: Optional[int] = None):
        """
        Genereer briefs voor top N gaps.
        
        Args:
            top_n: Aantal briefs om te genereren (None = use config default)
        """
        if top_n is None:
            top_n = BRIEF_CONFIG['auto_generate_for_top_n']
        
        gaps = self.gaps_data.get('gaps', [])
        gaps_to_brief = gaps[:top_n]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"GENERATING BRIEFS FOR TOP {len(gaps_to_brief)} GAPS")
        logger.info(f"{'='*60}")
        
        briefs_generated = 0
        
        for i, gap in enumerate(gaps_to_brief, 1):
            logger.info(f"\n[{i}/{len(gaps_to_brief)}] Generating brief for: {gap['title']}")
            
            try:
                brief = self.generate_brief(gap)
                self._save_brief(brief, gap)
                briefs_generated += 1
                logger.info(f"  ✓ Brief saved")
            except Exception as e:
                logger.error(f"  ✗ Failed to generate brief: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ Generated {briefs_generated}/{len(gaps_to_brief)} briefs")
        logger.info(f"✓ Saved to: {BRIEFS_DIR}")
        logger.info(f"{'='*60}")
    
    def generate_brief(self, gap: Dict) -> Dict:
        """Generate a single content brief"""
        
        if self.use_gpt:
            return self._generate_gpt_brief(gap)
        else:
            return self._generate_template_brief(gap)
    
    def _generate_template_brief(self, gap: Dict) -> Dict:
        """Generate brief using templates (no GPT)"""
        
        # Calculate target metrics
        target_word_count = int(
            gap.get('word_count', 800) * 
            BRIEF_CONFIG['target_word_count_multiplier']
        )
        
        # Suggested H2s based on competitor
        suggested_h2s = gap.get('h2s_sample', [])
        if len(suggested_h2s) < BRIEF_CONFIG['min_h2_count']:
            # Add generic H2s
            suggested_h2s.extend([
                "Wat is het?",
                "Voordelen",
                "Toepassingen",
                "Tips & Advies"
            ])
        
        # Find related DEMO products (simple keyword matching)
        related_products = self._find_related_demo_content(gap)
        
        brief = {
            'gap_id': gap.get('rank', 0),
            'title': gap['title'],
            'competitor_url': gap['competitor_url'],
            'competitor_name': gap['competitor_name'],
            'content_type': gap['category'],
            'priority_score': gap.get('priority_score', 0),
            
            # Target specs
            'target_word_count': target_word_count,
            'target_h2_count': max(len(suggested_h2s), BRIEF_CONFIG['min_h2_count']),
            
            # Content structure
            'suggested_h1': self._generate_h1(gap),
            'suggested_h2s': suggested_h2s[:10],  # Max 10
            'suggested_meta_title': self._generate_meta_title(gap),
            'suggested_meta_description': self._generate_meta_description(gap),
            
            # Internal linking
            'suggested_internal_links': related_products[:BRIEF_CONFIG['suggested_internal_links']],
            
            # Action items
            'action_items': self._generate_action_items(gap),
            
            # Metadata
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'template'
        }
        
        return brief
    
    def _generate_gpt_brief(self, gap: Dict) -> Dict:
        """Generate brief using GPT-4"""
        
        prompt = f"""Je bent een SEO content strategist voor DemoShop.example, een professionele verfwebshop.

CONCURRENT CONTENT ANALYSE:
Concurrent: {gap['competitor_name']}
URL: {gap['competitor_url']}
Titel: {gap['title']}
Content type: {gap['category']}
Woordenaantal: {gap.get('word_count', 'onbekend')}
H2 structuur: {', '.join(gap.get('h2s_sample', [])[:5])}

TAAK:
Maak een gedetailleerde content brief voor DemoShop.example om deze gap te dichten.

OUTPUT FORMAT (JSON):
{{
    "suggested_h1": "Optimale H1 titel voor DEMO",
    "suggested_h2s": ["H2 1", "H2 2", "H2 3", ...],
    "suggested_meta_title": "SEO meta title (max 60 tekens)",
    "suggested_meta_description": "SEO meta description (max 155 tekens)",
    "target_word_count": 1200,
    "content_angle": "Welke unieke invalshoek moet DEMO gebruiken?",
    "key_topics": ["Topic 1", "Topic 2", ...],
    "internal_link_suggestions": ["Productcategorie om naar te linken", ...]
}}

BELANGRIJKE CONTEXT:
- DEMO richt zich op professionals (schilders, industriële klanten)
- Focus op kwaliteit, technische specs, verwerkingstips
- Gebruik merknamen uit assortiment: Sika, International, Epifanes, Jotun, Hempel, etc.
- Vermijd consumer-taal, focus op professioneel niveau

Genereer ALLEEN de JSON, geen extra uitleg."""

        try:
            response = self.openai_client.chat.completions.create(
                model=BRIEF_CONFIG['gpt_model'],
                messages=[
                    {"role": "system", "content": "Je bent een SEO content strategist. Output alleen JSON, geen markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse JSON response
            gpt_output = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            gpt_output = gpt_output.replace('```json', '').replace('```', '').strip()
            
            gpt_data = json.loads(gpt_output)
            
            # Combine with template data
            brief = self._generate_template_brief(gap)
            brief.update(gpt_data)
            brief['generation_method'] = 'gpt-4'
            
            return brief
            
        except Exception as e:
            logger.warning(f"GPT generation failed: {e}. Falling back to template.")
            return self._generate_template_brief(gap)
    
    def _generate_h1(self, gap: Dict) -> str:
        """Generate H1 from gap data"""
        title = gap['title']
        category = gap['category']
        
        # Clean up competitor title
        # Remove competitor branding
        for comp_name in ['CompetitorA', 'Competitor B', 'Competitor C']:
            title = title.replace(comp_name, '').replace(comp_name.lower(), '')
        
        # Add DEMO angle based on category
        if category == 'comparison':
            if 'vergelijk' not in title.lower():
                title = f"{title} - Vergelijking & Advies"
        elif category == 'guide':
            if 'gids' not in title.lower():
                title = f"{title} - Complete Gids"
        
        return title.strip()
    
    def _generate_meta_title(self, gap: Dict) -> str:
        """Generate meta title (max 60 chars)"""
        h1 = self._generate_h1(gap)
        
        # Truncate if needed
        if len(h1) > 57:
            h1 = h1[:57] + '...'
        
        return h1
    
    def _generate_meta_description(self, gap: Dict) -> str:
        """Generate meta description (max 155 chars)"""
        category = gap['category']
        title_base = gap['title'].split('-')[0].strip()
        
        templates = {
            'comparison': f"Vergelijk {title_base} merken en kies de beste voor jouw project. Professioneel advies van DemoShop.example.",
            'guide': f"Complete gids over {title_base}. Ontdek toepassingen, tips en productadvies voor professionals.",
            'product': f"{title_base} kopen? Bestel bij DemoShop.example ✓ Professioneel ✓ Snelle levering ✓ Deskundig advies.",
            'category': f"Ruim assortiment {title_base} voor professionals. Topmerken, scherpe prijzen, deskundig advies.",
        }
        
        desc = templates.get(category, f"{title_base} - Professioneel advies en topkwaliteit bij DemoShop.example.")
        
        # Truncate if needed
        if len(desc) > 155:
            desc = desc[:152] + '...'
        
        return desc
    
    def _find_related_demo_content(self, gap: Dict) -> List[str]:
        """Find related DEMO content voor internal linking"""
        # Simpele keyword matching
        # In production, could use TF-IDF or embeddings
        
        gap_keywords = set(gap['title'].lower().split())
        
        try:
            with open(DEMO_SITEMAP_FILE, 'r', encoding='utf-8') as f:
                demo_data = json.load(f)
            
            demo_urls = [url_data['url'] for url_data in demo_data.get('urls', [])]
            
            # Score URLs based on keyword overlap
            scored_urls = []
            for url in demo_urls:
                url_keywords = set(url.lower().split('/'))
                overlap = len(gap_keywords & url_keywords)
                if overlap > 0:
                    scored_urls.append((overlap, url))
            
            # Sort by overlap (descending)
            scored_urls.sort(reverse=True, key=lambda x: x[0])
            
            # Return top matches
            return [url for score, url in scored_urls[:5]]
            
        except Exception as e:
            logger.warning(f"Could not find related DEMO content: {e}")
            return []
    
    def _generate_action_items(self, gap: Dict) -> List[str]:
        """Generate concrete action items"""
        items = [
            f"Schrijf content van minimaal {int(gap.get('word_count', 800) * 1.1)} woorden",
            f"Gebruik H2 structuur zoals voorgesteld (minimaal {BRIEF_CONFIG['min_h2_count']} H2s)",
            "Voeg minimaal 2-3 afbeeldingen toe (product foto's of infographics)",
            f"Link naar {BRIEF_CONFIG['suggested_internal_links']} gerelateerde DEMO pagina's",
            "Optimaliseer meta title en description voor SEO",
            "Upload naar CMS en submit via Google Search Console"
        ]
        
        # Category-specific items
        if gap['category'] == 'comparison':
            items.append("Maak vergelijkingstabel met minimaal 3-5 producten/merken")
        elif gap['category'] == 'guide':
            items.append("Voeg stap-voor-stap instructies of verwerkingstips toe")
        
        return items
    
    def _save_brief(self, brief: Dict, gap: Dict):
        """Save brief as markdown file"""
        
        # Filename from gap title (sanitized)
        filename = gap['title'].lower()
        filename = filename.replace(' ', '_').replace('/', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in ['_', '-'])
        filename = f"{gap.get('rank', 0):03d}_{filename[:50]}.md"
        
        filepath = BRIEFS_DIR / filename
        
        # Generate markdown content
        md_content = self._brief_to_markdown(brief)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # Also save JSON version
        json_filepath = filepath.with_suffix('.json')
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(brief, f, indent=2, ensure_ascii=False)
    
    def _brief_to_markdown(self, brief: Dict) -> str:
        """Convert brief dict to markdown format"""
        
        md = f"""# CONTENT BRIEF: {brief['title']}

{'='*60}
**Gegenereerd:** {brief['generated_at'][:10]}  
**Methode:** {brief['generation_method']}  
**Priority Score:** {brief['priority_score']}/100  
{'='*60}

## 🎯 WAAROM DEZE CONTENT?

**Concurrent:** {brief['competitor_name']}  
**Concurrent URL:** {brief['competitor_url']}  
**Content Type:** {brief['content_type']}  

Deze concurrent heeft content die DemoShop.example mist. Door dit te maken kunnen we:
- Traffic winnen van concurrent
- Autoriteit opbouwen in dit onderwerp
- Klanten beter informeren

---

## 📝 CONTENT SPECIFICATIES

### H1 (Page Title)
```
{brief.get('suggested_h1', brief['title'])}
```

### H2 Structuur
"""
        
        for i, h2 in enumerate(brief.get('suggested_h2s', []), 1):
            md += f"{i}. {h2}\n"
        
        md += f"""
### Target Metrics
- **Woordenaantal:** {brief['target_word_count']}+ woorden
- **Aantal H2s:** {brief['target_h2_count']}+
- **Afbeeldingen:** 2-3+

---

## 🔍 SEO OPTIMALISATIE

### Meta Title (max 60 tekens)
```
{brief.get('suggested_meta_title', brief['title'][:60])}
```

### Meta Description (max 155 tekens)
```
{brief.get('suggested_meta_description', 'N/A')}
```

---

## 🔗 INTERNAL LINKING

Link naar deze DEMO pagina's (minimaal {BRIEF_CONFIG['suggested_internal_links']}):
"""
        
        for i, link in enumerate(brief.get('suggested_internal_links', []), 1):
            md += f"{i}. {link}\n"
        
        if brief.get('content_angle'):
            md += f"""
---

## 💡 CONTENT ANGLE

{brief['content_angle']}
"""
        
        if brief.get('key_topics'):
            md += f"""
---

## 📌 KEY TOPICS OM TE BEHANDELEN

"""
            for topic in brief['key_topics']:
                md += f"- {topic}\n"
        
        md += f"""
---

## ✅ ACTION ITEMS

"""
        for i, action in enumerate(brief.get('action_items', []), 1):
            md += f"- [ ] {action}\n"
        
        md += f"""
---

## 📊 VERWACHTE IMPACT

**Basis:** Concurrent heeft deze content en {brief['target_word_count']} woorden.  
**Verwachting:** Als DEMO dit maakt met vergelijkbare of betere kwaliteit:
- Ranking: Top 5-10 binnen 60-90 dagen
- Traffic: +{int(brief['target_word_count'] / 50)}-{int(brief['target_word_count'] / 30)} impressies/dag

*Note: Dit zijn schattingen op basis van concurrent performance. Werkelijke resultaten kunnen afwijken.*

---

**GENERATED BY:** Demo Gap Intelligence Suite  
**BRIEF ID:** #{brief.get('gap_id', 0)}
"""
        
        return md


def generate_briefs_main():
    """Main function"""
    generator = BriefGenerator()
    generator.generate_all_briefs()


if __name__ == '__main__':
    generate_briefs_main()
