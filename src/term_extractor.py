"""
Text Processor and Term Extractor for Social Services Legislation

Analyzes text from legislation sources and:
1. Extracts ALL unique terms and phrases
2. Counts frequency for each term
3. Identifies key vocabulary
4. Filters stopwords
5. Exports complete list to CSV
"""

import os
import logging
from pathlib import Path
from collections import Counter
import re
import sys
import csv
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
    
    def extract_all_terms(self, text):
        """
        Extracts ALL unique single words (unigrams) with frequencies
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: ALL unique words with counts (sorted by frequency)
        """
        tokens = self.tokenize_and_clean(text)
        
        # Count ALL occurrences
        counter = Counter(tokens)
        
        # Filter by minimum frequency (default MIN_FREQUENCY = 2)
        # This keeps words that appear at least twice
        filtered = {term: count for term, count in counter.items() 
                   if count >= MIN_FREQUENCY}
        
        # Sort by frequency (highest first)
        sorted_terms = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_terms
    
    def analyze_source(self, source_name):
        """
        Analyzes all text from a single source and extracts ALL terms
        
        Args:
            source_name (str): 'lagen_nu', 'lagar_se', or 'infolex'
            
        Returns:
            dict: Analysis results with ALL terms
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
        
        # Extract ALL terms
        logger.info("Extracting ALL terms from text...")
        all_terms = self.extract_all_terms(full_text)
        
        logger.info(f"\n✓ Found {len(all_terms)} unique terms")
        logger.info(f"✓ Showing top 20:")
        for i, (term, freq) in enumerate(all_terms[:20], 1):
            logger.info(f"   {i:2d}. {freq:4d}x  {term}")
        
        results = {
            'source': source_name,
            'total_chars': len(full_text),
            'all_terms': all_terms,
            'total_unique_terms': len(all_terms)
        }
        
        return results
    
    def analyze_all_sources(self):
        """
        Analyzes all available sources and extracts ALL terms
        
        Returns:
            list: Analysis results for all sources
        """
        logger.info("\n" + "=" * 70)
        logger.info("TERM EXTRACTION AND ANALYSIS - ALL TERMS")
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
    
    def export_all_terms_to_csv(self, results, filename="all_terms_complete.csv"):
        """
        Exports ALL extracted terms to CSV (sorted by frequency)
        
        Args:
            results: Analysis results from all sources
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        output_path = self.output_dir / filename
        
        # Collect all terms from all sources with metadata
        all_rows = []
        
        for result in results:
            source = result['source']
            
            # Get all terms (not just top 20!)
            for term, freq in result['all_terms']:
                all_rows.append({
                    'source': source,
                    'term': term,
                    'frequency': freq,
                    'english': '',
                    'italian': '',
                    'etymology': '',
                    'category': '',
                    'notes': '',
                    'status': 'uncurated'
                })
        
        # Sort all rows by frequency (highest first)
        all_rows.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'source', 'term', 'frequency', 'english', 'italian', 
                'etymology', 'category', 'notes', 'status'
            ])
            writer.writeheader()
            writer.writerows(all_rows)
        
        logger.info(f"\n✓ Exported {len(all_rows)} terms to: {output_path}")
        return output_path, len(all_rows)
    
    def create_statistics_report(self, results, filename="analysis_statistics.txt"):
        """
        Creates a detailed statistics report
        
        Args:
            results: Analysis results
            filename: Output filename
        """
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("SOCIAL SERVICES LEGISLATION - TERM ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            total_unique = 0
            total_occurrences = 0
            
            for result in results:
                source = result['source']
                source_display = {
                    'lagen_nu': 'Lagen.nu (Consolidated Law)',
                    'lagar_se': 'Lagar.se (Legislative DB)',
                    'infolex': 'Infolex.se (Expert Commentary)'
                }.get(source, source)
                
                unique_count = result['total_unique_terms']
                total_chars = result['total_chars']
                
                # Count total occurrences
                occurrences = sum(freq for _, freq in result['all_terms'])
                
                total_unique += unique_count
                total_occurrences += occurrences
                
                f.write(f"\n{'='*70}\n")
                f.write(f"{source_display}\n")
                f.write(f"{'='*70}\n")
                f.write(f"Characters analyzed: {total_chars:,}\n")
                f.write(f"Unique terms found: {unique_count}\n")
                f.write(f"Total term occurrences: {occurrences:,}\n")
                f.write(f"Average frequency: {occurrences/unique_count:.1f}x per term\n")
                
                f.write(f"\nTop 30 Most Frequent Terms:\n")
                f.write(f"{'-'*70}\n")
                f.write(f"{'Rank':<5} {'Frequency':<12} {'Term':<50}\n")
                f.write(f"{'-'*70}\n")
                
                for rank, (term, freq) in enumerate(result['all_terms'][:30], 1):
                    f.write(f"{rank:<5} {freq:<12} {term}\n")
            
            f.write(f"\n\n{'='*70}\n")
            f.write("OVERALL STATISTICS\n")
            f.write(f"{'='*70}\n")
            f.write(f"Sources analyzed: {len(results)}\n")
            f.write(f"Total unique terms (all sources): {total_unique}\n")
            f.write(f"Total term occurrences: {total_occurrences:,}\n")
            f.write(f"Average frequency across all: {total_occurrences/total_unique:.1f}x\n")
            
            f.write(f"\n\nFILES GENERATED:\n")
            f.write(f"  1. all_terms_complete.csv - All {total_unique} terms with metadata\n")
            f.write(f"  2. analysis_statistics.txt - This report\n")
            f.write(f"\nOPEN: all_terms_complete.csv in Excel or Google Sheets to review!\n")
        
        logger.info(f"✓ Statistics report saved to: {output_path}")


def main():
    """Main function to extract and analyze ALL terms"""
    
    extractor = TermExtractor()
    results = extractor.analyze_all_sources()
    
    if results:
        logger.info("\n" + "=" * 70)
        logger.info("✅ ANALYSIS COMPLETE!")
        logger.info("=" * 70)
        
        # Export ALL terms to CSV
        csv_path, term_count = extractor.export_all_terms_to_csv(results)
        
        # Create statistics report
        extractor.create_statistics_report(results)
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"   Total terms extracted: {term_count}")
        logger.info(f"   CSV file: {csv_path.name}")
        
        logger.info(f"\n📁 Output directory: {extractor.output_dir}")
        
        logger.info(f"\n🎯 NEXT STEPS:")
        logger.info(f"   1. Download and open: all_terms_complete.csv")
        logger.info(f"   2. Use Excel/Google Sheets to review ALL {term_count} terms")
        logger.info(f"   3. Add English translations for each term")
        logger.info(f"   4. Add Italian translations")
        logger.info(f"   5. Categorize by type (child welfare, abuse, etc.)")
        logger.info(f"   6. Mark status: keep/discard/uncertain")
        logger.info(f"\n   The 'frequency' column shows how important each term is!")
    else:
        logger.error("No results to process")


if __name__ == "__main__":
    main()
