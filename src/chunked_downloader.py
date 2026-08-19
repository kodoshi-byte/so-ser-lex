"""
Chunked PDF Downloader for Swedish Social Services Legislation

Downloads large PDFs in manageable chunks and processes them incrementally.
Particularly useful for long documents like Socialtjänstlag.
"""

import os
import logging
import requests
from pathlib import Path
from typing import List, Dict, Generator
import pdfplumber
from datetime import datetime
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, SOCIALTJANSTLAG_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChunkedPDFDownloader:
    """Downloads and processes large PDFs in chunks"""
    
    def __init__(self, save_dir=RAW_DATA_DIR, chunk_size=100 * 1024 * 1024):
        """
        Args:
            save_dir: Directory to save PDFs
            chunk_size: Size of each download chunk in bytes (default 100MB)
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def find_pdf_link(self, url):
        """
        Finds the PDF download link from Riksdagen legislation page
        
        Args:
            url: URL to legislation page
            
        Returns:
            str: Direct PDF URL or None
        """
        logger.info(f"Searching for PDF link at: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Look for PDF link patterns in Riksdagen
            # Common patterns: .pdf in href
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'pdf' in href.lower():
                    if href.startswith('/'):
                        href = 'https://www.riksdagen.se' + href
                    elif not href.startswith('http'):
                        href = 'https://www.riksdagen.se/' + href
                    
                    logger.info(f"Found PDF link: {href}")
                    return href
            
            logger.warning("No PDF link found")
            return None
            
        except Exception as e:
            logger.error(f"Error finding PDF link: {e}")
            return None
    
    def get_file_size(self, url):
        """
        Gets the size of a file from its URL without downloading it
        
        Args:
            url: URL to check
            
        Returns:
            int: File size in bytes, or None if unable to determine
        """
        try:
            response = self.session.head(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            size = response.headers.get('content-length')
            if size:
                size = int(size)
                size_mb = size / (1024 * 1024)
                logger.info(f"File size: {size_mb:.2f} MB ({size} bytes)")
                return size
            
            logger.warning("Could not determine file size")
            return None
            
        except Exception as e:
            logger.error(f"Error checking file size: {e}")
            return None
    
    def download_file_chunked(self, url, filename=None, progress_callback=None):
        """
        Downloads file in chunks
        
        Args:
            url: File URL
            filename: Custom filename (optional)
            progress_callback: Function to call with progress (bytes_downloaded, total_bytes)
            
        Returns:
            Path: Path to downloaded file or None if failed
        """
        try:
            logger.info(f"Starting chunked download from: {url}")
            
            # Get file size first
            total_size = self.get_file_size(url)
            if not total_size:
                logger.warning("Could not determine file size, proceeding anyway")
                total_size = None
            
            # Generate filename
            if filename is None:
                filename = url.split('/')[-1]
                if not filename.endswith('.pdf'):
                    filename = f"socialtjanstlag_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            filepath = self.save_dir / filename
            
            # Download with streaming
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size:
                            progress_callback(downloaded, total_size)
                        
                        # Log progress
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            logger.info(f"Downloaded: {mb_downloaded:.2f} MB / {mb_total:.2f} MB ({percent:.1f}%)")
                        else:
                            mb_downloaded = downloaded / (1024 * 1024)
                            logger.info(f"Downloaded: {mb_downloaded:.2f} MB")
            
            logger.info(f"Download complete: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None
    
    def extract_pages_chunked(self, pdf_path, pages_per_chunk=10, output_dir=None):
        """
        Extracts PDF in chunks by pages
        
        Args:
            pdf_path: Path to PDF
            pages_per_chunk: Number of pages per chunk
            output_dir: Directory to save text chunks
            
        Yields:
            Dict with chunk data: {
                'chunk_number': int,
                'start_page': int,
                'end_page': int,
                'text': str,
                'page_texts': list,
                'filepath': Path
            }
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return
        
        if output_dir is None:
            output_dir = PROCESSED_DATA_DIR / pdf_path.stem
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Opening PDF: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Total pages: {total_pages}")
                
                chunk_number = 0
                for start_page in range(0, total_pages, pages_per_chunk):
                    end_page = min(start_page + pages_per_chunk, total_pages)
                    chunk_number += 1
                    
                    logger.info(f"Processing chunk {chunk_number}: pages {start_page + 1} to {end_page}")
                    
                    chunk_text = ""
                    page_texts = []
                    
                    for page_num in range(start_page, end_page):
                        try:
                            page = pdf.pages[page_num]
                            text = page.extract_text()
                            
                            if text:
                                page_texts.append({
                                    'page_number': page_num + 1,
                                    'text': text
                                })
                                chunk_text += f"\n--- PAGE {page_num + 1} ---\n{text}\n"
                                
                        except Exception as e:
                            logger.warning(f"Error extracting page {page_num + 1}: {e}")
                    
                    # Save chunk to file
                    chunk_filename = f"chunk_{chunk_number:03d}_pages_{start_page + 1}-{end_page}.txt"
                    chunk_filepath = output_dir / chunk_filename
                    
                    with open(chunk_filepath, 'w', encoding='utf-8') as f:
                        f.write(chunk_text)
                    
                    logger.info(f"Saved chunk to: {chunk_filepath}")
                    
                    yield {
                        'chunk_number': chunk_number,
                        'start_page': start_page + 1,
                        'end_page': end_page,
                        'text': chunk_text,
                        'page_texts': page_texts,
                        'filepath': chunk_filepath
                    }
        
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
    
    def process_large_pdf(self, url, filename=None, pages_per_chunk=10):
        """
        Complete workflow: download PDF in chunks and extract pages in chunks
        
        Args:
            url: PDF URL
            filename: Custom filename
            pages_per_chunk: Pages per extraction chunk
            
        Returns:
            Generator yielding chunk data as extraction progresses
        """
        # Download PDF
        pdf_path = self.download_file_chunked(url, filename)
        
        if not pdf_path:
            logger.error("Failed to download PDF")
            return
        
        # Extract pages in chunks
        logger.info("Starting page extraction in chunks...")
        
        for chunk_data in self.extract_pages_chunked(pdf_path, pages_per_chunk):
            yield chunk_data


def progress_callback(downloaded, total):
    """Example progress callback function"""
    percent = (downloaded / total) * 100
    mb_downloaded = downloaded / (1024 * 1024)
    mb_total = total / (1024 * 1024)
    
    # Simple progress bar
    bar_length = 40
    filled = int(bar_length * downloaded / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f'\r[{bar}] {percent:.1f}% ({mb_downloaded:.1f}MB/{mb_total:.1f}MB)', end='')


def main():
    """Main function to demonstrate chunked download"""
    
    downloader = ChunkedPDFDownloader()
    
    # Step 1: Find PDF link
    logger.info("=" * 60)
    logger.info("STEP 1: Finding PDF link on Riksdagen")
    logger.info("=" * 60)
    
    pdf_url = downloader.find_pdf_link(SOCIALTJANSTLAG_URL)
    
    if not pdf_url:
        logger.error("Could not find PDF link")
        return
    
    # Step 2: Download PDF in chunks
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Downloading PDF in chunks")
    logger.info("=" * 60)
    
    pdf_path = downloader.download_file_chunked(pdf_url, progress_callback=progress_callback)
    print()  # New line after progress bar
    
    if not pdf_path:
        logger.error("Could not download PDF")
        return
    
    # Step 3: Extract pages in chunks
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Extracting pages in chunks")
    logger.info("=" * 60)
    
    chunk_count = 0
    total_text = ""
    
    for chunk_data in downloader.extract_pages_chunked(pdf_path, pages_per_chunk=15):
        chunk_count += 1
        total_text += chunk_data['text']
        
        logger.info(f"✓ Chunk {chunk_data['chunk_number']} complete: "
                   f"pages {chunk_data['start_page']}-{chunk_data['end_page']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("DOWNLOAD AND EXTRACTION COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"Total chunks processed: {chunk_count}")
    logger.info(f"Total text size: {len(total_text) / 1024:.2f} KB")
    
    # Save combined text
    combined_path = PROCESSED_DATA_DIR / "socialtjanstlag_complete.txt"
    with open(combined_path, 'w', encoding='utf-8') as f:
        f.write(total_text)
    
    logger.info(f"Combined text saved to: {combined_path}")


if __name__ == "__main__":
    main()
