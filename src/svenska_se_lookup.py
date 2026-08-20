"""
Svenska.se Lookup Module

Queries svenska.se (Swedish Academy Dictionary) for each extracted term and retrieves:
1. Official definitions and meanings
2. Complete grammar forms (singular/plural, definite/indefinite, genitive)
3. Word class (noun, verb, adjective, etc.)
4. Pronunciation
5. Etymology information when available
"""

import os
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import csv
import time
import sys
from typing import Dict, Optional, List
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SvenskaSeLooup:
    """Queries Svenska.se (Swedish Academy Dictionary) for word information"""
    
    def __init__(self):
        self.output_dir = PROCESSED_DATA_DIR / "svenska_se_lookup"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Track statistics
        self.stats = {
            'total_queries': 0,
            'successful_lookups': 0,
            'failed_lookups': 0,
            'not_found': 0
        }
    
    def lookup_term(self, term):
        """
        Looks up a single term on svenska.se
        
        Args:
            term (str): Swedish word to look up
            
        Returns:
            dict: Word information or None if not found
        """
        self.stats['total_queries'] += 1
        
        try:
            # Svenska.se search URL
            search_url = f"https://svenska.se/tre/?sok={term}"
            
            logger.debug(f"Looking up: {term}")
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse the response
            word_info = self._parse_svenska_se_response(soup, term)
            
            if word_info:
                self.stats['successful_lookups'] += 1
                return word_info
            else:
                self.stats['not_found'] += 1
                logger.warning(f"No entry found for: {term}")
                return None
                
        except Exception as e:
            self.stats['failed_lookups'] += 1
            logger.error(f"Error looking up '{term}': {e}")
            return None
    
    def _parse_svenska_se_response(self, soup, term):
        """
        Parses the HTML response from svenska.se
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            term (str): Original search term
            
        Returns:
            dict: Extracted word information or None
        """
        try:
            # Try to find the main article/entry
            article = soup.find(['article', 'div'], class_=['entry', 'artikel', 'ordbok-entry'])
            
            if not article:
                # Try alternative selectors
                article = soup.find('div', class_='ordbok')
            
            if not article:
                return None
            
            word_info = {
                'term': term,
                'found': True,
                'definition': '',
                'word_class': '',
                'pronunciation': '',
                'grammar_forms': {},
                'etymology': '',
                'examples': [],
                'url': f'https://svenska.se/tre/?sok={term}'
            }
            
            # Extract definition (usually in <p> tags)
            def_paragraphs = article.find_all('p', class_=['definition', 'betydelse'])
            if def_paragraphs:
                word_info['definition'] = def_paragraphs[0].get_text().strip()
            
            # Extract word class (noun, verb, adj, etc.)
            word_class_elem = article.find(['span', 'em'], class_=['wordclass', 'ordklass', 'grammatik'])
            if word_class_elem:
                word_info['word_class'] = word_class_elem.get_text().strip()
            
            # Extract pronunciation
            pronunciation_elem = article.find('span', class_=['pronunciation', 'uttal'])
            if pronunciation_elem:
                word_info['pronunciation'] = pronunciation_elem.get_text().strip()
            
            # Extract grammar forms (singular, plural, genitive, etc.)
            grammar_table = article.find('table', class_=['grammar', 'grammatik', 'böjning'])
            if grammar_table:
                word_info['grammar_forms'] = self._parse_grammar_table(grammar_table)
            
            # Extract etymology
            etymology_elem = article.find('div', class_=['etymology', 'etymologi', 'ursprung'])
            if etymology_elem:
                word_info['etymology'] = etymology_elem.get_text().strip()
            
            # Extract examples
            examples = article.find_all('blockquote', class_=['example', 'exempel'])
            word_info['examples'] = [ex.get_text().strip() for ex in examples[:3]]
            
            return word_info
            
        except Exception as e:
            logger.error(f"Error parsing svenska.se response for '{term}': {e}")
            return None
    
    def _parse_grammar_table(self, table):
        """
        Parses grammar information table
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            dict: Grammar forms
        """
        grammar = {}
        
        try:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    form_type = cells[0].get_text().strip().lower()
                    form_value = cells[1].get_text().strip()
                    
                    if form_type and form_value:
                        grammar[form_type] = form_value
            
            return grammar
            
        except Exception as e:
            logger.error(f"Error parsing grammar table: {e}")
            return {}
    
    def lookup_from_csv(self, csv_path, max_terms=None, delay=0.5):
        """
        Looks up all terms from extracted CSV file
        
        Args:
            csv_path (Path): Path to all_terms_complete.csv
            max_terms (int): Limit lookups (for testing)
            delay (float): Delay between requests (seconds, be respectful!)
            
        Yields:
            dict: Enriched term data with svenska.se information
        """
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return
        
        logger.info(f"Loading terms from: {csv_path}")
        
        terms_processed = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                term = row.get('term', '').strip()
                
                if not term:
                    continue
                
                if max_terms and terms_processed >= max_terms:
                    logger.info(f"Reached max_terms limit: {max_terms}")
                    break
                
                # Look up the term
                word_info = self.lookup_term(term)
                
                # Combine original data with lookup results
                enriched = {
                    'term': term,
                    'source': row.get('source', ''),
                    'frequency': row.get('frequency', ''),
                    'definition': word_info['definition'] if word_info else '',
                    'word_class': word_info['word_class'] if word_info else '',
                    'pronunciation': word_info['pronunciation'] if word_info else '',
                    'singular_indefinite': word_info['grammar_forms'].get('singular indefinite', '') if word_info else '',
                    'singular_definite': word_info['grammar_forms'].get('singular definite', '') if word_info else '',
                    'plural_indefinite': word_info['grammar_forms'].get('plural indefinite', '') if word_info else '',
                    'plural_definite': word_info['grammar_forms'].get('plural definite', '') if word_info else '',
                    'genitive': word_info['grammar_forms'].get('genitive', '') if word_info else '',
                    'etymology': word_info['etymology'] if word_info else '',
                    'examples': ' | '.join(word_info['examples']) if word_info and word_info['examples'] else '',
                    'found_on_svenska': 'yes' if word_info else 'no',
                    'english': '',
                    'italian': '',
                    'category': '',
                    'notes': '',
                    'status': 'uncurated'
                }
                
                terms_processed += 1
                
                if terms_processed % 10 == 0:
                    logger.info(f"Processed {terms_processed} terms...")
                
                # Be respectful to the server - add delay between requests
                time.sleep(delay)
                
                yield enriched
    
    def enrich_csv(self, csv_path, output_filename="terms_with_svenska_se.csv", max_terms=None):
        """
        Enriches CSV with svenska.se lookup results
        
        Args:
            csv_path (Path): Path to all_terms_complete.csv
            output_filename (str): Output CSV filename
            max_terms (int): Limit lookups for testing
            
        Returns:
            Path: Path to enriched CSV file
        """
        output_path = self.output_dir / output_filename
        
        logger.info(f"\n{'='*70}")
        logger.info("ENRICHING TERMS WITH SVENSKA.SE DATA")
        logger.info(f"{'='*70}\n")
        
        # Collect all enriched rows
        enriched_rows = []
        
        for enriched_row in self.lookup_from_csv(csv_path, max_terms=max_terms):
            enriched_rows.append(enriched_row)
        
        # Write to CSV
        if enriched_rows:
            fieldnames = [
                'term', 'source', 'frequency',
                'definition', 'word_class', 'pronunciation',
                'singular_indefinite', 'singular_definite',
                'plural_indefinite', 'plural_definite', 'genitive',
                'etymology', 'examples',
                'found_on_svenska',
                'english', 'italian', 'category', 'notes', 'status'
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(enriched_rows)
            
            logger.info(f"\n✓ Enriched CSV saved to: {output_path}")
            logger.info(f"  Total terms: {len(enriched_rows)}")
            logger.info(f"  Successfully looked up: {self.stats['successful_lookups']}")
            logger.info(f"  Not found on svenska.se: {self.stats['not_found']}")
            logger.info(f"  Failed to query: {self.stats['failed_lookups']}")
            
            return output_path
        else:
            logger.error("No enriched rows to write")
            return None
    
    def print_statistics(self):
        """Prints lookup statistics"""
        logger.info(f"\n{'='*70}")
        logger.info("SVENSKA.SE LOOKUP STATISTICS")
        logger.info(f"{'='*70}")
        logger.info(f"Total queries: {self.stats['total_queries']}")
        logger.info(f"Successful lookups: {self.stats['successful_lookups']}")
        logger.info(f"Not found: {self.stats['not_found']}")
        logger.info(f"Failed queries: {self.stats['failed_lookups']}")
        
        if self.stats['total_queries'] > 0:
            success_rate = (self.stats['successful_lookups'] / self.stats['total_queries']) * 100
            logger.info(f"Success rate: {success_rate:.1f}%")


def main():
    """Main function to enrich terms with svenska.se data"""
    
    looup = SvenskaSeLooup()
    
    # Find the extracted terms CSV
    term_csv = PROCESSED_DATA_DIR / "term_analysis" / "all_terms_complete.csv"
    
    if not term_csv.exists():
        logger.error(f"Terms CSV not found: {term_csv}")
        logger.error("Please run: python run_term_extractor.py first")
        return
    
    # Enrich with svenska.se data
    # For testing, limit to first 100 terms
    # Remove max_terms parameter to process all terms
    enriched_csv = looup.enrich_csv(term_csv, max_terms=100)
    
    looup.print_statistics()
    
    if enriched_csv:
        logger.info(f"\n🎯 NEXT STEPS:")
        logger.info(f"   1. Download: {enriched_csv.name}")
        logger.info(f"   2. Open in Excel/Google Sheets")
        logger.info(f"   3. Review definitions and grammar forms")
        logger.info(f"   4. Add English translations")
        logger.info(f"   5. Add Italian translations")
        logger.info(f"   6. Categorize terms")


if __name__ == "__main__":
    main()
