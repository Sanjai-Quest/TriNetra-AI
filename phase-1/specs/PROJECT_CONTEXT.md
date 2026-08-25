# TriNetra AI: Phase 1 Project Context

## 1. Project Identity
- Name: TriNetra AI
- Phase: Phase 1 (Research MVP)
- Objective: Validate core hypothesis about cross-organizational evidence reconciliation
- Duration: 4-6 weeks
- Technology: PostgreSQL + Python (ONLY - no React, no APIs, no LLM)

## 2. Core Hypothesis (CRITICAL - Don't change this)
"Can multi-source, cross-organizational evidence reconciliation reduce false negatives 
compared with single-source verification?"

## 3. Why This Matters
- Real problem: 162 verified social media complaints about fragmented evidence
- Market gap: Nobody has built cross-org evidence reconciliation (248-paper literature review confirms)
- Customer pain: 106 trust issues, 82 refund issues, 55 delivery problems all map to this
- Research contribution: First validation that multi-source reconciliation outperforms single-source

## 4. What We Learned From Literature Review
- 248 research papers analyzed
- 41 core papers identified (only 20% truly multi-org, 80% component papers)
- This confirms: The gap exists. Nobody has orchestrated these components together.

## 5. Phase 1 Success Metrics (MUST ACHIEVE)
- FN Reduction: Multi-source must reduce false negatives by >15% vs. baselines (p<0.05)
- Precision: ≥0.80 (avoid false accusations)
- Recall: ≥0.75 (catch real conflicts)
- F1: ≥0.77
- FPR: ≤0.15
- Results must be reproducible

## 6. Absolute Rules (NON-NEGOTIABLE)
1. Never invent evidence (only use synthetic data with known ground truth)
2. Never use LLM (Phase 1 is deterministic + statistical only)
3. Never fabricate results (if baselines outperform, document it)
4. Never scope creep (no React, APIs, authentication, LLM, production infrastructure)
5. STOP after Phase 1 (don't automatically proceed to Phase 2)
