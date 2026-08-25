"""
Main execution script for TriNetra AI Social Media Complaint Mining Tool.
Orchestrates multi-platform OSINT collection (Reddit, X/Twitter, LinkedIn, Facebook, Instagram),
multi-dimensional classification, deduplication, quality filtering, dataset persistence,
and generates statistical and problem cluster CSV exports.
"""

import sys
import logging
from pathlib import Path

# Ensure complaint_mining directory is on python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from complaint_mining.config import (
    SEARCH_KEYWORDS,
    LOG_FILE_PATH,
    COMPLAINTS_CSV_PATH,
    STATISTICS_CSV_PATH,
    CLUSTERS_CSV_PATH,
)
from complaint_mining.collectors.reddit import RedditCollector
from complaint_mining.collectors.twitter import TwitterCollector
from complaint_mining.collectors.linkedin import LinkedInCollector
from complaint_mining.collectors.facebook import FacebookCollector
from complaint_mining.collectors.instagram import InstagramCollector
from complaint_mining.processing.classifier import ComplaintClassifier
from complaint_mining.processing.duplicate_checker import ComplaintDuplicateChecker
from complaint_mining.storage.csv_writer import ComplaintCSVManager


def setup_logger() -> logging.Logger:
    """Configure logger to write to stdout and complaint_collection_log.txt."""
    logger = logging.getLogger("complaint_logger")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def main():
    logger = setup_logger()
    logger.info("=" * 70)
    logger.info("STARTING TRINETRA AI SOCIAL MEDIA COMPLAINT MINING PIPELINE")
    logger.info("=" * 70)

    # Initialize Modules
    csv_manager = ComplaintCSVManager()
    dup_checker = ComplaintDuplicateChecker(fuzzy_threshold=0.85)
    classifier = ComplaintClassifier()

    # Pre-populate duplicate checker with existing records
    existing_count = csv_manager.populate_duplicate_checker(dup_checker)

    # Instantiate Platform Collectors
    collectors = [
        RedditCollector(),      # Priority 1
        TwitterCollector(),     # Priority 2
        LinkedInCollector(),    # Priority 3
        FacebookCollector(),    # Priority 4
        InstagramCollector(),   # Priority 5
    ]

    total_collected = 0
    total_rejected = 0
    total_duplicates = 0
    collected_complaints = []

    # Process each search keyword across platforms
    for idx, keyword in enumerate(SEARCH_KEYWORDS, 1):
        logger.info("-" * 60)
        logger.info(f"[{idx}/{len(SEARCH_KEYWORDS)}] Mining Complaints for Keyword: '{keyword}'")

        kw_fetched = 0
        kw_passed = 0

        for collector in collectors:
            try:
                raw_posts = collector.fetch_complaints(keyword, limit=25)
                kw_fetched += len(raw_posts)
                logger.info(f"[{collector.platform_name}] Found {len(raw_posts)} raw posts for '{keyword}'")

                for post in raw_posts:
                    total_collected += 1

                    # 1. Quality Check (reject ads/promos/news/memes/spam/irrelevant)
                    is_valid, reason = classifier.inspect_quality(
                        post.get("Complaint_Text", ""), post.get("Complaint_Title", "")
                    )
                    if not is_valid:
                        total_rejected += 1
                        logger.debug(f"[{collector.platform_name}] Quality rejected: {reason}")
                        continue

                    # 2. Duplicate Check
                    if dup_checker.is_duplicate(post):
                        total_duplicates += 1
                        logger.debug(f"[{collector.platform_name}] Duplicate detected and removed")
                        continue

                    # Mark as seen
                    dup_checker.add_complaint(post)
                    kw_passed += 1

                    # 3. Multi-Dimensional Classification & Mapping
                    classified_complaint = classifier.classify_complaint(post)
                    collected_complaints.append(classified_complaint)

            except Exception as e:
                logger.error(f"[{collector.platform_name}] Error during keyword '{keyword}': {e}", exc_info=True)

        # Log per-keyword precision across platforms
        if kw_fetched > 0:
            precision_pct = round((kw_passed / kw_fetched) * 100, 1)
            if precision_pct < 20.0:
                logger.warning(
                    f"[PRECISION WARNING] Keyword '{keyword}' overall precision is {precision_pct}% "
                    f"({kw_passed}/{kw_fetched} kept). Query construction flagged for review."
                )
            else:
                logger.info(f"[PRECISION] Keyword '{keyword}' overall precision: {precision_pct}% ({kw_passed}/{kw_fetched} kept)")

    logger.info("=" * 70)
    logger.info("SAVING COMPLAINTS AND GENERATING DERIVATIVE DATASETS")

    added_count, msg = csv_manager.save_complaints(collected_complaints)

    final_df = csv_manager.existing_df
    total_final = len(final_df)

    logger.info("=" * 70)
    logger.info("TRINETRA COMPLAINT MINING PIPELINE COMPLETE")
    logger.info(f"Existing Complaints Pre-Run:    {existing_count}")
    logger.info(f"Total Posts Evaluated:          {total_collected}")
    logger.info(f"Quality Rejected (Ads/Spam):    {total_rejected}")
    logger.info(f"Duplicates Removed:             {total_duplicates}")
    logger.info(f"New Complaints Added:           {added_count}")
    logger.info(f"Total Master Dataset Size:      {total_final}")

    # Log Brand (Company) Breakdown
    logger.info("-" * 60)
    logger.info("COMPANY (BRAND) COVERAGE BREAKDOWN:")
    if not final_df.empty and "Company" in final_df.columns:
        comp_counts = final_df["Company"].value_counts()
        for comp, cnt in comp_counts.items():
            pct = round((cnt / total_final) * 100, 1)
            logger.info(f"  - {comp:18s}: {cnt:4d} ({pct}%)")

    # Log Product_Category Breakdown
    logger.info("-" * 60)
    logger.info("PRODUCT CATEGORY BREAKDOWN:")
    fashion_pct = 0.0
    if not final_df.empty and "Product_Category" in final_df.columns:
        cat_counts = final_df["Product_Category"].value_counts()
        fashion_cnt = cat_counts.get("Apparel/Clothing", 0) + cat_counts.get("Footwear", 0)
        fashion_pct = round((fashion_cnt / total_final) * 100, 1) if total_final > 0 else 0.0

        for cat, cnt in cat_counts.items():
            pct = round((cnt / total_final) * 100, 1)
            logger.info(f"  - {cat:22s}: {cnt:4d} ({pct}%)")

        logger.info(f"Combined Fashion/Apparel + Footwear Share: {fashion_cnt}/{total_final} ({fashion_pct}%)")

        if fashion_pct < 15.0:
            logger.warning(
                f"[CATEGORY COVERAGE WARNING] Apparel/Clothing + Footwear combined share is {fashion_pct}% "
                f"(< 15.0% target threshold). Recommend adding more fashion-specific search queries."
            )
        else:
            logger.info(f"[CATEGORY COVERAGE SUCCESS] Apparel/Clothing + Footwear share is {fashion_pct}% (>= 15.0% target).")

    logger.info("=" * 70)
    logger.info(f"[Master Dataset] customer_complaints_dataset.csv: {COMPLAINTS_CSV_PATH}")
    logger.info(f"[Statistics]     complaint_statistics.csv:        {STATISTICS_CSV_PATH}")
    logger.info(f"[Clusters]       problem_clusters.csv:            {CLUSTERS_CSV_PATH}")
    logger.info(f"Process Log: {LOG_FILE_PATH}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
