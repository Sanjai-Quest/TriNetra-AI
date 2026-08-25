"""
OpenAlex API integration module (Priority 1 source).
"""

import logging
from typing import List, Dict, Any, Optional
from research_tool.api.base_api import BaseAPIClient
from research_tool.config import OPENALEX_DELAY

logger = logging.getLogger("tri_netra_logger")


class OpenAlexClient(BaseAPIClient):
    """Client for OpenAlex API."""

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self):
        super().__init__(name="OpenAlex", delay=OPENALEX_DELAY)

    @staticmethod
    def _reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
        """Reconstruct plain text abstract from OpenAlex inverted index structure."""
        if not inverted_index or not isinstance(inverted_index, dict):
            return ""
        try:
            position_word_pairs = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    position_word_pairs.append((pos, word))
            position_word_pairs.sort(key=lambda x: x[0])
            return " ".join([word for _, word in position_word_pairs]).strip()
        except Exception as e:
            logger.error(f"[OpenAlex] Error reconstructing abstract: {e}")
            return ""

    def _parse_work(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAlex work object into unified TriNetra paper dict."""
        paper = self.create_empty_paper_dict(source="OpenAlex")

        paper["Title"] = (item.get("title") or "").strip()
        paper["Abstract"] = self._reconstruct_abstract(item.get("abstract_inverted_index"))

        # Authors
        authorships = item.get("authorships", [])
        author_names = []
        for auth in authorships:
            name = auth.get("author", {}).get("display_name")
            if name:
                author_names.append(name)
        paper["Authors"] = "; ".join(author_names)

        # Year
        year = item.get("publication_year")
        paper["Year"] = str(year) if year else ""

        # DOI
        doi_raw = item.get("doi") or ""
        paper["DOI"] = doi_raw.replace("https://doi.org/", "").strip()

        # Venue / Journal & Publisher
        primary_location = item.get("primary_location") or {}
        source_info = primary_location.get("source") or {}
        paper["Journal"] = source_info.get("display_name") or ""
        paper["Publisher"] = source_info.get("publisher") or ""

        # Concepts / Keywords
        concepts = item.get("concepts", [])
        keyword_list = [c.get("display_name") for c in concepts if c.get("display_name")]
        paper["Keywords"] = "; ".join(keyword_list[:10])

        # Citations
        paper["Citation_Count"] = item.get("cited_by_count", 0) or 0

        # Research Area
        primary_topic = item.get("primary_topic") or {}
        subfield = primary_topic.get("subfield") or {}
        paper["Research_Area"] = subfield.get("display_name") or (keyword_list[0] if keyword_list else "")

        # Open Access & URL
        oa_info = item.get("open_access") or {}
        paper["Open_Access"] = "Yes" if oa_info.get("is_oa") else "No"
        paper["URL"] = item.get("doi") or item.get("id") or ""

        return paper

    def search_papers(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Search OpenAlex works for query."""
        params = {
            "search": query,
            "per_page": min(limit, 50),
            "sort": "relevance_score:desc"
        }
        data = self._make_request(self.BASE_URL, params=params)
        if not data or "results" not in data:
            return []

        parsed_papers = []
        for item in data.get("results", []):
            try:
                p = self._parse_work(item)
                if p["Title"]:
                    parsed_papers.append(p)
            except Exception as e:
                logger.error(f"[OpenAlex] Error parsing search result: {e}")
        return parsed_papers

    def fetch_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Fetch work metadata by DOI."""
        if not doi:
            return None
        clean_doi = doi.replace("https://doi.org/", "").strip()
        url = f"https://api.openalex.org/works/https://doi.org/{clean_doi}"
        data = self._make_request(url)
        if data:
            return self._parse_work(data)
        return None
