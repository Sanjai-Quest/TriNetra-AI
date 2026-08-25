"""
Crossref API integration module (Priority 3 source).
"""

import re
import logging
from typing import List, Dict, Any, Optional
from research_tool.api.base_api import BaseAPIClient
from research_tool.config import CROSSREF_DELAY

logger = logging.getLogger("tri_netra_logger")


class CrossrefClient(BaseAPIClient):
    """Client for Crossref REST API."""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self):
        super().__init__(name="Crossref", delay=CROSSREF_DELAY)

    @staticmethod
    def _clean_abstract(abstract_raw: Optional[str]) -> str:
        """Strip JATS XML tags and whitespace from Crossref abstracts."""
        if not abstract_raw:
            return ""
        # Remove XML/HTML tags
        cleaned = re.sub(r"<[^>]+>", " ", abstract_raw)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _parse_work(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Crossref work item to unified TriNetra paper dict."""
        paper = self.create_empty_paper_dict(source="Crossref")

        # Title
        titles = item.get("title") or []
        paper["Title"] = (titles[0] if titles else "").strip()

        # Abstract
        paper["Abstract"] = self._clean_abstract(item.get("abstract"))

        # Authors
        authors_raw = item.get("author") or []
        author_names = []
        for a in authors_raw:
            given = a.get("given", "")
            family = a.get("family", "")
            full = f"{given} {family}".strip()
            if full:
                author_names.append(full)
        paper["Authors"] = "; ".join(author_names)

        # Year
        created = item.get("published-print") or item.get("published-online") or item.get("created") or {}
        date_parts = created.get("date-parts", [[]])
        if date_parts and date_parts[0]:
            paper["Year"] = str(date_parts[0][0])

        # DOI
        paper["DOI"] = (item.get("DOI") or "").strip()

        # Journal & Publisher
        container = item.get("container-title") or []
        paper["Journal"] = container[0] if container else ""
        paper["Publisher"] = item.get("publisher") or ""

        # Citations
        paper["Citation_Count"] = item.get("is-referenced-by-count", 0) or 0

        # Keywords / Subject
        subjects = item.get("subject") or []
        paper["Keywords"] = "; ".join(subjects)
        paper["Research_Area"] = subjects[0] if subjects else ""

        # Open Access & URL
        paper["Open_Access"] = "No"  # Default unless license specified
        paper["URL"] = item.get("URL") or (f"https://doi.org/{paper['DOI']}" if paper["DOI"] else "")

        return paper

    def search_papers(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Search Crossref works for query."""
        params = {
            "query": query,
            "rows": min(limit, 50),
            "sort": "relevance"
        }
        data = self._make_request(self.BASE_URL, params=params)
        if not data or "message" not in data or "items" not in data["message"]:
            return []

        parsed_papers = []
        for item in data["message"].get("items", []):
            try:
                p = self._parse_work(item)
                if p["Title"]:
                    parsed_papers.append(p)
            except Exception as e:
                logger.error(f"[Crossref] Error parsing item: {e}")
        return parsed_papers

    def fetch_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Fetch work metadata by DOI."""
        if not doi:
            return None
        clean_doi = doi.replace("https://doi.org/", "").strip()
        url = f"{self.BASE_URL}/{clean_doi}"
        data = self._make_request(url)
        if data and "message" in data:
            return self._parse_work(data["message"])
        return None
