# utilities/technical_report_extractor.py

import re
import fitz
from typing import Dict, List, Any, Optional

class TechnicalReportExtractor:
    """
    Specialized extractor for technical report PDFs
    """
    
    def extract_report_structure(self, pdf_path: str) -> Dict[str, Any]:
        """Extract technical report structural elements"""
        
        try:
            doc = fitz.open(pdf_path)
            
            # Extract report components
            executive_summary = self._extract_executive_summary(doc)
            recommendations = self._extract_recommendations(doc)
            technical_specs = self._extract_technical_specifications(doc)
            appendices = self._extract_appendices(doc)
            methodology = self._extract_methodology(doc)
            
            doc.close()
            
            return {
                'document_type': 'technical_report',
                'executive_summary': executive_summary,
                'recommendations': recommendations,
                'technical_specifications': technical_specs,
                'appendices': appendices,
                'methodology': methodology,
                'report_metadata': self._extract_report_metadata(pdf_path)
            }
            
        except Exception as e:
            return {'error': f"Technical report extraction failed: {str(e)}"}
    
    def _extract_executive_summary(self, doc) -> Dict[str, Any]:
        """Extract executive summary section"""
        
        for page in doc[:5]:  # Usually in first 5 pages
            text = page.get_text()
            
            # Look for executive summary
            summary_match = re.search(r'executive\s+summary\s*[\n:]?(.*?)(?=\n\s*(?:\d+\.|\w+:|\n\n))', 
                                    text, re.IGNORECASE | re.DOTALL)
            
            if summary_match:
                summary_text = summary_match.group(1).strip()
                return {
                    'present': True,
                    'content': summary_text,
                    'word_count': len(summary_text.split()),
                    'page': page.number + 1
                }
        
        return {'present': False, 'content': '', 'word_count': 0}
    
    def _extract_recommendations(self, doc) -> Dict[str, Any]:
        """Extract recommendations section"""
        
        recommendations_text = ""
        recommendations_list = []
        
        for page in doc:
            text = page.get_text()
            
            # Look for recommendations section
            if re.search(r'recommendations?\s*$', text, re.IGNORECASE | re.MULTILINE):
                recommendations_text = text
                
                # Extract individual recommendations
                rec_patterns = [
                    r'^\d+\.\s*(.+?)(?=^\d+\.|\Z)',  # 1. recommendation format
                    r'^[•·]\s*(.+?)(?=^[•·]|\Z)',    # • bullet format
                ]
                
                for pattern in rec_patterns:
                    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
                    recommendations_list.extend([rec.strip() for rec in matches])
                
                break
        
        return {
            'present': bool(recommendations_text),
            'content': recommendations_text[:1500] if recommendations_text else "",
            'recommendations': recommendations_list[:10],  # First 10 recommendations
            'count': len(recommendations_list)
        }
    
    def _extract_technical_specifications(self, doc) -> Dict[str, Any]:
        """Extract technical specifications and data"""
        
        tech_specs = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            
            # Look for technical specification patterns
            spec_patterns = [
                r'(specification[s]?\s*[:]\s*[^\n]+)',
                r'(technical\s+data\s*[:]\s*[^\n]+)',
                r'(parameters?\s*[:]\s*[^\n]+)',
                r'(\w+\s*[:]\s*\d+[\.\d]*\s*\w+)'  # Parameter: value unit
            ]
            
            for pattern in spec_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    tech_specs.append({
                        'specification': match.strip(),
                        'page': page_num + 1
                    })
        
        return {
            'specifications': tech_specs[:20],  # First 20 specs
            'count': len(tech_specs)
        }
    
    def _extract_appendices(self, doc) -> Dict[str, Any]:
        """Extract appendices information"""
        
        appendices = []
        
        # Look for appendices in last portion of document
        for page_num, page in enumerate(doc[-20:], start=len(doc)-20):
            text = page.get_text()
            
            # Look for appendix markers
            appendix_matches = re.findall(r'(appendix\s+[a-z]\s*[:\-]?\s*[^\n]+)', text, re.IGNORECASE)
            
            for match in appendix_matches:
                appendices.append({
                    'title': match.strip(),
                    'page': page_num + 1
                })
        
        return {
            'present': bool(appendices),
            'appendices': appendices,
            'count': len(appendices)
        }
    
    def _extract_methodology(self, doc) -> Dict[str, Any]:
        """Extract methodology section"""
        
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Look for methodology section
        methodology_match = re.search(r'methodology\s*[\n:]?(.*?)(?=\n\s*(?:\d+\.|\w+:))', 
                                    full_text, re.IGNORECASE | re.DOTALL)
        
        if methodology_match:
            methodology_text = methodology_match.group(1).strip()
            return {
                'present': True,
                'content': methodology_text[:1000],  # First 1000 chars
                'word_count': len(methodology_text.split())
            }
        
        return {'present': False, 'content': '', 'word_count': 0}
