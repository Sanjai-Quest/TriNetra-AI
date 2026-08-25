"""
Multi-Stage Deduplication Engine for Social Media Complaints.
Eliminates duplicate complaints across Reddit, X, Facebook, LinkedIn, Instagram
using URL exact match, normalized text hashing, and sequence matching fuzzy similarity.
"""

import re
import logging
from difflib import SequenceMatcher
from typing import Dict, Any, Set, List

logger = logging.getLogger("complaint_logger")


class ComplaintDuplicateChecker:
    """Multi-stage duplicate checker enforcing single master records."""

    def __init__(self, fuzzy_threshold: float = 0.85):
        self.fuzzy_threshold = fuzzy_threshold
        self.seen_urls: Set[str] = set()
        self.seen_normalized_texts: Set[str] = set()
        self.indexed_texts: List[str] = []

    @staticmethod
    def normalize_text(text: str) -> str:
        """Strip punctuation, whitespace, and lower-case text for deduplication."""
        text = (text or "").lower()
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"[^\w\s]", "", text)
        return " ".join(text.split())

    def is_duplicate(self, complaint: Dict[str, Any]) -> bool:
        """
        Check if complaint is duplicate via:
        1. URL exact match
        2. Normalized text match
        3. Fuzzy text similarity (difflib SequenceMatcher >= 0.85)
        """
        url = (complaint.get("Complaint_URL") or "").strip().lower()
        raw_text = complaint.get("Complaint_Text", "")
        norm_text = self.normalize_text(raw_text)

        if not norm_text or len(norm_text) < 15:
            return True

        # 1. URL exact match
        if url and url in self.seen_urls:
            return True

        # 2. Normalized text exact match
        if norm_text in self.seen_normalized_texts:
            return True

        # 3. Fuzzy similarity against existing texts
        for existing in self.indexed_texts:
            # Quick length heuristic
            if abs(len(existing) - len(norm_text)) > len(norm_text) * 0.4:
                continue

            ratio = SequenceMatcher(None, norm_text, existing).ratio()
            if ratio >= self.fuzzy_threshold:
                return True

        return False

    def add_complaint(self, complaint: Dict[str, Any]) -> None:
        """Index complaint into deduplication tracking sets."""
        url = (complaint.get("Complaint_URL") or "").strip().lower()
        norm_text = self.normalize_text(complaint.get("Complaint_Text", ""))

        if url:
            self.seen_urls.add(url)
        if norm_text:
            self.seen_normalized_texts.add(norm_text)
            self.indexed_texts.append(norm_text)
