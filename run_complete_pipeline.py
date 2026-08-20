#!/usr/bin/env python3
"""
COMPLETE PIPELINE RUNNER
Executes the entire workflow automatically:
1. Scrape legislation from 3 sources
2. Extract all terms and their frequencies
3. Look up each term on Svenska.se for definitions and grammar
4. Create enriched vocabulary CSV ready for curation

Run with: python run_complete_pipeline.py
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from multi_source_scraper import MultiSourceScraper
from term_extractor import TermExtractor
from svenska_se_lookup import SvenskaSeLooup
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompletePipeline:
    """Orchestrates the complete vocabulary building pipeline"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            'scraping': None,
            'extraction': None,
            'lookup': None
        }
    
    def print_header(self, title):
        """Print a formatted header"""
        print("\n" + "=" * 80)
        print(" " * (40 - len(title)//2) + title)
        print("=" * 80 + "\n")
    
    def print_footer(self):
        """Print completion footer"""
        elapsed = datetime.now() - self.start_time
        print("\n" + "=" * 80)
        print("✅ COMPLETE PIPELINE FINISHED!")
        print("=" * 80)
        print(f"\n⏱️  Total time: {elapsed}")
        print(f"📁 Output directory: {PROCESSED_DATA_DIR}")
    
    def step_1_scrape_legislation(self):
        """Step 1: Scrape from all three sources"""
        self.print_header("STEP 1: SCRAPING LEGISLATION FROM 3 SOURCES")
        
        try:
            scraper = MultiSourceScraper()
            results = scraper.scrape_all_sources(chunk_by='sections')
            
            if results and len(results) > 0:
                print(f"\n✅ SCRAPING SUCCESSFUL!")
                
                total_chars = 0
                for result in results:
                    source_name = result['source']
                    char_count = result['char_count']
                    total_chars += char_count
                    
                    print(f"\n  📚 {source_name.upper()}")
                    print(f"     Characters: {char_count:,}")
                    print(f"     Sections: {len(result['chunks'])}")
                
                print(f"\n  📊 TOTAL: {total_chars:,} characters from {len(results)} sources")
                print(f"  📁 Saved to: {RAW_DATA_DIR / 'web_text'}")
                
                self.results['scraping'] = {
                    'status': 'success',
                    'sources': len(results),
                    'total_chars': total_chars
                }
                return True
            else:
                print("❌ Scraping failed")
                self.results['scraping'] = {'status': 'failed'}
                return False
                
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            self.results['scraping'] = {'status': 'error', 'message': str(e)}
            return False
    
    def step_2_extract_terms(self):
        """Step 2: Extract all terms from scraped text"""
        self.print_header("STEP 2: EXTRACTING ALL TERMS FROM LEGISLATION")
        
        try:
            extractor = TermExtractor()
            results = extractor.analyze_all_sources()
            
            if results and len(results) > 0:
                print(f"\n✅ TERM EXTRACTION SUCCESSFUL!")
                
                total_unique_terms = 0
                for result in results:
                    source = result['source']
                    unique_count = result['total_unique_terms']
                    total_unique_terms += unique_count
                    
                    print(f"\n  📚 {source.upper()}")
                    print(f"     Unique terms: {unique_count}")
                    
                    # Show top 10
                    print(f"     Top 10:")
                    for i, (term, freq) in enumerate(result['all_terms'][:10], 1):
                        print(f"        {i:2d}. {freq:5d}x  {term}")
                
                print(f"\n  📊 TOTAL UNIQUE TERMS: {total_unique_terms}")
                
                # Export to CSV
                csv_path, term_count = extractor.export_all_terms_to_csv(results)
                extractor.create_statistics_report(results)
                
                print(f"\n  📄 CSV exported: all_terms_complete.csv")
                print(f"  📁 Location: {PROCESSED_DATA_DIR / 'term_analysis'}")
                
                self.results['extraction'] = {
                    'status': 'success',
                    'total_terms': term_count,
                    'csv_path': csv_path
                }
                return True
            else:
                print("❌ Term extraction failed")
                self.results['extraction'] = {'status': 'failed'}
                return False
                
        except Exception as e:
            print(f"❌ Error during extraction: {e}")
            import traceback
            traceback.print_exc()
            self.results['extraction'] = {'status': 'error', 'message': str(e)}
            return False
    
    def step_3_lookup_svenska_se(self):
        """Step 3: Look up terms on Svenska.se"""
        self.print_header("STEP 3: LOOKING UP TERMS ON SVENSKA.SE")
        
        try:
            # Check if CSV exists
            term_csv = PROCESSED_DATA_DIR / "term_analysis" / "all_terms_complete.csv"
            
            if not term_csv.exists():
                print(f"❌ ERROR: Terms CSV not found at: {term_csv}")
                print("Make sure step 2 completed successfully")
                self.results['lookup'] = {'status': 'failed', 'message': 'CSV not found'}
                return False
            
            looup = SvenskaSeLooup()
            
            print(f"📁 Found terms file: all_terms_complete.csv")
            print(f"⏳ Starting lookup... This may take several minutes.")
            print(f"   (Being respectful to svenska.se servers with 0.5s delays)\n")
            
            # Process all terms
            enriched_csv = looup.enrich_csv(
                term_csv,
                output_filename="terms_with_svenska_se.csv",
                max_terms=None  # Process ALL terms
            )
            
            looup.print_statistics()
            
            if enriched_csv:
                print(f"\n✅ SVENSKA.SE LOOKUP SUCCESSFUL!")
                print(f"\n  📄 Enriched CSV: terms_with_svenska_se.csv")
                print(f"  📁 Location: {PROCESSED_DATA_DIR / 'svenska_se_lookup'}")
                
                print(f"\n  📋 CSV NOW CONTAINS:")
                print(f"     • All extracted terms with frequencies")
                print(f"     • Definitions from Svenska.se")
                print(f"     • Grammar forms (singular, plural, definite, indefinite)")
                print(f"     • Pronunciation")
                print(f"     • Etymology (word origins)")
                print(f"     • Example sentences")
                
                self.results['lookup'] = {
                    'status': 'success',
                    'csv_path': enriched_csv,
                    'successful_lookups': looup.stats['successful_lookups'],
                    'not_found': looup.stats['not_found'],
                    'failed': looup.stats['failed_lookups']
                }
                return True
            else:
                print("❌ Failed to create enriched CSV")
                self.results['lookup'] = {'status': 'failed', 'message': 'CSV creation failed'}
                return False
                
        except Exception as e:
            print(f"❌ Error during lookup: {e}")
            import traceback
            traceback.print_exc()
            self.results['lookup'] = {'status': 'error', 'message': str(e)}
            return False
    
    def print_final_summary(self):
        """Print final summary and next steps"""
        print("\n" + "=" * 80)
        print("📊 PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        
        # Step 1: Scraping
        scraping = self.results['scraping']
        if scraping['status'] == 'success':
            print(f"\n✅ STEP 1: SCRAPING")
            print(f"   Sources: {scraping['sources']}")
            print(f"   Total characters: {scraping['total_chars']:,}")
        else:
            print(f"\n❌ STEP 1: SCRAPING FAILED")
        
        # Step 2: Extraction
        extraction = self.results['extraction']
        if extraction['status'] == 'success':
            print(f"\n✅ STEP 2: TERM EXTRACTION")
            print(f"   Total unique terms: {extraction['total_terms']}")
            print(f"   CSV: all_terms_complete.csv")
        else:
            print(f"\n❌ STEP 2: TERM EXTRACTION FAILED")
        
        # Step 3: Lookup
        lookup = self.results['lookup']
        if lookup['status'] == 'success':
            print(f"\n✅ STEP 3: SVENSKA.SE LOOKUP")
            print(f"   Successfully looked up: {lookup['successful_lookups']}")
            print(f"   Not found on svenska.se: {lookup['not_found']}")
            print(f"   Failed queries: {lookup['failed']}")
            print(f"   CSV: terms_with_svenska_se.csv")
        else:
            print(f"\n❌ STEP 3: SVENSKA.SE LOOKUP FAILED")
        
        print("\n" + "=" * 80)
        print("🎯 WHAT TO DO NEXT")
        print("=" * 80)
        print(f"\n1. DOWNLOAD: terms_with_svenska_se.csv")
        print(f"   Location: {PROCESSED_DATA_DIR / 'svenska_se_lookup'}")
        print(f"\n2. OPEN in Excel or Google Sheets")
        print(f"\n3. REVIEW the extracted data:")
        print(f"   • Check definitions from Svenska.se")
        print(f"   • Verify grammar forms are correct")
        print(f"   • Review pronunciation")
        print(f"\n4. FILL IN MISSING COLUMNS:")
        print(f"   • english - English translation")
        print(f"   • italian - Italian translation (from Latin roots)")
        print(f"   • category - Type of term (child_welfare, abuse, etc.)")
        print(f"   • notes - Your personal notes")
        print(f"   • status - keep/discard/uncertain")
        print(f"\n5. SAVE your curated version")
        print(f"\n6. USE IT! Study professional Swedish social services vocabulary")
        
        print("\n" + "=" * 80)
        print("💡 THE COMPLETE CSV INCLUDES:")
        print("=" * 80)
        print(f"   term - Swedish word")
        print(f"   source - Where it came from (lagen_nu/lagar_se/infolex)")
        print(f"   frequency - How often it appears (higher = more important)")
        print(f"   definition - Official definition from Svenska.se")
        print(f"   word_class - Part of speech (noun, verb, adj, etc.)")
        print(f"   pronunciation - How to pronounce it")
        print(f"   singular_indefinite - e.g., 'ett barn'")
        print(f"   singular_definite - e.g., 'barnet'")
        print(f"   plural_indefinite - e.g., 'barn'")
        print(f"   plural_definite - e.g., 'barnen'")
        print(f"   genitive - Possessive form")
        print(f"   etymology - Word origin and history")
        print(f"   examples - Example sentences")
        print(f"   found_on_svenska - yes/no")
        print(f"   english - (FILL IN)")
        print(f"   italian - (FILL IN)")
        print(f"   category - (FILL IN)")
        print(f"   notes - (FILL IN)")
        print(f"   status - (FILL IN)")
        
        print("\n" + "=" * 80 + "\n")
    
    def run(self):
        """Execute the complete pipeline"""
        self.print_header("COMPLETE VOCABULARY PIPELINE")
        
        print("This will automatically:")
        print("  1. Scrape legislation from Lagen.nu, Lagar.se, Infolex.se")
        print("  2. Extract ALL unique terms and count frequencies")
        print("  3. Look up each term on Svenska.se for definitions & grammar")
        print("  4. Create a complete CSV ready for you to review & curate")
        print("\n" + "=" * 80)
        
        # Execute pipeline
        if not self.step_1_scrape_legislation():
            print("\n⚠️  Pipeline stopped at Step 1")
            return False
        
        if not self.step_2_extract_terms():
            print("\n⚠️  Pipeline stopped at Step 2")
            return False
        
        if not self.step_3_lookup_svenska_se():
            print("\n⚠️  Pipeline stopped at Step 3")
            return False
        
        # All steps successful
        self.print_footer()
        self.print_final_summary()
        
        return True


def main():
    """Main entry point"""
    pipeline = CompletePipeline()
    
    try:
        success = pipeline.run()
        
        if success:
            print("\n✨ PIPELINE COMPLETED SUCCESSFULLY! ✨\n")
            sys.exit(0)
        else:
            print("\n❌ PIPELINE FAILED\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
