"""
PEC Water Splitting — Prediction API
=====================================
Endpoints:
  GET  /          — health check
  POST /predict   — predict STH, Photocurrent, H2 from material parameters
  GET  /dataset   — return clean dataset as JSON

Run:
    python app.py
"""

import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("pec_api")

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS

from utils.preprocessing import engineer_features, TARGETS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": os.getenv("FRONTEND_ORIGIN", "*")}})

MODEL_DIR = Path(__file__).parent / "model"
DATA_DIR  = Path(__file__).parent / "data"


# ── Load models at startup ────────────────────────────────────────────────────

def _load_model(key: str):
    path = MODEL_DIR / f"model_{key}.pkl"
    if not path.exists():
        log.warning("Model file not found: %s", path)
        return None
    artifact = joblib.load(path)
    log.info("Loaded model_%s — best=%s  CV R²=%+.3f",
             key,
             artifact["models"][artifact["best_idx"]]["name"],
             artifact["cv_r2"])
    return artifact


MODELS = {k: _load_model(k) for k in ("pc", "sth", "h2")}

_loaded  = [k for k, v in MODELS.items() if v is not None]
_missing = [k for k, v in MODELS.items() if v is None]
if _missing:
    log.warning("Models not found: %s — run python train.py first.", _missing)


# ── Input validation ──────────────────────────────────────────────────────────

_BOUNDS = {
    "pH":              (0.0,   14.0,     "pH must be 0–14"),
    "bias":            (-2.0,  5.0,      "bias must be −2 to 5 V vs RHE"),
    "bandgap":         (0.5,   6.0,      "bandgap must be 0.5–6.0 eV"),
    "temperature":     (200.0, 1500.0,   "temperature must be 200–1500 K"),
    "light_intensity": (0.0,   2000.0,   "light_intensity must be 0–2000 mW/cm²"),
    "thickness":       (0.0,   100000.0, "thickness must be 0–100000 nm"),
}

_REQUIRED = ["material", "electrolyte", "pH", "bias", "light_source"]

_UNICODE_MAP = str.maketrans({
    "₄": "4", "₂": "2", "₃": "3", "₁": "1", "₀": "0",
    "²": "2", "³": "3",
})


def _normalize_material(name: str) -> str:
    cleaned = str(name).translate(_UNICODE_MAP).split("(")[0].strip()
    return cleaned


def _validate(data: dict) -> list[str]:
    errors = []
    # Normalise keys to lowercase for case-insensitive lookup
    data_lower = {k.lower(): v for k, v in data.items()}
    for req in _REQUIRED:
        if req.lower() not in data_lower:
            errors.append(f"'{req}' is required.")
    # Range checks — match against lowercase keys too (ph == pH)
    for field, (lo, hi, msg) in _BOUNDS.items():
        val = data_lower.get(field.lower())
        if val is not None:
            try:
                v = float(val)
                if not (lo <= v <= hi):
                    errors.append(msg)
            except (ValueError, TypeError):
                errors.append(f"'{field}' must be a number")
    return errors


# ── Build inference row ───────────────────────────────────────────────────────

_FIELD_MAP = {
    "pH":                  "ph",
    "ph":                  "ph",
    "bias":                "bias",
    "light_source":        "illumination_type",
    "material":            "material",
    "electrolyte":         "electrolyte",
    "bandgap":             "bandgap",
    "temperature":         "temperature_k",
    "light_intensity":     "light_intensity",
    "thickness":           "thickness",
    "cocatalyst":          "cocatalyst",
    "synthesis_method":    "synthesis_method",
    "photoelectrode_type": "photoelectrode_type",
    "nanostructure":       "nanostructure",
    "morphology":          "morphology",
    "protective_layer":    "protective_layer",
}


def _build_row(data: dict, artifact: dict) -> pd.DataFrame:
    medians  = artifact["dataset_medians"]
    modes    = artifact["dataset_modes"]
    num_cols = artifact["feature_cols"]["numeric"]
    cat_cols = artifact["feature_cols"]["cat"]

    row = {}
    for api_key, internal in _FIELD_MAP.items():
        val = data.get(api_key)
        if val is not None and str(val).strip() != "":
            row[internal] = _normalize_material(str(val)) if internal == "material" else val

    df = pd.DataFrame([row])

    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = engineer_features(df)

    for col in num_cols:
        if col not in df.columns or pd.isna(df[col].iloc[0]):
            df[col] = medians.get(col, 0.0)

    for col in cat_cols:
        if col not in df.columns or pd.isna(df[col].iloc[0]) or df[col].iloc[0] == "":
            df[col] = modes.get(col, "Unknown")

    return df[num_cols + cat_cols]


# ── Ensemble prediction with uncertainty ─────────────────────────────────────

def _predict_ensemble(key: str, row_df: pd.DataFrame) -> dict | None:
    """
    Run all saved models for this target and return:
      - value: weighted-average prediction (weight = CV R², floored at 0)
      - predictions: list of individual predictions
      - std: std-dev across models (spread = disagreement = lower confidence)
      - confidence: 0–1 score derived from model agreement and model quality
    """
    artifact = MODELS.get(key)
    if artifact is None:
        return None

    transform   = artifact["transform"]
    thresholds  = artifact["thresholds"]
    preds_orig  = []
    weights     = []

    for m in artifact["models"]:
        raw = float(m["pipeline"].predict(row_df)[0])
        if transform == "log1p":
            raw = float(np.expm1(raw))
        raw = max(0.0, raw)
        preds_orig.append(raw)
        # Weight = max(0, CV R²) so a negative-R² model contributes near zero
        weights.append(max(0.0, m["cv_r2"]))

    weights = np.array(weights)
    preds   = np.array(preds_orig)

    total_weight = weights.sum()
    if total_weight > 0:
        value = float(np.dot(weights, preds) / total_weight)
    else:
        value = float(preds.mean())

    # Relative std: how much do models disagree relative to the prediction
    if value > 1e-6:
        rel_std = float(preds.std() / value)
    else:
        rel_std = float(preds.std())

    # Confidence: high agreement + high CV R² → high confidence
    mean_r2    = float(weights.mean()) if total_weight > 0 else 0.0
    r2_score_n = max(0.0, min(1.0, mean_r2))          # normalised R² ∈ [0,1]
    agreement  = max(0.0, 1.0 - min(rel_std, 1.0))    # 0 when models diverge >100%
    confidence = round(0.6 * r2_score_n + 0.4 * agreement, 3)

    return {
        "value":       round(value, 4),
        "predictions": [round(p, 4) for p in preds_orig],
        "std":         round(float(preds.std()), 4),
        "confidence":  confidence,
        "thresholds":  thresholds,
    }


# ── Performance classification ────────────────────────────────────────────────

def _classify_performance(pc_result: dict | None,
                           sth_result: dict | None) -> dict:
    """
    Data-driven classification using per-target percentile thresholds
    stored in the artifact (p75 = HIGH boundary, p40 = MEDIUM boundary).

    Returns perf_class (HIGH/MEDIUM/LOW) and a composite score 0–100.
    """
    if pc_result is None:
        return {"class": "UNKNOWN", "score": None}

    pc_val  = pc_result["value"]
    pc_thr  = pc_result["thresholds"]
    conf    = pc_result["confidence"]

    # Points from photocurrent position relative to training distribution
    if pc_val >= pc_thr["high"]:
        pc_points = 100
    elif pc_val >= pc_thr["medium"]:
        # Interpolate linearly between medium and high threshold
        span = pc_thr["high"] - pc_thr["medium"]
        pc_points = 50 + 50 * (pc_val - pc_thr["medium"]) / max(span, 1e-9)
    else:
        span = pc_thr["medium"]
        pc_points = 50 * (pc_val / max(span, 1e-9))

    pc_points = float(np.clip(pc_points, 0, 100))

    # Bonus from STH (if available)
    sth_bonus = 0.0
    if sth_result is not None:
        sth_val = sth_result["value"]
        sth_thr = sth_result["thresholds"]
        if sth_val >= sth_thr["high"]:
            sth_bonus = 15.0
        elif sth_val >= sth_thr["medium"]:
            sth_bonus = 7.0

    # Confidence penalty: low-confidence predictions are downgraded
    # A model with R² < 0 gets max 40 points regardless of predicted value
    conf_factor = 0.4 + 0.6 * conf   # range [0.4, 1.0]
    composite   = float(np.clip((pc_points + sth_bonus) * conf_factor, 0, 100))

    if composite >= 70:
        perf_class = "HIGH"
    elif composite >= 40:
        perf_class = "MEDIUM"
    else:
        perf_class = "LOW"

    return {"class": perf_class, "score": round(composite, 1)}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health():
    model_info = {}
    for k, artifact in MODELS.items():
        if artifact:
            model_info[k] = {
                "best_model": artifact["models"][artifact["best_idx"]]["name"],
                "cv_r2": round(artifact["cv_r2"], 3),
            }
    return jsonify({
        "status":         "ok",
        "models_loaded":  _loaded,
        "models_missing": _missing,
        "model_info":     model_info,
    })


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True) or {}
    log.info("POST /predict — keys: %s", list(data.keys()))

    errors = _validate(data)
    if errors:
        log.warning("Validation failed: %s", errors)
        return jsonify({"status": "error", "message": "Validation failed",
                        "details": errors}), 400

    try:
        results = {}
        for key, label in [("pc", "Photocurrent"), ("sth", "STH"), ("h2", "H2")]:
            artifact = MODELS.get(key)
            if artifact is None:
                results[label] = None
                continue
            row_df = _build_row(data, artifact)
            results[label] = _predict_ensemble(key, row_df)

        perf = _classify_performance(results.get("Photocurrent"), results.get("STH"))

        def _fmt(r):
            if r is None:
                return None
            return {
                "value":      r["value"],
                "confidence": r["confidence"],
                "std":        r["std"],
            }

        log.info("Prediction done — PC=%.3f  STH=%s  perf=%s  score=%.1f",
                 results["Photocurrent"]["value"] if results.get("Photocurrent") else -1,
                 results["STH"]["value"] if results.get("STH") else "n/a",
                 perf["class"], perf["score"] or 0)

        return jsonify({
            "status":            "ok",
            "Photocurrent":      _fmt(results.get("Photocurrent")),
            "STH":               _fmt(results.get("STH")),
            "H2":                _fmt(results.get("H2")),
            "performance_class": perf["class"],
            "performance_score": perf["score"],
            "units": {
                "Photocurrent": "mA/cm²",
                "STH":          "%",
                "H2":           "µmol/h/cm²",
            },
        })

    except Exception:
        log.exception("Unhandled error in /predict")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route("/dataset", methods=["GET"])
def dataset():
    try:
        # Always serve the original expanded CSV — it has user-friendly column names
        # (pec_dataset_clean.csv uses internal names like 'sth', 'h2' and is for ML only)
        path = DATA_DIR / "pec_dataset.csv"
        if not path.exists():
            return jsonify({"status": "error", "message": "Dataset file not found"}), 404
        df = pd.read_csv(path)
        # Limit to columns useful for display; drop heavy/internal columns
        drop = ["№", "doi", "source_url", "source_verified", "Units Normalized"]
        df = df.drop(columns=[c for c in drop if c in df.columns])
        return jsonify(df.where(df.notna(), other=None).to_dict(orient="records"))
    except Exception:
        log.exception("Error in /dataset")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    log.info("Starting PEC API on http://localhost:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
