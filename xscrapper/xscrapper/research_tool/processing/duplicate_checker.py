"""
Duplicate Checker Module.
Identifies duplicate research papers across APIs using DOI, normalized title, and title similarity matching.
"""

import re
import logging
from difflib import SequenceMatcher
from typing import Dict, Any, Set, List

logger = logging.getLogger("tri_netra_logger")


class DuplicateChecker:
    """Detects duplicate papers using DOI, normalized title, and fuzzy title similarity."""

    def __init__(self, title_similarity_threshold: float = 0.90):
        self.seen_dois: Set[str] = set()
        self.seen_normalized_titles: Set[str] = set()
        self.raw_titles: List[str] = []
        self.similarity_threshold = title_similarity_threshold

    @staticmethod
    def normalize_doi(doi: str) -> str:
        """Normalize DOI string."""
        if not doi:
            return ""
        clean = doi.lower().replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
        return clean

    @staticmethod
    def normalize_title(title: str) -> str:
        """Normalize title string by lowercasing and keeping alphanumeric characters."""
        if not title:
            return ""
        clean = re.sub(r"[^\w\s]", "", title.lower())
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def is_duplicate(self, paper: Dict[str, Any]) -> bool:
        """Check if paper is a duplicate based on DOI, normalized title, or fuzzy title similarity."""
        doi = self.normalize_doi(paper.get("DOI", ""))
        norm_title = self.normalize_title(paper.get("Title", ""))

        # Check DOI match
        if doi and doi in self.seen_dois:
            return True

        # Check exact normalized title match
        if norm_title and norm_title in self.seen_normalized_titles:
            return True

        # Check fuzzy title similarity
        if norm_title and len(norm_title) > 15:
            for existing_title in self.raw_titles:
                existing_norm = self.normalize_title(existing_title)
                if abs(len(norm_title) - len(existing_norm)) > 20:
                    continue
                ratio = SequenceMatcher(None, norm_title, existing_norm).ratio()
                if ratio >= self.similarity_threshold:
                    return True

        return False

    def add_paper(self, paper: Dict[str, Any]) -> None:
        """Add paper identifiers to seen index."""
        doi = self.normalize_doi(paper.get("DOI", ""))
        title = paper.get("Title", "")
        norm_title = self.normalize_title(title)

        if doi:
            self.seen_dois.add(doi)
        if norm_title:
            self.seen_normalized_titles.add(norm_title)
        if title:
            self.raw_titles.append(title)
