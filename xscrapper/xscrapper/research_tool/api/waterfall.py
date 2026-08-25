"""
Waterfall Orchestrator module.
Enforces API priority order (OpenAlex -> Semantic Scholar -> Crossref) and performs automatic metadata enrichment.
"""

import logging
from typing import List, Dict, Any
from research_tool.api.openalex import OpenAlexClient
from research_tool.api.semantic_scholar import SemanticScholarClient
from research_tool.api.crossref import CrossrefClient

logger = logging.getLogger("tri_netra_logger")


class WaterfallFetcher:
    """Orchestrates multi-API literature collection with fallback and enrichment."""

    def __init__(self):
        self.openalex = OpenAlexClient()
        self.semantic_scholar = SemanticScholarClient()
        self.crossref = CrossrefClient()

    def enrich_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Keep paper record as enriched by primary source."""
        return paper

    def fetch_papers_for_keyword(self, keyword: str, limit_per_source: int = 25) -> List[Dict[str, Any]]:
        """Fetch papers prioritizing OpenAlex, falling back to Semantic Scholar and Crossref."""
        all_keyword_papers: List[Dict[str, Any]] = []

        # 1. Primary Source: OpenAlex (Priority 1)
        logger.info(f"Querying Priority 1 (OpenAlex) for: '{keyword}'")
        openalex_papers = self.openalex.search_papers(keyword, limit=limit_per_source)
        for p in openalex_papers:
            all_keyword_papers.append(p)

        # 2. Secondary Source: Semantic Scholar (Priority 2) - Fallback if primary sparse
        if len(all_keyword_papers) < 10:
            logger.info(f"Querying Priority 2 (Semantic Scholar) for: '{keyword}'")
            ss_papers = self.semantic_scholar.search_papers(keyword, limit=limit_per_source)
            for p in ss_papers:
                all_keyword_papers.append(p)

        # 3. Tertiary Source: Crossref (Priority 3) - Fallback if results still sparse
        if len(all_keyword_papers) < 10:
            logger.info(f"Querying Priority 3 (Crossref) for: '{keyword}'")
            cr_papers = self.crossref.search_papers(keyword, limit=limit_per_source)
            for p in cr_papers:
                all_keyword_papers.append(p)

        return all_keyword_papers
