"""
Problem Statement Extraction Module.
Extracts problem statement, motivation, or objective sentences deterministically from abstracts without LLM generation or paraphrasing.
"""

import re
import logging
from typing import List
from research_tool.config import PROBLEM_INDICATOR_PATTERNS

logger = logging.getLogger("tri_netra_logger")


class ProblemStatementExtractor:
    """Deterministic extractor for problem statement sentences from paper abstracts."""

    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in PROBLEM_INDICATOR_PATTERNS]

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Split text into sentences deterministically."""
        if not text:
            return []
        # Split on sentence boundaries (period, question mark, exclamation point followed by space/end)
        raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in raw_sentences if s.strip()]

    def extract_problem_statement(self, abstract: str) -> str:
        """
        Extract exact sentences describing problem, motivation, or objective from abstract.
        Returns exact matching sentences joined by space, or empty string if none match.
        """
        if not abstract:
            return ""

        sentences = self._split_into_sentences(abstract)
        matched_sentences = []

        for sentence in sentences:
            # Check if sentence matches any indicator pattern
            for pattern in self.compiled_patterns:
                if pattern.search(sentence):
                    if sentence not in matched_sentences:
                        matched_sentences.append(sentence)
                    break

        # Fallback heuristic: If no pattern matches, check first 2 sentences if they contain key terms
        if not matched_sentences and len(sentences) >= 1:
            first_sentence = sentences[0]
            if any(term in first_sentence.lower() for term in ["fraud", "return", "dispute", "challenge", "problem", "trust", "cost", "issue"]):
                matched_sentences.append(first_sentence)

        return " ".join(matched_sentences).strip()
