"""
Base Collector Interface & Bing OSINT Helper for Social Media Complaint Mining.
Provides reliable HTTP fetching, retries, rate limiting, XML RSS parsing, and record normalization.
"""

import time
import logging
import requests
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote
from typing import Dict, Any, List, Optional
from complaint_mining.config import HEADERS

logger = logging.getLogger("complaint_logger")


class BaseCollector:
    """Base class for platform OSINT complaint collectors."""

    def __init__(self, platform_name: str, delay_seconds: float = 0.5):
        self.platform_name = platform_name
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Optional[requests.Response]:
        """HTTP GET helper with rate limiting and retry."""
        time.sleep(self.delay_seconds)
        for attempt in range(3):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code == 200:
                    return response
                elif response.status_code in [429, 503]:
                    wait = (attempt + 1) * 1.5
                    logger.warning(f"[{self.platform_name}] HTTP {response.status_code} on {url}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.warning(f"[{self.platform_name}] HTTP {response.status_code} on {url}")
                    return None
            except Exception as e:
                logger.error(f"[{self.platform_name}] Network error requesting {url}: {e}")
                time.sleep(1.0)
        return None

    def log_precision(self, keyword: str, fetched_count: int, kept_count: int) -> float:
        """Log per-keyword precision rate and flag low precision (<20%)."""
        if fetched_count == 0:
            return 0.0

        precision_pct = round((kept_count / fetched_count) * 100, 1)
        if precision_pct < 20.0:
            logger.warning(
                f"[{self.platform_name}] PRECISION WARNING: Keyword '{keyword}' precision is {precision_pct}% "
                f"({kept_count}/{fetched_count} kept). Flagged for query construction review."
            )
        else:
            logger.info(
                f"[{self.platform_name}] Keyword '{keyword}' precision: {precision_pct}% ({kept_count}/{fetched_count} kept)"
            )

        return precision_pct

    def _fetch_bing_osint(self, site_query: str, keyword: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch publicly indexed posts using Bing RSS OSINT search engine."""
        complaints = []
        full_query = f'{site_query} "{keyword}"'
        rss_url = f"https://www.bing.com/search?q={quote(full_query)}&format=rss"

        res = self._get(rss_url, timeout=10)
        if res and res.status_code == 200:
            try:
                # Clean invalid XML characters if any
                clean_text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", res.text)
                root = ET.fromstring(clean_text)
                items = root.findall("./channel/item")

                for item in items[:limit]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    pub_elem = item.find("pubDate")

                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                    desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else title
                    pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""

                    if not title or len(desc) < 15:
                        continue

                    # Generate clean complaint title (first sentence)
                    clean_desc = re.sub(r"<[^>]+>", "", desc).strip()
                    first_sentence = title.split("-")[0].split("|")[0].split(".")[0].strip()
                    if len(first_sentence) > 100:
                        first_sentence = first_sentence[:97] + "..."

                    # Infer username if present in title or link
                    username = ""
                    if "reddit.com" in link:
                        sub_m = re.search(r"reddit\.com/r/([A-Za-z0-9_]+)", link)
                        username = f"r/{sub_m.group(1)}" if sub_m else ""
                    elif "x.com" in link or "twitter.com" in link:
                        u_m = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]+)", link)
                        username = f"@{u_m.group(1)}" if u_m else ""

                    complaints.append({
                        "Platform": self.platform_name,
                        "Date": pub_date[:16] if pub_date else "",
                        "Username": username,
                        "Complaint_Title": first_sentence,
                        "Complaint_Text": f"{title}\n\n{clean_desc}",
                        "Complaint_URL": link,
                        "Likes": 0,
                        "Replies": 0,
                        "Shares": 0,
                        "Language": "en",
                        "Country": "India" if any(b in (title + clean_desc).lower() for b in ["flipkart", "amazonin", "meesho", "myntra", "ajio", "jiomart", "india"]) else "",
                    })
            except Exception as e:
                logger.error(f"[{self.platform_name}] Error parsing Bing RSS XML: {e}")

        return complaints

    def fetch_complaints(self, keyword: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Override in platform subclass."""
        raise NotImplementedError
