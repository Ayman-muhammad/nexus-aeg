import pandas as pd
import os
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .excel_parser import parse_excel

def parse_file(file_path: str) -> pd.DataFrame:
    """
    Parse a file (PDF, DOCX, XLSX, CSV) into a pandas DataFrame.
    Raises ValueError if file type is unsupported.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return parse_pdf(file_path)
    elif ext == '.docx':
        return parse_docx(file_path)
    elif ext in ['.xlsx', '.xls']:
        return parse_excel(file_path)
    elif ext == '.csv':
        return pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")