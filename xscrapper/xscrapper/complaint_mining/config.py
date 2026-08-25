"""
Configuration file for TriNetra AI Social Media Complaint Mining Tool.
Defines platforms, target brands, search keywords, classification rules,
severity heuristics, stakeholder rules, TriNetra module mappings, and file paths.
"""

import socket
import urllib3.util.connection as urllib3_cn
from pathlib import Path

# Enable IPv6 / dual-stack socket resolution on Windows networks
def _allowed_gai_family():
    return socket.AF_INET6

urllib3_cn.allowed_gai_family = _allowed_gai_family

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

COMPLAINTS_CSV_PATH = OUTPUT_DIR / "customer_complaints_dataset.csv"
STATISTICS_CSV_PATH = OUTPUT_DIR / "complaint_statistics.csv"
CLUSTERS_CSV_PATH   = OUTPUT_DIR / "problem_clusters.csv"
LOG_FILE_PATH       = LOG_DIR / "complaint_collection_log.txt"

# Network Headers
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Target Brands
TARGET_BRANDS = [
    "Amazon",
    "Flipkart",
    "Myntra",
    "Meesho",
    "Ajio",
    "Nykaa",
    "JioMart",
    "Snapdeal",
    "Shopify",
    "D2C Brand",
]

# Product Categories
PRODUCT_CATEGORIES = [
    "Apparel/Clothing",
    "Footwear",
    "Accessories",
    "Electronics",
    "Beauty/Personal Care",
    "Home/Kitchen",
    "Other/Unspecified",
]

# Search Keywords
SEARCH_KEYWORDS = [
    "return fraud",
    "return abuse",
    "refund delayed",
    "refund rejected",
    "return rejected",
    "wrong product received",
    "fake product",
    "counterfeit product",
    "used product received",
    "damaged product delivered",
    "missing items",
    "empty box delivery",
    "return pickup failed",
    "seller fraud",
    "fake seller",
    "delivery failed",
    "customer support",
    "poor customer service",
    "refund not received",
    "replacement rejected",
    "delivery scam",
    "warehouse issue",
    "return policy",
    "COD fraud",
    "open box delivery",
    "marketplace fraud",
    "broken product",
    "refund process",
    "order cancelled",
    "return window",
    "lost package",
    "price mismatch",
    "product mismatch",
    "quality issue",
    # Apparel & Fashion Specific Keywords
    "wrong size received",
    "size doesn't match",
    "wrong color dress",
    "fabric quality issue",
    "wrong fit clothing",
    "return rejected clothes",
    "used clothes delivered",
    "wrong garment sent",
    "fake branded clothing",
    "stitching defect",
    "myntra return issue",
    "ajio wrong size",
    "wrong shoe size delivered",
]

# Target Subreddits for Reddit OSINT Collector
TARGET_SUBREDDITS = [
    "AmazonIn",
    "Flipkart",
    "eCommerce",
    "IndiaTech",
    "LegalAdviceIndia",
    "ConsumerRights",
    "IndiaGamer",
    "IndianBeautyDeals",
    "retail",
]

# Complaint Types
COMPLAINT_TYPES = [
    "Wrong Product",
    "Damaged Product",
    "Used Product",
    "Counterfeit Product",
    "Refund Delay",
    "Return Rejected",
    "Replacement Rejected",
    "Pickup Failure",
    "Delivery Failure",
    "Lost Package",
    "Seller Fraud",
    "Fake Seller",
    "COD Scam",
    "Packaging Issue",
    "Customer Support",
    "Policy Issue",
    "Warehouse Issue",
    "Price Mismatch",
    "Missing Items",
    "Other",
]

# TriNetra AI Modules
TRINETRA_MODULES = [
    "Evidence Collection",
    "Evidence Consistency",
    "Adaptive Verification",
    "Trust Score",
    "Case Timeline",
    "Explainability",
    "Human Review",
    "Marketplace Dashboard",
]

# Problem Clusters
PROBLEM_CLUSTERS = [
    "Trust Issues",
    "Refund Issues",
    "Return Abuse",
    "Seller Problems",
    "Delivery Problems",
    "Verification Problems",
    "Customer Service",
    "Policy Problems",
    "Marketplace Transparency",
    "Evidence Problems",
]
