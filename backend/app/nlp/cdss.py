"""
CDSS ML Model Loader & Evaluator
Loads cdss_model.joblib once at startup, exposes predict_risk().
"""
import os
import joblib

_model = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'cdss_model.joblib')


def initialize_cdss_model() -> None:
    global _model
    resolved = os.path.abspath(MODEL_PATH)
    _model = joblib.load(resolved)
    print(f"CDSS ML model loaded from {resolved}")


def get_cdss_model():
    return _model


def predict_risk(proposed_salt: str, active_items: list[str]) -> dict:
    """
    Evaluate proposed drug against all active meds/conditions/allergies.

    Returns:
        {
            "status": "SAFE" | "DANGER",
            "risk_probability": float (0.0-1.0, max across all items),
            "conflicting_item": str | None,
            "details": list of { "item": str, "probability": float }
        }
    """
    if not _model or not active_items:
        return {
            "status": "SAFE",
            "risk_probability": 0.0,
            "conflicting_item": None,
            "details": [],
        }

    max_prob = 0.0
    worst_item = None
    details = []

    for item in active_items:
        if not item:
            continue
        feature_text = f"{proposed_salt} | {item}"
        proba = _model.predict_proba([feature_text])[0]
        # Index 1 = DANGER class probability
        danger_prob = float(proba[1]) if len(proba) > 1 else 0.0
        details.append({"item": item, "probability": round(danger_prob, 4)})

        if danger_prob > max_prob:
            max_prob = danger_prob
            worst_item = item

    return {
        "status": "DANGER" if max_prob >= 0.40 else "SAFE",
        "risk_probability": round(max_prob, 4),
        "conflicting_item": worst_item if max_prob >= 0.40 else None,
        "details": details,
    }
