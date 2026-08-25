"""
Configuration file for TriNetra AI Phase 2 Literature Analysis & Knowledge Extraction Engine.
Defines input/output paths, 15 research themes, 8 TriNetra modules, and extraction patterns.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Input Literature Dataset Path (Dataset B - relevant papers)
INPUT_CSV_PATH = Path(r"c:\Users\LENOVO\Downloads\xscrapper\research_tool\output\relevant_papers.csv")
ALL_PAPERS_PATH = Path(r"c:\Users\LENOVO\Downloads\xscrapper\research_tool\output\all_papers.csv")

# Output Export Paths
LITERATURE_MATRIX_CSV   = OUTPUT_DIR / "literature_matrix.csv"
THEME_CLASSIFICATION_CSV = OUTPUT_DIR / "theme_classification.csv"
RESEARCH_GAP_CSV         = OUTPUT_DIR / "research_gap_analysis.csv"
EXISTING_VS_PROPOSED_CSV = OUTPUT_DIR / "existing_vs_proposed.csv"
TRINETRA_MAPPING_CSV     = OUTPUT_DIR / "trinetra_mapping.csv"
RESEARCH_SUMMARY_MD      = OUTPUT_DIR / "research_summary.md"
LOG_FILE_PATH            = LOG_DIR / "literature_analysis_log.txt"

# 15 Required Research Themes
RESEARCH_THEMES = [
    "Return Fraud",
    "Return Abuse",
    "Reverse Logistics",
    "Consumer Trust",
    "Customer Experience",
    "Decision Support",
    "Explainable AI",
    "Human in the Loop",
    "Marketplace",
    "Risk Assessment",
    "Return Policy",
    "Refund Management",
    "Seller Trust",
    "Transparency",
    "Evidence Management",
]

# 8 Required TriNetra AI Core Modules
TRINETRA_MODULES = [
    "Evidence Collection",
    "Evidence Consistency",
    "Adaptive Verification",
    "Trust Intelligence",
    "Case Timeline",
    "Explainability",
    "Human Review",
    "Marketplace Dashboard",
]
