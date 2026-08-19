"""
Multi-source Web Text Scraper for Swedish Social Services Legislation

Scrapes from multiple authoritative sources:
1. Lagen.nu - Consolidated law with legal interpretation
2. Lagar.se - Legislative database with full text
3. Infolex.se - Expert commentary on legislation
"""

import os
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List
from datetime import datetime
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiSourceScraper:
    """Scrapes legislation from multiple Swedish legal sources"""
    
    def __init__(self, save_dir=RAW_DATA_DIR):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Create separate folders for each source
        self.web_text_dir = self.save_dir / "web_text"
        self.web_text_dir.mkdir(parents=True, exist_ok=True)
        
        self.sources = {
            'lagen_nu': {
                'name': 'Lagen.nu',
                'url': 'https://lagen.nu/2025:400/konsolidering/2025:400',
                'dir': self.web_text_dir / 'lagen_nu'
            },
            'lagar_se': {
                'name': 'Lagar.se',
                'url': 'https://www.lagar.se/lag/sfs-2025-400/',
                'dir': self.web_text_dir / 'lagar_se'
            },
            'infolex': {
                'name': 'Infolex',
                'url': 'https://infolex.se/lag/socialtjanstlagen/',
                'dir': self.web_text_dir / 'infolex'
            }
        }
        
        # Create directories for each source
        for source in self.sources.values():
            source['dir'].mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_lagen_nu(self):
        """
        Scrapes from Lagen.nu (consolidated law)
        
        Returns:
            dict with 'full_text' and 'filepath'
        """
        logger.info("\n" + "=" * 70)
        logger.info("SCRAPING LAGEN.NU")
        logger.info("=" * 70)
        
        url = self.sources['lagen_nu']['url']
        
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Lagen.nu typically has content in div with class 'container' or 'content'
            main_content = soup.find(['main', 'article'])
            if not main_content:
                main_content = soup.find('div', class_=['container', 'content', 'dokumenttext'])
            if not main_content:
                main_content = soup.body
            
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_text = '\n'.join(lines)
            
            logger.info(f"✓ Scraped {len(cleaned_text):,} characters from Lagen.nu")
            
            # Save file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"lagen_nu_full_{timestamp}.txt"
            filepath = self.sources['lagen_nu']['dir'] / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            logger.info(f"✓ Saved to: {filepath}")
            
            return {
                'source': 'lagen_nu',
                'full_text': cleaned_text,
                'filepath': filepath,
                'char_count': len(cleaned_text)
            }
            
        except Exception as e:
            logger.error(f"Error scraping Lagen.nu: {e}")
            return None
    
    def scrape_lagar_se(self):
        """
        Scrapes from Lagar.se (legislative database)
        
        Returns:
            dict with 'full_text' and 'filepath'
        """
        logger.info("\n" + "=" * 70)
        logger.info("SCRAPING LAGAR.SE")
        logger.info("=" * 70)
        
        url = self.sources['lagar_se']['url']
        
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Lagar.se typically has content in specific div
            main_content = soup.find(['main', 'article'])
            if not main_content:
                main_content = soup.find('div', class_=['container', 'content', 'body', 'dokumenttext'])
            if not main_content:
                main_content = soup.body
            
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_text = '\n'.join(lines)
            
            logger.info(f"✓ Scraped {len(cleaned_text):,} characters from Lagar.se")
            
            # Save file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"lagar_se_full_{timestamp}.txt"
            filepath = self.sources['lagar_se']['dir'] / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            logger.info(f"✓ Saved to: {filepath}")
            
            return {
                'source': 'lagar_se',
                'full_text': cleaned_text,
                'filepath': filepath,
                'char_count': len(cleaned_text)
            }
            
        except Exception as e:
            logger.error(f"Error scraping Lagar.se: {e}")
            return None
    
    def scrape_infolex(self):
        """
        Scrapes from Infolex.se (expert commentary)
        
        Returns:
            dict with 'full_text' and 'filepath'
        """
        logger.info("\n" + "=" * 70)
        logger.info("SCRAPING INFOLEX.SE")
        logger.info("=" * 70)
        
        url = self.sources['infolex']['url']
        
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav"]):
                script.decompose()
            
            # Infolex typically has content in div with class 'text-content' or similar
            main_content = soup.find(['main', 'article'])
            if not main_content:
                main_content = soup.find('div', class_=['content', 'text-content', 'body', 'dokumenttext'])
            if not main_content:
                main_content = soup.body
            
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_text = '\n'.join(lines)
            
            logger.info(f"✓ Scraped {len(cleaned_text):,} characters from Infolex")
            
            # Save file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"infolex_full_{timestamp}.txt"
            filepath = self.sources['infolex']['dir'] / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            logger.info(f"✓ Saved to: {filepath}")
            
            return {
                'source': 'infolex',
                'full_text': cleaned_text,
                'filepath': filepath,
                'char_count': len(cleaned_text)
            }
            
        except Exception as e:
            logger.error(f"Error scraping Infolex: {e}")
            return None
    
    def chunk_text(self, text, source_name, chunk_size=5000):
        """
        Splits text into chunks by character count
        
        Args:
            text (str): Full text to chunk
            source_name (str): Name of source for output folder
            chunk_size (int): Approximate characters per chunk
            
        Yields:
            dict with chunk data
        """
        output_dir = self.sources[source_name]['dir'] / "chunks"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Splitting text into chunks of ~{chunk_size} characters")
        
        chunk_number = 0
        start_idx = 0
        
        while start_idx < len(text):
            chunk_number += 1
            end_idx = min(start_idx + chunk_size, len(text))
            
            # Try to break at a paragraph boundary
            if end_idx < len(text):
                last_newline = text.rfind('\n', start_idx, end_idx)
                if last_newline > start_idx:
                    end_idx = last_newline
            
            chunk_text = text[start_idx:end_idx].strip()
            
            if not chunk_text:
                start_idx = end_idx
                continue
            
            # Save chunk to file
            chunk_filename = f"chunk_{chunk_number:03d}.txt"
            chunk_filepath = output_dir / chunk_filename
            
            with open(chunk_filepath, 'w', encoding='utf-8') as f:
                f.write(chunk_text)
            
            logger.info(f"  Saved chunk {chunk_number}: {len(chunk_text)} characters")
            
            yield {
                'chunk_number': chunk_number,
                'text': chunk_text,
                'char_count': len(chunk_text),
                'filepath': chunk_filepath
            }
            
            start_idx = end_idx
    
    def chunk_by_sections(self, text, source_name):
        """
        Splits text by sections (using § as delimiter)
        
        Args:
            text (str): Full text
            source_name (str): Name of source for output folder
            
        Yields:
            dict with section data
        """
        output_dir = self.sources[source_name]['dir'] / "sections"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Splitting text by sections (§)")
        
        # Split by § symbol
        sections = text.split('§')
        
        section_number = 0
        for idx, section_text in enumerate(sections):
            if not section_text.strip():
                continue
            
            section_number += 1
            
            # Add the § symbol back except for the first section
            if idx > 0:
                section_text = '§ ' + section_text
            
            section_text = section_text.strip()
            
            # Save section to file
            section_filename = f"section_{section_number:03d}.txt"
            section_filepath = output_dir / section_filename
            
            with open(section_filepath, 'w', encoding='utf-8') as f:
                f.write(section_text)
            
            logger.info(f"  Saved section {section_number}: {len(section_text)} characters")
            
            yield {
                'section_number': section_number,
                'text': section_text,
                'char_count': len(section_text),
                'filepath': section_filepath
            }
    
    def scrape_all_sources(self, chunk_by='sections'):
        """
        Scrape all sources and chunk the text
        
        Args:
            chunk_by (str): 'size' or 'sections' - how to chunk
            
        Returns:
            dict with results from all sources
        """
        logger.info("\n" + "=" * 70)
        logger.info("MULTI-SOURCE LEGISLATION SCRAPER")
        logger.info("=" * 70)
        
        results = []
        
        # Scrape all three sources
        for scraper_method in [self.scrape_lagen_nu, self.scrape_lagar_se, self.scrape_infolex]:
            result = scraper_method()
            
            if result:
                # Chunk the text
                chunks = []
                if chunk_by == 'size':
                    for chunk_data in self.chunk_text(result['full_text'], result['source']):
                        chunks.append(chunk_data)
                elif chunk_by == 'sections':
                    for section_data in self.chunk_by_sections(result['full_text'], result['source']):
                        chunks.append(section_data)
                
                result['chunks'] = chunks
                results.append(result)
                
                # Small delay between requests to be respectful
                time.sleep(2)
        
        return results


def main():
    """Main function to scrape all sources"""
    
    scraper = MultiSourceScraper()
    results = scraper.scrape_all_sources(chunk_by='sections')
    
    logger.info("\n" + "=" * 70)
    logger.info("SCRAPING COMPLETE!")
    logger.info("=" * 70)
    
    total_chars = 0
    for result in results:
        source_name = result['source']
        char_count = result['char_count']
        chunk_count = len(result['chunks'])
        
        total_chars += char_count
        
        logger.info(f"\n✓ {source_name.upper()}")
        logger.info(f"  Characters: {char_count:,}")
        logger.info(f"  Sections: {chunk_count}")
        logger.info(f"  Saved to: {result['filepath'].parent}")
    
    logger.info(f"\n📊 TOTAL")
    logger.info(f"  Sources scraped: {len(results)}")
    logger.info(f"  Total characters: {total_chars:,}")
    logger.info(f"  Output directory: {scraper.web_text_dir}")


if __name__ == "__main__":
    main()
