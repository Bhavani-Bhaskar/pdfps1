# utilities/table_extractor.py (Enhanced for research papers)

import os
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

import camelot
import pdfplumber
import pandas as pd

# Suppress warnings at module level
warnings.filterwarnings("ignore", category=UserWarning, module="camelot")
warnings.filterwarnings("ignore", message=".*does not lie in column range.*")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_tables(pdf_path: str):
    """
    Enhanced table extraction optimized for research papers
    """
    if not os.path.isfile(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        return [{'error': 'File not found'}]
    
    try:
        # Suppress warnings during extraction
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Try multiple strategies for research papers
            strategies = [
                ("camelot_lattice_research", lambda: _camelot_research_optimized(pdf_path, "lattice")),
                ("camelot_stream_research", lambda: _camelot_research_optimized(pdf_path, "stream")),
                ("pdfplumber_research", lambda: _pdfplumber_research_optimized(pdf_path)),
            ]
            
            results = []
            with ThreadPoolExecutor(max_workers=len(strategies)) as executor:
                future_to_name = {executor.submit(func): name for name, func in strategies}
                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        tables, score = future.result()
                        results.append((name, tables, score))
                    except Exception as e:
                        logger.warning(f"Strategy {name} raised exception: {e}")
            
            # Select best strategy by highest average score
            if results:
                best_name, best_tables, best_score = max(results, key=lambda x: x[2], default=(None, [], 0))
                logger.info(f"Best strategy: {best_name} with score={best_score:.2f}")
                
                # Prepare output
                output = []
                for idx, df in enumerate(best_tables, start=1):
                    output.append({
                        'page': idx,
                        'table': df,
                        'method': best_name,
                        'score': best_score,
                        'shape': f"{df.shape[0]} rows × {df.shape[1]} columns" if hasattr(df, 'shape') else "Unknown",
                        'accuracy': f"{best_score:.1f}%"
                    })
                
                return output if output else [{'info': 'No tables detected'}]
            else:
                return [{'info': 'All extraction strategies failed'}]
        
    except Exception as e:
        logger.error(f"Table extraction failed: {str(e)}")
        return [{'error': f'Extraction failed: {str(e)}'}]

def _camelot_research_optimized(pdf_path, flavor):
    """Camelot extraction optimized for research papers"""
    try:
        # Research paper specific settings
        if flavor == "lattice":
            tables = camelot.read_pdf(
                pdf_path, 
                flavor='lattice',
                pages='all',
                line_scale=40,
                copy_text=['h'],
                strip_text='\n',
                suppress_stdout=True  # Suppress camelot warnings
            )
        else:  # stream
            tables = camelot.read_pdf(
                pdf_path,
                flavor='stream',
                pages='all',
                row_tol=2,
                edge_tol=100,
                suppress_stdout=True  # Suppress camelot warnings
            )
        
        dfs = []
        scores = []
        
        for table in tables:
            try:
                df = table.df
                if not df.empty:
                    # Clean the dataframe
                    df = df.replace('', pd.NA).dropna(how='all').dropna(axis=1, how='all')
                    if not df.empty:
                        dfs.append(df)
                        # Calculate confidence score
                        score = (df.count().sum() / df.size) * 100 if df.size > 0 else 0
                        scores.append(score)
            except Exception as e:
                logger.warning(f"Error processing table: {e}")
                continue
        
        avg_score = sum(scores) / len(scores) if scores else 0
        logger.info(f"Camelot {flavor}: extracted {len(dfs)} tables, score={avg_score:.2f}")
        return dfs, avg_score
        
    except Exception as e:
        logger.warning(f"Camelot {flavor} failed: {e}")
        return [], 0

def _pdfplumber_research_optimized(pdf_path):
    """PDFPlumber extraction optimized for research papers"""
    dfs = []
    scores = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    # Research paper optimized settings
                    tables = page.extract_tables(table_settings={
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines", 
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "edge_min_length": 3,
                        "min_words_vertical": 2,
                        "min_words_horizontal": 1
                    })
                    
                    for table in tables:
                        if table and len(table) > 1:
                            try:
                                # Convert to DataFrame
                                headers = table[0] if table[0] else [f"Col_{i}" for i in range(len(table[0]))]
                                data = table[1:] if len(table) > 1 else []
                                
                                if data:
                                    df = pd.DataFrame(data, columns=headers)
                                    df = df.replace('', pd.NA).dropna(how='all').dropna(axis=1, how='all')
                                    
                                    if not df.empty:
                                        dfs.append(df)
                                        score = (df.count().sum() / df.size) * 100 if df.size > 0 else 0
                                        scores.append(score)
                            except Exception as e:
                                logger.warning(f"Error converting table to DataFrame: {e}")
                                continue
                                
                except Exception as e:
                    logger.warning(f"Error extracting tables from page: {e}")
                    continue
        
        avg_score = sum(scores) / len(scores) if scores else 0
        logger.info(f"PDFPlumber research: extracted {len(dfs)} tables, score={avg_score:.2f}")
        return dfs, avg_score
        
    except Exception as e:
        logger.warning(f"PDFPlumber research extraction failed: {e}")
        return [], 0
