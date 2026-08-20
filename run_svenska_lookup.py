#!/usr/bin/env python3
"""
Runner script for Svenska.se Dictionary Lookup
Enriches extracted terms with Swedish Academy Dictionary information

Run this after run_term_extractor.py with: python run_svenska_lookup.py
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from svenska_se_lookup import SvenskaSeLooup
from config import PROCESSED_DATA_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" " * 15 + "SVENSKA.SE DICTIONARY LOOKUP")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Read all extracted terms from all_terms_complete.csv")
    print("  2. Look up each term on svenska.se (Swedish Academy Dictionary)")
    print("  3. Extract definitions, grammar forms, and pronunciation")
    print("  4. Create a new CSV with all this information")
    print("\n" + "=" * 80 + "\n")
    
    looup = SvenskaSeLooup()
    
    # Find the extracted terms CSV
    term_csv = PROCESSED_DATA_DIR / "term_analysis" / "all_terms_complete.csv"
    
    if not term_csv.exists():
        print(f"\n❌ ERROR: Terms CSV not found at: {term_csv}")
        print(f"\nPlease run this first:")
        print(f"   python run_term_extractor.py")
        sys.exit(1)
    
    try:
        print(f"📁 Found terms file: {term_csv.name}")
        print(f"📍 Location: {term_csv.parent}\n")
        
        # Enrich with svenska.se data
        # Remove max_terms parameter to process ALL terms
        # For first run, we test with 50 terms to verify it works
        print("⏳ Starting lookup... This may take several minutes.")
        print("   (Being respectful to svenska.se servers with delays)\n")
        
        enriched_csv = looup.enrich_csv(
            term_csv, 
            output_filename="terms_with_svenska_se.csv",
            max_terms=None  # Set to None to process ALL terms
        )
        
        looup.print_statistics()
        
        if enriched_csv:
            print(f"\n" + "=" * 80)
            print("✅ SVENSKA.SE LOOKUP COMPLETE!")
            print("=" * 80)
            print(f"\n📊 Output file: {enriched_csv.name}")
            print(f"📁 Location: {enriched_csv.parent}")
            
            print(f"\n📋 CSV COLUMNS NOW INCLUDE:")
            print(f"   • term - The Swedish word")
            print(f"   • source - Where it came from (lagen_nu/lagar_se/infolex)")
            print(f"   • frequency - How often it appears in the law")
            print(f"   • definition - Meaning from Svenska.se")
            print(f"   • word_class - noun/verb/adjective/etc.")
            print(f"   • pronunciation - How to pronounce it")
            print(f"   • singular_indefinite - e.g., 'ett barn'")
            print(f"   • singular_definite - e.g., 'barnet'")
            print(f"   • plural_indefinite - e.g., 'barn'")
            print(f"   • plural_definite - e.g., 'barnen'")
            print(f"   • genitive - Possessive form")
            print(f"   • etymology - Word origin information")
            print(f"   • examples - Example sentences from Svenska.se")
            print(f"   • found_on_svenska - 'yes' or 'no'")
            print(f"   • english - (empty for you to fill)")
            print(f"   • italian - (empty for you to fill)")
            print(f"   • category - (empty for you to fill)")
            print(f"   • notes - (empty for you to fill)")
            print(f"   • status - uncurated/keep/discard")
            
            print(f"\n🎯 NEXT STEPS:")
            print(f"   1. Download: {enriched_csv.name}")
            print(f"   2. Open in Excel/Google Sheets")
            print(f"   3. Review definitions and grammar forms")
            print(f"   4. Add English translations in 'english' column")
            print(f"   5. Add Italian translations in 'italian' column")
            print(f"   6. Categorize terms in 'category' column")
            print(f"   7. Mark status (keep/discard/uncertain)")
            
            print(f"\n💡 KEY FEATURES:")
            print(f"   • All grammar forms included (singular, plural, definite, indefinite)")
            print(f"   • Pronunciation for each word")
            print(f"   • Etymology showing word origins")
            print(f"   • Example sentences from Svenska.se")
            print(f"   • Frequency ranking (how important each term is)")
            
            print("\n" + "=" * 80 + "\n")
        else:
            print("\n❌ Failed to create enriched CSV")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during lookup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
