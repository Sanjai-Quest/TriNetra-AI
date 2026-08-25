"""
Deterministic Knowledge Extractor Module.
Extracts problem, solution, methodology, contribution, limitations, and research gap
from paper title, problem statement, and abstract.
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger("literature_logger")


class KnowledgeExtractor:
    """Extracts 6 core knowledge dimensions from research paper text."""

    @staticmethod
    def safe_str(val: Any) -> str:
        """Safely convert value to string, handling None or empty inputs."""
        return str(val) if val is not None else ""

    @staticmethod
    def extract_methodology(text: str) -> str:
        """Identify methodology used in the paper."""
        text_lower = text.lower()

        methods = [
            ("Mixed Integer Linear Programming (MILP)", ["mixed integer linear programming", "milp", "integer programming"]),
            ("Hierarchical Clustering & Spatial Modeling", ["hierarchical clustering", "cluster analysis", "spatial modeling"]),
            ("Empirical Survey & Structural Equation Modeling (SEM)", ["structural equation modeling", "sem", "survey of", "questionnaire", "empirical survey"]),
            ("Case Study & Qualitative Analysis", ["case study", "qualitative analysis", "interviews", "field study"]),
            ("Logistic Regression & Penalized Likelihood", ["logistic regression", "penalised likelihood", "regression model"]),
            ("Deep Learning & Ensemble Machine Learning", ["deep learning", "xgboost", "random forest", "neural network", "machine learning"]),
            ("Reinforcement Learning & Online Learning", ["reinforcement learning", "online learning", "adaptive machine learning"]),
            ("Game Theory & Oligopoly Modeling", ["game theory", "oligopoly model", "mathematical model", "theoretical model"]),
            ("Systematic Literature Review & Meta-Analysis", ["literature review", "systematic review", "meta-analysis", "comprehensive review"]),
            ("Blockchain & Smart Contracts", ["blockchain", "smart contract", "ethereum", "distributed ledger"]),
            ("Multi-Criteria Decision Analysis (MCDA / SWARA)", ["swara", "mcda", "multi-criteria", "multi attribute", "step-wise weight"]),
        ]

        for label, keywords in methods:
            if any(k in text_lower for k in keywords):
                return label

        return "Empirical & Analytical Framework"

    @staticmethod
    def extract_contribution(paper: Dict[str, Any]) -> str:
        """Extract main contribution statement."""
        abstract = KnowledgeExtractor.safe_str(paper.get("Abstract"))
        title = KnowledgeExtractor.safe_str(paper.get("Title"))

        # Look for explicit contribution sentences in abstract
        patterns = [
            r"(?:this study|this paper|we propose|we present|results show that|findings indicate that|the paper contributes|contributes to)[^.?!]*[.?!]",
            r"(?:this paper proposes|this study introduces|a novel framework)[^.?!]*[.?!]"
        ]

        for p in patterns:
            match = re.search(p, abstract, re.IGNORECASE)
            if match:
                sentence = match.group(0).strip()
                if len(sentence) > 20 and len(sentence) < 300:
                    return sentence

        return f"Provides theoretical and empirical insights on {title[:80]}."

    @staticmethod
    def extract_limitations(paper: Dict[str, Any]) -> str:
        """Extract explicit or inferred research limitations."""
        abstract = KnowledgeExtractor.safe_str(paper.get("Abstract")).lower()

        # Look for limitation phrases
        lim_patterns = [
            r"(?:however|limitations?|restricted to|focused only on|lacks|confined to|case study based)[^.?!]*[.?!]"
        ]

        for p in lim_patterns:
            match = re.search(p, abstract, re.IGNORECASE)
            if match:
                sentence = match.group(0).strip()
                if len(sentence) > 15 and len(sentence) < 250:
                    return sentence

        # Inferred limitations based on methodology/topic
        if "case study" in abstract:
            return "Limited to single-firm or regional case study data; generalizability across diverse e-commerce marketplaces remains unverified."
        elif "survey" in abstract or "questionnaire" in abstract:
            return "Relies on self-reported consumer survey data, which is susceptible to response bias and lacks real-time transaction verification."
        elif "static" in abstract or "framework" in abstract:
            return "Static framework lacking real-time evidence orchestration, automated cross-verification, and dynamic multi-stakeholder trust scoring."

        return "Static analysis lacking automated real-time multi-stakeholder evidence cross-verification."

    @staticmethod
    def extract_research_gap(paper: Dict[str, Any]) -> str:
        """Extract research gap relevant to TriNetra AI."""
        abstract = KnowledgeExtractor.safe_str(paper.get("Abstract")).lower()

        if "fraud" in abstract and "return" in abstract:
            return "Focuses on isolated fraud detection without integrating multi-stakeholder evidence (customer photos, courier tracking, warehouse scans) into an explainable case timeline."
        elif "reverse logistics" in abstract or "return" in abstract:
            return "Optimizes reverse logistics infrastructure but fails to address return fraud detection, evidence verification, and consumer trust preservation."
        elif "trust" in abstract:
            return "Examines consumer trust conceptually without providing an automated, transparent evidence verification engine for dispute resolution."
        elif "explainable" in abstract or "xai" in abstract:
            return "Proposes generic explainability without tailoring explanations for multi-stakeholder e-commerce dispute resolution."

        return "Does not provide an end-to-end evidence-driven, explainable dispute resolution platform."

    def extract_knowledge(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full knowledge extraction on a paper."""
        title = self.safe_str(paper.get("Title"))
        abstract = self.safe_str(paper.get("Abstract"))
        problem_stmt = self.safe_str(paper.get("Problem_Statement")) or f"Addresses challenges in {title[:60]}."

        methodology = self.extract_methodology(f"{title} {abstract}")
        contribution = self.extract_contribution(paper)
        limitations = self.extract_limitations(paper)
        research_gap = self.extract_research_gap(paper)

        solution = contribution

        return {
            "Paper_ID": self.safe_str(paper.get("Paper_ID")),
            "Paper": f"[{self.safe_str(paper.get('Year'))}] {title}",
            "Problem": problem_stmt,
            "Solution": solution,
            "Methodology": methodology,
            "Contribution": contribution,
            "Limitation": limitations,
            "Research_Gap": research_gap,
            "TriNetra_Opportunity": f"TriNetra bridges this gap via {research_gap.lower().replace('focuses on', 'replacing').replace('lacks', 'with')}",
        }
