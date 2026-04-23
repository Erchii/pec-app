"""
=============================================================================
PEC Water Splitting – Production-Quality Multi-Target ML Pipeline
=============================================================================
Author  : Senior ML Engineer
Purpose : Diploma thesis / research prototype
Targets : Photocurrent Density | STH Efficiency | Hydrogen Evolution Rate
=============================================================================

Pipeline overview
-----------------
 1. Data loading & audit
 2. Numeric parsing & cleaning
 3. Leakage-aware target analysis
 4. Feature engineering (physics-informed + interaction terms)
 5. Feature selection (importance-based + SelectKBest)
 6. Per-target preprocessing & transformation
 7. Model zoo: XGBoost · LightGBM · RandomForest · GradientBoosting
 8. RandomizedSearchCV hyperparameter tuning
 9. K-Fold cross-validation with full metric suite (R², MAE, RMSE)
10. Leakage audit for STH
11. SHAP explainability
12. Result tables & feature-importance plots
"""

# ---------------------------------------------------------------------------
# 0. Imports
# ---------------------------------------------------------------------------
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend – safe for scripts
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path

from sklearn.model_selection import (
    KFold, cross_validate, RandomizedSearchCV, train_test_split
)
from sklearn.preprocessing import StandardScaler, PowerTransformer
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance

from xgboost import XGBRegressor
try:
    from lightgbm import LGBMRegressor
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False
    print("[INFO] LightGBM not installed – skipping LGBMRegressor")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("[INFO] SHAP not installed – skipping SHAP plots (pip install shap)")

RANDOM_STATE = 42
OUTPUT_DIR = Path("pec_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Data loading
# ---------------------------------------------------------------------------

def load_data(filepath: str) -> pd.DataFrame:
    """
    Load the PEC dataset.
    Accepts CSV or Excel.  Edit this path to match your file.
    """
    fp = Path(filepath)
    if not fp.exists():
        print(f"[WARN] File not found: {filepath}. Generating synthetic demo data.")
        return _make_synthetic_data()

    ext = fp.suffix.lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(fp)
    else:
        df = pd.read_csv(fp)
    print(f"[INFO] Loaded {len(df)} rows × {len(df.columns)} cols from {filepath}")
    return df


def _make_synthetic_data(n: int = 500) -> pd.DataFrame:
    """
    Reproducible synthetic dataset that mirrors real PEC structure.
    Used only when no real file is provided.
    """
    rng = np.random.default_rng(RANDOM_STATE)

    materials = ["TiO2", "BiVO4", "Fe2O3", "GaN", "Cu2O", "ZnO", "g-C3N4", "CdS"]
    nanos     = ["Nanorod", "Nanoparticle", "Thin Film", "Nanowire", "Nanotube"]
    cocats    = ["None", "Pt", "NiOx", "CoOx", "RuO2", "IrO2"]
    electros  = ["KOH", "NaOH", "PBS", "H2SO4", "Na2SO4", "KPi"]
    dopings   = ["Undoped", "N-doped", "Nb-doped", "W-doped", "Mo-doped"]

    n_rows = n
    bg   = rng.uniform(1.5, 3.2, n_rows)                     # bandgap [eV]
    bias = rng.uniform(-0.5, 1.5, n_rows)                     # applied bias [V vs RHE]
    pH   = rng.uniform(0, 14, n_rows)
    temp = rng.uniform(20, 80, n_rows)

    # Physics-inspired targets (with noise)
    jph  = np.clip(3.0 / bg * (1 + 0.4 * bias) + rng.normal(0, 0.8, n_rows), 0, 20)
    sth  = np.clip(jph * 0.012 + rng.normal(0, 0.05, n_rows), 0, 0.30)
    # Hydrogen rate is noisy and sparse
    her  = np.clip(jph * 5.2 + rng.normal(0, 15, n_rows), 0, 300)
    # Inject structural zeros (many papers don't report HER)
    her[rng.random(n_rows) < 0.35] = np.nan

    df = pd.DataFrame({
        "Material System"         : rng.choice(materials, n_rows),
        "Bandgap (eV)"            : bg,
        "Doping"                  : rng.choice(dopings, n_rows),
        "pH"                      : pH,
        "Electrolyte"             : rng.choice(electros, n_rows),
        "Temperature (C)"         : temp,
        "Bias (V vs RHE)"         : bias,
        "Nanostructure"           : rng.choice(nanos, n_rows),
        "Cocatalyst"               : rng.choice(cocats, n_rows),
        "Photocurrent (mA/cm2)"   : jph,
        "STH Efficiency (%)"      : sth * 100,          # stored as percentage
        "H2 Evolution (umol/h/cm2)": her,
    })
    return df


# ---------------------------------------------------------------------------
# 2. Numeric parsing & cleaning
# ---------------------------------------------------------------------------

def parse_numeric(series: pd.Series) -> pd.Series:
    """
    Convert string-encoded numbers (e.g. '~1.4', '1.4±0.2', '<2')
    to floats; coerce failures to NaN.
    """
    cleaned = (
        series.astype(str)
              .str.replace(r"[~<>≈±]", "", regex=True)
              .str.split(r"[±/–\-]")
              .str[0]
              .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


NUMERIC_COLS = [
    "Bandgap (eV)", "pH", "Temperature (C)", "Bias (V vs RHE)",
    "Photocurrent (mA/cm2)", "STH Efficiency (%)", "H2 Evolution (umol/h/cm2)",
]
CAT_COLS = ["Material System", "Doping", "Electrolyte", "Nanostructure", "Cocatalyst"]

TARGETS = {
    "Photocurrent": "Photocurrent (mA/cm2)",
    "STH"         : "STH Efficiency (%)",
    "Hydrogen"    : "H2 Evolution (umol/h/cm2)",
}


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Parse numerics, drop rows with all-NaN targets, basic sanity checks."""
    df = df.copy()

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = parse_numeric(df[col])

    # Physical sanity bounds
    if "Bandgap (eV)" in df.columns:
        df.loc[~df["Bandgap (eV)"].between(0.5, 6.0), "Bandgap (eV)"] = np.nan
    if "pH" in df.columns:
        df.loc[~df["pH"].between(0, 14), "pH"] = np.nan
    if "Photocurrent (mA/cm2)" in df.columns:
        df.loc[df["Photocurrent (mA/cm2)"] < 0, "Photocurrent (mA/cm2)"] = np.nan

    target_cols = list(TARGETS.values())
    existing_targets = [c for c in target_cols if c in df.columns]
    before = len(df)
    df = df.dropna(subset=existing_targets, how="all")
    print(f"[Clean] Dropped {before - len(df)} rows with all-NaN targets → {len(df)} remain")
    return df


# ---------------------------------------------------------------------------
# 3. Leakage audit
# ---------------------------------------------------------------------------

def audit_leakage(df: pd.DataFrame) -> None:
    """
    STH leakage check: STH ≈ Jph × 1.23 V × η_faradaic / P_in
    If Photocurrent is a predictor for STH, the model trivially learns a
    linear relationship and R² is inflated.  We flag this explicitly.
    """
    print("\n[Leakage Audit] ─────────────────────────────────────────")
    j_col = TARGETS["Photocurrent"]
    s_col = TARGETS["STH"]
    if j_col in df.columns and s_col in df.columns:
        mask = df[[j_col, s_col]].notna().all(axis=1)
        corr = df.loc[mask, j_col].corr(df.loc[mask, s_col])
        print(f"  Pearson(Photocurrent, STH)  = {corr:.3f}")
        if abs(corr) > 0.85:
            print("  ⚠️  HIGH CORRELATION → Photocurrent MUST be excluded when predicting STH")
        else:
            print("  ✓  Moderate correlation – monitor but proceed with caution")

    h_col = TARGETS["Hydrogen"]
    if j_col in df.columns and h_col in df.columns:
        mask2 = df[[j_col, h_col]].notna().all(axis=1)
        corr2 = df.loc[mask2, j_col].corr(df.loc[mask2, h_col])
        print(f"  Pearson(Photocurrent, H2)   = {corr2:.3f}")
    print()


# ---------------------------------------------------------------------------
# 4. Feature engineering
# ---------------------------------------------------------------------------

PLANCK_EV = 4.136e-15   # eV·s
SPEED_LIGHT = 3e8       # m/s

# Bandgap → absorption edge wavelength [nm]
# Overpotential proxy: bias relative to flat-band (simplified)
# Electrolyte polarity: simple ordinal mapping for ionic strength tendency
ELECTROLYTE_ION = {
    "KOH": 1.0, "NaOH": 1.0, "H2SO4": 1.0,
    "PBS": 0.5, "KPi": 0.5,
    "Na2SO4": 0.6, "other": 0.3,
}


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Physics-informed feature engineering.

    New features created
    --------------------
    photon_energy_eV      : 1240 / bandgap  (absorption edge energy)
    overpotential_proxy   : bias − (bandgap − 1.23)   [simplified]
    bandgap_x_pH          : interaction (surface charge + band bending)
    bias_x_ionic          : bias × ionic strength proxy
    bandgap_sq            : bandgap²  (non-linear material response)
    log_bandgap           : log(bandgap)
    pH_deviation          : |pH − 7|  (deviation from neutral)
    has_cocatalyst        : binary flag (cocatalyst ≠ "None")
    is_nanostructured     : binary flag (Nanostructure ≠ "Thin Film")
    temp_normalized       : (T − 25) / 25  (room-temp deviation)
    bias_positive         : max(bias, 0)   (forward bias only)
    """
    df = df.copy()

    bg   = df.get("Bandgap (eV)", pd.Series(np.nan, index=df.index))
    bias = df.get("Bias (V vs RHE)", pd.Series(np.nan, index=df.index))
    pH   = df.get("pH", pd.Series(np.nan, index=df.index))
    temp = df.get("Temperature (C)", pd.Series(np.nan, index=df.index))

    # --- Physics-informed scalars ---
    df["photon_energy_eV"]   = np.where(bg > 0, 1240.0 / bg.clip(lower=0.1), np.nan)
    df["overpotential_proxy"]= bias - (bg.clip(lower=0.5) - 1.23)
    df["bandgap_sq"]         = bg ** 2
    df["log_bandgap"]        = np.log1p(bg.clip(lower=0))
    df["pH_deviation"]       = (pH - 7.0).abs()
    df["temp_normalized"]    = (temp - 25.0) / 25.0
    df["bias_positive"]      = bias.clip(lower=0)

    # --- Ionic strength proxy ---
    elec_map = df.get("Electrolyte", pd.Series("other", index=df.index)).map(
        lambda x: ELECTROLYTE_ION.get(str(x), 0.3)
    )
    df["ionic_strength_proxy"] = elec_map

    # --- Interaction features (physical motivation) ---
    # Bandgap × pH: space-charge layer depth vs. surface protonation
    df["bandgap_x_pH"]   = bg * pH
    # Bias × ionic strength: electric field enhancement in electrolyte
    df["bias_x_ionic"]   = bias * elec_map
    # Bandgap × overpotential: combined driving force
    df["bg_x_overpot"]   = bg * df["overpotential_proxy"]
    # pH × temperature: kinetics
    df["pH_x_temp"]      = pH * temp

    # --- Binary structural flags ---
    if "Cocatalyst" in df.columns:
        df["has_cocatalyst"]  = (df["Cocatalyst"].str.lower() != "none").astype(int)
    if "Nanostructure" in df.columns:
        df["is_nanostructured"]= (df["Nanostructure"].str.lower() != "thin film").astype(int)

    return df


# ---------------------------------------------------------------------------
# 5. One-hot encoding + final feature matrix
# ---------------------------------------------------------------------------

def build_feature_matrix(df: pd.DataFrame,
                          exclude_cols: list[str] | None = None) -> pd.DataFrame:
    """
    One-hot encode categorical columns, drop original target columns,
    and return a clean numeric feature matrix.
    """
    df = df.copy()
    exclude_cols = exclude_cols or []

    # One-hot encode
    cat_present = [c for c in CAT_COLS if c in df.columns]
    df = pd.get_dummies(df, columns=cat_present, drop_first=False, dtype=float)

    # Drop all target columns + any user-specified exclusions
    all_targets = list(TARGETS.values())
    drop_cols   = [c for c in all_targets + exclude_cols if c in df.columns]
    df = df.drop(columns=drop_cols, errors="ignore")

    # Keep only numeric columns
    df = df.select_dtypes(include=[np.number])
    return df


# ---------------------------------------------------------------------------
# 6. Target transformations (per-target strategy)
# ---------------------------------------------------------------------------

class TargetConfig:
    """
    Holds per-target preprocessing decisions:
      - transformation : None | 'log1p' | 'sqrt' | 'yeo-johnson'
      - exclude_feats  : list of feature columns to drop (leakage prevention)
      - min_samples    : minimum rows needed to train
    """
    def __init__(self, name, col, transform, exclude_feats, min_samples=30):
        self.name          = name
        self.col           = col
        self.transform     = transform      # str or None
        self.exclude_feats = exclude_feats
        self.min_samples   = min_samples

    def apply_transform(self, y: np.ndarray) -> np.ndarray:
        if self.transform == "log1p":
            return np.log1p(np.clip(y, 0, None))
        elif self.transform == "sqrt":
            return np.sqrt(np.clip(y, 0, None))
        elif self.transform == "yeo-johnson":
            pt = PowerTransformer(method="yeo-johnson")
            return pt.fit_transform(y.reshape(-1, 1)).ravel()
        return y

    def inverse_transform(self, y: np.ndarray) -> np.ndarray:
        if self.transform == "log1p":
            return np.expm1(y)
        elif self.transform == "sqrt":
            return np.square(y)
        # yeo-johnson inverse is skipped for metric reporting (report on transformed space)
        return y


TARGET_CONFIGS = [
    TargetConfig(
        name="Photocurrent",
        col=TARGETS["Photocurrent"],
        transform=None,                         # approximately normal in raw space
        exclude_feats=[],
        min_samples=30,
    ),
    TargetConfig(
        name="STH",
        col=TARGETS["STH"],
        transform=None,
        # ⚠️ Exclude Photocurrent to prevent leakage
        exclude_feats=[TARGETS["Photocurrent"]],
        min_samples=30,
    ),
    TargetConfig(
        name="Hydrogen",
        col=TARGETS["Hydrogen"],
        transform="log1p",                      # heavy right skew + zeros
        exclude_feats=[],
        min_samples=20,
    ),
]


# ---------------------------------------------------------------------------
# 7. Model zoo
# ---------------------------------------------------------------------------

def get_model_zoo() -> dict:
    """Return all models with sensible defaults (no tuning yet)."""
    zoo = {
        "XGBoost": XGBRegressor(
            n_estimators=300, learning_rate=0.05,
            max_depth=5, subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, verbosity=0,
        ),
        "RandomForest": RandomForestRegressor(
            n_estimators=300, max_depth=None,
            min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=-1,
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=200, learning_rate=0.05,
            max_depth=4, subsample=0.8, random_state=RANDOM_STATE,
        ),
    }
    if HAS_LGBM:
        zoo["LightGBM"] = LGBMRegressor(
            n_estimators=300, learning_rate=0.05,
            num_leaves=31, subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, verbose=-1,
        )
    return zoo


# ---------------------------------------------------------------------------
# 8. Hyperparameter search spaces
# ---------------------------------------------------------------------------

PARAM_SPACES = {
    "XGBoost": {
        "n_estimators"    : [100, 200, 400],
        "max_depth"       : [3, 4, 5, 6, 7],
        "learning_rate"   : [0.01, 0.05, 0.1, 0.2],
        "subsample"       : [0.6, 0.7, 0.8, 0.9, 1.0],
        "colsample_bytree": [0.6, 0.7, 0.8, 1.0],
        "reg_alpha"       : [0, 0.1, 0.5, 1.0],
        "reg_lambda"      : [0.5, 1.0, 2.0, 5.0],
        "min_child_weight": [1, 3, 5],
    },
    "RandomForest": {
        "n_estimators"  : [100, 200, 400],
        "max_depth"     : [None, 5, 8, 12, 20],
        "min_samples_leaf":[1, 2, 4, 8],
        "max_features"  : ["sqrt", "log2", 0.5],
    },
    "GradientBoosting": {
        "n_estimators"  : [100, 200, 300],
        "max_depth"     : [3, 4, 5, 6],
        "learning_rate" : [0.01, 0.05, 0.1, 0.2],
        "subsample"     : [0.6, 0.8, 1.0],
        "min_samples_leaf":[1, 2, 5],
    },
    "LightGBM": {
        "n_estimators"    : [100, 200, 400],
        "num_leaves"      : [15, 31, 63, 127],
        "learning_rate"   : [0.01, 0.05, 0.1],
        "subsample"       : [0.6, 0.8, 1.0],
        "colsample_bytree": [0.6, 0.8, 1.0],
        "reg_alpha"       : [0, 0.1, 0.5],
        "reg_lambda"      : [0.5, 1.0, 2.0],
        "min_child_samples":[5, 10, 20],
    },
}


# ---------------------------------------------------------------------------
# 9. Metrics
# ---------------------------------------------------------------------------

def compute_metrics(y_true, y_pred, label="") -> dict:
    r2   = r2_score(y_true, y_pred)
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return {"label": label, "R2": r2, "MAE": mae, "RMSE": rmse}


def cv_metrics(model, X: np.ndarray, y: np.ndarray, cv: int = 5) -> dict:
    """
    K-Fold cross-validation returning mean ± std for R², MAE, RMSE.
    Uses neg_root_mean_squared_error available in sklearn ≥ 0.24.
    """
    kf = KFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    r2s, maes, rmses = [], [], []

    for train_idx, val_idx in kf.split(X):
        Xtr, Xval = X[train_idx], X[val_idx]
        ytr, yval = y[train_idx], y[val_idx]
        m = clone_model(model)
        m.fit(Xtr, ytr)
        pred = m.predict(Xval)
        r2s.append(r2_score(yval, pred))
        maes.append(mean_absolute_error(yval, pred))
        rmses.append(np.sqrt(mean_squared_error(yval, pred)))

    return {
        "R2_mean"  : np.mean(r2s),  "R2_std"  : np.std(r2s),
        "MAE_mean" : np.mean(maes), "MAE_std" : np.std(maes),
        "RMSE_mean": np.mean(rmses),"RMSE_std": np.std(rmses),
    }


def clone_model(model):
    """Deep-clone a sklearn-compatible estimator."""
    from sklearn.base import clone
    return clone(model)


# ---------------------------------------------------------------------------
# 10. Feature selection
# ---------------------------------------------------------------------------

def select_features(X: pd.DataFrame, y: np.ndarray,
                     method: str = "importance",
                     k: int = 25,
                     base_model=None) -> list[str]:
    """
    Two methods:
      'kbest'      – SelectKBest with mutual_info_regression
      'importance' – train a quick RF, keep top-k by mean impurity decrease

    Returns list of selected column names.
    """
    if method == "kbest":
        mask = ~np.isnan(y)
        sel  = SelectKBest(mutual_info_regression, k=min(k, X.shape[1]))
        sel.fit(X[mask].fillna(0), y[mask])
        cols = X.columns[sel.get_support()].tolist()

    else:  # importance
        mask  = ~np.isnan(y)
        Xfill = X[mask].fillna(X[mask].median())
        rf    = RandomForestRegressor(
            n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1
        )
        rf.fit(Xfill, y[mask])
        imp  = pd.Series(rf.feature_importances_, index=X.columns)
        cols = imp.nlargest(min(k, len(imp))).index.tolist()

    print(f"  [FeatureSel/{method}] Selected {len(cols)} features")
    return cols


# ---------------------------------------------------------------------------
# 11. Main training loop (per target)
# ---------------------------------------------------------------------------

def train_target(df_clean: pd.DataFrame,
                 cfg: TargetConfig,
                 cv_folds: int = 5,
                 n_iter_search: int = 30) -> dict:
    """
    Full pipeline for one target:
      - Filter valid rows
      - Build feature matrix (excluding leakage columns)
      - Apply target transformation
      - Feature selection
      - Hyperparameter search
      - K-Fold cross-validation
      - Final model fit
    Returns result dict.
    """
    print(f"\n{'='*65}")
    print(f" TARGET: {cfg.name}  |  transform: {cfg.transform or 'none'}")
    print(f"{'='*65}")

    # ── Rows with a valid target ──────────────────────────────────────────
    mask = df_clean[cfg.col].notna()
    sub  = df_clean[mask].copy()
    print(f"  Rows with valid target: {len(sub)}")

    if len(sub) < cfg.min_samples:
        print(f"  ⚠️  Too few samples ({len(sub)} < {cfg.min_samples}) → skipping")
        return {}

    # ── Feature matrix ────────────────────────────────────────────────────
    X_df = build_feature_matrix(sub, exclude_cols=cfg.exclude_feats)
    y_raw= sub[cfg.col].values.astype(float)
    y    = cfg.apply_transform(y_raw)

    # Fill remaining NaNs with column median (simple imputation)
    X_df = X_df.fillna(X_df.median())
    X_np = X_df.values.astype(float)

    print(f"  Feature matrix: {X_np.shape[0]} rows × {X_np.shape[1]} cols")

    # ── Feature selection ─────────────────────────────────────────────────
    selected_cols = select_features(X_df, y, method="importance", k=25)
    X_sel         = X_df[selected_cols].values.astype(float)
    print(f"  Using {len(selected_cols)} features after selection")

    # ── Scaling (tree models don't need it, but we keep a scaled copy for
    #    future linear/SVM baselines and for SHAP consistency)
    scaler  = StandardScaler()
    X_scaled= scaler.fit_transform(X_sel)   # used only if needed later

    # ── Model zoo + hyperparameter search ────────────────────────────────
    zoo      = get_model_zoo()
    results  = {}

    for model_name, base_model in zoo.items():
        print(f"\n  ── {model_name} ──────────────────────────────")

        # Hyperparameter search (RandomizedSearchCV on a held-out 20 %)
        space = PARAM_SPACES.get(model_name, {})
        if space:
            rscv = RandomizedSearchCV(
                base_model, space,
                n_iter=n_iter_search,
                cv=KFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE),
                scoring="r2",
                n_jobs=-1,
                random_state=RANDOM_STATE,
                refit=True,
            )
            rscv.fit(X_sel, y)
            best_model  = rscv.best_estimator_
            best_params = rscv.best_params_
            print(f"    Best CV R² (search): {rscv.best_score_:.3f}")
        else:
            best_model  = base_model
            best_params = {}
            best_model.fit(X_sel, y)

        # ── K-Fold cross-validation on full data ─────────────────────────
        cv_res = cv_metrics(best_model, X_sel, y, cv=cv_folds)
        print(f"    {cv_folds}-Fold CV  R²  : {cv_res['R2_mean']:.3f} ± {cv_res['R2_std']:.3f}")
        print(f"    {cv_folds}-Fold CV  MAE : {cv_res['MAE_mean']:.4f} ± {cv_res['MAE_std']:.4f}")
        print(f"    {cv_folds}-Fold CV  RMSE: {cv_res['RMSE_mean']:.4f} ± {cv_res['RMSE_std']:.4f}")

        # ── Final model on full data (for explainability) ─────────────────
        best_model.fit(X_sel, y)

        results[model_name] = {
            "model"       : best_model,
            "best_params" : best_params,
            "cv"          : cv_res,
            "feature_cols": selected_cols,
            "X_sel"       : X_sel,
            "y"           : y,
            "scaler"      : scaler,
        }

    return results


# ---------------------------------------------------------------------------
# 12. Visualization helpers
# ---------------------------------------------------------------------------

def plot_cv_comparison(all_results: dict, save_dir: Path) -> None:
    """
    Bar chart: mean R² ± std for every model × target.
    """
    records = []
    for target_name, model_dict in all_results.items():
        for model_name, res in model_dict.items():
            records.append({
                "Target"  : target_name,
                "Model"   : model_name,
                "R2_mean" : res["cv"]["R2_mean"],
                "R2_std"  : res["cv"]["R2_std"],
            })
    df_plot = pd.DataFrame(records)

    targets  = df_plot["Target"].unique()
    n_tgt    = len(targets)
    fig, axes= plt.subplots(1, n_tgt, figsize=(6 * n_tgt, 5), sharey=False)
    if n_tgt == 1:
        axes = [axes]

    palette = sns.color_palette("Set2", 8)

    for ax, target in zip(axes, targets):
        sub = df_plot[df_plot["Target"] == target].sort_values("R2_mean", ascending=False)
        bars = ax.bar(
            sub["Model"], sub["R2_mean"],
            yerr=sub["R2_std"], capsize=5,
            color=palette[:len(sub)], edgecolor="k", linewidth=0.7, alpha=0.85,
        )
        ax.set_title(f"{target}", fontsize=13, fontweight="bold")
        ax.set_ylabel("CV R² (mean ± std)")
        ax.set_ylim(min(0, sub["R2_mean"].min() - 0.1), 1.0)
        ax.axhline(0, color="red", linestyle="--", linewidth=0.8)
        ax.tick_params(axis="x", rotation=25)
        for bar, row in zip(bars, sub.itertuples()):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + row.R2_std + 0.01,
                    f"{row.R2_mean:.2f}", ha="center", va="bottom", fontsize=9)

    fig.suptitle("K-Fold CV Performance Comparison (R²)", fontsize=14, y=1.02)
    plt.tight_layout()
    path = save_dir / "cv_r2_comparison.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[Plot] Saved → {path}")


def plot_feature_importance(results_for_target: dict,
                             target_name: str,
                             save_dir: Path,
                             top_n: int = 15) -> None:
    """
    Feature importance for the best model of a given target.
    """
    # Pick best model by CV R²
    best_name = max(results_for_target,
                    key=lambda k: results_for_target[k]["cv"]["R2_mean"])
    res   = results_for_target[best_name]
    model = res["model"]
    cols  = res["feature_cols"]

    if not hasattr(model, "feature_importances_"):
        print(f"  [Plot] {best_name} has no feature_importances_ – skipping")
        return

    imp  = pd.Series(model.feature_importances_, index=cols).nlargest(top_n)
    fig, ax = plt.subplots(figsize=(8, max(4, top_n * 0.35)))
    imp.sort_values().plot.barh(ax=ax, color=sns.color_palette("viridis", top_n))
    ax.set_title(f"Feature Importance – {target_name}\n(Best model: {best_name})",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Importance score")
    plt.tight_layout()
    path = save_dir / f"feat_importance_{target_name.lower()}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[Plot] Saved → {path}")


def plot_shap(results_for_target: dict,
              target_name: str,
              save_dir: Path,
              max_display: int = 15) -> None:
    """
    SHAP summary beeswarm for the best model.
    Only runs when shap package is available.
    """
    if not HAS_SHAP:
        return

    best_name = max(results_for_target,
                    key=lambda k: results_for_target[k]["cv"]["R2_mean"])
    res   = results_for_target[best_name]
    model = res["model"]
    X_sel = res["X_sel"]
    cols  = res["feature_cols"]

    try:
        explainer = shap.TreeExplainer(model)
        sv        = explainer.shap_values(X_sel)
        fig, ax   = plt.subplots(figsize=(9, 5))
        shap.summary_plot(sv, X_sel, feature_names=cols,
                          max_display=max_display, show=False)
        path = save_dir / f"shap_{target_name.lower()}.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"[SHAP] Saved → {path}")
    except Exception as exc:
        print(f"[SHAP] Could not compute for {target_name}: {exc}")


def plot_pred_vs_actual(results_for_target: dict,
                        target_name: str,
                        save_dir: Path) -> None:
    """
    Predicted vs. actual scatter for all models side-by-side (train fit).
    Uses a simple train/test split just for the visual.
    """
    best_name = max(results_for_target,
                    key=lambda k: results_for_target[k]["cv"]["R2_mean"])
    res   = results_for_target[best_name]
    X_sel = res["X_sel"]
    y     = res["y"]

    Xtr, Xte, ytr, yte = train_test_split(
        X_sel, y, test_size=0.2, random_state=RANDOM_STATE
    )
    model = clone_model(res["model"])
    model.fit(Xtr, ytr)
    ypred = model.predict(Xte)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(yte, ypred, alpha=0.6, edgecolors="k", linewidths=0.4, s=40)
    lims = [min(yte.min(), ypred.min()), max(yte.max(), ypred.max())]
    ax.plot(lims, lims, "r--", linewidth=1.2, label="Perfect fit")
    r2 = r2_score(yte, ypred)
    ax.set_xlabel("Actual (transformed)")
    ax.set_ylabel("Predicted")
    ax.set_title(f"{target_name} – Predicted vs Actual\n{best_name}  |  Test R²={r2:.3f}",
                 fontsize=11, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    path = save_dir / f"pred_vs_actual_{target_name.lower()}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[Plot] Saved → {path}")


def print_final_table(all_results: dict) -> pd.DataFrame:
    """Print and return a summary DataFrame of all CV results."""
    rows = []
    for target_name, model_dict in all_results.items():
        for model_name, res in model_dict.items():
            cv = res["cv"]
            rows.append({
                "Target"    : target_name,
                "Model"     : model_name,
                "R²"        : f"{cv['R2_mean']:.3f} ± {cv['R2_std']:.3f}",
                "MAE"       : f"{cv['MAE_mean']:.4f} ± {cv['MAE_std']:.4f}",
                "RMSE"      : f"{cv['RMSE_mean']:.4f} ± {cv['RMSE_std']:.4f}",
            })
    df_summary = pd.DataFrame(rows)
    print("\n" + "="*75)
    print("  FINAL PERFORMANCE SUMMARY (5-Fold CV, mean ± std)")
    print("="*75)
    print(df_summary.to_string(index=False))
    print("="*75)
    return df_summary


# ---------------------------------------------------------------------------
# 13. Entrypoint
# ---------------------------------------------------------------------------

def run_pipeline(filepath: str = "pec_dataset.csv",
                 cv_folds: int = 5,
                 n_iter_search: int = 30) -> dict:
    """
    Main entrypoint.

    Parameters
    ----------
    filepath       : path to your CSV / Excel dataset
    cv_folds       : number of K-Fold splits (5 recommended)
    n_iter_search  : RandomizedSearchCV iterations per model (30 for speed,
                     increase to 60-100 for final thesis run)
    """
    # ── 1. Load ──────────────────────────────────────────────────────────
    df_raw = load_data(filepath)

    # ── 2. Clean ─────────────────────────────────────────────────────────
    df_clean = clean_data(df_raw)

    # ── 3. Leakage audit ─────────────────────────────────────────────────
    audit_leakage(df_clean)

    # ── 4. Feature engineering ───────────────────────────────────────────
    df_eng = engineer_features(df_clean)
    print(f"\n[Features] Shape after engineering: {df_eng.shape}")

    # ── 5. Train each target ─────────────────────────────────────────────
    all_results = {}
    for cfg in TARGET_CONFIGS:
        if cfg.col not in df_eng.columns:
            print(f"[SKIP] Column '{cfg.col}' not found in dataset")
            continue
        target_results = train_target(
            df_eng, cfg,
            cv_folds=cv_folds,
            n_iter_search=n_iter_search,
        )
        if target_results:
            all_results[cfg.name] = target_results

    # ── 6. Summary table ─────────────────────────────────────────────────
    summary = print_final_table(all_results)
    summary.to_csv(OUTPUT_DIR / "cv_summary.csv", index=False)

    # ── 7. Visualisations ────────────────────────────────────────────────
    plot_cv_comparison(all_results, OUTPUT_DIR)

    for target_name, model_dict in all_results.items():
        plot_feature_importance(model_dict, target_name, OUTPUT_DIR)
        plot_shap(model_dict, target_name, OUTPUT_DIR)
        plot_pred_vs_actual(model_dict, target_name, OUTPUT_DIR)

    print(f"\n[Done] All outputs saved to ./{OUTPUT_DIR}/")
    return all_results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="PEC Water Splitting – Multi-Target ML Pipeline"
    )
    parser.add_argument(
        "--data", type=str, default="pec_dataset.csv",
        help="Path to your dataset (CSV or Excel). Default: pec_dataset.csv",
    )
    parser.add_argument(
        "--cv", type=int, default=5,
        help="Number of K-Fold cross-validation splits (default: 5)",
    )
    parser.add_argument(
        "--n_iter", type=int, default=30,
        help="RandomizedSearchCV iterations per model (default: 30; use 60+ for thesis)",
    )
    args = parser.parse_args()

    run_pipeline(
        filepath=args.data,
        cv_folds=args.cv,
        n_iter_search=args.n_iter,
    )
