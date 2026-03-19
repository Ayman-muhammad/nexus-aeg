import pdfplumber
import pandas as pd
from typing import List

def parse_pdf(file_path: str) -> pd.DataFrame:
    """
    Extract tables from a PDF and return as DataFrame.
    Assumes the first page contains a table with headers.
    """
    with pdfplumber.open(file_path) as pdf:
        # Try to extract table from first page
        first_page = pdf.pages[0]
        table = first_page.extract_table()
        if table:
            # First row as headers
            headers = table[0]
            data = table[1:]
            return pd.DataFrame(data, columns=headers)
        else:
            # Fallback: extract text and try to parse as CSV-like
            text = first_page.extract_text()
            # Simple heuristic: split lines and assume comma-separated
            lines = text.strip().split('\n')
            if lines:
                data = [line.split(',') for line in lines]
                return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame()