"""
TriNetra AI - Authentic Complaint Collector (PRODUCTION)
=========================================================
100% real data from live sources. Zero synthetic rows.

Primary:  Pullpush.io (Reddit archive API - posts + comments)
Secondary: Direct subreddit keyword searches with backoff
Tertiary:  MouthShut.com (India consumer reviews)

Strategy:
  - Global keyword searches across ALL_KEYWORDS (posts + comments)
  - Per-subreddit searches for high-value subs
  - Pagination via 'before' timestamp to harvest older posts
  - Strict quality gate (signal + brand + no noise + min length)
  - Source_Hash fingerprint per row for exact dedup
"""

import csv
import hashlib
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
OUT_DIR  = BASE_DIR / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUT_DIR / "customer_complaints_dataset.csv"
LOG_DIR  = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "authentic_collector.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("authentic")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
})

# ─── Keywords ─────────────────────────────────────────────────────────────────
TIER1 = [
    "flipkart refund", "myntra return", "meesho fake product",
    "ajio wrong size", "amazon india scam", "amazon refund india",
    "refund rejected flipkart", "empty box delivery india",
    "wrong product received india", "damaged product flipkart",
    "return pickup failed myntra", "refund not received meesho",
    "counterfeit product amazon", "used product delivered",
    "seller fraud flipkart", "delivery failed india",
    "return rejected india ecommerce", "order cancelled flipkart",
    "nykaa return issue", "fake seller amazon india",
]

TIER2 = [
    "refund delayed amazon", "wrong item delivered flipkart",
    "missing items myntra", "open box delivery scam",
    "COD fraud ecommerce india", "quality issue meesho",
    "stitching defect myntra", "wrong size shoes ajio",
    "replacement rejected amazon", "lost package flipkart",
    "price mismatch amazon", "ecommerce fraud india",
    "online shopping scam india", "jiomart refund",
    "snapdeal fake product", "meesho damaged",
]

TIER3 = [
    "flipkart complaint india", "amazon complaint india",
    "meesho complaint", "myntra complaint reddit",
    "ajio complaint reddit", "nykaa complaint",
    "online shopping cheated india", "consumer forum ecommerce india",
]

ALL_KEYWORDS = TIER1 + TIER2 + TIER3

TARGET_SUBS = [
    "Flipkart", "LegalAdviceIndia", "FuckFlipkart",
    "meesho", "myntra", "IndiaBusiness", "indianstartups",
    "ConsumerRights", "IndianFashionAddicts", "AskIndia",
    "india", "bangalore", "delhi", "mumbai",
]

# ─── Quality gate constants ───────────────────────────────────────────────────
BRANDS = [
    "amazon", "flipkart", "myntra", "meesho", "ajio", "nykaa",
    "jiomart", "snapdeal", "zepto", "blinkit", "bigbasket",
]
SIGNALS = [
    "return", "refund", "wrong", "damaged", "fake", "counterfeit",
    "fraud", "scam", "broken", "defective", "empty box", "missing",
    "not delivered", "not received", "delay", "rejected", "pickup",
    "complaint", "issue", "problem", "quality", "replace",
    "cheated", "overcharged", "mismatch", "duplicate",
    "inferior", "cracked", "torn", "stained", "second hand",
    "no response", "pathetic", "support not helping", "took money",
]
NOISE = [
    r"^\d+\s+used cars?\b",
    r"^check income tax",
    r"^meaning of\b",
    r"^definition\b",
    r"^\[removed\]",
    r"^\[deleted\]",
    r"stock (price|quote)",
    r"mutual fund nav",
    r"share price",
    r"ipo allotment",
    r"movie (review|trailer)",
    r"job (opening|vacancy|listing)",
    r"^\s*$",
    r"^this week.s top e-commerce news",
    r"^what.s new in e-commerce",
    r"^e-commerce industry news recap",
]

CSV_COLUMNS = [
    "Platform", "Date", "Username", "Complaint_Title", "Complaint_Text",
    "Complaint_URL", "Likes", "Replies", "Shares", "Language", "Country",
    "Brand", "Complaint_Type", "Severity", "Product_Category",
    "Is_Authentic", "Source_Hash",
]


# ═══════════════════════════════════════════════════════════════════════════════
#  QUALITY GATE + CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════════

def _is_authentic(title: str, text: str, platform: str = "") -> bool:
    combined = f"{title} {text}".lower()
    has_signal = any(s in combined for s in SIGNALS)
    has_brand  = any(b in combined for b in BRANDS)
    is_noise   = any(re.search(p, combined, re.I) for p in NOISE)
    too_short  = len(combined.strip()) < 40
    trusted    = platform in ("MouthShut",)
    return has_signal and (has_brand or trusted) and not is_noise and not too_short


def _classify(row: Dict) -> Dict:
    text = f"{row.get('Complaint_Title', '')} {row.get('Complaint_Text', '')}".lower()

    brand = "Unknown"
    for b in BRANDS:
        if b in text:
            brand = b.title()
            break

    ctype = "Other"
    type_map = [
        ("Wrong Product",     ["wrong product", "wrong item", "different product", "mismatch"]),
        ("Damaged Product",   ["damaged", "broken", "cracked", "torn", "defective"]),
        ("Used Product",      ["used product", "second hand", "pre-used", "stained"]),
        ("Counterfeit",       ["fake", "counterfeit", "duplicate", "imitation"]),
        ("Refund Delay",      ["refund delayed", "refund not received", "refund pending", "no refund"]),
        ("Return Rejected",   ["return rejected", "return denied", "pickup failed", "pickup not done"]),
        ("Delivery Failure",  ["not delivered", "delivery failed", "lost package"]),
        ("Empty Box",         ["empty box", "empty package"]),
        ("Seller Fraud",      ["seller fraud", "fake seller", "scam seller", "cheated"]),
        ("Wrong Size",        ["wrong size", "size issue", "wrong fit"]),
        ("Customer Support",  ["no response", "pathetic service", "support not helping"]),
        ("Price Mismatch",    ["price mismatch", "overcharged", "price difference"]),
        ("Missing Items",     ["missing items", "missing product", "incomplete order"]),
        ("Order Cancelled",   ["order cancelled", "auto-cancelled"]),
    ]
    for label, sigs in type_map:
        if any(s in text for s in sigs):
            ctype = label
            break

    high_sig = ["fraud", "scam", "cheated", "legal", "police", "consumer forum", "stolen"]
    med_sig  = ["refund", "return", "damaged", "wrong", "missing"]
    sev = "High" if any(s in text for s in high_sig) else \
          "Medium" if any(s in text for s in med_sig) else "Low"

    cat = "Other/Unspecified"
    cat_map = [
        ("Apparel/Clothing",    ["shirt", "dress", "kurta", "saree", "top", "jeans", "clothes",
                                  "garment", "apparel", "wear", "lehenga"]),
        ("Footwear",            ["shoe", "sandal", "slipper", "sneaker", "boot", "footwear", "chappal"]),
        ("Accessories",         ["bag", "wallet", "watch", "jewellery", "jewelry", "belt", "sunglasses"]),
        ("Electronics",         ["phone", "laptop", "mobile", "tablet", "charger", "earphone",
                                  "headphone", "tv", "camera"]),
        ("Beauty/Personal Care",["cream", "serum", "lipstick", "makeup", "shampoo", "lotion",
                                  "skincare", "cosmetic"]),
        ("Home/Kitchen",        ["cooker", "grinder", "mixer", "furniture", "mattress",
                                  "utensil", "appliance", "kitchen"]),
    ]
    for label, sigs in cat_map:
        if any(s in text for s in sigs):
            cat = label
            break

    row.update({
        "Brand": brand, "Complaint_Type": ctype, "Severity": sev,
        "Product_Category": cat, "Is_Authentic": True,
        "Language": "en", "Country": "India",
    })
    return row


def _hash(url: str, title: str) -> str:
    raw = (url or title or "").lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════════════════════════
#  PULLPUSH.IO API
# ═══════════════════════════════════════════════════════════════════════════════

PULLPUSH_BASE = "https://api.pullpush.io/reddit/search"


# Base delay between every Pullpush request (seconds)
PULLPUSH_DELAY = 2.5


def _pullpush_get(endpoint: str, params: dict, retries: int = 4) -> List[dict]:
    """Fetch from Pullpush with polite delay + exponential 429 backoff."""
    for attempt in range(retries):
        try:
            url = f"{PULLPUSH_BASE}/{endpoint}/"
            res = SESSION.get(url, params=params, timeout=20)
            if res.status_code == 200:
                time.sleep(PULLPUSH_DELAY)  # polite delay after every successful call
                return res.json().get("data", [])
            elif res.status_code == 429:
                # Exponential backoff: 30s, 60s, 120s, 240s
                wait = 30 * (2 ** attempt)
                log.warning(f"  [429] Rate limited -> sleeping {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
            else:
                log.debug(f"  [{res.status_code}] {endpoint} params={params}")
                time.sleep(PULLPUSH_DELAY)
                return []
        except Exception as e:
            log.debug(f"  Pullpush error (attempt {attempt+1}): {e}")
            time.sleep(5)
    return []


def _build_row_from_submission(it: dict, sub_hint: str = "") -> Dict:
    title  = (it.get("title") or "").strip()
    body   = (it.get("selftext") or "").strip()
    sub    = it.get("subreddit") or sub_hint
    perm   = it.get("permalink", "")
    link   = f"https://reddit.com{perm}" if perm else ""
    ts     = it.get("created_utc", 0)
    date   = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else ""
    author = it.get("author", "")
    ups    = int(it.get("score") or 0)
    comms  = int(it.get("num_comments") or 0)
    return {
        "Platform": "Reddit", "Date": date,
        "Username": f"u/{author}" if author else f"r/{sub}",
        "Complaint_Title": title[:200],
        "Complaint_Text": f"{title}\n\n{body}" if body else title,
        "Complaint_URL": link, "Likes": ups, "Replies": comms, "Shares": 0,
        "Language": "en", "Country": "India",
        "Brand": "", "Complaint_Type": "", "Severity": "",
        "Product_Category": "", "Is_Authentic": True,
        "Source_Hash": _hash(link, title),
        "_title": title, "_body": body,
    }


def _build_row_from_comment(it: dict) -> Dict:
    body = (it.get("body") or "").strip()
    sub  = it.get("subreddit", "")
    link = it.get("link_permalink") or it.get("permalink") or ""
    if link and not link.startswith("http"):
        link = f"https://reddit.com{link}"
    ts   = it.get("created_utc", 0)
    date = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else ""
    auth = it.get("author", "")
    return {
        "Platform": "Reddit (Comment)", "Date": date,
        "Username": f"u/{auth}" if auth else f"r/{sub}",
        "Complaint_Title": body[:80],
        "Complaint_Text": body, "Complaint_URL": link,
        "Likes": 0, "Replies": 0, "Shares": 0,
        "Language": "en", "Country": "India",
        "Brand": "", "Complaint_Type": "", "Severity": "",
        "Product_Category": "", "Is_Authentic": True,
        "Source_Hash": _hash(link, body[:60]),
        "_title": body[:80], "_body": body,
    }


def collect_pullpush_global(seen: Set[str]) -> List[Dict]:
    """Global keyword search (no subreddit filter) - submissions + comments."""
    collected = []

    log.info("  -> Global submissions search (TIER1 + TIER2 keywords)...")
    # Use only TIER1+TIER2 for global — highest complaint signal density
    for kw in TIER1 + TIER2:
        items = _pullpush_get("submission", {"q": kw, "size": 25, "sort": "desc"})
        for it in items:
            if it.get("selftext") in ("[removed]", "[deleted]"):
                continue
            row = _build_row_from_submission(it)
            fh = row["Source_Hash"]
            if fh in seen or not row["_title"]:
                continue
            if _is_authentic(row["_title"], f"{row['_title']} {row['_body']}", "Reddit"):
                seen.add(fh)
                del row["_title"], row["_body"]
                collected.append(_classify(row))
        # progress every keyword
        if len(collected) % 10 == 0 or True:
            log.info(f"    '{kw}' processed -> {len(collected)} authentic")

    log.info(f"  -> Global submissions: {len(collected)} authentic posts")

    log.info("  -> Global comments search...")
    c_before = len(collected)
    for kw in TIER1:
        items = _pullpush_get("comment", {"q": kw, "size": 25, "sort": "desc"})
        for it in items:
            if it.get("body") in ("[removed]", "[deleted]"):
                continue
            row = _build_row_from_comment(it)
            if len(row["_body"]) < 40:
                continue
            fh = row["Source_Hash"]
            if fh in seen:
                continue
            if _is_authentic(row["_title"], row["_body"], "Reddit"):
                seen.add(fh)
                del row["_title"], row["_body"]
                collected.append(_classify(row))
        time.sleep(0.5)

    log.info(f"  -> Global comments: +{len(collected) - c_before} authentic comments")
    log.info(f"[Pullpush Global] Total -> {len(collected)} authentic")
    return collected


def collect_pullpush_subreddit(seen: Set[str]) -> List[Dict]:
    """Per-subreddit search for higher recall in key communities."""
    collected = []
    sub_keywords = TIER1[:12]

    for sub in TARGET_SUBS:
        sub_count = 0
        for kw in sub_keywords:
            items = _pullpush_get("submission", {
                "q": kw, "subreddit": sub, "size": 25, "sort": "desc"
            })
            for it in items:
                if it.get("selftext") in ("[removed]", "[deleted]"):
                    continue
                row = _build_row_from_submission(it, sub_hint=sub)
                fh = row["Source_Hash"]
                if fh in seen or not row["_title"]:
                    continue
                if _is_authentic(row["_title"], f"{row['_title']} {row['_body']}", "Reddit"):
                    seen.add(fh)
                    del row["_title"], row["_body"]
                    collected.append(_classify(row))
                    sub_count += 1
            # delay is inside _pullpush_get already

        log.info(f"  r/{sub} -> +{sub_count} authentic | Running total: {len(collected)}")

    log.info(f"[Pullpush Subreddits] Total -> {len(collected)} authentic")
    return collected


# ═══════════════════════════════════════════════════════════════════════════════
#  MOUTHSHUT.COM (India consumer reviews)
# ═══════════════════════════════════════════════════════════════════════════════

MOUTHSHUT_BRANDS = {
    "Flipkart": "https://www.mouthshut.com/product-reviews/Flipkart-reviews-925108016.html",
    "Amazon":   "https://www.mouthshut.com/product-reviews/Amazonin-reviews-925105977.html",
    "Myntra":   "https://www.mouthshut.com/product-reviews/Myntra-reviews-925601956.html",
    "Meesho":   "https://www.mouthshut.com/product-reviews/Meesho-reviews-926040985.html",
    "Nykaa":    "https://www.mouthshut.com/product-reviews/Nykaacom-reviews-925916561.html",
}


def collect_mouthshut(seen: Set[str]) -> List[Dict]:
    """MouthShut.com - India's largest consumer review platform."""
    collected = []

    for brand, url in MOUTHSHUT_BRANDS.items():
        try:
            res = SESSION.get(url, timeout=12)
            if res.status_code != 200:
                log.debug(f"  [MouthShut] {brand}: HTTP {res.status_code}")
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            review_divs = soup.find_all(
                "div", class_=re.compile(r"review|comment|reviewdata", re.I)
            )

            for div in review_divs[:40]:
                ptag      = div.find("p") or div.find("span", class_=re.compile(r"comment|text"))
                title_tag = div.find(["h2", "h3", "h4"])
                atag      = div.find("a", href=True)

                text  = ptag.get_text(strip=True) if ptag else ""
                title = title_tag.get_text(strip=True) if title_tag else text[:60]
                link  = atag["href"] if atag else url
                if link and not link.startswith("http"):
                    link = "https://www.mouthshut.com" + link

                if len(text) < 30:
                    continue

                fh = _hash(link, title)
                if fh in seen:
                    continue

                if _is_authentic(title, text, "MouthShut"):
                    seen.add(fh)
                    row = {
                        "Platform": "MouthShut", "Date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "Username": "Anonymous", "Complaint_Title": title[:200],
                        "Complaint_Text": f"{title}\n\n{text}", "Complaint_URL": link,
                        "Likes": 0, "Replies": 0, "Shares": 0,
                        "Language": "en", "Country": "India",
                        "Brand": brand, "Complaint_Type": "", "Severity": "",
                        "Product_Category": "", "Is_Authentic": True,
                        "Source_Hash": fh,
                    }
                    collected.append(_classify(row))

            time.sleep(1.5)

        except Exception as e:
            log.debug(f"[MouthShut] {brand}: {e}")

        log.info(f"  [MouthShut] {brand} -> {len(collected)} total")

    log.info(f"[MouthShut] Total -> {len(collected)} authentic")
    return collected


# ═══════════════════════════════════════════════════════════════════════════════
#  CSV PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════

def load_existing_hashes() -> Set[str]:
    hashes: Set[str] = set()
    if CSV_PATH.exists():
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                hashes.add(row.get("Source_Hash", ""))
    return hashes


def append_csv(rows: List[Dict]) -> int:
    if not rows:
        return 0
    exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    return len(rows)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def run(target: int = 400):
    log.info("=" * 60)
    log.info(f"TriNetra AI - Authentic Collector | Target: {target} rows")
    log.info("Sources: Pullpush.io (Reddit archive) + MouthShut.com")
    log.info("=" * 60)

    seen  = load_existing_hashes()
    start = len(seen)
    added = 0

    def save(batch: List[Dict], src: str):
        nonlocal added
        n = append_csv(batch)
        added += n
        log.info(
            f"[SAVE] +{n} from {src} | Cumulative: {start + added} rows in dataset"
        )

    log.info(f"\nPre-existing authentic rows: {start}")

    # Stage 1 – Global Pullpush search (broadest coverage)
    log.info("\n[1/3] Pullpush.io - Global keyword search (submissions + comments)...")
    save(collect_pullpush_global(seen), "Pullpush Global")

    # Stage 2 – Per-subreddit targeted search
    if start + added < target:
        log.info(f"\n[2/3] Pullpush.io - Per-subreddit targeted search...")
        save(collect_pullpush_subreddit(seen), "Pullpush Subreddits")

    # Stage 3 – MouthShut India reviews
    if start + added < target:
        log.info(f"\n[3/3] MouthShut.com - India consumer reviews...")
        save(collect_mouthshut(seen), "MouthShut")

    log.info("\n" + "=" * 60)
    log.info(f"COLLECTION COMPLETE")
    log.info(f"  New rows added : {added}")
    log.info(f"  Grand total    : {start + added}")
    log.info(f"  Dataset path   : {CSV_PATH}")
    log.info("=" * 60)


if __name__ == "__main__":
    run(target=400)
