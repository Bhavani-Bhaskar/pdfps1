import camelot
import pandas as pd
from typing import List, Dict, Any
import os

def extract_tables(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from PDF using Camelot
    """
    tables_info = []
    
    try:
        # Extract tables using Camelot
        tables = camelot.read_pdf(pdf_path, pages='all')
        
        for i, table in enumerate(tables):
            try:
                # Get table properties
                parsing_report = table.parsing_report
                
                # Convert to pandas DataFrame
                df = table.df
                
                # Get table content as string
                table_content = df.to_string(index=False)
                
                # Generate table summary
                summary = generate_table_summary(df)
                
                table_info = {
                    'index': i + 1,
                    'page': parsing_report.get('page', 'unknown'),
                    'shape': f"{df.shape[0]} rows x {df.shape[1]} columns",
                    'rows': df.shape[0],
                    'columns': df.shape[1],
                    'accuracy': round(parsing_report.get('accuracy', 0), 2),
                    'whitespace': round(parsing_report.get('whitespace', 0), 2),
                    'content': table_content,
                    'summary': summary,
                    'has_headers': detect_headers(df)
                }
                
                tables_info.append(table_info)
                
            except Exception as e:
                error_info = {
                    'index': i + 1,
                    'error': f"Failed to process table: {str(e)}"
                }
                tables_info.append(error_info)
        
        return tables_info
        
    except Exception as e:
        return [{'error': f"Table extraction failed: {str(e)}"}]

def generate_table_summary(df: pd.DataFrame) -> str:
    """
    Generate a summary of the table content
    """
    try:
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"Table with {df.shape[0]} rows and {df.shape[1]} columns")
        
        # Check for numeric data
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_parts.append(f"Contains {len(numeric_cols)} numeric columns")
        
        # Check for empty cells
        total_cells = df.shape[0] * df.shape[1]
        empty_cells = df.isnull().sum().sum()
        if empty_cells > 0:
            empty_percentage = (empty_cells / total_cells) * 100
            summary_parts.append(f"{empty_percentage:.1f}% of cells are empty")
        
        # Try to identify table type based on content
        table_type = identify_table_type(df)
        if table_type:
            summary_parts.append(f"Appears to be: {table_type}")
        
        # Sample content (first few non-empty cells)
        sample_content = get_sample_content(df)
        if sample_content:
            summary_parts.append(f"Sample content: {sample_content}")
        
        return ". ".join(summary_parts)
        
    except Exception as e:
        return f"Summary generation failed: {str(e)}"

def detect_headers(df: pd.DataFrame) -> bool:
    """
    Simple heuristic to detect if table has headers
    """
    try:
        if df.empty:
            return False
        
        # Check if first row is different from others (potential header)
        first_row = df.iloc[0]
        
        # Headers often contain text while data contains numbers
        first_row_has_text = any(isinstance(val, str) and not val.isdigit() for val in first_row if pd.notna(val))
        
        if df.shape[0] > 1:
            second_row = df.iloc[1]
            second_row_has_numbers = any(isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '').isdigit()) 
                                       for val in second_row if pd.notna(val))
            
            return first_row_has_text and second_row_has_numbers
        
        return first_row_has_text
        
    except Exception:
        return False

def identify_table_type(df: pd.DataFrame) -> str:
    """
    Try to identify the type of table based on content
    """
    try:
        if df.empty:
            return "empty table"
        
        # Convert to string for analysis
        content_str = df.to_string().lower()
        
        # Financial table indicators
        financial_keywords = ['revenue', 'profit', 'cost', 'expense', 'income', 'sales', '$', 'total', 'amount']
        if any(keyword in content_str for keyword in financial_keywords):
            return "financial/accounting table"
        
        # Statistical table indicators
        stats_keywords = ['mean', 'average', 'std', 'min', 'max', 'count', 'percentage', '%']
        if any(keyword in content_str for keyword in stats_keywords):
            return "statistical table"
        
        # Schedule/time table indicators
        time_keywords = ['date', 'time', 'schedule', 'monday', 'tuesday', 'january', 'february']
        if any(keyword in content_str for keyword in time_keywords):
            return "schedule/timeline table"
        
        # Contact/directory table indicators
        contact_keywords = ['name', 'email', 'phone', 'address', 'contact']
        if any(keyword in content_str for keyword in contact_keywords):
            return "contact/directory table"
        
        # Check if mostly numeric
        numeric_cells = 0
        total_cells = 0
        
        for col in df.columns:
            for val in df[col]:
                if pd.notna(val):
                    total_cells += 1
                    if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit()):
                        numeric_cells += 1
        
        if total_cells > 0 and (numeric_cells / total_cells) > 0.7:
            return "numerical data table"
        
        return "general data table"
        
    except Exception:
        return "unknown table type"

def get_sample_content(df: pd.DataFrame, max_samples: int = 3) -> str:
    """
    Get sample content from the table
    """
    try:
        samples = []
        
        for i in range(min(df.shape[0], 2)):  # First 2 rows
            for j in range(min(df.shape[1], 3)):  # First 3 columns
                val = df.iloc[i, j]
                if pd.notna(val) and str(val).strip():
                    val_str = str(val).strip()
                    if len(val_str) > 0 and val_str not in samples:
                        samples.append(val_str)
                        if len(samples) >= max_samples:
                            break
            if len(samples) >= max_samples:
                break
        
        return ", ".join(samples) if samples else ""
        
    except Exception:
        return ""

def save_tables_to_csv(pdf_path: str, output_dir: str = "extracted_tables") -> List[str]:
    """
    Save extracted tables as CSV files (optional utility)
    """
    saved_files = []
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        tables = camelot.read_pdf(pdf_path, pages='all')
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for i, table in enumerate(tables):
            try:
                filename = f"{pdf_name}_table_{i+1}.csv"
                filepath = os.path.join(output_dir, filename)
                table.to_csv(filepath)
                saved_files.append(filepath)
            except Exception as e:
                print(f"Failed to save table {i+1}: {str(e)}")
        
        return saved_files
        
    except Exception as e:
        print(f"Table saving failed: {str(e)}")
        return saved_files
