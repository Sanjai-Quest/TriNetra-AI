"""
Matrix Builder Module for Phase 2 Literature Analysis.
Constructs all 5 required structured CSV DataFrames from extracted knowledge.
"""

import logging
import pandas as pd
from typing import List, Dict, Any
from literature_analysis.config import TRINETRA_MODULES

logger = logging.getLogger("literature_logger")


class MatrixBuilder:
    """Constructs the 5 Phase 2 literature comparison matrices."""

    # 1. Literature Matrix DataFrame
    @staticmethod
    def build_literature_matrix(knowledge_list: List[Dict[str, Any]]) -> pd.DataFrame:
        cols = ["Paper", "Problem", "Solution", "Contribution", "Limitation", "Research Gap", "TriNetra Opportunity"]
        rows = []
        for k in knowledge_list:
            rows.append({
                "Paper": k.get("Paper", ""),
                "Problem": k.get("Problem", ""),
                "Solution": k.get("Solution", ""),
                "Contribution": k.get("Contribution", ""),
                "Limitation": k.get("Limitation", ""),
                "Research Gap": k.get("Research_Gap", ""),
                "TriNetra Opportunity": k.get("TriNetra_Opportunity", ""),
            })
        return pd.DataFrame(rows, columns=cols)

    # 2. Theme Classification DataFrame
    @staticmethod
    def build_theme_classification(processed_papers: List[Dict[str, Any]]) -> pd.DataFrame:
        cols = ["Paper_ID", "Title", "Primary_Theme", "Secondary_Themes", "Relevance_Score", "Year"]
        rows = []
        for p in processed_papers:
            rows.append({
                "Paper_ID": p.get("Paper_ID", ""),
                "Title": p.get("Title", ""),
                "Primary_Theme": p.get("Primary_Theme", ""),
                "Secondary_Themes": "; ".join(p.get("Secondary_Themes", [])),
                "Relevance_Score": p.get("Relevance_Score", 0.0),
                "Year": p.get("Year", ""),
            })
        return pd.DataFrame(rows, columns=cols)

    # 3. Research Gap Analysis DataFrame
    @staticmethod
    def build_research_gap_analysis(processed_papers: List[Dict[str, Any]]) -> pd.DataFrame:
        cols = ["Paper_ID", "Title", "Identified_Gap", "TriNetra_Solution", "Module_Impact"]
        rows = []
        for p in processed_papers:
            gap = p.get("Research_Gap", "")
            rows.append({
                "Paper_ID": p.get("Paper_ID", ""),
                "Title": p.get("Title", ""),
                "Identified_Gap": gap,
                "TriNetra_Solution": f"TriNetra addresses this by providing {gap.lower().replace('focuses on', 'replacing with')}",
                "Module_Impact": "; ".join(p.get("TriNetra_Modules", [])[:2]),
            })
        return pd.DataFrame(rows, columns=cols)

    # 4. Existing vs Proposed Comparison DataFrame
    @staticmethod
    def build_existing_vs_proposed() -> pd.DataFrame:
        cols = ["Literature_Limitation", "How_TriNetra_Addresses_It", "Target_Module", "Research_Advantage"]
        comparisons = [
            {
                "Literature_Limitation": "Isolated fraud detection focusing only on customer account history without physical package verification.",
                "How_TriNetra_Addresses_It": "Integrates multi-stakeholder evidence (customer unboxing videos, carrier pickup scans, warehouse weight inspection).",
                "Target_Module": "Evidence Collection & Evidence Consistency",
                "Research_Advantage": "Eliminates blind spots by cross-verifying multi-source evidence before assigning fraud risk."
            },
            {
                "Literature_Limitation": "Static return policies that apply uniform verification friction to all customers regardless of risk level.",
                "How_TriNetra_Addresses_It": "Dynamically adjusts verification friction based on real-time evidence consistency and multi-stakeholder trust scores.",
                "Target_Module": "Adaptive Verification",
                "Research_Advantage": "Reduces return friction for honest customers while applying targeted verification to high-risk transactions."
            },
            {
                "Literature_Limitation": "Black-box ML decision support that fails to explain recommendation rationale to merchants and customers.",
                "How_TriNetra_Addresses_It": "Generates natural language, evidence-backed decision explanations for every dispute recommendation.",
                "Target_Module": "Explainability & Human Review",
                "Research_Advantage": "Preserves buyer-seller trust and ensures compliance with explainable AI principles."
            },
            {
                "Literature_Limitation": "Binary fraud labeling ('fraudulent' vs 'legitimate') without tracking the full dispute lifecycle.",
                "How_TriNetra_Addresses_It": "Tracks every evidence item, scan event, and communication step across an immutable dispute timeline.",
                "Target_Module": "Case Timeline",
                "Research_Advantage": "Provides complete auditability and continuous resolution tracking for e-commerce marketplaces."
            },
            {
                "Literature_Limitation": "Focuses solely on buyer behavior while ignoring seller fraudulent practices (e.g. counterfeit shipping, wrong items).",
                "How_TriNetra_Addresses_It": "Computes symmetric, dynamic trust scores for both buyers and sellers across historical transaction lifecycles.",
                "Target_Module": "Trust Intelligence & Marketplace Dashboard",
                "Research_Advantage": "Protects honest buyers and honest sellers equally, fostering multi-stakeholder ecosystem trust."
            }
        ]
        return pd.DataFrame(comparisons, columns=cols)

    # 5. TriNetra Mapping DataFrame
    @staticmethod
    def build_trinetra_mapping(processed_papers: List[Dict[str, Any]]) -> pd.DataFrame:
        cols = ["TriNetra_Module", "Supporting_Paper_IDs", "Total_Papers", "Core_Concepts_Covered"]
        
        module_papers = {m: [] for m in TRINETRA_MODULES}
        for p in processed_papers:
            pid = p.get("Paper_ID", "")
            for m in p.get("TriNetra_Modules", []):
                if m in module_papers:
                    module_papers[m].append(pid)

        concept_map = {
            "Evidence Collection": "Unboxing videos, photo proof, carrier scans, packaging weight, serial numbers.",
            "Evidence Consistency": "Multi-modal cross-verification, discrepancy detection, counterfeit/wardrobing verification.",
            "Adaptive Verification": "Proportional inspection friction, dynamic return policy, risk-based intervention.",
            "Trust Intelligence": "Multi-stakeholder trust scoring, seller risk profiling, buyer reputation tracking.",
            "Case Timeline": "Immutable dispute lifecycle tracking, event logging, status tracking.",
            "Explainability": "Natural language decision rationale, transparent evidence attribution, XAI support.",
            "Human Review": "Machine-in-the-loop co-pilot, evaluative AI, dispute arbitration support.",
            "Marketplace Dashboard": "Centralized marketplace visibility, reverse logistics tracking, fraud analytics.",
        }

        rows = []
        for m in TRINETRA_MODULES:
            pids = module_papers.get(m, [])
            rows.append({
                "TriNetra_Module": m,
                "Supporting_Paper_IDs": "; ".join(pids[:10]) + (f" (+{len(pids)-10} more)" if len(pids) > 10 else ""),
                "Total_Papers": len(pids),
                "Core_Concepts_Covered": concept_map.get(m, "Core dispute resolution capability."),
            })
        return pd.DataFrame(rows, columns=cols)
