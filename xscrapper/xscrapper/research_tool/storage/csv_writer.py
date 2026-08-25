"""
CSV Dataset Manager for TriNetra AI Literature Mining Tool.
Manages dataset storage, ID assignment, quality validation, and saves outputs to:
  - trinetra_literature_dataset.csv (32-Column Master Export)
  - relevant_papers.csv (Filtered Score >= 5.0)
  - all_papers.csv (Archive)
"""

import os
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple
from pathlib import Path

from research_tool.config import (
    TRINETRA_DATASET_PATH,
    RELEVANT_PAPERS_PATH,
    ALL_PAPERS_PATH,
)
from research_tool.processing.duplicate_checker import DuplicateChecker

logger = logging.getLogger("tri_netra_logger")


class CSVDatasetManager:
    """Manages literature datasets with full 32-column schema enforcement."""

    COLUMNS_32 = [
        "Paper_ID",
        "Title",
        "Abstract",
        "Problem_Statement",
        "Solution",
        "Methodology",
        "Dataset",
        "Existing_Systems",
        "Authors",
        "Year",
        "Journal",
        "Conference",
        "DOI",
        "Keywords",
        "Citation_Count",
        "Research_Area",
        "Verification_Stage",
        "Evidence_Sources",
        "Organization_Scope",
        "Product_Identity",
        "Evidence_Reconciliation",
        "Explainability",
        "Human_In_The_Loop",
        "Return_Dispute",
        "Limitations",
        "Research_Gap",
        "TriNetra_Relevance",
        "TriNetra_Module",
        "Source",
        "URL",
        "Relevance_Score",
        "Classification",
    ]

    def __init__(self, main_csv_path: Path = TRINETRA_DATASET_PATH):
        self.csv_path = main_csv_path
        self.existing_df: pd.DataFrame = pd.DataFrame(columns=self.COLUMNS_32)
        self.next_id_counter = 1
        self._load_existing_dataset()

    def _load_existing_dataset(self) -> None:
        """Load existing dataset to determine next available Paper_ID."""
        target = self.csv_path if self.csv_path.exists() else ALL_PAPERS_PATH
        if target.exists():
            try:
                self.existing_df = pd.read_csv(target)
                logger.info(f"Loaded existing dataset with {len(self.existing_df)} rows from {target}")
                if "Paper_ID" in self.existing_df.columns and len(self.existing_df) > 0:
                    id_nums = []
                    for pid in self.existing_df["Paper_ID"].dropna():
                        if isinstance(pid, str) and pid.startswith("TRINETRA_"):
                            num_part = pid.replace("TRINETRA_", "")
                            if num_part.isdigit():
                                id_nums.append(int(num_part))
                    if id_nums:
                        self.next_id_counter = max(id_nums) + 1
            except Exception as e:
                logger.error(f"Error loading existing dataset {target}: {e}")
                self.existing_df = pd.DataFrame(columns=self.COLUMNS_32)

    def populate_duplicate_checker(self, dup_checker: DuplicateChecker) -> int:
        """Seed DuplicateChecker with existing records."""
        count = 0
        if not self.existing_df.empty:
            for _, row in self.existing_df.iterrows():
                paper = {
                    "DOI": str(row.get("DOI", "")),
                    "Title": str(row.get("Title", ""))
                }
                dup_checker.add_paper(paper)
                count += 1
        logger.info(f"Populated duplicate checker with {count} existing records.")
        return count

    @staticmethod
    def validate_quality(paper: Dict[str, Any]) -> Tuple[bool, str]:
        """Quality gate: Must have Title and non-empty Abstract."""
        title = str(paper.get("Title", "")).strip()
        abstract = str(paper.get("Abstract", "")).strip()
        if not title:
            return False, "Missing Title"
        if not abstract or len(abstract) < 15:
            return False, "Missing or extremely short Abstract"
        return True, "Valid"

    def save_dataset(self, new_papers: List[Dict[str, Any]]) -> Tuple[int, str]:
        """
        Formats, validates, assigns Paper_IDs, appends to existing frame,
        and saves trinetra_literature_dataset.csv, relevant_papers.csv, and all_papers.csv.
        """
        valid_rows = []

        for p in new_papers:
            is_valid, reason = self.validate_quality(p)
            if not is_valid:
                continue

            paper_id = f"TRINETRA_{self.next_id_counter:04d}"
            self.next_id_counter += 1

            row = {
                "Paper_ID": paper_id,
                "Title": str(p.get("Title", "")).strip(),
                "Abstract": str(p.get("Abstract", "")).strip(),
                "Problem_Statement": str(p.get("Problem_Statement", "")).strip(),
                "Solution": str(p.get("Solution", "")).strip(),
                "Methodology": str(p.get("Methodology", "")).strip(),
                "Dataset": str(p.get("Dataset", "")).strip(),
                "Existing_Systems": str(p.get("Existing_Systems", "")).strip(),
                "Authors": str(p.get("Authors", "")).strip(),
                "Year": str(p.get("Year", "")).strip(),
                "Journal": str(p.get("Journal", "")).strip(),
                "Conference": str(p.get("Conference", "")).strip(),
                "DOI": str(p.get("DOI", "")).strip(),
                "Keywords": str(p.get("Keywords", "")).strip(),
                "Citation_Count": int(p.get("Citation_Count", 0) or 0),
                "Research_Area": str(p.get("Research_Area", "")).strip(),
                "Verification_Stage": str(p.get("Verification_Stage", "End-to-End")).strip(),
                "Evidence_Sources": str(p.get("Evidence_Sources", "Multi-Source")).strip(),
                "Organization_Scope": str(p.get("Organization_Scope", "Cross-Organizational")).strip(),
                "Product_Identity": str(p.get("Product_Identity", "Barcode/QR")).strip(),
                "Evidence_Reconciliation": str(p.get("Evidence_Reconciliation", "Multi-Source Cross-Organization")).strip(),
                "Explainability": str(p.get("Explainability", "Rule-Based")).strip(),
                "Human_In_The_Loop": str(p.get("Human_In_The_Loop", "Conditional")).strip(),
                "Return_Dispute": str(p.get("Return_Dispute", "Yes")).strip(),
                "Limitations": str(p.get("Limitations", "")).strip(),
                "Research_Gap": str(p.get("Research_Gap", "")).strip(),
                "TriNetra_Relevance": str(p.get("TriNetra_Relevance", "")).strip(),
                "TriNetra_Module": str(p.get("TriNetra_Module", "Evidence Consistency")).strip(),
                "Source": str(p.get("Source", "API")).strip(),
                "URL": str(p.get("URL", "")).strip(),
                "Relevance_Score": float(p.get("Relevance_Score", 0.0)),
                "Classification": str(p.get("Classification", "Irrelevant")).strip(),
            }
            valid_rows.append(row)

        if not valid_rows:
            return 0, "No new valid rows."

        new_df = pd.DataFrame(valid_rows, columns=self.COLUMNS_32)

        if not self.existing_df.empty:
            # Align existing_df columns
            for col in self.COLUMNS_32:
                if col not in self.existing_df.columns:
                    self.existing_df[col] = ""
            final_df = pd.concat([self.existing_df[self.COLUMNS_32], new_df], ignore_index=True)
        else:
            final_df = new_df

        # Sort by Relevance_Score descending
        final_df = final_df.sort_values(by="Relevance_Score", ascending=False).reset_index(drop=True)

        # Save main 32-column export
        final_df.to_csv(TRINETRA_DATASET_PATH, index=False, encoding="utf-8-sig")
        logger.info(f"Saved {len(final_df)} total records to {TRINETRA_DATASET_PATH}")

        # Save relevant_papers.csv (Score >= 5.0)
        rel_df = final_df[final_df["Relevance_Score"] >= 5.0]
        rel_df.to_csv(RELEVANT_PAPERS_PATH, index=False, encoding="utf-8-sig")
        logger.info(f"Saved {len(rel_df)} relevant records (score >= 5.0) to {RELEVANT_PAPERS_PATH}")

        # Save all_papers.csv archive
        final_df.to_csv(ALL_PAPERS_PATH, index=False, encoding="utf-8-sig")

        self.existing_df = final_df
        return len(valid_rows), f"Successfully saved {len(valid_rows)} new papers."
