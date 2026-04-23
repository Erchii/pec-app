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

import sys
import os
from pathlib import Path

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
        return None
    return joblib.load(path)


MODELS = {k: _load_model(k) for k in ("pc", "sth", "h2")}

_loaded = [k for k, v in MODELS.items() if v is not None]
_missing = [k for k, v in MODELS.items() if v is None]
if _missing:
    print(f"[WARN] Models not found: {_missing}. Run python train.py first.")
print(f"[INFO] Loaded models: {_loaded}")


# ── Input validation ──────────────────────────────────────────────────────────

_BOUNDS = {
    "pH":          (0.0, 14.0,  "pH must be 0–14"),
    "bias":        (-2.0, 5.0,  "bias must be −2 to 5 V vs RHE"),
    "bandgap":     (0.5, 6.0,   "bandgap must be 0.5–6.0 eV"),
    "temperature": (200.0, 1500.0, "temperature must be 200–1500 K"),
    "light_intensity": (0.0, 2000.0, "light_intensity must be 0–2000 mW/cm²"),
    "thickness":   (0.0, 100000.0, "thickness must be 0–100000 nm"),
}

def _safe_float(value, default):
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


_REQUIRED = ["material", "electrolyte", "pH", "bias", "light_source"]

# Unicode subscript/superscript → clean ASCII for material names
_UNICODE_MAP = str.maketrans({
    "₄": "4", "₂": "2", "₃": "3", "₁": "1", "₀": "0",
    "²": "2", "³": "3",
})

def _normalize_material(name: str) -> str:
    """'BiVO₄ (Bismuth Vanadate)' → 'BiVO4'"""
    cleaned = str(name).translate(_UNICODE_MAP)
    # Keep only the first token (before space or parenthesis)
    cleaned = cleaned.split("(")[0].strip()
    return cleaned


def _validate(data: dict) -> list[str]:
    errors = []
    # Required field check
    for req in _REQUIRED:
        alt = "pH" if req == "pH" else req   # handle case variants
        if not any(k.lower() == req.lower() for k in data):
            errors.append(f"'{req}' is required.")
    # Range checks
    for field, (lo, hi, msg) in _BOUNDS.items():
        if field in data and data[field] is not None:
            try:
                v = float(data[field])
                if not (lo <= v <= hi):
                    errors.append(msg)
            except (ValueError, TypeError):
                errors.append(f"'{field}' must be a number")
    return errors


# ── Build inference row ───────────────────────────────────────────────────────

def _build_row(data: dict, artifact: dict) -> pd.DataFrame:
    """
    Construct a single-row DataFrame matching the training feature schema.
    Missing fields are filled with per-column training medians / modes.
    """
    medians = artifact["dataset_medians"]
    modes   = artifact["dataset_modes"]
    num_cols = artifact["feature_cols"]["numeric"]
    cat_cols = artifact["feature_cols"]["cat"]

    # Map API field names → internal names
    field_map = {
        "pH":            "ph",
        "ph":            "ph",
        "bias":          "bias",
        "light_source":  "illumination_type",
        "material":      "material",
        "electrolyte":   "electrolyte",
        "bandgap":       "bandgap",
        "temperature":   "temperature_k",
        "light_intensity": "light_intensity",
        "thickness":     "thickness",
        "cocatalyst":    "cocatalyst",
        "synthesis_method": "synthesis_method",
        "photoelectrode_type": "photoelectrode_type",
        "nanostructure": "nanostructure",
        "morphology":    "morphology",
        "protective_layer": "protective_layer",
    }

    row = {}
    for api_key, internal in field_map.items():
        if api_key in data and data[api_key] is not None and str(data[api_key]).strip() != "":
            val = data[api_key]
            # Normalize material names: "BiVO₄ (Bismuth Vanadate)" → "BiVO4"
            if internal == "material":
                val = _normalize_material(str(val))
            row[internal] = val

    df = pd.DataFrame([row])

    # Convert numeric fields from string → float
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Engineer derived features (photon_energy, overpotential_proxy, etc.)
    df = engineer_features(df)

    # Fill missing numeric with training medians
    for col in num_cols:
        if col not in df.columns or pd.isna(df[col].iloc[0]):
            df[col] = medians.get(col, 0.0)

    # Fill missing categorical with training modes
    for col in cat_cols:
        if col not in df.columns or pd.isna(df[col].iloc[0]) or df[col].iloc[0] == "":
            df[col] = modes.get(col, "Unknown")

    return df[num_cols + cat_cols]


# ── Prediction helper ─────────────────────────────────────────────────────────

def _predict_one(key: str, row_df: pd.DataFrame) -> float | None:
    artifact = MODELS.get(key)
    if artifact is None:
        return None
    pipeline  = artifact["pipeline"]
    transform = artifact["transform"]
    val = pipeline.predict(row_df)[0]
    if transform == "log1p":
        val = float(np.expm1(val))
    return round(float(np.clip(val, 0.0, None)), 4)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status":         "ok",
        "models_loaded":  _loaded,
        "models_missing": _missing,
    })


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True) or {}

        errors = _validate(data)
        if errors:
            return jsonify({"status": "error", "message": "Validation failed",
                            "details": errors}), 400

        results = {}
        for key, out_name in [("pc", "Photocurrent"), ("sth", "STH"), ("h2", "H2")]:
            artifact = MODELS.get(key)
            if artifact is None:
                results[out_name] = None
                continue
            row_df = _build_row(data, artifact)
            results[out_name] = _predict_one(key, row_df)

        # Classify performance
        pc = results.get("Photocurrent") or 0.0
        if pc >= 8:
            perf_class = "HIGH"
        elif pc >= 3:
            perf_class = "MEDIUM"
        else:
            perf_class = "LOW"

        return jsonify({
            "status":            "ok",
            "STH":               results.get("STH"),
            "Photocurrent":      results.get("Photocurrent"),
            "H2":                results.get("H2"),
            "performance_class": perf_class,
            "units": {
                "STH":          "%",
                "Photocurrent": "mA/cm²",
                "H2":           "µmol/h/cm²",
            },
        })

    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/dataset", methods=["GET"])
def dataset():
    try:
        clean = DATA_DIR / "pec_dataset_clean.csv"
        raw   = DATA_DIR / "pec_dataset.csv"
        path  = clean if clean.exists() else raw
        df = pd.read_csv(path)
        # Replace NaN with None so JSON serialises cleanly
        return jsonify(df.where(df.notna(), other=None).to_dict(orient="records"))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    print(f"[PEC API] Starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
