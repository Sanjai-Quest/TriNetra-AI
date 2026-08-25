"""
Semantic Scholar API integration module (Priority 2 source).
"""

import logging
from typing import List, Dict, Any, Optional
from research_tool.api.base_api import BaseAPIClient
from research_tool.config import SEMANTIC_SCHOLAR_DELAY

logger = logging.getLogger("tri_netra_logger")


class SemanticScholarClient(BaseAPIClient):
    """Client for Semantic Scholar Graph API."""

    SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    PAPER_URL = "https://api.semanticscholar.org/graph/v1/paper/"

    FIELDS = "paperId,title,abstract,authors,year,journal,publisher,citationCount,isOpenAccess,openAccessPdf,externalIds,url,fieldsOfStudy"

    def __init__(self):
        super().__init__(name="SemanticScholar", delay=SEMANTIC_SCHOLAR_DELAY)

    def _parse_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Semantic Scholar item to unified TriNetra paper dict."""
        paper = self.create_empty_paper_dict(source="SemanticScholar")

        paper["Title"] = (item.get("title") or "").strip()
        paper["Abstract"] = (item.get("abstract") or "").strip()

        # Authors
        authors = item.get("authors") or []
        paper["Authors"] = "; ".join([a.get("name", "") for a in authors if a.get("name")])

        # Year
        year = item.get("year")
        paper["Year"] = str(year) if year else ""

        # DOI
        ext_ids = item.get("externalIds") or {}
        paper["DOI"] = (ext_ids.get("DOI") or "").strip()

        # Journal & Publisher
        journal_info = item.get("journal") or {}
        if isinstance(journal_info, dict):
            paper["Journal"] = journal_info.get("name") or ""
        elif isinstance(journal_info, str):
            paper["Journal"] = journal_info
        paper["Publisher"] = item.get("publisher") or ""

        # Citations
        paper["Citation_Count"] = item.get("citationCount", 0) or 0

        # Fields of Study / Keywords
        fos = item.get("fieldsOfStudy") or []
        paper["Keywords"] = "; ".join([str(f) for f in fos if f])
        paper["Research_Area"] = fos[0] if fos else ""

        # Open Access & URL
        paper["Open_Access"] = "Yes" if item.get("isOpenAccess") else "No"
        paper["URL"] = item.get("url") or (f"https://doi.org/{paper['DOI']}" if paper["DOI"] else "")

        return paper

    def search_papers(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Search Semantic Scholar papers for query."""
        params = {
            "query": query,
            "limit": min(limit, 50),
            "fields": self.FIELDS
        }
        data = self._make_request(self.SEARCH_URL, params=params)
        if not data or "data" not in data:
            return []

        parsed_papers = []
        for item in data.get("data", []):
            try:
                p = self._parse_paper(item)
                if p["Title"]:
                    parsed_papers.append(p)
            except Exception as e:
                logger.error(f"[SemanticScholar] Error parsing paper: {e}")
        return parsed_papers

    def fetch_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Fetch paper metadata by DOI."""
        if not doi:
            return None
        import urllib.parse
        clean_doi = urllib.parse.quote(doi.replace("https://doi.org/", "").strip(), safe="")
        url = f"{self.PAPER_URL}DOI:{clean_doi}"
        params = {"fields": self.FIELDS}
        data = self._make_request(url, params=params)
        if data:
            return self._parse_paper(data)
        return None
