"""
Multi‑format file parser.
Supports CSV, Excel, and (optionally) PDF/DOCX with Gemini AI.
"""
import pandas as pd
import logging
from typing import List, Optional
from engine.models import Building, Unit, Assessment
from engine.gemini import GeminiReasoner

# Optional imports for PDF/DOCX – handle gracefully if not installed
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_bytes) -> str:
    """Extract text from a PDF file using PyPDF2."""
    if PyPDF2 is None:
        raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")
    text = ""
    from io import BytesIO
    reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_bytes) -> str:
    """Extract text from a DOCX file using python-docx."""
    if docx is None:
        raise ImportError("python-docx not installed. Install with: pip install python-docx")
    from io import BytesIO
    doc = docx.Document(BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

def parse_file(uploaded_file, file_type: str, reasoner: Optional[GeminiReasoner] = None) -> List:
    """
    Parse uploaded file into a list of model instances.
    Supports CSV, Excel, PDF, DOCX. For PDF/DOCX, uses Gemini if provided.

    Args:
        uploaded_file: A Streamlit UploadedFile object.
        file_type: One of 'buildings', 'units', 'assessments'.
        reasoner: Optional GeminiReasoner instance for AI extraction.

    Returns:
        List of model objects (Building, Unit, or Assessment).
    """
    if uploaded_file is None:
        return []

    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    # 1. Structured formats
    if file_name.endswith('.csv'):
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            logger.exception("CSV parsing failed")
            raise ValueError(f"Could not read CSV: {e}")
    elif file_name.endswith(('.xls', '.xlsx')):
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            logger.exception("Excel parsing failed")
            raise ValueError(f"Could not read Excel: {e}")
    else:
        # 2. Unstructured formats – need AI
        if reasoner is None:
            raise ValueError(f"File type {file_name} requires an AI reasoner (Gemini). Please configure Gemini.")
        if file_name.endswith('.pdf'):
            text = extract_text_from_pdf(file_bytes)
        elif file_name.endswith('.docx'):
            text = extract_text_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_name}")

        data = reasoner.extract_data(text, file_type)
        if not data:
            raise ValueError(f"Gemini could not extract {file_type} data from the document.")
        # Convert dicts to models
        return _dicts_to_models(data, file_type)

    # If we got here, we have a DataFrame
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    required_columns = {
        'buildings': ['code', 'name', 'capacity'],
        'units': ['code', 'name', 'year', 'semester', 'exam_duration_minutes'],
        'assessments': ['unit_code', 'student_count', 'current_room', 'current_slot']
    }

    if file_type in required_columns:
        missing = set(required_columns[file_type]) - set(df.columns)
        if missing:
            found = list(df.columns)
            raise ValueError(
                f"Missing columns: {missing}. "
                f"Found columns: {found}. "
                f"Expected: {required_columns[file_type]}"
            )

    records = df.to_dict(orient='records')
    return _dicts_to_models(records, file_type)

def _dicts_to_models(records: List[dict], file_type: str) -> List:
    """Convert list of dicts to appropriate model objects."""
    models = []
    if file_type == 'buildings':
        models = [Building(**r) for r in records]
    elif file_type == 'units':
        models = [Unit(**r) for r in records]
    elif file_type == 'assessments':
        models = [Assessment(**r) for r in records]
    else:
        raise ValueError(f"Unknown file_type: {file_type}")
    return models