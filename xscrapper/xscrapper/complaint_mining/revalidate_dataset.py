"""
Dataset Revalidation & Audit Cleanup Script for TriNetra AI Complaint Mining.
Loads existing customer_complaints_dataset.csv, re-runs inspect_quality against every row,
logs failing rows to rejected_rows_audit.csv, overwrites dataset with clean rows,
and regenerates complaint_statistics.csv and problem_clusters.csv from clean data.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from complaint_mining.config import (
    COMPLAINTS_CSV_PATH,
    OUTPUT_DIR,
    LOG_FILE_PATH,
)
from complaint_mining.processing.classifier import ComplaintClassifier
from complaint_mining.storage.csv_writer import ComplaintCSVManager

REJECTED_CSV_PATH = OUTPUT_DIR / "rejected_rows_audit.csv"

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("revalidation")


def revalidate():
    logger.info("=" * 70)
    logger.info("STARTING DATASET REVALIDATION & AUDIT CLEANUP")
    logger.info(f"Target Master Dataset: {COMPLAINTS_CSV_PATH}")
    logger.info("=" * 70)

    if not COMPLAINTS_CSV_PATH.exists():
        logger.error(f"Dataset file {COMPLAINTS_CSV_PATH} does not exist!")
        return

    df = pd.read_csv(COMPLAINTS_CSV_PATH)
    total_original = len(df)
    logger.info(f"Original dataset row count: {total_original}")

    classifier = ComplaintClassifier()
    csv_manager = ComplaintCSVManager()

    clean_rows = []
    rejected_rows = []

    for idx, row in df.iterrows():
        title = str(row.get("Complaint_Title", ""))
        text = str(row.get("Complaint_Text", ""))
        cid = str(row.get("Complaint_ID", f"CMP_{idx+1:05d}"))

        is_valid, reason = classifier.inspect_quality(text, title)

        if is_valid:
            row_dict = row.to_dict()
            # Ensure Product_Category is up to date
            row_dict["Product_Category"] = classifier.classify_product_category(text, title)
            clean_rows.append(row_dict)
        else:
            rejected_dict = row.to_dict()
            rejected_dict["Rejection_Reason"] = reason
            rejected_rows.append(rejected_dict)

    clean_count = len(clean_rows)
    rejected_count = len(rejected_rows)

    logger.info("-" * 60)
    logger.info(f"Revalidation Complete:")
    logger.info(f"  Total Rows Evaluated: {total_original}")
    logger.info(f"  Clean Rows Kept:     {clean_count} ({round(clean_count/total_original*100, 1)}%)")
    logger.info(f"  Rejected Rows:       {rejected_count} ({round(rejected_count/total_original*100, 1)}%)")
    logger.info("-" * 60)

    # Save Rejected Rows Audit CSV
    if rejected_rows:
        rejected_df = pd.DataFrame(rejected_rows)
        rejected_df.to_csv(REJECTED_CSV_PATH, index=False, encoding="utf-8-sig")
        logger.info(f"Saved rejected rows audit log to: {REJECTED_CSV_PATH}")

    # Overwrite Master Dataset with Clean Rows
    if clean_rows:
        clean_df = pd.DataFrame(clean_rows, columns=csv_manager.COLUMNS)
    else:
        clean_df = pd.DataFrame(columns=csv_manager.COLUMNS)

    clean_df.to_csv(COMPLAINTS_CSV_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"Updated master dataset {COMPLAINTS_CSV_PATH} with {clean_count} clean complaints.")

    # Regenerate Statistics and Problem Clusters from Clean Dataset
    csv_manager._generate_statistics_csv(clean_df)
    csv_manager._generate_clusters_csv(clean_df)

    logger.info("=" * 70)
    logger.info("REVALIDATION & DERIVATIVE GENERATION COMPLETED SUCCESSFULLY")
    logger.info("=" * 70)


if __name__ == "__main__":
    revalidate()
