"""
CSV Exporter Module for Phase 2 Literature Analysis.
Handles export and disk persistence for all 5 Phase 2 CSV matrices.
"""

import logging
import pandas as pd
from literature_analysis.config import (
    LITERATURE_MATRIX_CSV,
    THEME_CLASSIFICATION_CSV,
    RESEARCH_GAP_CSV,
    EXISTING_VS_PROPOSED_CSV,
    TRINETRA_MAPPING_CSV,
)

logger = logging.getLogger("literature_logger")


class CSVExporter:
    """Exports structured pandas DataFrames to CSV files on disk."""

    @staticmethod
    def export_all(
        lit_matrix_df: pd.DataFrame,
        theme_df: pd.DataFrame,
        gap_df: pd.DataFrame,
        existing_vs_proposed_df: pd.DataFrame,
        trinetra_map_df: pd.DataFrame,
    ) -> None:
        """Export all 5 CSV matrices to disk with UTF-8 encoding."""
        lit_matrix_df.to_csv(str(LITERATURE_MATRIX_CSV), index=False, encoding="utf-8-sig")
        logger.info(f"Saved literature_matrix.csv ({len(lit_matrix_df)} rows) -> {LITERATURE_MATRIX_CSV}")

        theme_df.to_csv(str(THEME_CLASSIFICATION_CSV), index=False, encoding="utf-8-sig")
        logger.info(f"Saved theme_classification.csv ({len(theme_df)} rows) -> {THEME_CLASSIFICATION_CSV}")

        gap_df.to_csv(str(RESEARCH_GAP_CSV), index=False, encoding="utf-8-sig")
        logger.info(f"Saved research_gap_analysis.csv ({len(gap_df)} rows) -> {RESEARCH_GAP_CSV}")

        existing_vs_proposed_df.to_csv(str(EXISTING_VS_PROPOSED_CSV), index=False, encoding="utf-8-sig")
        logger.info(f"Saved existing_vs_proposed.csv ({len(existing_vs_proposed_df)} rows) -> {EXISTING_VS_PROPOSED_CSV}")

        trinetra_map_df.to_csv(str(TRINETRA_MAPPING_CSV), index=False, encoding="utf-8-sig")
        logger.info(f"Saved trinetra_mapping.csv ({len(trinetra_map_df)} rows) -> {TRINETRA_MAPPING_CSV}")
