import pandas as pd

def parse_excel(file_path: str) -> pd.DataFrame:
    """
    Read first sheet of an Excel file into a DataFrame.
    """
    return pd.read_excel(file_path, sheet_name=0)