"""
Gap Intelligence Suite - Main Orchestrator
===========================================
Run de complete gap analysis workflow.
"""
import sys
import logging
from datetime import datetime
from pathlib import Path

# Import alle modules
try:
    from competitor_crawler import crawl_all_competitors
    from gap_detector import detect_and_report
    from brief_generator import generate_briefs_main
    from config_gaps import validate_config, LOG_FILE
except ImportError as e:
    print(f"Import error: {e}")
    print("Zorg dat alle bestanden in dezelfde directory staan.")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print ASCII banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           GAP INTELLIGENCE SUITE v1.0                        ║
║           DemoShop.example Competitor Analysis Tool                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def run_full_workflow():
    """Run de complete gap analysis workflow"""
    
    print_banner()
    
    logger.info(f"Starting Gap Intelligence workflow - {datetime.now()}")
    
    try:
        # Validate config
        logger.info("\n" + "="*60)
        logger.info("STEP 0: Validating configuration")
        logger.info("="*60)
        validate_config()
        logger.info("✓ Configuration valid")
        
        # Step 1: Crawl competitors
        logger.info("\n" + "="*60)
        logger.info("STEP 1: Crawling competitors")
        logger.info("="*60)
        crawl_all_competitors()
        logger.info("✓ Crawling complete")
        
        # Step 2: Detect gaps
        logger.info("\n" + "="*60)
        logger.info("STEP 2: Detecting gaps")
        logger.info("="*60)
        gaps_data = detect_and_report()
        logger.info("✓ Gap detection complete")
        
        # Step 3: Generate briefs
        logger.info("\n" + "="*60)
        logger.info("STEP 3: Generating content briefs")
        logger.info("="*60)
        generate_briefs_main()
        logger.info("✓ Brief generation complete")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("WORKFLOW COMPLETE!")
        logger.info("="*60)
        
        summary = gaps_data.get('summary', {})
        logger.info(f"\nResults:")
        logger.info(f"  Total gaps found: {summary.get('total', 0)}")
        logger.info(f"  Briefs generated: Check output/content_briefs/")
        logger.info(f"\nNext steps:")
        logger.info(f"  1. Review briefs in: output/content_briefs/")
        logger.info(f"  2. Prioritize top gaps based on scores")
        logger.info(f"  3. Start creating content!")
        
        logger.info(f"\nLog file: {LOG_FILE}")
        
    except Exception as e:
        logger.error(f"\n❌ Workflow failed: {e}", exc_info=True)
        sys.exit(1)


def run_step(step: str):
    """Run een specifieke stap"""
    
    steps = {
        'crawl': ("Crawling competitors", crawl_all_competitors),
        'detect': ("Detecting gaps", detect_and_report),
        'brief': ("Generating briefs", generate_briefs_main)
    }
    
    if step not in steps:
        logger.error(f"Unknown step: {step}")
        logger.error(f"Valid steps: {', '.join(steps.keys())}")
        sys.exit(1)
    
    step_name, step_func = steps[step]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Running: {step_name}")
    logger.info(f"{'='*60}")
    
    try:
        result = step_func()
        logger.info(f"✓ {step_name} complete")
        return result
    except Exception as e:
        logger.error(f"❌ {step_name} failed: {e}", exc_info=True)
        sys.exit(1)


def show_help():
    """Show help message"""
    help_text = """
Gap Intelligence Suite - Usage
===============================

Run complete workflow:
    python gap_intelligence.py

Run individual steps:
    python gap_intelligence.py crawl   # Crawl competitors
    python gap_intelligence.py detect  # Detect gaps
    python gap_intelligence.py brief   # Generate briefs

Options:
    -h, --help    Show this help message

Output:
    data/competitors.json       # Crawled competitor data
    data/gaps_detected.json     # Detected gaps
    output/content_briefs/      # Generated briefs (MD + JSON)
    output/gap_report.csv       # Gap report for Excel
    logs/gap_intelligence.log   # Log file

Examples:
    # Full workflow (recommended first run)
    python gap_intelligence.py
    
    # Only generate new briefs (after gaps are detected)
    python gap_intelligence.py brief
    
    # Re-crawl competitors without detecting gaps
    python gap_intelligence.py crawl
"""
    print(help_text)


if __name__ == '__main__':
    import sys
    
    # Parse arguments
    args = sys.argv[1:]
    
    if not args:
        # No arguments - run full workflow
        run_full_workflow()
    elif args[0] in ['-h', '--help']:
        show_help()
    elif args[0] in ['crawl', 'detect', 'brief']:
        run_step(args[0])
    else:
        print(f"Unknown argument: {args[0]}")
        print("Run with -h for help")
        sys.exit(1)
