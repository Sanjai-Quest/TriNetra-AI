"""
Canonical Normalization Engine for TriNetra AI Phase 1.
Normalizes raw textual/heterogeneous attributes into standardized canonical representations.
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union


class CanonicalNormalizer:
    """Unified Normalizer executing attribute-specific canonical transformations."""

    @staticmethod
    def normalize_sku(raw_sku: Optional[str]) -> Optional[str]:
        """
        Normalizes SKU strings.
        Examples: 'TS-204', 'TS204', 'ts204', 'ts-204', 'TS 204' -> 'TS-204'
        """
        if raw_sku is None:
            return None
        cleaned = str(raw_sku).strip().upper()
        # Remove spaces, underscores, dots
        cleaned = re.sub(r'[\s_.]+', '', cleaned)
        # Standardize hyphen between letter block and number block if missing
        match = re.match(r'^([A-Z]+)-?(\d+)$', cleaned)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return cleaned

    @staticmethod
    def normalize_weight(raw_weight: Union[str, int, float, None]) -> Optional[int]:
        """
        Normalizes weight into integer grams.
        Examples: '500g', '0.5kg', '500 grams', '0.5 kilograms', 500 -> 500
        """
        if raw_weight is None:
            return None
        if isinstance(raw_weight, (int, float)):
            return int(round(raw_weight))

        text = str(raw_weight).strip().lower()
        # Check kilograms
        kg_match = re.search(r'([\d.]+)\s*(kg|kilogram|kilograms|kilo)', text)
        if kg_match:
            val = float(kg_match.group(1))
            return int(round(val * 1000))

        # Check grams
        g_match = re.search(r'([\d.]+)\s*(g|gram|grams|gm)', text)
        if g_match:
            val = float(g_match.group(1))
            return int(round(val))

        # Check plain number
        num_match = re.search(r'^[\d.]+$', text)
        if num_match:
            return int(round(float(text)))

        return None

    @staticmethod
    def normalize_size(raw_size: Optional[str]) -> Optional[str]:
        """
        Normalizes apparel sizing variations to canonical codes.
        Examples: 'Extra Large', 'XL', 'x-large', 'extra-large' -> 'XL'
        """
        if raw_size is None:
            return None
        text = str(raw_size).strip().upper()
        mapping = {
            'EXTRA SMALL': 'XS',
            'X-SMALL': 'XS',
            'XS': 'XS',
            'SMALL': 'S',
            'S': 'S',
            'MEDIUM': 'M',
            'M': 'M',
            'LARGE': 'L',
            'L': 'L',
            'EXTRA LARGE': 'XL',
            'EXTRA-LARGE': 'XL',
            'X-LARGE': 'XL',
            'XL': 'XL',
            'DOUBLE EXTRA LARGE': 'XXL',
            '2XL': 'XXL',
            'XXL': 'XXL',
            'FREE SIZE': 'FREE',
            'ONESIZE': 'FREE',
            'ONE SIZE': 'FREE'
        }
        return mapping.get(text, text)

    @staticmethod
    def normalize_color(raw_color: Optional[str]) -> Optional[str]:
        """
        Normalizes color names by stripping modifiers.
        Examples: 'dark red', 'bright red', 'red', 'RED' -> 'RED'
        """
        if raw_color is None:
            return None
        text = str(raw_color).strip().upper()
        # Remove common prefixes / modifiers
        text = re.sub(r'^(DARK|LIGHT|BRIGHT|DEEP|NAVY|METALLIC|NEON|PALE)\s+', '', text)
        return text

    @staticmethod
    def normalize_timestamp(raw_timestamp: Union[str, datetime, None]) -> Optional[str]:
        """
        Normalizes timestamp variations into ISO 8601 UTC format string: YYYY-MM-DDTHH:MM:SSZ
        """
        if raw_timestamp is None:
            return None
        if isinstance(raw_timestamp, datetime):
            return raw_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

        text = str(raw_timestamp).strip()
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %I:%M %p",
            "%m/%d/%Y %H:%M:%S",
            "%d-%b-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(text, fmt)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
        return text

    def normalize_evidence_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes all fields inside an evidence dictionary."""
        normalized = dict(record)
        if 'sku' in normalized:
            normalized['sku'] = self.normalize_sku(normalized['sku'])
        if 'weight' in normalized:
            normalized['weight'] = self.normalize_weight(normalized['weight'])
        if 'size' in normalized:
            normalized['size'] = self.normalize_size(normalized['size'])
        if 'color' in normalized:
            normalized['color'] = self.normalize_color(normalized['color'])
        if 'timestamp' in normalized:
            normalized['timestamp'] = self.normalize_timestamp(normalized['timestamp'])
        return normalized
