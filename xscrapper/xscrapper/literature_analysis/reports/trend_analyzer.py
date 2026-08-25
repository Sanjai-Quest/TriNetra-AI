"""
Trend Analyzer Module for Phase 2 Literature Analysis.
Calculates trend statistics across themes, methodologies, limitations, and research gaps.
"""

import logging
import pandas as pd
from typing import List, Dict, Any

logger = logging.getLogger("literature_logger")


class TrendAnalyzer:
    """Calculates research trend statistics from literature dataset."""

    @staticmethod
    def analyze_trends(processed_papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute comprehensive research trend statistics."""
        df = pd.DataFrame(processed_papers)
        total = len(df)

        if total == 0:
            return {}

        # 1. Primary Themes Count
        primary_counts = df["Primary_Theme"].value_counts().to_dict()

        # 2. All Mentioned Themes Count
        all_themes = []
        for p in processed_papers:
            all_themes.append(p.get("Primary_Theme"))
            all_themes.extend(p.get("Secondary_Themes", []))

        theme_series = pd.Series(all_themes).value_counts()
        theme_counts = theme_series.to_dict()

        most_researched = theme_series.head(3).to_dict()
        least_researched = theme_series.tail(3).to_dict()

        # 3. Methodologies Breakdown
        method_counts = df["Methodology"].value_counts().to_dict()

        # 4. TriNetra Module Coverage Breakdown
        all_modules = []
        for p in processed_papers:
            all_modules.extend(p.get("TriNetra_Modules", []))
        module_counts = pd.Series(all_modules).value_counts().to_dict()

        return {
            "Total_Papers_Analyzed": total,
            "Primary_Theme_Counts": primary_counts,
            "All_Theme_Counts": theme_counts,
            "Most_Researched_Themes": most_researched,
            "Least_Researched_Themes": least_researched,
            "Methodology_Breakdown": method_counts,
            "Module_Coverage_Counts": module_counts,
        }
