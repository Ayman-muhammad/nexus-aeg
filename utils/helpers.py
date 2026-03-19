import pandas as pd
import os
import tempfile
from streamlit.runtime.uploaded_file_manager import UploadedFile

def load_csv_data(filepath: str) -> pd.DataFrame:
    """Load CSV from data folder, return DataFrame. If file missing, return empty."""
    if not os.path.exists(filepath):
        return pd.DataFrame()
    return pd.read_csv(filepath)

def save_uploaded_file(uploaded_file: UploadedFile) -> str:
    """Save an uploaded file to a temporary location and return the path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name