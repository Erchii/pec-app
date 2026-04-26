"""
Train ensemble ML models for each PEC target.
Saves two models per target (XGBoost + RandomForest) and computes
per-tree variance for uncertainty estimation at inference time.

Artifacts saved to model/:
  model_pc.pkl  — Photocurrent Density (mA/cm²)
  model_sth.pkl — STH Efficiency (%)
  model_h2.pkl  — Hydrogen Evolution Rate (µmol/h/cm²)

Each artifact:
  {
    "models":          [{"name": str, "pipeline": Pipeline, "cv_r2": float}, ...],
    "best_idx":        int,
    "feature_cols":    {"numeric": [...], "cat": [...]},
    "target":          str,
    "transform":       None | "log1p",
    "cv_r2":           float,          # best model CV R²
    "cv_mae":          float,
    "dataset_medians": {col: float},
    "dataset_modes":   {col: str},
    "thresholds":      {"high": float, "medium": float},  # p75/p40 of train y
  }

Run:
    python train.py
    python train.py --data data/pec_dataset.csv --cv 5
"""

import argparse
import logging
import warnings
import sys
from pathlib import Path

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

import numpy as np
import pandas as pd
import joblib
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

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
    return {
        "r2_mean": float(np.mean(r2s)),
        "r2_std":  float(np.std(r2s)),
        "mae_mean": float(np.mean(maes)),
    }


# ── Per-target training ───────────────────────────────────────────────────────

def train_target(df_eng: pd.DataFrame, target_key: str, cv_folds: int) -> dict | None:
    target_col = TARGETS[target_key]
    exclusions = TARGET_EXCLUSIONS[target_key]

    sub = df_eng[df_eng[target_col].notna()].copy()

    if target_key == "pc" and "photoelectrode_type" in sub.columns:
        before = len(sub)
        sub = sub[~sub["photoelectrode_type"].fillna("").str.lower().str.contains("cathode")]
        log.info("  [PC] Removed %d photocathode rows", before - len(sub))

    log.info("\n%s", "=" * 55)
    log.info("  Target: %s  (%d valid rows)", target_col, len(sub))
    log.info("%s", "=" * 55)

    if len(sub) < 15:
        log.warning("  Too few rows (%d < 15) — skipping", len(sub))
        return None

    transform = "log1p" if target_key == "h2" else None
    y_raw = sub[target_col].values.astype(float)
    y = np.log1p(np.clip(y_raw, 0, None)) if transform == "log1p" else y_raw

    num_cols, cat_cols = get_feature_columns(sub, exclude=exclusions)
    X = sub[num_cols + cat_cols].copy()

    dataset_medians = {
        c: float(v) if pd.notna(v := sub[c].median()) else 0.0
        for c in num_cols
    }
    dataset_modes = {
        c: str(sub[c].mode().iloc[0]) if len(sub[c].mode()) > 0 else "Unknown"
        for c in cat_cols
    }

    log.info("  Features: %d numeric + %d categorical", len(num_cols), len(cat_cols))

    safe_cv = min(cv_folds, max(2, len(sub) // 5))
    log.info("  Using %d-fold CV", safe_cv)

    preprocessor = build_preprocessor(num_cols, cat_cols)

    trained_models = []
    for name, model in _make_models().items():
        pipe = Pipeline([("pre", preprocessor), ("model", model)])
        cv_res = _cv_score(pipe, X, y, cv=safe_cv)
        log.info("  %-14s  R²=%+.3f ± %.3f  MAE=%.4f",
                 name, cv_res["r2_mean"], cv_res["r2_std"], cv_res["mae_mean"])

        # Fit on full data for inference
        final_pipe = clone(pipe)
        final_pipe.fit(X, y)
        trained_models.append({
            "name":     name,
            "pipeline": final_pipe,
            "cv_r2":    cv_res["r2_mean"],
            "cv_mae":   cv_res["mae_mean"],
            "cv_r2_std": cv_res["r2_std"],
        })

    best_idx = int(np.argmax([m["cv_r2"] for m in trained_models]))
    best = trained_models[best_idx]
    log.info("  ✓ Best: %s  (CV R²=%+.3f)", best["name"], best["cv_r2"])

    # Percentile-based thresholds computed on training targets (in original space)
    y_orig = np.expm1(y) if transform == "log1p" else y
    thresholds = {
        "high":   float(np.percentile(y_orig, 75)),
        "medium": float(np.percentile(y_orig, 40)),
    }
    log.info("  Thresholds (orig space) — high≥%.3f  medium≥%.3f",
             thresholds["high"], thresholds["medium"])

    artifact = {
        "models":          trained_models,
        "best_idx":        best_idx,
        "feature_cols":    {"numeric": num_cols, "cat": cat_cols},
        "target":          target_col,
        "transform":       transform,
        "cv_r2":           best["cv_r2"],
        "cv_mae":          best["cv_mae"],
        "dataset_medians": dataset_medians,
        "dataset_modes":   dataset_modes,
        "thresholds":      thresholds,
    }

    out_path = MODEL_DIR / f"model_{target_key}.pkl"
    joblib.dump(artifact, out_path)
    log.info("  Saved → %s", out_path)
    return artifact


# ── Main ──────────────────────────────────────────────────────────────────────

def run(data_path: str, cv_folds: int) -> None:
    log.info("[1/4] Loading dataset: %s", data_path)
    df_raw = load_and_map(data_path)
    log.info("      %d rows × %d cols", *df_raw.shape)

    log.info("[2/4] Cleaning & enriching...")
    df_clean = clean_data(df_raw)
    df_enrich = add_source_columns(df_clean)

    enriched_path = Path(__file__).parent / "data" / "pec_dataset_clean.csv"
    df_enrich.to_csv(enriched_path, index=False)
    log.info("      Saved clean dataset → %s", enriched_path)

    log.info("[3/4] Engineering features...")
    df_eng = engineer_features(df_enrich)

    log.info("[4/4] Training models...")
    summary = []
    for key in ("pc", "sth", "h2"):
        result = train_target(df_eng, key, cv_folds=cv_folds)
        if result:
            summary.append({
                "target": result["target"],
                "best_model": result["models"][result["best_idx"]]["name"],
                "cv_r2":  f"{result['cv_r2']:+.3f}",
                "cv_mae": f"{result['cv_mae']:.4f}",
                "thr_high": f"{result['thresholds']['high']:.3f}",
                "thr_med":  f"{result['thresholds']['medium']:.3f}",
            })

    log.info("\n%s", "=" * 65)
    log.info("  TRAINING COMPLETE")
    log.info("%s", "=" * 65)
    df_sum = pd.DataFrame(summary)
    print(df_sum.to_string(index=False))
    log.info("\n  Models saved in: %s", MODEL_DIR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PEC ML models")
    parser.add_argument("--data", default="data/pec_dataset.csv")
    parser.add_argument("--cv", type=int, default=5,
                        help="K-fold CV splits (default 5)")
    args = parser.parse_args()
    run(args.data, args.cv)
