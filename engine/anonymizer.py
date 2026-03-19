import hashlib
import pandas as pd
from typing import Dict, List

class Anonymizer:
    """
    Handles tokenization of student data for privacy compliance.
    Maps real names to index numbers (tokens) and back.
    """
    def __init__(self, students_df: pd.DataFrame):
        """
        students_df must have columns: 'index' (unique token) and 'name'
        """
        self.token_to_name: Dict[str, str] = {}
        self.name_to_token: Dict[str, str] = {}
        self.token_to_phone: Dict[str, str] = {}

        for _, row in students_df.iterrows():
            token = row["index"]
            name = row["name"]
            phone = row.get("phone", "")
            self.token_to_name[token] = name
            self.name_to_token[name] = token
            self.token_to_phone[token] = phone

    def tokenize(self, name: str) -> str:
        """Return token (index number) for a given student name."""
        return self.name_to_token.get(name, name)

    def detokenize(self, token: str) -> str:
        """Return real name for a given token."""
        return self.token_to_name.get(token, token)

    def get_phone(self, token: str) -> str:
        """Return phone number for a token."""
        return self.token_to_phone.get(token, "")

    def anonymize_student_list(self, names: List[str]) -> List[str]:
        """Convert list of names to list of tokens."""
        return [self.tokenize(n) for n in names]

    def reveal_student_list(self, tokens: List[str]) -> List[str]:
        """Convert list of tokens back to names."""
        return [self.detokenize(t) for t in tokens]

    def hash_token(self, token: str) -> str:
        """Create a SHA‑256 hash of a token for ledger entries."""
        return hashlib.sha256(token.encode()).hexdigest()[:16]