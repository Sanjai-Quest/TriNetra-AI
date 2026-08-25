"""
Research Problem Clustering Engine for TriNetra AI Complaints.
Clusters complaints into 10 major research problem themes and outputs problem_clusters.csv.
"""

import re
import logging
import pandas as pd
from typing import Dict, Any, List

logger = logging.getLogger("complaint_logger")

CLUSTER_RULES = {
    "Trust Issues": [
        "trust", "fake seller", "counterfeit", "replica", "cheated", "scam", "fraud", "seller fraud"
    ],
    "Refund Issues": [
        "refund", "money", "bank", "account", "transaction", "amount not credited", "refund delay", "refund rejected"
    ],
    "Return Abuse": [
        "return abuse", "wardrobing", "used product", "empty box", "brick inside", "product switching", "serial returner"
    ],
    "Seller Problems": [
        "seller", "merchant", "vendor", "bad seller", "unresponsive seller", "fake rating"
    ],
    "Delivery Problems": [
        "delivery", "pickup", "courier", "logistic", "transit", "lost package", "agent", "delivery failed"
    ],
    "Verification Problems": [
        "verification", "proof", "serial number", "photo proof", "video proof", "imei", "otp", "open box"
    ],
    "Customer Service": [
        "customer service", "customer support", "customer care", "bot", "call center", "no response", "agent refused"
    ],
    "Policy Problems": [
        "policy", "return window", "terms", "condition", "non returnable", "7 days", "10 days"
    ],
    "Marketplace Transparency": [
        "transparency", "hidden fee", "price mismatch", "overcharged", "hidden policy", "misleading"
    ],
    "Evidence Problems": [
        "evidence", "unboxing video", "photo rejected", "claim rejected", "dispute", "proof rejected"
    ],
}


class ComplaintClusterer:
    """Assigns complaints to research problem clusters and generates cluster summary dataset."""

    @staticmethod
    def assign_cluster(complaint: Dict[str, Any]) -> str:
        """Assign single best-matching research problem cluster to complaint."""
        combined = f"{complaint.get('Complaint_Title', '')} {complaint.get('Complaint_Text', '')} {complaint.get('Complaint_Type', '')}".lower()

        best_cluster = "Trust Issues"
        max_hits = 0

        for cluster_name, keywords in CLUSTER_RULES.items():
            hits = sum(1 for k in keywords if re.search(r"\b" + re.escape(k) + r"\b", combined))
            if hits > max_hits:
                max_hits = hits
                best_cluster = cluster_name

        return best_cluster

    @classmethod
    def generate_clusters_summary(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Generate structured problem_clusters.csv dataframe summarizing themes and key stats."""
        if df.empty:
            return pd.DataFrame(columns=["Cluster_Name", "Frequency", "Percentage", "Top_Platforms", "Top_Companies", "Severity_Breakdown", "TriNetra_Research_Relevance"])

        if "Problem_Cluster" not in df.columns:
            df["Problem_Cluster"] = df.apply(cls.assign_cluster, axis=1)

        total_count = len(df)
        cluster_rows = []

        for cluster in CLUSTER_RULES.keys():
            cdf = df[df["Problem_Cluster"] == cluster]
            freq = len(cdf)
            pct = round((freq / total_count) * 100, 2) if total_count > 0 else 0.0

            top_platforms = ", ".join(cdf["Platform"].value_counts().head(3).index.tolist()) if not cdf.empty else "N/A"
            top_companies = ", ".join(cdf["Company"].value_counts().head(3).index.tolist()) if not cdf.empty else "N/A"

            sev_counts = cdf["Severity"].value_counts().to_dict() if not cdf.empty else {}
            sev_str = "; ".join([f"{k}: {v}" for k, v in sev_counts.items()]) if sev_counts else "None"

            # TriNetra research relevance mapping
            relevance_map = {
                "Trust Issues": "Validates Multi-Stakeholder Trust Score module and seller risk profiling.",
                "Refund Issues": "Validates Case Timeline tracking and automated refund trigger mechanics.",
                "Return Abuse": "Validates Adaptive Verification & Evidence Consistency to detect fraudulent returns.",
                "Seller Problems": "Validates Marketplace Dashboard & Seller Verification infrastructure.",
                "Delivery Problems": "Validates Reverse Logistics integration and courier tracking verification.",
                "Verification Problems": "Validates Evidence Collection (unboxing proof, serial number matching).",
                "Customer Service": "Validates Human Review co-pilot & Explainability decision support.",
                "Policy Problems": "Validates Dynamic & Transparent Return Policy orchestration.",
                "Marketplace Transparency": "Validates Transparent Decision Support and dispute audit trails.",
                "Evidence Problems": "Validates Evidence Consistency Engine & multi-modal proof analysis."
            }

            cluster_rows.append({
                "Cluster_Name": cluster,
                "Frequency": freq,
                "Percentage": f"{pct}%",
                "Top_Platforms": top_platforms,
                "Top_Companies": top_companies,
                "Severity_Breakdown": sev_str,
                "TriNetra_Research_Relevance": relevance_map.get(cluster, "Direct TriNetra AI research validation.")
            })

        return pd.DataFrame(cluster_rows)
