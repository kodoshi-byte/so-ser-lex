"""
Web Text Scraper for Swedish Social Services Legislation

Scrapes the full text content from Riksdagen webpage (when PDF is not available)
and saves it in organized chunks.
"""

import os
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Generator, Dict
from datetime import datetime
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, SOCIALTJANSTLAG_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebTextScraper:
    """Scrapes and processes text from Riksdagen webpage"""
    
    def __init__(self, save_dir=RAW_DATA_DIR):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Create separate folder for web text
        self.web_text_dir = self.save_dir / "web_text"
        self.web_text_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_legislation_text(self, url):
        """
        Scrapes the full text content from Riksdagen legislation page
        
        Args:
            url (str): URL to the legislation page
            
        Returns:
            str: Full text content, or None if failed
        """
        logger.info(f"Scraping text from: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Look for main content containers (common Riksdagen patterns)
            main_content = None
            
            # Try different selectors for Riksdagen pages
            selectors = [
                'main',
                'article',
                {'class': 'content'},
                {'class': 'dokumenttext'},
                {'class': 'main-content'},
                {'id': 'mainContent'},
            ]
            
            for selector in selectors:
                if isinstance(selector, dict):
                    main_content = soup.find(attrs=selector)
                else:
                    main_content = soup.find(selector)
                
                if main_content:
                    logger.info(f"Found content with selector: {selector}")
                    break
            
            # If no main content found, use body
            if not main_content:
                logger.warning("No specific content container found, using body")
                main_content = soup.body
            
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_text = '\n'.join(lines)
            
            logger.info(f"Scraped {len(cleaned_text)} characters")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error scraping webpage: {e}")
            return None
    
    def save_full_text(self, text, filename=None):
        """
        Saves the full text to a file
        
        Args:
            text (str): Text content
            filename (str, optional): Custom filename
            
        Returns:
            Path: Path to saved file
        """
        if filename is None:
            filename = f"socialtjanstlag_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filepath = self.web_text_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Full text saved to: {filepath}")
        return filepath
    
    def chunk_text(self, text, chunk_size=5000, output_dir=None):
        """
        Splits text into chunks by character count
        
        Args:
            text (str): Full text to chunk
            chunk_size (int): Approximate characters per chunk
            output_dir (Path, optional): Where to save chunks
            
        Yields:
            Dict with chunk data
        """
        if output_dir is None:
            output_dir = self.web_text_dir / "chunks"
        
        output_dir = Path(output_dir)
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
            
            logger.info(f"Saved chunk {chunk_number}: {len(chunk_text)} characters")
            
            yield {
                'chunk_number': chunk_number,
                'text': chunk_text,
                'char_count': len(chunk_text),
                'filepath': chunk_filepath
            }
            
            start_idx = end_idx
    
    def chunk_by_sections(self, text, output_dir=None):
        """
        Splits text by sections (using § as delimiter)
        
        Args:
            text (str): Full text
            output_dir (Path, optional): Where to save chunks
            
        Yields:
            Dict with section data
        """
        if output_dir is None:
            output_dir = self.web_text_dir / "sections"
        
        output_dir = Path(output_dir)
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
            
            logger.info(f"Saved section {section_number}: {len(section_text)} characters")
            
            yield {
                'section_number': section_number,
                'text': section_text,
                'char_count': len(section_text),
                'filepath': section_filepath
            }
    
    def process_legislation(self, url, chunk_by='size'):
        """
        Complete workflow: scrape webpage and chunk text
        
        Args:
            url (str): Legislation webpage URL
            chunk_by (str): 'size' or 'sections' - how to chunk the text
            
        Returns:
            Dict with processing results
        """
        logger.info("=" * 60)
        logger.info("STARTING WEB TEXT SCRAPER")
        logger.info("=" * 60)
        
        # Step 1: Scrape text
        logger.info("\nSTEP 1: Scraping webpage...")
        text = self.scrape_legislation_text(url)
        
        if not text:
            logger.error("Failed to scrape webpage")
            return None
        
        logger.info(f"✓ Scraped {len(text):,} characters")
        
        # Step 2: Save full text
        logger.info("\nSTEP 2: Saving full text...")
        full_text_path = self.save_full_text(text)
        
        # Step 3: Chunk text
        logger.info(f"\nSTEP 3: Chunking text by {chunk_by}...")
        
        chunks = []
        if chunk_by == 'size':
            for chunk_data in self.chunk_text(text):
                chunks.append(chunk_data)
        elif chunk_by == 'sections':
            for section_data in self.chunk_by_sections(text):
                chunks.append(section_data)
        else:
            logger.error(f"Unknown chunking method: {chunk_by}")
            return None
        
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Total text size: {len(text):,} characters")
        logger.info(f"Total chunks/sections: {len(chunks)}")
        logger.info(f"Full text saved to: {full_text_path}")
        
        return {
            'full_text_path': full_text_path,
            'chunks': chunks,
            'total_chars': len(text),
            'total_chunks': len(chunks),
            'web_text_dir': self.web_text_dir
        }


def main():
    """Main function to scrape and chunk legislation text"""
    
    scraper = WebTextScraper()
    
    # Process the legislation
    result = scraper.process_legislation(SOCIALTJANSTLAG_URL, chunk_by='sections')
    
    if result:
        print(f"\n✓ Processing complete!")
        print(f"  Full text: {result['full_text_path']}")
        print(f"  Chunks/sections: {result['total_chunks']}")
        print(f"  Location: {result['web_text_dir']}")


if __name__ == "__main__":
    main()
