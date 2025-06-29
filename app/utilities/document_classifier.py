# utilities/document_classifier.py

import re
import fitz  # PyMuPDF
from typing import Dict, List, Any, Optional
from collections import Counter
import numpy as np

class DocumentTypeClassifier:
    """
    Intelligent document type classification for books, research papers, and technical reports
    """
    
    def __init__(self):
        self.classification_rules = {
            'book': {
                'keywords': ['chapter', 'table of contents', 'index', 'preface', 'foreword', 'appendix'],
                'structure_patterns': [r'chapter\s+\d+', r'part\s+[ivx]+', r'section\s+\d+\.\d+'],
                'min_pages': 50,
                'toc_indicators': ['contents', 'table of contents']
            },
            'research_paper': {
                'keywords': ['abstract', 'introduction', 'methodology', 'results', 'discussion', 'references', 'bibliography'],
                'structure_patterns': [r'abstract\s*$', r'introduction\s*$', r'conclusion\s*$', r'references\s*$'],
                'min_pages': 4,
                'max_pages': 50,
                'citation_patterns': [r'\[\d+\]', r'\(\w+\s+et\s+al\.?\s*,\s*\d{4}\)']
            },
            'technical_report': {
                'keywords': ['executive summary', 'recommendations', 'technical specifications', 'methodology', 'findings'],
                'structure_patterns': [r'executive\s+summary', r'recommendations?', r'technical\s+specifications?'],
                'min_pages': 10,
                'report_indicators': ['report', 'technical document', 'analysis', 'evaluation']
            }
        }
    
    def classify_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Classify PDF document type and extract type-specific characteristics
        """
        try:
            doc = fitz.open(pdf_path)
            
            # Extract document characteristics
            characteristics = self._extract_characteristics(doc)
            
            # Calculate scores for each document type
            scores = self._calculate_type_scores(characteristics)
            
            # Determine primary classification
            primary_type = max(scores, key=scores.get)
            confidence = scores[primary_type]
            
            doc.close()
            
            return {
                'primary_type': primary_type,
                'confidence': confidence,
                'scores': scores,
                'characteristics': characteristics,
                'processing_strategy': self._get_processing_strategy(primary_type),
                'extraction_priorities': self._get_extraction_priorities(primary_type)
            }
            
        except Exception as e:
            return {
                'primary_type': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_characteristics(self, doc) -> Dict[str, Any]:
        """Extract document characteristics for classification"""
        
        # Basic document info
        page_count = len(doc)
        
        # Extract text from first few pages and last few pages
        first_pages_text = ""
        last_pages_text = ""
        full_text = ""
        
        # Analyze first 5 pages
        for i in range(min(5, page_count)):
            first_pages_text += doc[i].get_text().lower()
        
        # Analyze last 5 pages
        for i in range(max(0, page_count-5), page_count):
            last_pages_text += doc[i].get_text().lower()
        
        # Sample middle pages for full analysis
        sample_pages = min(10, page_count)
        for i in range(0, page_count, max(1, page_count // sample_pages)):
            full_text += doc[i].get_text().lower()
        
        # Extract structural elements
        headings = self._extract_headings(doc)
        toc_present = self._detect_table_of_contents(doc)
        citations = self._count_citations(full_text)
        
        return {
            'page_count': page_count,
            'first_pages_text': first_pages_text,
            'last_pages_text': last_pages_text,
            'full_text': full_text,
            'headings': headings,
            'toc_present': toc_present,
            'citation_count': citations,
            'has_abstract': 'abstract' in first_pages_text,
            'has_references': 'references' in last_pages_text or 'bibliography' in last_pages_text,
            'has_chapters': bool(re.search(r'chapter\s+\d+', full_text)),
            'has_executive_summary': 'executive summary' in first_pages_text
        }
    
    def _calculate_type_scores(self, characteristics: Dict) -> Dict[str, float]:
        """Calculate classification scores for each document type"""
        
        scores = {'book': 0.0, 'research_paper': 0.0, 'technical_report': 0.0}
        
        # Book scoring
        if characteristics['page_count'] >= 50:
            scores['book'] += 0.3
        if characteristics['has_chapters']:
            scores['book'] += 0.4
        if characteristics['toc_present']:
            scores['book'] += 0.3
        
        # Research paper scoring
        if 4 <= characteristics['page_count'] <= 50:
            scores['research_paper'] += 0.2
        if characteristics['has_abstract']:
            scores['research_paper'] += 0.3
        if characteristics['has_references']:
            scores['research_paper'] += 0.2
        if characteristics['citation_count'] > 10:
            scores['research_paper'] += 0.3
        
        # Technical report scoring
        if characteristics['page_count'] >= 10:
            scores['technical_report'] += 0.2
        if characteristics['has_executive_summary']:
            scores['technical_report'] += 0.4
        if 'recommendation' in characteristics['full_text']:
            scores['technical_report'] += 0.2
        if 'technical' in characteristics['full_text']:
            scores['technical_report'] += 0.2
        
        return scores
    
    def _get_processing_strategy(self, doc_type: str) -> Dict[str, Any]:
        """Get type-specific processing strategy"""
        
        strategies = {
            'book': {
                'chapter_extraction': True,
                'toc_processing': True,
                'index_processing': True,
                'footnote_extraction': True,
                'cross_reference_tracking': True
            },
            'research_paper': {
                'abstract_extraction': True,
                'citation_extraction': True,
                'figure_caption_processing': True,
                'reference_parsing': True,
                'author_extraction': True
            },
            'technical_report': {
                'executive_summary_extraction': True,
                'recommendation_extraction': True,
                'technical_specs_processing': True,
                'appendix_processing': True,
                'data_table_extraction': True
            }
        }
        
        return strategies.get(doc_type, {})
    
    def _get_extraction_priorities(self, doc_type: str) -> List[str]:
        """Get extraction priorities for document type"""
        
        priorities = {
            'book': ['chapters', 'table_of_contents', 'index', 'text_content', 'images'],
            'research_paper': ['abstract', 'citations', 'references', 'figures', 'tables', 'text_content'],
            'technical_report': ['executive_summary', 'recommendations', 'technical_specs', 'appendices', 'tables']
        }
        
        return priorities.get(doc_type, ['text_content', 'images', 'tables'])
    
    def _extract_headings(self, doc) -> List[str]:
        """Extract potential headings from document"""
        headings = []
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["size"] > 12:  # Larger font likely heading
                                headings.append(span["text"].strip())
        return headings
    
    def _detect_table_of_contents(self, doc) -> bool:
        """Detect presence of table of contents"""
        for page in doc[:5]:  # Check first 5 pages
            text = page.get_text().lower()
            if any(indicator in text for indicator in ['table of contents', 'contents', 'toc']):
                return True
        return False
    
    def _count_citations(self, text: str) -> int:
        """Count citation patterns in text"""
        citation_patterns = [
            r'\[\d+\]',  # [1], [23], etc.
            r'\(\w+\s+et\s+al\.?\s*,?\s*\d{4}\)',  # (Smith et al., 2020)
            r'\(\w+,?\s*\d{4}\)',  # (Smith, 2020)
        ]
        
        total_citations = 0
        for pattern in citation_patterns:
            total_citations += len(re.findall(pattern, text))
        
        return total_citations
