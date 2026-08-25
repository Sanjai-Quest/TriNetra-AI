"""
Baseline 3: Timeline-Only Verification (Single-Source Temporal Model)
Evaluates dispute validity solely based on chronological event ordering across checkpoints.
"""

from datetime import datetime
from typing import List, Dict, Any


class Baseline3TimelineOnly:
    """Baseline 3 checking only timestamp chronology."""

    EVENT_HIERARCHY = {
        "ORDER": 1,
        "SELLER": 2,
        "WAREHOUSE": 3,
        "CARRIER": 4,
        "DELIVERY": 5,
        "RETURN": 6
    }

    def predict(self, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses timestamps and verifies that earlier lifecycle events precede later events.
        Flags CONFLICT if a later lifecycle event has a timestamp strictly before an earlier event.
        """
        parsed_events = []
        for ev in evidence_list:
            source = ev.get("source", "").upper()
            ts_str = ev.get("timestamp")
            if source in self.EVENT_HIERARCHY and ts_str:
                try:
                    dt = datetime.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S")
                    parsed_events.append((self.EVENT_HIERARCHY[source], source, dt))
                except Exception:
                    continue

        if len(parsed_events) < 2:
            return {
                "baseline": "TIMELINE_ONLY",
                "prediction": "CONSISTENT",
                "reasoning": "Insufficient timestamped events to establish ordering."
            }

        # Check all pairs for inverted causality
        for i in range(len(parsed_events)):
            for j in range(i + 1, len(parsed_events)):
                rank_i, source_i, dt_i = parsed_events[i]
                rank_j, source_j, dt_j = parsed_events[j]

                # If source_i is supposed to occur before source_j, but dt_i > dt_j
                if rank_i < rank_j and dt_i > dt_j:
                    return {
                        "baseline": "TIMELINE_ONLY",
                        "prediction": "CONFLICT",
                        "reasoning": f"Temporal inversion: {source_i} ({dt_i}) occurred after {source_j} ({dt_j})."
                    }
                elif rank_i > rank_j and dt_i < dt_j:
                    return {
                        "baseline": "TIMELINE_ONLY",
                        "prediction": "CONFLICT",
                        "reasoning": f"Temporal inversion: {source_i} ({dt_i}) occurred before {source_j} ({dt_j})."
                    }

        return {
            "baseline": "TIMELINE_ONLY",
            "prediction": "CONSISTENT",
            "reasoning": "All timestamped events follow expected chronological order."
        }
