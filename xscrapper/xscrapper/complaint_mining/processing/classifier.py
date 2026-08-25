import re
import logging
from typing import Dict, Any, Tuple, List
from complaint_mining.config import TARGET_BRANDS, COMPLAINT_TYPES, TRINETRA_MODULES, PRODUCT_CATEGORIES

logger = logging.getLogger("complaint_logger")


class ComplaintClassifier:
    """Classifies complaints into structured research dimensions."""

    # ── Quality Checks ────────────────────────────────────────────────────────
    @staticmethod
    def inspect_quality(text: str, title: str) -> Tuple[bool, str]:
        """
        Quality gate: Keep only genuine customer complaint experiences.
        Reject ads, promo posts, news articles, spam, memes, software docs, tax returns,
        movies, dictionaries, stock quotes, car sales, and travel reviews.
        Requires e-commerce context AND complaint indicator within proximity.
        """
        if len(text.strip()) < 25:
            return False, "Too short / non-descriptive"

        combined = f"{title} {text}".lower()

        # Explicit non-retail & software/tax/media exclusion patterns
        exclusion_patterns = [
            r"\b(?:income tax|tax return|incometax|nsdl|cpc-bangalore|tax refund|taxpayer|e-filing|tax information network)\b",
            r"\b(?:github|copilot|vs code|visual studio|code extension|prompts|chat mode|python3|repo|npm|api docs|codex)\b",
            r"\b(?:job|hiring|become a partner|delivery service partner|franchise|business opportunity|rejoignez la communaute|devenez proprietaire)\b",
            r"\b(?:buy now|shop now|discount|coupon code|promocode|limited offer|affiliate|subscribe to|click link|special deal|flash sale|best price|giveaway|contest|promo)\b",
            r"\b(?:sponsored|ad|advertisement|paid partnership|pr post)\b",
            r"\b(?:news|press release|article|report by|reporter|journalism)\b",
            r"\b(?:meme|lol|funny|joke|roast|satire)\b",
            r"\b(?:film|movie|box office|trailer|directed by|starring|fbi|kidnappings|missing persons)\b",
            r"\b(?:definition & meaning|meaning in english|dictionary|pronunciation|synonyms|antonyms|prezzo dei titoli|stock price|share price)\b",
            r"\b(?:viking cruises|cruise reviews|cruise line|used cars in|used car price|buy used car)\b",
        ]

        for pattern in exclusion_patterns:
            if re.search(pattern, combined):
                return False, f"Filtered out by exclusion pattern: {pattern}"

        # Context & Indicator keywords for proximity check
        ecommerce_context = [
            "amazon", "flipkart", "meesho", "myntra", "ajio", "nykaa", "jiomart", "snapdeal", "shopify", "d2c",
            "order", "product", "item", "seller", "package", "parcel", "delivery", "courier", "store", "purchase",
            "bought", "customer", "retail", "shopping", "ecommerce", "e-commerce", "marketplace", "buyer", "brand"
        ]

        complaint_indicators = [
            "return", "refund", "damaged", "wrong", "fake", "counterfeit", "used", "delay", "delayed",
            "rejected", "failed", "scam", "fraud", "stolen", "empty box", "missing", "broken",
            "terrible", "worst", "cheated", "customer support", "customer care", "pickup", "policy",
            "dispute", "abuse", "chargeback", "complaint", "lost", "overcharged"
        ]

        # Check proximity: E-commerce term AND complaint indicator must occur in same sentence or within 200 chars
        sentences = re.split(r"[.!?\n]+", combined)
        proximity_matched = False

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue
            has_ecom = any(re.search(r"\b" + re.escape(k) + r"\b", sentence_clean) for k in ecommerce_context)
            has_comp = any(re.search(r"\b" + re.escape(k) + r"\b", sentence_clean) for k in complaint_indicators)
            if has_ecom and has_comp:
                proximity_matched = True
                break

        if not proximity_matched:
            # Check sliding window of 200 characters across combined string
            window_size = 200
            for i in range(0, max(1, len(combined) - window_size + 1), 50):
                window = combined[i: i + window_size]
                has_ecom = any(re.search(r"\b" + re.escape(k) + r"\b", window) for k in ecommerce_context)
                has_comp = any(re.search(r"\b" + re.escape(k) + r"\b", window) for k in complaint_indicators)
                if has_ecom and has_comp:
                    proximity_matched = True
                    break

        if not proximity_matched:
            return False, "Lacks proximity between e-commerce context and complaint indicator (must match within sentence or 200 chars)"

        return True, "Valid complaint"

    # ── Product Category Identification ───────────────────────────────────────
    @staticmethod
    def classify_product_category(text: str, title: str) -> str:
        """Classify post into e-commerce product categories (Apparel, Footwear, Electronics, etc.)."""
        combined = f"{title} {text}".lower()

        category_rules = [
            ("Apparel/Clothing", [
                "shirt", "dress", "kurta", "jeans", "t-shirt", "tshirt", "top", "saree", "sari",
                "fit", "fabric", "garment", "clothing", "wardrobe", "tailoring", "stitching",
                "clothes", "innerwear", "jacket", "trousers", "pants", "skirt", "lehenga", "suit"
            ]),
            ("Footwear", [
                "shoes", "shoe", "sneakers", "sandals", "heels", "footwear", "boots", "slippers"
            ]),
            ("Accessories", [
                "watch", "bag", "handbag", "wallet", "jewelry", "jewellery", "belt", "sunglasses", "backpack", "luggage"
            ]),
            ("Electronics", [
                "phone", "smartphone", "laptop", "tv", "television", "earphone", "headphone", "charger",
                "appliance", "mobile", "camera", "monitor", "gadget", "macbook", "iphone", "android"
            ]),
            ("Beauty/Personal Care", [
                "lipstick", "makeup", "cream", "shampoo", "lotion", "cosmetics", "skincare", "perfume", "face wash"
            ]),
            ("Home/Kitchen", [
                "furniture", "cooktop", "bed", "curtain", "utensil", "mattress", "bottle", "kitchen", "chair", "table"
            ]),
        ]

        for cat, keywords in category_rules:
            if any(re.search(r"\b" + re.escape(k) + r"\b", combined) for k in keywords):
                return cat

        # Special check for size keywords in apparel context (S/M/L/XL/XXL/size)
        if re.search(r"\b(?:size|small|medium|large|xl|xxl|xs)\b", combined) and any(w in combined for w in ["received", "wrong", "fit", "wear", "return", "item", "product"]):
            return "Apparel/Clothing"

        return "Other/Unspecified"

    # ── Company Identification ────────────────────────────────────────────────
    @staticmethod
    def identify_company(text: str, title: str, url: str) -> str:
        """Extract primary target e-commerce brand from text/URL."""
        combined = f"{url} {title} {text}".lower()

        brand_keywords = {
            "Amazon": ["amazon", "amazonin", "amzn"],
            "Flipkart": ["flipkart", "fk"],
            "Myntra": ["myntra"],
            "Meesho": ["meesho"],
            "Ajio": ["ajio"],
            "Nykaa": ["nykaa"],
            "JioMart": ["jiomart", "jio mart"],
            "Snapdeal": ["snapdeal"],
            "Shopify": ["shopify"],
            "D2C Brand": ["d2c", "brand store", "direct to consumer"],
        }

        for brand, keywords in brand_keywords.items():
            if any(k in combined for k in keywords):
                return brand

        return "Other E-Commerce"

    # ── Complaint Type Classification ──────────────────────────────────────────
    @staticmethod
    def classify_type(text: str, title: str) -> str:
        """Classify into one of 20 exact complaint types."""
        combined = f"{title} {text}".lower()

        rules = [
            ("Counterfeit Product", ["fake", "counterfeit", "replica", "duplicate product", "forged", "first copy"]),
            ("Used Product", ["used product", "refurbished", "second hand", "opened seal", "already used", "pre-owned", "tampered box"]),
            ("Wrong Product", ["wrong product", "different item", "wrong item", "received different", "sent wrong", "product mismatch"]),
            ("Damaged Product", ["damaged", "broken", "cracked", "defective", "smashed", "shattered", "destroyed"]),
            ("Empty Box Delivery", ["empty box", "box was empty", "nothing inside", "soap inside", "brick inside", "missing product"]),
            ("Missing Items", ["missing item", "missing accessory", "part missing", "incomplete delivery"]),
            ("Refund Delay", ["refund delay", "refund delayed", "refund pending", "money not received", "refund not processed", "waiting for refund", "where is my refund"]),
            ("Return Rejected", ["return rejected", "return denied", "return refused", "cannot return", "return request declined"]),
            ("Replacement Rejected", ["replacement rejected", "replacement denied", "replacement refused"]),
            ("Pickup Failure", ["pickup failed", "pickup delayed", "agent did not arrive", "pickup cancelled", "nobody came for pickup"]),
            ("Delivery Failure", ["delivery failed", "not delivered", "fake delivery", "marked delivered but not received", "delivery agent"]),
            ("Lost Package", ["lost package", "package lost", "transit lost", "parcel lost"]),
            ("COD Scam", ["cod scam", "cod fraud", "cash on delivery scam", "open box delivery fraud"]),
            ("Seller Fraud", ["seller fraud", "fake seller", "fraudulent seller", "scammer seller"]),
            ("Packaging Issue", ["packaging", "bad packing", "torn box", "open package"]),
            ("Customer Support", ["customer support", "customer care", "poor service", "no response", "call back", "chat support", "bot response"]),
            ("Policy Issue", ["return policy", "policy changed", "return window", "no return policy", "non returnable"]),
            ("Warehouse Issue", ["warehouse", "fulfillment center", "sorting center"]),
            ("Price Mismatch", ["price mismatch", "overcharged", "wrong price"]),
        ]

        for complaint_type, keywords in rules:
            if any(k in combined for k in keywords):
                return complaint_type

        return "Other"

    # ── Severity Classification ───────────────────────────────────────────────
    @staticmethod
    def classify_severity(text: str, complaint_type: str) -> str:
        """Assign Low, Medium, High, or Critical severity."""
        combined = text.lower()

        # Critical indicators
        if complaint_type in ["Counterfeit Product", "COD Scam", "Seller Fraud", "Empty Box Delivery"] or \
           any(k in combined for k in ["police", "cyber cell", "court", "consumer court", "legal action", "sue", "fir", "thousands", "lakh", "scam"]):
            return "Critical"

        # High indicators
        if complaint_type in ["Used Product", "Wrong Product", "Damaged Product", "Return Rejected", "Lost Package"] or \
           any(k in combined for k in ["cheated", "fraud", "terrible", "harassment", "stolen", "no refund"]):
            return "High"

        # Medium indicators
        if complaint_type in ["Refund Delay", "Pickup Failure", "Delivery Failure", "Customer Support"]:
            return "Medium"

        return "Low"

    # ── Stakeholder Identification ────────────────────────────────────────────
    @staticmethod
    def identify_stakeholder(text: str, complaint_type: str) -> str:
        """Identify primary affected stakeholder."""
        combined = text.lower()

        if any(k in combined for k in ["seller account", "buyer fraud", "wardrobing", "customer cheated seller"]):
            return "Seller"

        if complaint_type in ["Pickup Failure", "Delivery Failure", "Lost Package"] or "courier" in combined or "delivery guy" in combined:
            return "Delivery Partner"

        if complaint_type == "Warehouse Issue" or "warehouse" in combined:
            return "Warehouse"

        if complaint_type in ["Seller Fraud", "COD Scam", "Counterfeit Product"]:
            return "Multiple"

        return "Customer"

    # ── TriNetra Module Mapping ───────────────────────────────────────────────
    @staticmethod
    def map_trinetra_modules(complaint_type: str, text: str) -> str:
        """Map complaint to one or more TriNetra AI core modules."""
        combined = text.lower()
        modules = []

        if complaint_type in ["Wrong Product", "Damaged Product", "Used Product", "Counterfeit Product", "Empty Box Delivery", "Missing Items"]:
            modules.append("Evidence Collection")
            modules.append("Evidence Consistency")

        if complaint_type in ["Return Rejected", "Replacement Rejected", "Policy Issue"]:
            modules.append("Adaptive Verification")
            modules.append("Explainability")

        if complaint_type in ["Seller Fraud", "Fake Seller", "COD Scam"]:
            modules.append("Trust Score")

        if complaint_type in ["Refund Delay", "Pickup Failure", "Delivery Failure", "Lost Package"]:
            modules.append("Case Timeline")

        if complaint_type in ["Customer Support", "Other"]:
            modules.append("Human Review")

        modules.append("Marketplace Dashboard")

        seen = set()
        unique_modules = [m for m in modules if not (m in seen or seen.add(m))]
        return "; ".join(unique_modules)

    # ── Complete Classification Workflow ──────────────────────────────────────
    def classify_complaint(self, complaint: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full multi-dimensional classification on a single complaint dict."""
        text = complaint.get("Complaint_Text", "")
        title = complaint.get("Complaint_Title", "")
        url = complaint.get("Complaint_URL", "")

        company = self.identify_company(text, title, url)
        product_category = self.classify_product_category(text, title)
        complaint_type = self.classify_type(text, title)
        severity = self.classify_severity(text, complaint_type)
        stakeholder = self.identify_stakeholder(text, complaint_type)
        trinetra_modules = self.map_trinetra_modules(complaint_type, text)

        complaint["Company"] = company
        complaint["Product_Category"] = product_category
        complaint["Complaint_Type"] = complaint_type
        complaint["Severity"] = severity
        complaint["Stakeholder"] = stakeholder
        complaint["TriNetra_Module"] = trinetra_modules

        return complaint

