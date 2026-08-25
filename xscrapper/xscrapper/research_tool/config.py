"""
Configuration file for TriNetra AI Literature Mining Tool.
Defines API endpoints, tiered search keywords, relevance scoring weights, file paths, and rate limits.
"""

import os
import socket
import urllib3.util.connection as urllib3_cn
from pathlib import Path

# Enable dual-stack socket resolution on Windows networks
def _allowed_gai_family():
    return socket.AF_UNSPEC

urllib3_cn.allowed_gai_family = _allowed_gai_family

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Dataset file paths
ALL_PAPERS_PATH          = OUTPUT_DIR / "all_papers.csv"                   # Dataset A — all ever collected
RELEVANT_PAPERS_PATH     = OUTPUT_DIR / "relevant_papers.csv"              # Dataset B — relevant only (score >= 5)
CORE_TRINETRA_PATH       = OUTPUT_DIR / "core_trinetra.csv"                # Dataset C — top annotated core set
TRINETRA_DATASET_PATH    = OUTPUT_DIR / "trinetra_literature_dataset.csv"  # Full Output CSV (32 Columns)

CSV_FILE_PATH = ALL_PAPERS_PATH
LOG_FILE_PATH = LOG_DIR / "process_log.txt"

# Request Headers
USER_AGENT = "TriNetraResearchBot/1.0 (mailto:trinetra.ai.research@gmail.com)"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json"
}

# API Rate Limits & Timeouts (Seconds)
DEFAULT_TIMEOUT = 15
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
OPENALEX_DELAY = 0.2
SEMANTIC_SCHOLAR_DELAY = 1.0
CROSSREF_DELAY = 0.3

# Tiered Search Keywords per TriNetra Literature Execution Plan
TIER1_KEYWORDS = [
    "cross-organizational evidence reconciliation",
    "multi-source evidence reconciliation",
    "evidence fusion supply chain",
    "product verification e-commerce",
    "warehouse pack verification",
    "order packing verification",
    "product-content verification",
    "multi-stakeholder product verification",
    "product traceability e-commerce",
    "product identity verification",
    "supply chain evidence",
    "product provenance",
    "supply chain provenance",
    "product authentication e-commerce",
    "counterfeit prevention e-commerce",
    "return dispute evidence",
    "return fraud evidence",
    "return abuse",
    "e-commerce dispute resolution",
    "pre-dispatch product verification",
    "cross-enterprise data reconciliation",
    "inter-organizational data reconciliation",
    "evidence provenance",
    "evidence consistency",
    "product lifecycle traceability",
    "multi-source data reconciliation",
    "evidence-based dispute resolution"
]

TIER2_KEYWORDS = [
    "warehouse verification",
    "warehouse computer vision",
    "SKU verification",
    "barcode packing verification",
    "package weight verification",
    "shipment verification",
    "logistics evidence",
    "reverse logistics",
    "return authorization",
    "return inspection",
    "product serialization",
    "QR product authentication",
    "RFID product traceability",
    "supply chain visibility",
    "anomaly detection supply chain",
    "multimodal verification",
    "image-based product verification",
    "explainable decision support",
    "human-in-the-loop verification",
    "trust management marketplace",
    "seller trust",
    "consumer trust",
    "digital evidence management"
]

TIER3_KEYWORDS = [
    "e-commerce",
    "online marketplace",
    "fulfillment",
    "logistics",
    "warehouse management",
    "supply chain security",
    "customer experience",
    "return management",
    "fraud prevention",
    "risk assessment"
]

# Combined search order by priority tier
SEARCH_KEYWORDS = TIER1_KEYWORDS + TIER2_KEYWORDS + TIER3_KEYWORDS

# Relevance Scoring Weights
POSITIVE_WEIGHTS = {
    # Core Tier 1 Concepts (+6 to +10)
    "cross-organizational": 9,
    "evidence reconciliation": 10,
    "multi-source evidence": 10,
    "evidence fusion": 8,
    "product verification": 8,
    "warehouse pack verification": 9,
    "order packing": 8,
    "product-content": 8,
    "multi-stakeholder": 9,
    "product traceability": 8,
    "product identity": 8,
    "supply chain evidence": 9,
    "product provenance": 8,
    "supply chain provenance": 8,
    "product authentication": 8,
    "counterfeit prevention": 8,
    "return dispute": 9,
    "return fraud": 9,
    "return abuse": 9,
    "dispute resolution": 8,
    "pre-dispatch": 9,
    "cross-enterprise": 9,
    "inter-organizational": 9,
    "evidence provenance": 9,
    "evidence consistency": 9,
    "product lifecycle": 8,
    "data reconciliation": 8,

    # Core Tier 2 & Supporting (+4 to +7)
    "reverse logistics": 7,
    "warehouse verification": 7,
    "sku verification": 7,
    "package weight": 7,
    "shipment verification": 6,
    "logistics evidence": 7,
    "return authorization": 7,
    "return inspection": 7,
    "product serialization": 7,
    "qr product": 7,
    "rfid product": 7,
    "anomaly detection supply chain": 7,
    "multimodal verification": 7,
    "image-based product": 6,
    "explainable decision support": 7,
    "explainable ai": 6,
    "human-in-the-loop": 6,
    "trust management": 6,
    "seller trust": 6,
    "consumer trust": 5,
    "digital evidence": 7,
    "audit trail": 6,
    "e-commerce": 4,
    "marketplace": 4,
    "wardrobing": 8,
    "product switching": 8,
    "empty box": 8
}

# Negative Penalties
NEGATIVE_WEIGHTS = {
    "credit card fraud": -15,
    "insurance fraud": -15,
    "medical": -15,
    "healthcare": -15,
    "wireless networks": -12,
    "image compression": -12,
    "agriculture": -12,
    "biology": -15,
    "genomics": -15,
    "cancer": -15,
    "patient": -15,
    "clinical": -15,
    "bioinformatics": -15,
    "sensor network": -10,
    "crop": -15,
    "solar": -15,
    "banking fraud": -15,
    "intrusion detection": -12
}

# Relevance Classification Thresholds (matching README brackets)
CLASSIFICATION_THRESHOLDS = {
    "Highly Relevant": 15.0,
    "Relevant": 10.0,
    "Possibly Relevant": 5.0,
    "Irrelevant": 0.0
}

# Problem Statement Extraction Indicators
PROBLEM_INDICATOR_PATTERNS = [
    r"\bthis (?:paper|study|article|research|work) (?:addresses|investigates|focuses on|tackles|examines|proposes|presents)\b",
    r"\bthe (?:main|primary|key) (?:problem|challenge|issue|objective|goal|aim)\b",
    r"\baims to (?:address|resolve|mitigate|tackle|investigate|explore)\b",
    r"\bmotivated by\b",
    r"\bhowever,?\b",
    r"\bdespite\b",
    r"\bchallenge of\b",
    r"\black of\b",
    r"\bdispute resolution\b",
    r"\breturn fraud\b",
    r"\bfinancial losses?\b",
    r"\btrust gap\b",
    r"\bfragmented evidence\b"
]
