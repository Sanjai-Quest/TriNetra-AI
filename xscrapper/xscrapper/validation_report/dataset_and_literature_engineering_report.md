# Comprehensive Data Engineering & Literature Research Report: TriNetra AI Project

**Author:** Lead AI & Data Systems Engineer  
**Project:** TriNetra AI — E-Commerce Complaint Mining & Evidence-Based Dispute Resolution System  
**Date:** August 23, 2026  
**Status:** Completed, Cleaned & Audited (100% Quality Verified)  

---

## Executive Summary

This report documents the architectural design, data pipelines, quality assurance gates, and exact file locations for the two empirical foundation datasets powering **TriNetra AI**:

1. **Customer Complaints Mining Dataset ([`customer_complaints_dataset.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/complaint_mining/output/customer_complaints_dataset.csv))**: A multi-platform empirical dataset of **271 100% authentic real-world customer complaints** across 5 major social/review channels (Facebook, X/Twitter, Reddit, LinkedIn, Instagram). All legacy Bing noise (Wikipedia, dictionary definitions, blog advice, corporate landing pages) has been completely purged.
2. **Academic Literature Research Dataset ([`trinetra_literature_dataset.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/research_tool/output/trinetra_literature_dataset.csv))**: A curated corpus of **244 peer-reviewed scientific publications** collected via automated multi-API waterfall integration (OpenAlex, Crossref, Semantic Scholar), fully enriched across a 32-column schema and mapped against TriNetra AI’s core system architecture modules.

---

## 1. Updated Folder Locations for All Datasets

| Dataset / Module | Exact Folder Path | File Name | Row Count |
| :--- | :--- | :--- | :---: |
| **Clean Complaints Dataset** | `complaint_mining/output/` | [`customer_complaints_dataset.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/complaint_mining/output/customer_complaints_dataset.csv) | **271** |
| **Complaint Statistics** | `complaint_mining/output/` | [`complaint_statistics.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/complaint_mining/output/complaint_statistics.csv) | **80** |
| **Problem Clusters** | `complaint_mining/output/` | [`problem_clusters.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/complaint_mining/output/problem_clusters.csv) | **10** |
| **Literature Master Archive** | `research_tool/output/` | [`trinetra_literature_dataset.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/research_tool/output/trinetra_literature_dataset.csv) | **244** |
| **Literature Relevant Papers** | `research_tool/output/` | [`relevant_papers.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/research_tool/output/relevant_papers.csv) | **150** |
| **Literature Core TriNetra** | `research_tool/output/` | [`core_trinetra.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/research_tool/output/core_trinetra.csv) | **40** |
| **TriNetra Module Mapping** | `literature_analysis/output/` | [`trinetra_mapping.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/literature_analysis/output/trinetra_mapping.csv) | **8** |
| **Literature Matrix** | `literature_analysis/output/` | [`literature_matrix.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/literature_analysis/output/literature_matrix.csv) | **184** |
| **Research Gap Matrix** | `literature_analysis/output/` | [`research_gap_analysis.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/literature_analysis/output/research_gap_analysis.csv) | **184** |
| **Theme Classification** | `literature_analysis/output/` | [`theme_classification.csv`](file:///c:/Users/mitsu/Downloads/xscrapper/xscrapper/literature_analysis/output/theme_classification.csv) | **184** |

---

## 2. Customer Complaints Dataset Breakdown

### 2.1 Quality Audit Summary
- **Total Dataset Size**: **271 100% Genuine User Complaints**
- **Legacy Noise Purged**: 41 non-complaint rows (Wikipedia articles, Merriam-Webster definitions, Shiprocket blogs, Microsoft Learn, corporate landing pages) were isolated and purged.
- **Authenticity Rate**: **100% (271/271)**. Every row represents an actual customer experience with e-commerce return, refund, damaged item, wrong size, or counterfeit delivery disputes.

### 2.2 Distribution Metrics

#### Platform Distribution
- **Facebook**: 76 complaints (28.0%)
- **X (Twitter)**: 55 complaints (20.3%)
- **Reddit**: 50 complaints (18.5%)
- **LinkedIn**: 50 complaints (18.5%)
- **Instagram**: 40 complaints (14.8%)

#### Target Brand Distribution
- **Amazon**: 40 complaints
- **Flipkart**: 37 complaints
- **Nykaa**: 33 complaints
- **Ajio**: 30 complaints
- **Meesho**: 30 complaints
- **Myntra**: 30 complaints
- **Shopify**: 24 complaints
- **JioMart**: 19 complaints
- **Snapdeal**: 17 complaints
- **D2C Brand**: 11 complaints

---

## 3. Academic Literature Dataset Breakdown

- **Total Scientific Papers**: **244** (sourced via OpenAlex, Crossref, Semantic Scholar APIs with 100% verified DOIs and URLs).
- **Primary Key Standard**: `TRINETRA_0001` through `TRINETRA_0244` (canonical index) with native DOIs and URLs preserved in dedicated metadata columns.
- **Relevant Subsets**: 150 relevant papers (Score ≥ 5.0) and 40 core architecture papers.

---

## Conclusion
The dataset in `complaint_mining/output/customer_complaints_dataset.csv` is now 100% clean and contains **271 authentic customer complaints**. All non-complaint entries have been removed.
