"""
Text Processor and Term Extractor for Social Services Legislation

Analyzes text from legislation sources and:
1. Extracts unique terms and phrases
2. Counts frequency
3. Identifies key vocabulary
4. Filters stopwords
"""

import os
import logging
from pathlib import Path
from collections import Counter
import re
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, STOPWORDS_SWEDISH, MIN_FREQUENCY, CATEGORIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TermExtractor:
    """Extracts and analyzes terms from legislation text"""
    
    def __init__(self):
        self.raw_text_dir = RAW_DATA_DIR / "web_text"
        self.output_dir = PROCESSED_DATA_DIR / "term_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Swedish stopwords and common words to filter
        self.stopwords = STOPWORDS_SWEDISH
    
    def load_text_from_sections(self, source_dir):
        """
        Loads all section files from a source directory
        
        Args:
            source_dir: Path to source directory (e.g., lagen_nu/)
            
        Returns:
            str: Combined text from all sections
        """
        sections_dir = source_dir / "sections"
        
        if not sections_dir.exists():
            logger.warning(f"Sections directory not found: {sections_dir}")
            return ""
        
        all_text = ""
        section_files = sorted(sections_dir.glob("section_*.txt"))
        
        logger.info(f"Loading {len(section_files)} section files from {source_dir.name}")
        
        for section_file in section_files:
            with open(section_file, 'r', encoding='utf-8') as f:
                all_text += f.read() + "\n"
        
        return all_text
    
    def tokenize_and_clean(self, text):
        """
        Tokenizes text into words and cleans them
        
        Args:
            text (str): Raw text
            
        Returns:
            list: List of cleaned tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Keep Swedish characters (åäö) and remove unwanted punctuation
        # But keep § which is important in law
        tokens = re.findall(r'[\wåäö§]+', text)
        
        # Filter out stopwords and very short words
        filtered = [
            token for token in tokens 
            if token not in self.stopwords 
            and len(token) > 2
            and not token.isdigit()
        ]
        
        return filtered
    
    def extract_phrases(self, text, n_grams=(1, 2, 3)):
        """
        Extracts single words and multi-word phrases
        
        Args:
            text (str): Text to analyze
            n_grams: Tuple of n-gram sizes to extract
            
        Returns:
            dict: Dictionary with counts for each n-gram size
        """
        tokens = self.tokenize_and_clean(text)
        
        result = {}
        
        for n in n_grams:
            ngrams = []
            for i in range(len(tokens) - n + 1):
                phrase = ' '.join(tokens[i:i+n])
                ngrams.append(phrase)
            
            # Count occurrences, filter by minimum frequency
            counter = Counter(ngrams)
            filtered = {term: count for term, count in counter.items() 
                       if count >= MIN_FREQUENCY}
            
            result[f'{n}_gram'] = filtered
        
        return result
    
    def analyze_source(self, source_name):
        """
        Analyzes all text from a single source
        
        Args:
            source_name (str): 'lagen_nu', 'lagar_se', or 'infolex'
            
        Returns:
            dict: Analysis results
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"ANALYZING SOURCE: {source_name}")
        logger.info(f"{'='*70}")
        
        source_dir = self.raw_text_dir / source_name
        
        if not source_dir.exists():
            logger.error(f"Source directory not found: {source_dir}")
            return None
        
        # Load all text from sections
        logger.info(f"Loading text from {source_dir}...")
        full_text = self.load_text_from_sections(source_dir)
        
        if not full_text:
            logger.error(f"No text found in {source_dir}")
            return None
        
        logger.info(f"Loaded {len(full_text):,} characters")
        
        # Extract phrases
        logger.info("Extracting phrases...")
        phrases = self.extract_phrases(full_text)
        
        # Get top terms for each n-gram
        results = {
            'source': source_name,
            'total_chars': len(full_text),
            'unique_terms': {}
        }
        
        for gram_type, terms_dict in phrases.items():
            n = int(gram_type.split('_')[0])
            sorted_terms = sorted(terms_dict.items(), key=lambda x: x[1], reverse=True)
            
            results['unique_terms'][gram_type] = {
                'count': len(sorted_terms),
                'top_30': sorted_terms[:30]
            }
            
            logger.info(f"\n{gram_type.upper()}")
            logger.info(f"  Total unique: {len(sorted_terms)}")
            logger.info(f"  Top 10:")
            for term, freq in sorted_terms[:10]:
                logger.info(f"    {freq:4d}x  {term}")
        
        return results
    
    def analyze_all_sources(self):
        """
        Analyzes all available sources
        
        Returns:
            dict: Analysis results for all sources
        """
        logger.info("\n" + "=" * 70)
        logger.info("TERM EXTRACTION AND ANALYSIS")
        logger.info("=" * 70)
        
        all_results = []
        
        sources = ['lagen_nu', 'lagar_se', 'infolex']
        
        for source_name in sources:
            source_dir = self.raw_text_dir / source_name
            if source_dir.exists():
                result = self.analyze_source(source_name)
                if result:
                    all_results.append(result)
            else:
                logger.warning(f"Skipping {source_name} - directory not found")
        
        return all_results
    
    def export_terms_to_csv(self, results, filename="terms_extracted.csv"):
        """
        Exports extracted terms to CSV for manual review
        
        Args:
            results: Analysis results
            filename: Output filename
        """
        import csv
        
        output_path = self.output_dir / filename
        
        rows = []
        for result in results:
            source = result['source']
            
            # Add unigrams (single words)
            if '1_gram' in result['unique_terms']:
                for term, freq in result['unique_terms']['1_gram']['top_30']:
                    rows.append({
                        'source': source,
                        'term': term,
                        'frequency': freq,
                        'type': 'word',
                        'english': '',
                        'italian': '',
                        'etymology': '',
                        'category': '',
                        'notes': '',
                        'status': 'uncurated'
                    })
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'source', 'term', 'frequency', 'type', 'english', 'italian', 
                'etymology', 'category', 'notes', 'status'
            ])
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"\n✓ Exported {len(rows)} terms to: {output_path}")
        return output_path


def main():
    """Main function to extract and analyze terms"""
    
    extractor = TermExtractor()
    results = extractor.analyze_all_sources()
    
    if results:
        logger.info("\n" + "=" * 70)
        logger.info("✅ ANALYSIS COMPLETE!")
        logger.info("=" * 70)
        
        # Export to CSV
        extractor.export_terms_to_csv(results)
        
        logger.info(f"\n📊 Sources analyzed: {len(results)}")
        logger.info(f"📁 Output directory: {extractor.output_dir}")
        
        logger.info("\n🎯 Next steps:")
        logger.info("   1. Review extracted terms in CSV file")
        logger.info("   2. Mark which terms are important for your vocabulary")
        logger.info("   3. Look up grammar on svenska.se")
        logger.info("   4. Find etymologies (Latin/Greek roots)")
        logger.info("   5. Add translations (English/Italian)")
    else:
        logger.error("No results to process")


if __name__ == "__main__":
    main()
