# utilities/research_paper_extractor.py

import re
import fitz
from typing import Dict, List, Any, Optional

class ResearchPaperExtractor:
    """
    Specialized extractor for research paper PDFs
    """
    
    def extract_paper_structure(self, pdf_path: str) -> Dict[str, Any]:
        """Extract research paper structural elements"""
        
        try:
            doc = fitz.open(pdf_path)
            
            # Extract paper components
            abstract = self._extract_abstract(doc)
            authors = self._extract_authors(doc)
            sections = self._extract_sections(doc)
            references = self._extract_references(doc)
            citations = self._extract_citations(doc)
            figures = self._extract_figure_captions(doc)
            
            doc.close()
            
            return {
                'document_type': 'research_paper',
                'abstract': abstract,
                'authors': authors,
                'sections': sections,
                'references': references,
                'citations': citations,
                'figures': figures,
                'paper_metadata': self._extract_paper_metadata(pdf_path)
            }
            
        except Exception as e:
            return {'error': f"Research paper extraction failed: {str(e)}"}
    
    def _extract_abstract(self, doc) -> Dict[str, Any]:
        """Extract abstract section"""
        
        for page in doc[:3]:  # Abstract usually in first 3 pages
            text = page.get_text()
            
            # Look for abstract section
            abstract_match = re.search(r'abstract\s*[\n:]?(.*?)(?=\n\s*(?:keywords?|introduction|1\.?\s+introduction))', 
                                     text, re.IGNORECASE | re.DOTALL)
            
            if abstract_match:
                abstract_text = abstract_match.group(1).strip()
                return {
                    'present': True,
                    'content': abstract_text,
                    'word_count': len(abstract_text.split()),
                    'page': page.number + 1
                }
        
        return {'present': False, 'content': '', 'word_count': 0}
    
    def _extract_authors(self, doc) -> List[Dict[str, Any]]:
        """Extract author information"""
        
        first_page_text = doc[0].get_text() if len(doc) > 0 else ""
        
        # Common author patterns in academic papers
        author_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*[,\n]\s*([A-Z][a-z]+\s+[A-Z][a-z]+))*',
            r'([A-Z]\.\s*[A-Z][a-z]+)(?:\s*[,\n]\s*([A-Z]\.\s*[A-Z][a-z]+))*'
        ]
        
        authors = []
        for pattern in author_patterns:
            matches = re.findall(pattern, first_page_text[:500])  # Check first 500 chars
            for match in matches:
                if isinstance(match, tuple):
                    authors.extend([name.strip() for name in match if name.strip()])
                else:
                    authors.append(match.strip())
        
        # Remove duplicates and clean
        unique_authors = list(dict.fromkeys(authors))
        
        return [{'name': author, 'affiliation': ''} for author in unique_authors[:10]]  # Limit to 10
    
    def _extract_sections(self, doc) -> List[Dict[str, Any]]:
        """Extract paper sections (Introduction, Methods, Results, etc.)"""
        
        sections = []
        full_text = ""
        
        # Collect all text
        for page in doc:
            full_text += f"\n--- Page {page.number + 1} ---\n"
            full_text += page.get_text()
        
        # Common academic section patterns
        section_patterns = [
            r'(\d+\.?\s*(?:introduction|background|literature\s+review))\s*\n',
            r'(\d+\.?\s*(?:methodology|methods|materials\s+and\s+methods))\s*\n',
            r'(\d+\.?\s*(?:results|findings|analysis))\s*\n',
            r'(\d+\.?\s*(?:discussion|conclusion|conclusions))\s*\n',
            r'(\d+\.?\s*(?:references|bibliography))\s*\n'
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                sections.append({
                    'title': match.group(1).strip(),
                    'start_position': match.start(),
                    'section_type': self._classify_section_type(match.group(1))
                })
        
        # Sort by position and extract content
        sections.sort(key=lambda x: x['start_position'])
        
        for i, section in enumerate(sections):
            start_pos = section['start_position']
            end_pos = sections[i + 1]['start_position'] if i + 1 < len(sections) else len(full_text)
            
            section['content'] = full_text[start_pos:end_pos].strip()[:1000]  # First 1000 chars
            section['word_count'] = len(section['content'].split())
        
        return sections
    
    def _extract_references(self, doc) -> Dict[str, Any]:
        """Extract references/bibliography"""
        
        references_text = ""
        reference_entries = []
        
        # Look for references in last pages
        for page in doc[-10:]:
            text = page.get_text()
            if re.search(r'references?\s*$', text, re.IGNORECASE | re.MULTILINE):
                references_text = text
                break
        
        if references_text:
            # Extract individual references
            ref_patterns = [
                r'^\[\d+\]\s*(.+?)(?=^\[\d+\]|\Z)',  # [1] reference format
                r'^\d+\.\s*(.+?)(?=^\d+\.|\Z)',      # 1. reference format
            ]
            
            for pattern in ref_patterns:
                matches = re.findall(pattern, references_text, re.MULTILINE | re.DOTALL)
                reference_entries.extend([ref.strip() for ref in matches])
        
        return {
            'present': bool(references_text),
            'content': references_text[:2000] if references_text else "",
            'entries': reference_entries[:20],  # First 20 references
            'count': len(reference_entries)
        }
    
    def _extract_citations(self, doc) -> Dict[str, Any]:
        """Extract in-text citations"""
        
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Citation patterns
        citation_patterns = [
            r'\[(\d+(?:,\s*\d+)*)\]',  # [1], [1,2,3]
            r'\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4})\)',  # (Smith, 2020), (Smith et al., 2020)
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, full_text)
            citations.extend(matches)
        
        return {
            'total_count': len(citations),
            'unique_citations': list(set(citations)),
            'citation_density': len(citations) / len(full_text.split()) if full_text else 0
        }
    
    def _extract_figure_captions(self, doc) -> List[Dict[str, Any]]:
        """Extract figure and table captions"""
        
        captions = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            
            # Figure caption patterns
            fig_patterns = [
                r'(Figure\s+\d+[.:]\s*[^\n]+)',
                r'(Fig\.\s+\d+[.:]\s*[^\n]+)',
                r'(Table\s+\d+[.:]\s*[^\n]+)'
            ]
            
            for pattern in fig_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    captions.append({
                        'caption': match.strip(),
                        'page': page_num + 1,
                        'type': 'figure' if 'fig' in match.lower() else 'table'
                    })
        
        return captions
