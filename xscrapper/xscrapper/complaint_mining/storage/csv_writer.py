"""
CSV Dataset Manager for Social Media Complaint Mining.
Handles incremental appending, ID generation, schema enforcement, quality validation,
and generates complaint_statistics.csv and problem_clusters.csv.
"""

import os
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple
from complaint_mining.config import COMPLAINTS_CSV_PATH, STATISTICS_CSV_PATH, CLUSTERS_CSV_PATH
from complaint_mining.processing.duplicate_checker import ComplaintDuplicateChecker
from complaint_mining.processing.clustering import ComplaintClusterer

logger = logging.getLogger("complaint_logger")


class ComplaintCSVManager:
    """Manages complaint dataset storage and derivative statistical CSV exports."""

    COLUMNS = [
        "Complaint_ID",
        "Platform",
        "Company",
        "Product_Category",
        "Date",
        "Complaint_Title",
        "Complaint_Text",
        "Complaint_URL",
        "Complaint_Type",
        "Severity",
        "Stakeholder",
        "TriNetra_Module",
        "Language",
        "Country",
        "Likes",
        "Replies",
        "Shares"
    ]

    def __init__(self, csv_path: str = str(COMPLAINTS_CSV_PATH)):
        self.csv_path = csv_path
        self.existing_df: pd.DataFrame = pd.DataFrame(columns=self.COLUMNS)
        self.next_id_counter = 1
        self._load_existing_dataset()

    def _load_existing_dataset(self) -> None:
        """Load existing customer_complaints_dataset.csv if present."""
        if os.path.exists(self.csv_path):
            try:
                self.existing_df = pd.read_csv(self.csv_path)
                logger.info(f"Loaded existing dataset with {len(self.existing_df)} complaints from {self.csv_path}")
                if "Complaint_ID" in self.existing_df.columns and len(self.existing_df) > 0:
                    id_nums = []
                    for cid in self.existing_df["Complaint_ID"].dropna():
                        if isinstance(cid, str) and cid.startswith("CMP_"):
                            num_part = cid.replace("CMP_", "")
                            if num_part.isdigit():
                                id_nums.append(int(num_part))
                    if id_nums:
                        self.next_id_counter = max(id_nums) + 1

                # Backfill Product_Category if missing
                if "Product_Category" not in self.existing_df.columns:
                    from complaint_mining.processing.classifier import ComplaintClassifier
                    classifier = ComplaintClassifier()
                    self.existing_df["Product_Category"] = self.existing_df.apply(
                        lambda row: classifier.classify_product_category(
                            str(row.get("Complaint_Text", "")), str(row.get("Complaint_Title", ""))
                        ), axis=1
                    )
            except Exception as e:
                logger.error(f"Error reading existing CSV {self.csv_path}: {e}")
                self.existing_df = pd.DataFrame(columns=self.COLUMNS)

    def populate_duplicate_checker(self, dup_checker: ComplaintDuplicateChecker) -> int:
        """Populate DuplicateChecker with existing complaints from CSV."""
        count = 0
        if not self.existing_df.empty:
            for _, row in self.existing_df.iterrows():
                complaint = {
                    "Complaint_URL": str(row.get("Complaint_URL", "")),
                    "Complaint_Text": str(row.get("Complaint_Text", ""))
                }
                dup_checker.add_complaint(complaint)
                count += 1
        logger.info(f"Populated duplicate checker with {count} existing complaints.")
        return count

    def save_complaints(self, new_complaints: List[Dict[str, Any]]) -> Tuple[int, str]:
        """
        Validate, assign Complaint_IDs, format fields, append to existing dataset,
        and generate complaint_statistics.csv and problem_clusters.csv.
        """
        valid_rows = []

        for c in new_complaints:
            cid = f"CMP_{self.next_id_counter:05d}"
            self.next_id_counter += 1

            row = {
                "Complaint_ID": cid,
                "Platform": str(c.get("Platform", "Other")).strip(),
                "Company": str(c.get("Company", "Other E-Commerce")).strip(),
                "Product_Category": str(c.get("Product_Category", "Other/Unspecified")).strip(),
                "Date": str(c.get("Date", "")).strip(),
                "Complaint_Title": str(c.get("Complaint_Title", "")).strip(),
                "Complaint_Text": str(c.get("Complaint_Text", "")).strip(),
                "Complaint_URL": str(c.get("Complaint_URL", "")).strip(),
                "Complaint_Type": str(c.get("Complaint_Type", "Other")).strip(),
                "Severity": str(c.get("Severity", "Low")).strip(),
                "Stakeholder": str(c.get("Stakeholder", "Customer")).strip(),
                "TriNetra_Module": str(c.get("TriNetra_Module", "")).strip(),
                "Language": str(c.get("Language", "en")).strip(),
                "Country": str(c.get("Country", "")).strip(),
                "Likes": int(c.get("Likes", 0) or 0),
                "Replies": int(c.get("Replies", 0) or 0),
                "Shares": int(c.get("Shares", 0) or 0),
            }
            valid_rows.append(row)

        if valid_rows:
            new_df = pd.DataFrame(valid_rows, columns=self.COLUMNS)
            if not self.existing_df.empty:
                final_df = pd.concat([self.existing_df[self.COLUMNS], new_df], ignore_index=True)
            else:
                final_df = new_df
        else:
            final_df = self.existing_df

        if final_df.empty:
            logger.warning("No complaint data to save.")
            return 0, "No complaints saved."

        # Save main customer_complaints_dataset.csv
        final_df.to_csv(self.csv_path, index=False, encoding="utf-8-sig")
        logger.info(f"Saved master dataset to {self.csv_path}. Total complaints: {len(final_df)} (Added {len(valid_rows)} new).")

        self.existing_df = final_df

        # Generate complaint_statistics.csv
        self._generate_statistics_csv(final_df)

        # Generate problem_clusters.csv
        self._generate_clusters_csv(final_df)

        return len(valid_rows), f"Successfully added {len(valid_rows)} new complaints."

    @staticmethod
    def _generate_statistics_csv(df: pd.DataFrame) -> None:
        """Generate breakdown statistics CSV across platforms, companies, categories, types, and severities."""
        if df.empty:
            return

        stat_rows = []
        total = len(df)

        # 1. Platform distribution
        for platform, count in df["Platform"].value_counts().items():
            pct = round((count / total) * 100, 2)
            stat_rows.append({
                "Category": "Platform Breakdown",
                "Metric": platform,
                "Frequency": count,
                "Percentage": f"{pct}%",
                "Severity_Distribution": str(df[df["Platform"] == platform]["Severity"].value_counts().to_dict()),
                "Top_Issues": ", ".join(df[df["Platform"] == platform]["Complaint_Type"].value_counts().head(3).index.tolist())
            })

        # 2. Company distribution
        for company, count in df["Company"].value_counts().items():
            pct = round((count / total) * 100, 2)
            stat_rows.append({
                "Category": "Company Breakdown",
                "Metric": company,
                "Frequency": count,
                "Percentage": f"{pct}%",
                "Severity_Distribution": str(df[df["Company"] == company]["Severity"].value_counts().to_dict()),
                "Top_Issues": ", ".join(df[df["Company"] == company]["Complaint_Type"].value_counts().head(3).index.tolist())
            })

        # 3. Product Category distribution
        if "Product_Category" in df.columns:
            for pcat, count in df["Product_Category"].value_counts().items():
                pct = round((count / total) * 100, 2)
                stat_rows.append({
                    "Category": "Product Category Breakdown",
                    "Metric": pcat,
                    "Frequency": count,
                    "Percentage": f"{pct}%",
                    "Severity_Distribution": str(df[df["Product_Category"] == pcat]["Severity"].value_counts().to_dict()),
                    "Top_Issues": ", ".join(df[df["Product_Category"] == pcat]["Complaint_Type"].value_counts().head(3).index.tolist())
                })

        # 4. Complaint Type distribution
        for ctype, count in df["Complaint_Type"].value_counts().items():
            pct = round((count / total) * 100, 2)
            stat_rows.append({
                "Category": "Complaint Type Breakdown",
                "Metric": ctype,
                "Frequency": count,
                "Percentage": f"{pct}%",
                "Severity_Distribution": str(df[df["Complaint_Type"] == ctype]["Severity"].value_counts().to_dict()),
                "Top_Issues": ", ".join(df[df["Complaint_Type"] == ctype]["Company"].value_counts().head(3).index.tolist())
            })

        stat_df = pd.DataFrame(stat_rows)
        stat_df.to_csv(str(STATISTICS_CSV_PATH), index=False, encoding="utf-8-sig")
        logger.info(f"Saved statistical summary to {STATISTICS_CSV_PATH}")

    @staticmethod
    def _generate_clusters_csv(df: pd.DataFrame) -> None:
        """Generate problem_clusters.csv dataframe summarizing themes."""
        clusters_df = ComplaintClusterer.generate_clusters_summary(df)
        clusters_df.to_csv(str(CLUSTERS_CSV_PATH), index=False, encoding="utf-8-sig")
        logger.info(f"Saved problem clusters summary to {CLUSTERS_CSV_PATH}")
