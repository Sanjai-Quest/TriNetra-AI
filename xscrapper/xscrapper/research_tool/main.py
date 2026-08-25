"""
Main Execution Script for TriNetra AI Literature Research Scraper.
Orchestrates multi-API paper collection across OpenAlex, Semantic Scholar, Crossref, and arXiv,
enforces 3-tier keyword search order, performs immediate relevance scoring & 32-column enrichment,
auto-saves every 50 papers, logs progress format [X/184], and halts when 150+ relevant papers (Score >= 5) are gathered.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

# Ensure research_tool directory is on python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from research_tool.config import (
    TIER1_KEYWORDS, TIER2_KEYWORDS, TIER3_KEYWORDS, SEARCH_KEYWORDS,
    LOG_FILE_PATH, TRINETRA_DATASET_PATH, RELEVANT_PAPERS_PATH, ALL_PAPERS_PATH
)
from research_tool.api.waterfall import WaterfallFetcher
from research_tool.processing.problem_statement import ProblemStatementExtractor
from research_tool.processing.relevance import RelevanceScorer
from research_tool.processing.duplicate_checker import DuplicateChecker
from research_tool.storage.csv_writer import CSVDatasetManager


def setup_logger() -> logging.Logger:
    """Configure logger to write to stdout and process_log.txt."""
    logger = logging.getLogger("tri_netra_logger")
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
    logger.info("STARTING TRINETRA AI RESEARCH LITERATURE SCRAPER PIPELINE")
    logger.info("=" * 70)

    # Initialize Modules
    csv_manager = CSVDatasetManager()
    dup_checker = DuplicateChecker(title_similarity_threshold=0.95)
    fetcher = WaterfallFetcher()
    extractor = ProblemStatementExtractor()
    scorer = RelevanceScorer()

    # Pre-populate duplicate checker with existing records
    existing_count = csv_manager.populate_duplicate_checker(dup_checker)

    total_processed = 0
    total_added = 0
    total_duplicates = 0
    relevant_count = 0

    # Count existing relevant papers if dataset present
    if not csv_manager.existing_df.empty and "Relevance_Score" in csv_manager.existing_df.columns:
        relevant_count = len(csv_manager.existing_df[csv_manager.existing_df["Relevance_Score"] >= 5.0])
        logger.info(f"Existing dataset has {len(csv_manager.existing_df)} total papers ({relevant_count} relevant with Score >= 5.0)")

    collected_batch = []
    target_relevant = 150
    target_total = 184

    tier_groups = [
        ("TIER 1 (27 Core Keywords)", TIER1_KEYWORDS),
        ("TIER 2 (23 Supporting Keywords)", TIER2_KEYWORDS),
        ("TIER 3 (10 Context Keywords)", TIER3_KEYWORDS),
    ]

    stop_pipeline = False

    for tier_name, keywords in tier_groups:
        if stop_pipeline:
            break

        logger.info("=" * 70)
        logger.info(f"STARTING SEARCH FOR {tier_name}")
        logger.info("=" * 70)

        for kw_idx, keyword in enumerate(keywords, 1):
            if relevant_count >= target_relevant or total_added >= target_total:
                logger.info(f"Target condition met: {relevant_count} relevant papers (Score >= 5.0), {total_added} total added. Stopping search.")
                stop_pipeline = True
                break

            logger.info(f"[{kw_idx}/{len(keywords)}] Keyword: '{keyword}'")

            try:
                # Fetch candidate papers across APIs
                raw_papers = fetcher.fetch_papers_for_keyword(keyword, limit_per_source=30)

                for paper in raw_papers:
                    total_processed += 1

                    # 1. Deduplication check (DOI or title similarity > 0.95)
                    if dup_checker.is_duplicate(paper):
                        total_duplicates += 1
                        logger.debug(f"Duplicate removed: '{paper.get('Title', '')[:40]}...'")
                        continue

                    # 2. Quality check (must have Title and Abstract)
                    is_valid, reason = csv_manager.validate_quality(paper)
                    if not is_valid:
                        continue

                    # Add to deduplication index
                    dup_checker.add_paper(paper)

                    # 3. Deterministic Problem Statement Extraction
                    paper["Problem_Statement"] = extractor.extract_problem_statement(
                        paper.get("Abstract", "")
                    )

                    # 4. Immediate Relevance Scoring & 32-column Metadata Enrichment
                    score, classification, meta = scorer.evaluate(paper)
                    paper["Relevance_Score"] = score
                    paper["Classification"] = classification

                    # Merge structured metadata
                    for k, v in meta.items():
                        paper[k] = v

                    # Filter out irrelevant papers (Score < 5.0) per stop instructions unless needed
                    if score < 5.0:
                        logger.debug(f"Filtering out irrelevant paper (Score {score}): '{paper.get('Title', '')[:40]}...'")
                        continue

                    collected_batch.append(paper)
                    total_added += 1
                    if score >= 5.0:
                        relevant_count += 1

                    # Progress reporting format: "[X/184] Papers processed, Y added, Z duplicates removed"
                    logger.info(
                        f"[{total_added}/{target_total}] Papers processed: {total_processed}, "
                        f"Added: {total_added} ({relevant_count} relevant), Duplicates removed: {total_duplicates}"
                    )

                    # Auto-save every 50 papers
                    if len(collected_batch) >= 50:
                        added, msg = csv_manager.save_dataset(collected_batch)
                        logger.info(f"AUTO-SAVE TRIGGERED: {msg}")
                        collected_batch.clear()

                    if relevant_count >= target_relevant or total_added >= target_total:
                        stop_pipeline = True
                        break

            except Exception as e:
                logger.error(f"Error processing keyword '{keyword}': {e}", exc_info=True)

    # Save any remaining batch
    if collected_batch:
        added, msg = csv_manager.save_dataset(collected_batch)
        logger.info(f"FINAL BATCH SAVE: {msg}")
        collected_batch.clear()

    # Final summary output
    final_df = csv_manager.existing_df
    final_relevant = len(final_df[final_df["Relevance_Score"] >= 5.0]) if not final_df.empty and "Relevance_Score" in final_df.columns else len(final_df)

    logger.info("=" * 70)
    logger.info("TRINETRA RESEARCH LITERATURE SCRAPER COMPLETE")
    logger.info(f"Total Papers Discovered & Processed: {total_processed}")
    logger.info(f"Total Duplicates Removed:          {total_duplicates}")
    logger.info(f"Total Papers in Master Dataset:     {len(final_df)}")
    logger.info(f"Total Relevant Papers (Score >= 5): {final_relevant}")
    logger.info(f"[Master Dataset CSV] {TRINETRA_DATASET_PATH}")
    logger.info(f"[Relevant Papers CSV] {RELEVANT_PAPERS_PATH}")
    logger.info(f"Process Log:          {LOG_FILE_PATH}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
