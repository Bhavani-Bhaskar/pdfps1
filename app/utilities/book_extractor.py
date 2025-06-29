# utilities/book_extractor.py

import re
import fitz
from typing import Dict, List, Any, Optional

class BookExtractor:
    """
    Specialized extractor for book-type PDFs
    """
    
    def extract_book_structure(self, pdf_path: str) -> Dict[str, Any]:
        """Extract book-specific structural elements"""
        
        try:
            doc = fitz.open(pdf_path)
            
            # Extract book components
            toc = self._extract_table_of_contents(doc)
            chapters = self._extract_chapters(doc, toc)
            index = self._extract_index(doc)
            bibliography = self._extract_bibliography(doc)
            
            doc.close()
            
            return {
                'document_type': 'book',
                'table_of_contents': toc,
                'chapters': chapters,
                'index': index,
                'bibliography': bibliography,
                'total_chapters': len(chapters),
                'book_metadata': self._extract_book_metadata(pdf_path)
            }
            
        except Exception as e:
            return {'error': f"Book extraction failed: {str(e)}"}
    
    def _extract_table_of_contents(self, doc) -> List[Dict[str, Any]]:
        """Extract table of contents with page numbers"""
        toc_entries = []
        
        # Try to use PDF bookmarks first
        try:
            bookmarks = doc.get_toc()
            for level, title, page in bookmarks:
                toc_entries.append({
                    'level': level,
                    'title': title.strip(),
                    'page': page,
                    'type': 'bookmark'
                })
        except:
            # Fallback to text-based TOC extraction
            toc_entries = self._extract_text_based_toc(doc)
        
        return toc_entries
    
    def _extract_chapters(self, doc, toc: List[Dict]) -> List[Dict[str, Any]]:
        """Extract chapter content based on TOC"""
        chapters = []
        
        chapter_entries = [entry for entry in toc if 'chapter' in entry.get('title', '').lower()]
        
        for i, chapter in enumerate(chapter_entries):
            start_page = chapter['page'] - 1  # Convert to 0-based
            end_page = chapter_entries[i + 1]['page'] - 1 if i + 1 < len(chapter_entries) else len(doc)
            
            chapter_text = ""
            for page_num in range(start_page, min(end_page, len(doc))):
                chapter_text += doc[page_num].get_text()
            
            chapters.append({
                'chapter_number': i + 1,
                'title': chapter['title'],
                'start_page': start_page + 1,
                'end_page': end_page,
                'content': chapter_text.strip(),
                'word_count': len(chapter_text.split())
            })
        
        return chapters
    
    def _extract_index(self, doc) -> Dict[str, Any]:
        """Extract index from end of book"""
        # Look for index in last few pages
        index_content = ""
        for page in doc[-10:]:  # Check last 10 pages
            text = page.get_text()
            if 'index' in text.lower()[:100]:  # Index likely at beginning of page
                index_content = text
                break
        
        return {
            'present': bool(index_content),
            'content': index_content[:1000] if index_content else "",  # First 1000 chars
            'entries_count': len(re.findall(r'^[A-Za-z]', index_content, re.MULTILINE))
        }
    
    def _extract_bibliography(self, doc) -> Dict[str, Any]:
        """Extract bibliography/references section"""
        bibliography_content = ""
        
        # Look for bibliography in last pages
        for page in doc[-20:]:
            text = page.get_text().lower()
            if any(keyword in text for keyword in ['bibliography', 'references', 'works cited']):
                bibliography_content = page.get_text()
                break
        
        return {
            'present': bool(bibliography_content),
            'content': bibliography_content[:2000] if bibliography_content else "",
            'reference_count': len(re.findall(r'^\d+\.', bibliography_content, re.MULTILINE))
        }
    
    def _extract_book_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract book-specific metadata"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            # Extract from first few pages
            first_page_text = doc[0].get_text() if len(doc) > 0 else ""
            
            # Try to extract title, author, publisher
            title = self._extract_title_from_text(first_page_text)
            author = self._extract_author_from_text(first_page_text)
            publisher = self._extract_publisher_from_text(first_page_text)
            
            doc.close()
            
            return {
                'title': title or metadata.get('title', ''),
                'author': author or metadata.get('author', ''),
                'publisher': publisher,
                'creation_date': metadata.get('creationDate', ''),
                'page_count': len(doc)
            }
            
        except Exception as e:
            return {'extraction_error': str(e)}
