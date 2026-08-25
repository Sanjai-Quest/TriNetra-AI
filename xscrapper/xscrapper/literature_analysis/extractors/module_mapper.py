"""
TriNetra Module Mapper for Phase 2 Literature Analysis.
Maps research papers to 8 TriNetra AI core modules.
"""

import re
import logging
from typing import Dict, Any, List
from literature_analysis.config import TRINETRA_MODULES

logger = logging.getLogger("literature_logger")

MODULE_PATTERNS = {
    "Evidence Collection": ["evidence", "proof", "photo", "unboxing", "inspection", "serial number", "footprint", "smart contract"],
    "Evidence Consistency": ["consistency", "cross-verification", "mismatch", "fraud detection", "discrepancy", "counterfeit", "wardrobing"],
    "Adaptive Verification": ["adaptive", "verification", "risk-based", "proportional", "selective inspection", "dynamic policy"],
    "Trust Intelligence": ["trust", "trustworthiness", "trust score", "reputation", "seller protection", "buyer trust"],
    "Case Timeline": ["timeline", "dispute", "lifecycle", "history", "tracking", "refund delay", "case management"],
    "Explainability": ["explainable", "xai", "explainability", "interpretability", "transparent", "decision support"],
    "Human Review": ["human in the loop", "human agent", "human review", "evaluative ai", "arbitration", "human expertise"],
    "Marketplace Dashboard": ["marketplace", "platform", "dashboard", "merchant", "supply chain", "reverse logistics"],
}


class ModuleMapper:
    """Maps research papers to 8 TriNetra AI core modules."""

    @staticmethod
    def map_modules(paper: Dict[str, Any]) -> List[str]:
        """Return list of TriNetra modules supported by paper evidence."""
        def safe_str(val):
            if val is None or isinstance(val, float):
                return ""
            return str(val)

        title = safe_str(paper.get("Title")).lower()
        abstract = safe_str(paper.get("Abstract")).lower()

        combined = f"{title} {abstract}"
        mapped = []

        for module_name, keywords in MODULE_PATTERNS.items():
            if any(re.search(r"\b" + re.escape(k) + r"\b", combined) for k in keywords):
                mapped.append(module_name)

        # Guarantee at least 1 module is mapped
        if not mapped:
            mapped = ["Marketplace Dashboard", "Trust Intelligence"]

        return mapped
