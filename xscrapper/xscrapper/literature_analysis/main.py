"""
Main Orchestrator Script for TriNetra AI Phase 2 Literature Knowledge Extraction.
Loads literature dataset, extracts knowledge, maps themes and modules, constructs matrices,
exports 5 CSV files, and generates research_summary.md.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

# Ensure xscrapper root is on python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from literature_analysis.config import (
    INPUT_CSV_PATH,
    ALL_PAPERS_PATH,
    LOG_FILE_PATH,
    LITERATURE_MATRIX_CSV,
    THEME_CLASSIFICATION_CSV,
    RESEARCH_GAP_CSV,
    EXISTING_VS_PROPOSED_CSV,
    TRINETRA_MAPPING_CSV,
    RESEARCH_SUMMARY_MD,
)
from literature_analysis.extractors.knowledge_extractor import KnowledgeExtractor
from literature_analysis.extractors.theme_mapper import ThemeMapper
from literature_analysis.extractors.module_mapper import ModuleMapper
from literature_analysis.reports.matrix_builder import MatrixBuilder
from literature_analysis.reports.trend_analyzer import TrendAnalyzer
from literature_analysis.reports.markdown_generator import MarkdownReportGenerator
from literature_analysis.storage.csv_exporter import CSVExporter


def setup_logger() -> logging.Logger:
    """Configure logger for Phase 2 analysis."""
    logger = logging.getLogger("literature_logger")
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


def load_dataset() -> pd.DataFrame:
    """Load relevant papers dataset (ignoring Irrelevant papers)."""
    target_path = INPUT_CSV_PATH if INPUT_CSV_PATH.exists() else ALL_PAPERS_PATH

    if not target_path.exists():
        raise FileNotFoundError(f"Literature dataset not found at {target_path}")

    df = pd.read_csv(target_path)
    if "Classification" in df.columns:
        relevant_df = df[df["Classification"].isin(["Highly Relevant", "Relevant", "Possibly Relevant"])].copy()
    else:
        relevant_df = df.copy()

    relevant_df = relevant_df.sort_values(by="Relevance_Score", ascending=False).reset_index(drop=True)
    return relevant_df


def main():
    logger = setup_logger()
    logger.info("=" * 70)
    logger.info("STARTING TRINETRA AI PHASE 2 LITERATURE ANALYSIS ENGINE")
    logger.info("=" * 70)

    # 1. Load Dataset
    df = load_dataset()
    logger.info(f"Loaded {len(df)} relevant research papers for Phase 2 analysis.")

    # 2. Initialize Extractors & Mappers
    extractor = KnowledgeExtractor()
    theme_mapper = ThemeMapper()
    module_mapper = ModuleMapper()

    knowledge_list = []
    processed_papers = []

    # 3. Process every relevant paper
    for idx, row in df.iterrows():
        paper = row.to_dict()

        # Extract 6 knowledge dimensions
        k_data = extractor.extract_knowledge(paper)
        knowledge_list.append(k_data)

        # Map themes & modules
        primary_theme, secondary_themes = theme_mapper.map_themes(paper)
        modules = module_mapper.map_modules(paper)

        paper["Primary_Theme"] = primary_theme
        paper["Secondary_Themes"] = secondary_themes
        paper["TriNetra_Modules"] = modules
        paper["Problem_Statement_Extracted"] = k_data["Problem"]
        paper["Solution_Extracted"] = k_data["Solution"]
        paper["Methodology"] = k_data["Methodology"]
        paper["Contribution"] = k_data["Contribution"]
        paper["Limitation"] = k_data["Limitation"]
        paper["Research_Gap"] = k_data["Research_Gap"]

        processed_papers.append(paper)

    logger.info(f"Successfully extracted knowledge, themes, and module mappings for {len(processed_papers)} papers.")

    # 4. Construct matrices
    lit_matrix_df = MatrixBuilder.build_literature_matrix(knowledge_list)
    theme_df = MatrixBuilder.build_theme_classification(processed_papers)
    gap_df = MatrixBuilder.build_research_gap_analysis(processed_papers)
    existing_vs_proposed_df = MatrixBuilder.build_existing_vs_proposed()
    trinetra_map_df = MatrixBuilder.build_trinetra_mapping(processed_papers)

    # 5. Export 5 CSV files
    CSVExporter.export_all(lit_matrix_df, theme_df, gap_df, existing_vs_proposed_df, trinetra_map_df)

    # 6. Trend Analysis & Markdown Report
    trends = TrendAnalyzer.analyze_trends(processed_papers)
    MarkdownReportGenerator.generate_report(trends, processed_papers)

    logger.info("=" * 70)
    logger.info("TRINETRA PHASE 2 LITERATURE ANALYSIS COMPLETE")
    logger.info(f"[Matrix 1] literature_matrix.csv:       {LITERATURE_MATRIX_CSV}")
    logger.info(f"[Matrix 2] theme_classification.csv:   {THEME_CLASSIFICATION_CSV}")
    logger.info(f"[Matrix 3] research_gap_analysis.csv:  {RESEARCH_GAP_CSV}")
    logger.info(f"[Matrix 4] existing_vs_proposed.csv:   {EXISTING_VS_PROPOSED_CSV}")
    logger.info(f"[Matrix 5] trinetra_mapping.csv:       {TRINETRA_MAPPING_CSV}")
    logger.info(f"[Report]   research_summary.md:        {RESEARCH_SUMMARY_MD}")
    logger.info(f"Process Log: {LOG_FILE_PATH}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
