"""
LinkedIn OSINT Collector (Priority 3).
"""
import logging
from typing import Dict, Any, List
from complaint_mining.collectors.base_collector import BaseCollector

logger = logging.getLogger("complaint_logger")


class LinkedInCollector(BaseCollector):
    def __init__(self):
        super().__init__(platform_name="LinkedIn", delay_seconds=0.3)

    def fetch_complaints(self, keyword: str, limit: int = 25) -> List[Dict[str, Any]]:
        complaints = self._fetch_bing_osint("site:linkedin.com/posts OR site:linkedin.com/pulse", keyword, limit=limit)
        logger.info(f"[LinkedIn] Collected {len(complaints)} posts for '{keyword}'")
        return complaints
