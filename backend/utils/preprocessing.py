"""
Preprocessing utilities: column mapping, cleaning, feature engineering,
and sklearn pipeline construction for PEC water-splitting ML models.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ── Column name mapping: raw CSV → internal ──────────────────────────────────
COLUMN_MAP = {
    "Publication ID":                              "doi",
    "Material System":                             "material",
    "Bandgap (eV)":                                "bandgap",
    "Synthesis Method":                            "synthesis_method",
    "Morphology":                                  "morphology",
    "Nanostructure":                               "nanostructure",
    "Cocatalyst":                                  "cocatalyst",
    "Protective Layer":                            "protective_layer",
    "Photoelectrode Type":                         "photoelectrode_type",
    "Thickness (nm)":                              "thickness",
    "Electrolyte":                                 "electrolyte",
    "pH":                                          "ph",
    "Illumination Type":                           "illumination_type",
    "Light Intensity (mW/cm\u00b2)":               "light_intensity",
    "Applied Bias (V vs RHE)":                     "bias",
    "Temperature (K)":                             "temperature_k",
    "Photocurrent Density (mA/cm\u00b2)":          "photocurrent",
    "STH Efficiency (%)":                          "sth",
    "Hydrogen Evolution Rate (\u00b5mol h\u207b\u00b9 cm\u207b\u00b2)": "h2",
}

# Internal target names
TARGETS = {"pc": "photocurrent", "sth": "sth", "h2": "h2"}

# ── Feature lists (before OHE) ────────────────────────────────────────────────
NUMERIC_FEATURES = [
    "bandgap", "ph", "temperature_k", "bias", "light_intensity", "thickness",
    # engineered
    "photon_energy", "overpotential_proxy", "bandgap_sq", "log_bandgap",
    "ph_deviation", "bias_positive", "has_cocatalyst", "is_nanostructured",
]

CATEGORICAL_FEATURES = [
    "material", "electrolyte", "synthesis_method",
    "photoelectrode_type", "nanostructure", "morphology",
]

# Exclusions per target to prevent leakage
TARGET_EXCLUSIONS = {
    "pc":  [],
    "sth": ["photocurrent"],   # STH ≈ Jph × const → exclude to avoid leakage
    "h2":  [],
}

# ── Numeric parsing ───────────────────────────────────────────────────────────

def parse_numeric(series: pd.Series) -> pd.Series:
    """Coerce messy strings like '~1.4', '1.4±0.2', '<2' to float."""
    cleaned = (
        series.astype(str)
              .str.replace(r"[~<>≈±]", "", regex=True)
              .str.split(r"[±/–\-]")
              .str[0]
              .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


# ── Load & rename ─────────────────────────────────────────────────────────────

def load_and_map(filepath: str) -> pd.DataFrame:
    """Load CSV and rename columns to internal names."""
    df = pd.read_csv(filepath)
    rename = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename)
    return df


# ── Cleaning ──────────────────────────────────────────────────────────────────

_NUMERIC_INTERNAL = [
    "bandgap", "ph", "temperature_k", "bias", "light_intensity",
    "thickness", "photocurrent", "sth", "h2",
]

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Parse numeric columns and apply physical sanity bounds."""
    df = df.copy()

    for col in _NUMERIC_INTERNAL:
        if col in df.columns:
            df[col] = parse_numeric(df[col])

    bounds = {
        "bandgap":      (0.5, 6.0),
        "ph":           (0.0, 14.0),
        "sth":          (0.0, 100.0),
        "temperature_k":(200.0, 1500.0),
    }
    for col, (lo, hi) in bounds.items():
        if col in df.columns:
            df.loc[~df[col].between(lo, hi), col] = np.nan

    for col in ["photocurrent", "h2"]:
        if col in df.columns:
            df.loc[df[col] < 0, col] = np.nan

    return df


# ── Feature engineering ───────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add physics-informed features. All new columns are numeric."""
    df = df.copy()

    bg   = df.get("bandgap",   pd.Series(np.nan, index=df.index))
    bias = df.get("bias",      pd.Series(np.nan, index=df.index))
    ph   = df.get("ph",        pd.Series(np.nan, index=df.index))

    df["photon_energy"]       = np.where(bg > 0, 1240.0 / bg.clip(lower=0.1), np.nan)
    df["overpotential_proxy"] = bias - (bg.clip(lower=0.5) - 1.23)
    df["bandgap_sq"]          = bg ** 2
    df["log_bandgap"]         = np.log1p(bg.clip(lower=0))
    df["ph_deviation"]        = (ph - 7.0).abs()
    df["bias_positive"]       = bias.clip(lower=0)

    _no_cocatalyst = {"none", "not reported", "nan", ""}
    if "cocatalyst" in df.columns:
        df["has_cocatalyst"] = (
            ~df["cocatalyst"].fillna("none").str.strip().str.lower().isin(_no_cocatalyst)
        ).astype(float)

    _no_nano = {"thin film", "bulk", "not reported", "nan", ""}
    if "nanostructure" in df.columns:
        df["is_nanostructured"] = (
            ~df["nanostructure"].fillna("thin film").str.strip().str.lower().isin(_no_nano)
        ).astype(float)

    return df


# ── sklearn preprocessor factory ─────────────────────────────────────────────

def get_feature_columns(df: pd.DataFrame,
                        exclude: list[str] | None = None) -> tuple[list[str], list[str]]:
    """Return (numeric_cols, cat_cols) that exist in df, minus exclusions."""
    exclude = set(exclude or [])
    num = [c for c in NUMERIC_FEATURES if c in df.columns and c not in exclude]
    cat = [c for c in CATEGORICAL_FEATURES if c in df.columns and c not in exclude]
    return num, cat


def build_preprocessor(numeric_cols: list[str],
                        cat_cols: list[str]) -> ColumnTransformer:
    """
    ColumnTransformer:
      - numeric → median imputation  (tree models don't need scaling)
      - categorical → most_frequent imputation + OHE (ignore unknown at inference)
    """
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
    ])
    cat_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    transformers = []
    if numeric_cols:
        transformers.append(("num", numeric_pipe, numeric_cols))
    if cat_cols:
        transformers.append(("cat", cat_pipe, cat_cols))

    return ColumnTransformer(transformers, remainder="drop")


# ── Dataset enrichment: source URLs ──────────────────────────────────────────

def add_source_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add source_url and source_verified columns.
    source_url  = https://doi.org/{doi}  when DOI is available, else NaN.
    source_verified = 0 (not programmatically verified; requires manual review).
    We never hallucinate data — values stay NaN when DOI is missing.
    """
    df = df.copy()
    if "doi" in df.columns:
        df["source_url"] = df["doi"].apply(
            lambda d: f"https://doi.org/{str(d).strip()}"
            if pd.notna(d) and str(d).strip() not in ("", "nan")
            else np.nan
        )
    else:
        df["source_url"] = np.nan
    df["source_verified"] = 0
    return df
