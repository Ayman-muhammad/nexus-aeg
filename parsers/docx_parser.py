from docx import Document
import pandas as pd

def parse_docx(file_path: str) -> pd.DataFrame:
    """
    Extract tables from a Word document. Returns first table as DataFrame.
    """
    doc = Document(file_path)
    for table in doc.tables:
        data = []
        for row in table.rows:
            data.append([cell.text.strip() for cell in row.cells])
        if data:
            return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame()