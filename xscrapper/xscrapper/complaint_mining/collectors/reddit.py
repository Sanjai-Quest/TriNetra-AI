"""
Reddit OSINT & Public Search API Collector (Priority 1).
Queries target subreddits via direct Reddit JSON search API with exact phrase matching.
"""
import logging
import datetime
from urllib.parse import quote
from typing import Dict, Any, List
from complaint_mining.collectors.base_collector import BaseCollector
from complaint_mining.config import TARGET_SUBREDDITS

logger = logging.getLogger("complaint_logger")


class RedditCollector(BaseCollector):
    def __init__(self):
        super().__init__(platform_name="Reddit", delay_seconds=0.5)

    def _fetch_reddit_api(self, keyword: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch posts directly using Reddit's public JSON search API."""
        complaints = []
        # Search target subreddits first
        subs_to_query = TARGET_SUBREDDITS[:4]  # Query top target subreddits

        for sub in subs_to_query:
            if len(complaints) >= limit:
                break

            url = f"https://www.reddit.com/r/{sub}/search.json"
            params = {
                "q": f'"{keyword}"',
                "restrict_sr": 1,
                "sort": "relevance",
                "limit": limit
            }

            res = self._get(url, params=params, timeout=5)
            if res and res.status_code == 200:
                try:
                    data = res.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        pdata = child.get("data", {})
                        title = pdata.get("title", "").strip()
                        selftext = pdata.get("selftext", "").strip()
                        permalink = pdata.get("permalink", "")
                        author = pdata.get("author", "[deleted]")
                        created_utc = pdata.get("created_utc", 0)

                        if not title:
                            continue

                        post_url = f"https://www.reddit.com{permalink}" if permalink else pdata.get("url", "")

                        date_str = ""
                        if created_utc:
                            dt = datetime.datetime.fromtimestamp(created_utc, tz=datetime.timezone.utc)
                            date_str = dt.strftime("%a, %d %b %Y")

                        clean_text = f"{title}\n\n{selftext}" if selftext else title

                        complaints.append({
                            "Platform": "Reddit",
                            "Date": date_str,
                            "Username": f"u/{author}" if author else f"r/{sub}",
                            "Complaint_Title": title[:100],
                            "Complaint_Text": clean_text,
                            "Complaint_URL": post_url,
                            "Likes": int(pdata.get("ups", 0) or 0),
                            "Replies": int(pdata.get("num_comments", 0) or 0),
                            "Shares": 0,
                            "Language": "en",
                            "Country": "India" if any(b in clean_text.lower() for b in ["flipkart", "amazonin", "meesho", "myntra", "ajio", "jiomart", "india", "rs", "inr", "rupees"]) else "",
                        })
                except Exception as e:
                    logger.debug(f"[Reddit API] Error parsing response for sub r/{sub}: {e}")
            elif res and res.status_code == 429:
                # API Rate limited — break sub loop immediately to fallback
                break

        # Global search fallback if subreddit search returned low count
        if len(complaints) < 5:
            url = "https://www.reddit.com/search.json"
            params = {
                "q": f'"{keyword}"',
                "sort": "relevance",
                "limit": limit
            }
            res = self._get(url, params=params, timeout=10)
            if res and res.status_code == 200:
                try:
                    data = res.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        pdata = child.get("data", {})
                        title = pdata.get("title", "").strip()
                        selftext = pdata.get("selftext", "").strip()
                        permalink = pdata.get("permalink", "")
                        author = pdata.get("author", "")
                        created_utc = pdata.get("created_utc", 0)
                        sub = pdata.get("subreddit", "")

                        if not title:
                            continue

                        post_url = f"https://www.reddit.com{permalink}" if permalink else pdata.get("url", "")
                        date_str = datetime.datetime.fromtimestamp(created_utc, tz=datetime.timezone.utc).strftime("%a, %d %b %Y") if created_utc else ""

                        clean_text = f"{title}\n\n{selftext}" if selftext else title

                        complaints.append({
                            "Platform": "Reddit",
                            "Date": date_str,
                            "Username": f"u/{author}" if author else f"r/{sub}",
                            "Complaint_Title": title[:100],
                            "Complaint_Text": clean_text,
                            "Complaint_URL": post_url,
                            "Likes": int(pdata.get("ups", 0) or 0),
                            "Replies": int(pdata.get("num_comments", 0) or 0),
                            "Shares": 0,
                            "Language": "en",
                            "Country": "India" if any(b in clean_text.lower() for b in ["flipkart", "amazonin", "meesho", "myntra", "ajio", "jiomart", "india"]) else "",
                        })
                except Exception as e:
                    logger.debug(f"[Reddit API] Error parsing global search: {e}")

        return complaints

    def fetch_complaints(self, keyword: str, limit: int = 25) -> List[Dict[str, Any]]:
        # 1. Try direct Reddit JSON API
        complaints = self._fetch_reddit_api(keyword, limit=limit)

        # 2. Fallback to Bing OSINT site:reddit.com search if API yielded < 3 results
        if len(complaints) < 3:
            logger.info(f"[Reddit] API yielded {len(complaints)} posts for '{keyword}'. Falling back to Bing OSINT...")
            bing_posts = self._fetch_bing_osint("site:reddit.com", keyword, limit=limit)
            complaints.extend(bing_posts)

        # Deduplicate within this single fetch call by URL
        seen_urls = set()
        unique_complaints = []
        for c in complaints:
            url = c.get("Complaint_URL", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_complaints.append(c)

        logger.info(f"[Reddit] Total fetched {len(unique_complaints)} posts for '{keyword}'")
        return unique_complaints[:limit]

