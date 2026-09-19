"""
Rule-based issue classifier for the CivicMysuru MVP.

This is intentionally lightweight and explainable. It does NOT claim to be
a trained computer-vision model. A real CNN/YOLO/etc. model can later replace
classify_issue() without changing the API contract.
"""


ISSUE_KEYWORDS = {
    "Pothole / Road Damage": [
        "pothole", "road", "crack", "broken road", "road damage", "asphalt"
    ],
    "Garbage / Waste": [
        "garbage", "waste", "trash", "dump", "litter", "rubbish"
    ],
    "Streetlight": [
        "streetlight", "street light", "lamp", "light pole", "dark road"
    ],
    "Drainage / Sewage": [
        "drain", "drainage", "sewage", "manhole", "overflow", "waterlogging"
    ],
    "Water Supply": [
        "water", "pipeline", "pipe leak", "water leak", "water supply"
    ],
    "Public Safety": [
        "danger", "hazard", "fallen pole", "exposed wire", "unsafe", "accident"
    ],
}


def normalize(value: str) -> str:
    return " ".join((value or "").lower().strip().split())


def classify_issue(filename: str = "", description: str = ""):
    text = normalize(f"{filename} {description}")

    scores = {}

    for issue, keywords in ISSUE_KEYWORDS.items():
        score = 0
        matched = []

        for keyword in keywords:
            if keyword in text:
                score += 1
                matched.append(keyword)

        scores[issue] = {
            "score": score,
            "matched_keywords": matched,
        }

    best_issue = max(scores, key=lambda x: scores[x]["score"])
    best_score = scores[best_issue]["score"]

    if best_score == 0:
        return {
            "issue_type": "Other",
            "confidence": 0.35,
            "matched_keywords": [],
            "model": "rule-based-demo-classifier",
            "note": "Demo classifier. Replace with a trained vision model for production.",
        }

    # Demo confidence, deliberately capped because this is not a trained model.
    confidence = min(0.55 + (best_score * 0.10), 0.90)

    return {
        "issue_type": best_issue,
        "confidence": round(confidence, 2),
        "matched_keywords": scores[best_issue]["matched_keywords"],
        "model": "rule-based-demo-classifier",
        "note": "Demo classifier. Replace with a trained vision model for production.",
    }

