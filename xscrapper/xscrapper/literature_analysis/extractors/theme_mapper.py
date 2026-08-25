"""
Theme Mapper Module for Phase 2 Literature Analysis.
Maps research papers across 15 explicit themes.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from literature_analysis.config import RESEARCH_THEMES

logger = logging.getLogger("literature_logger")

THEME_KEYWORDS_MAP = {
    "Return Fraud": ["return fraud", "fraudulent return", "empty box", "brick inside", "product switching", "forged return"],
    "Return Abuse": ["wardrobing", "return abuse", "opportunistic return", "unethical return", "serial returner", "policy abuse"],
    "Reverse Logistics": ["reverse logistics", "returns management", "return network", "circular logistics", "closed loop supply chain", "return process"],
    "Consumer Trust": ["consumer trust", "customer trust", "buyer trust", "trust building", "trusting belief", "trustworthiness"],
    "Customer Experience": ["customer experience", "post purchase", "consumer satisfaction", "shopping experience", "post-purchase"],
    "Decision Support": ["decision support", "decision making", "mcda", "swara", "multi attribute", "evaluative ai"],
    "Explainable AI": ["explainable ai", "xai", "explainability", "interpretability", "transparent model", "explainable recommendation"],
    "Human in the Loop": ["human in the loop", "human agent", "human review", "human expertise", "human-machine"],
    "Marketplace": ["marketplace", "e-commerce platform", "platform economy", "online retail", "multi sided marketplace"],
    "Risk Assessment": ["risk assessment", "fraud risk", "risk profiling", "financial fraud", "anomaly detection"],
    "Return Policy": ["return policy", "lenient policy", "stringent policy", "return window", "policy design"],
    "Refund Management": ["refund", "refund delay", "refund fraud", "refund process", "vat refund", "dispute resolution"],
    "Seller Trust": ["seller trust", "seller protection", "merchant trust", "seller risk"],
    "Transparency": ["transparency", "audit trail", "explainable", "openness", "legal certainty"],
    "Evidence Management": ["evidence", "proof", "unboxing", "verification", "smart contract", "blockchain evidence"],
}


class ThemeMapper:
    """Maps research papers to 15 explicit research themes."""

    @staticmethod
    def map_themes(paper: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Map paper to primary theme and list of secondary themes.
        Returns (primary_theme, secondary_themes_list).
        """
        def safe_str(val):
            if val is None or (isinstance(val, float)):
                return ""
            return str(val)

        title = safe_str(paper.get("Title")).lower()
        abstract = safe_str(paper.get("Abstract")).lower()
        keywords = safe_str(paper.get("Keywords")).lower()

        combined = f"{title} {abstract} {keywords}"

        scores = {}
        for theme, kw_list in THEME_KEYWORDS_MAP.items():
            count = 0
            for kw in kw_list:
                pattern = r"\b" + re.escape(kw) + r"\b"
                title_hits = 3 if re.search(pattern, title) else 0
                abstract_hits = len(re.findall(pattern, combined))
                count += title_hits + abstract_hits
            scores[theme] = count

        # Sort themes by hit count descending
        sorted_themes = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        matched = [t for t, score in sorted_themes if score > 0]

        if not matched:
            primary = "Marketplace"
            secondary = ["Consumer Trust", "Decision Support"]
        else:
            primary = matched[0]
            secondary = matched[1:4] if len(matched) > 1 else ["Consumer Trust"]

        return primary, secondary
