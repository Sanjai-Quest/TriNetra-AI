"""
Base API client defining standard paper schema, error handling, rate limiting, and HTTP request logic.
"""

import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from research_tool.config import HEADERS, DEFAULT_TIMEOUT, MAX_RETRIES, BACKOFF_FACTOR

logger = logging.getLogger("tri_netra_logger")


class BaseAPIClient(ABC):
    """Abstract Base Class for scholarly API clients."""

    def __init__(self, name: str, delay: float = 0.5):
        self.name = name
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Perform HTTP GET request with retries and backoff."""
        time.sleep(self.delay)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    logger.warning(f"[{self.name}] Rate limited (429). Skipping fallback query for this item.")
                    return None
                elif response.status_code in [500, 502, 503, 504]:
                    sleep_time = BACKOFF_FACTOR ** attempt
                    logger.warning(f"[{self.name}] Server error ({response.status_code}). Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"[{self.name}] Failed request {url} HTTP status {response.status_code}")
                    return None
            except Exception as e:
                logger.error(f"[{self.name}] Request error on {url} (Attempt {attempt}/{MAX_RETRIES}): {e}")
                time.sleep(BACKOFF_FACTOR ** attempt)
        return None

    @abstractmethod
    def search_papers(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Search papers for a given query."""
        pass

    @abstractmethod
    def fetch_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Fetch paper metadata by DOI."""
        pass

    @staticmethod
    def create_empty_paper_dict(source: str) -> Dict[str, Any]:
        """Return baseline empty paper record."""
        return {
            "Title": "",
            "Problem_Statement": "",
            "Abstract": "",
            "Authors": "",
            "Year": "",
            "Journal": "",
            "Publisher": "",
            "DOI": "",
            "Keywords": "",
            "Citation_Count": 0,
            "Research_Area": "",
            "Source": source,
            "URL": "",
            "Open_Access": "No"
        }
