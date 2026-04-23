"""
Train separate ML models for each PEC target:
  model_pc.pkl  — Photocurrent Density (mA/cm²)
  model_sth.pkl — STH Efficiency (%)
  model_h2.pkl  — Hydrogen Evolution Rate (µmol/h/cm²)

Each saved artifact is a dict:
  {
    "pipeline":     sklearn Pipeline (preprocessor + model),
    "feature_cols": {"numeric": [...], "cat": [...]},
    "target":       "photocurrent" | "sth" | "h2",
    "transform":    None | "log1p",          # target transform applied
    "cv_r2":        float,
    "cv_mae":       float,
    "dataset_medians": {col: median, ...},   # used for default filling at inference
  }

Run:
    python train.py
    python train.py --data data/pec_dataset.csv --cv 3
"""

import argparse
import warnings
import json
import sys
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from utils.preprocessing import (
    load_and_map, clean_data, engineer_features, add_source_columns,
    get_feature_columns, build_preprocessor, TARGETS, TARGET_EXCLUSIONS,
)

RANDOM_STATE = 42
MODEL_DIR = Path(__file__).parent / "model"
MODEL_DIR.mkdir(exist_ok=True)


# ── Model zoo ────────────────────────────────────────────────────────────────

def _make_models() -> dict:
    return {
        "XGBoost": XGBRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=4,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0, min_child_weight=3,
            random_state=RANDOM_STATE, verbosity=0,
        ),
        "RandomForest": RandomForestRegressor(
            n_estimators=300, max_depth=8, min_samples_leaf=2,
            max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1,
        ),
    }


# ── CV evaluation ─────────────────────────────────────────────────────────────

def _cv_score(pipeline, X: pd.DataFrame, y: np.ndarray, cv: int) -> dict:
    kf = KFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    r2s, maes = [], []
    for tr, val in kf.split(X):
        p = clone(pipeline)
        p.fit(X.iloc[tr], y[tr])
        pred = p.predict(X.iloc[val])
        r2s.append(r2_score(y[val], pred))
        maes.append(mean_absolute_error(y[val], pred))
    return {"r2_mean": float(np.mean(r2s)), "r2_std": float(np.std(r2s)),
            "mae_mean": float(np.mean(maes))}


# ── Per-target training ───────────────────────────────────────────────────────

def train_target(df_eng: pd.DataFrame,
                 target_key: str,
                 cv_folds: int) -> dict | None:
    """
    Train all models for one target, pick best by CV R², save artifact.
    """
    target_col = TARGETS[target_key]
    exclusions = TARGET_EXCLUSIONS[target_key]

    # ── subset: rows with valid target ───────────────────────────────────────
    sub = df_eng[df_eng[target_col].notna()].copy()

    # For photocurrent: exclude photocathode rows (produce negative Jph values
    # that represent a physically different measurement convention)
    if target_key == "pc" and "photoelectrode_type" in sub.columns:
        before = len(sub)
        sub = sub[~sub["photoelectrode_type"].fillna("").str.lower().str.contains("cathode")]
        print(f"  [PC] Removed {before - len(sub)} photocathode rows (negative Jph)")

    print(f"\n{'='*55}")
    print(f"  Target: {target_col}  ({len(sub)} valid rows)")
    print(f"{'='*55}")

    min_rows = 15
    if len(sub) < min_rows:
        print(f"  ⚠️  Too few rows ({len(sub)} < {min_rows}) — skipping")
        return None

    # ── target: apply log1p for h2 (heavy right skew) ────────────────────────
    transform = "log1p" if target_key == "h2" else None
    y_raw = sub[target_col].values.astype(float)
    y = np.log1p(np.clip(y_raw, 0, None)) if transform == "log1p" else y_raw

    # ── features ─────────────────────────────────────────────────────────────
    num_cols, cat_cols = get_feature_columns(sub, exclude=exclusions)
    X = sub[num_cols + cat_cols].copy()

    # store medians of numeric columns for inference-time defaults
    dataset_medians = {}
    for c in num_cols:
        v = sub[c].median()
        dataset_medians[c] = float(v) if pd.notna(v) else 0.0

    # store most-frequent of categorical columns
    dataset_modes = {}
    for c in cat_cols:
        mode_val = sub[c].mode()
        dataset_modes[c] = str(mode_val.iloc[0]) if len(mode_val) > 0 else "Unknown"

    print(f"  Features: {len(num_cols)} numeric + {len(cat_cols)} categorical")

    # ── CV folds: use min(cv_folds, len//5) to avoid tiny splits ────────────
    safe_cv = min(cv_folds, max(2, len(sub) // 5))
    print(f"  Using {safe_cv}-fold CV")

    preprocessor = build_preprocessor(num_cols, cat_cols)

    best_name, best_pipeline, best_cv = None, None, {"r2_mean": -9999}

    for name, model in _make_models().items():
        pipe = Pipeline([("pre", preprocessor), ("model", model)])
        cv_res = _cv_score(pipe, X, y, cv=safe_cv)
        print(f"  {name:14s}  R²={cv_res['r2_mean']:+.3f} ± {cv_res['r2_std']:.3f}"
              f"  MAE={cv_res['mae_mean']:.4f}")
        if cv_res["r2_mean"] > best_cv["r2_mean"]:
            best_name, best_pipeline, best_cv = name, pipe, cv_res

    # ── final fit on all data ─────────────────────────────────────────────────
    best_pipeline = clone(best_pipeline)
    best_pipeline.fit(X, y)
    print(f"\n  ✓ Best: {best_name}  (CV R²={best_cv['r2_mean']:+.3f})")

    artifact = {
        "pipeline":        best_pipeline,
        "feature_cols":    {"numeric": num_cols, "cat": cat_cols},
        "target":          target_col,
        "transform":       transform,
        "model_name":      best_name,
        "cv_r2":           best_cv["r2_mean"],
        "cv_mae":          best_cv["mae_mean"],
        "dataset_medians": dataset_medians,
        "dataset_modes":   dataset_modes,
    }

    out_path = MODEL_DIR / f"model_{target_key}.pkl"
    joblib.dump(artifact, out_path)
    print(f"  Saved → {out_path}")
    return artifact


# ── Main ──────────────────────────────────────────────────────────────────────

def run(data_path: str, cv_folds: int) -> None:
    print(f"\n[1/4] Loading dataset: {data_path}")
    df_raw = load_and_map(data_path)
    print(f"      {df_raw.shape[0]} rows × {df_raw.shape[1]} cols")

    print("\n[2/4] Cleaning & enriching...")
    df_clean = clean_data(df_raw)
    df_enrich = add_source_columns(df_clean)

    # save enriched dataset
    enriched_path = Path(__file__).parent / "data" / "pec_dataset_clean.csv"
    df_enrich.to_csv(enriched_path, index=False)
    print(f"      Saved clean dataset → {enriched_path}")

    print("\n[3/4] Engineering features...")
    df_eng = engineer_features(df_enrich)

    print("\n[4/4] Training models...")
    summary = []
    for key in ("pc", "sth", "h2"):
        result = train_target(df_eng, key, cv_folds=cv_folds)
        if result:
            summary.append({
                "target": result["target"],
                "model":  result["model_name"],
                "cv_r2":  f"{result['cv_r2']:+.3f}",
                "cv_mae": f"{result['cv_mae']:.4f}",
            })

    print("\n" + "="*55)
    print("  TRAINING COMPLETE")
    print("="*55)
    df_sum = pd.DataFrame(summary)
    print(df_sum.to_string(index=False))
    print(f"\n  Models saved in: {MODEL_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PEC ML models")
    parser.add_argument("--data", default="data/pec_dataset.csv",
                        help="Path to dataset CSV")
    parser.add_argument("--cv", type=int, default=3,
                        help="K-fold CV splits (default 3, safe for small targets)")
    args = parser.parse_args()
    run(args.data, args.cv)
