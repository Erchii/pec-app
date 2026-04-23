# PEC Water Splitting ML Pipeline — Design Guide

## How to run

```bash
# Install dependencies
pip install xgboost lightgbm scikit-learn shap matplotlib seaborn pandas numpy openpyxl

# Run with your real data
python pec_ml_pipeline.py --data your_dataset.csv --cv 5 --n_iter 60

# Run with synthetic demo data (no file needed)
python pec_ml_pipeline.py
```

All outputs are saved to `./pec_outputs/`.

---

## Architecture overview

```
Raw data
  └─ load_data()
       └─ clean_data()               ← numeric parsing, sanity bounds
            └─ audit_leakage()       ← Pearson check STH ↔ Photocurrent
                 └─ engineer_features()
                      └─ [per target]
                           └─ build_feature_matrix()   ← OHE + drop leakage
                                └─ select_features()   ← RF importance top-25
                                     └─ RandomizedSearchCV (3-fold inner CV)
                                          └─ cv_metrics()  (5-fold outer CV)
                                               └─ plots / SHAP
```

---

## Per-target strategy

| Target | Transform | Leakage exclusion | Rationale |
|---|---|---|---|
| Photocurrent | None | — | Approximately Gaussian in raw space |
| STH | None | **Exclude Photocurrent** | STH ≈ f(Jph) by physics → would inflate R² |
| H2 Evolution | log1p | — | Heavy right skew + structural zeros from missing reports |

---

## Feature engineering rationale

| Feature | Physics motivation |
|---|---|
| `photon_energy_eV` = 1240/Eg | Absorption edge; determines which photons are harvested |
| `overpotential_proxy` = V − (Eg − 1.23) | Net driving force beyond the thermodynamic minimum |
| `bandgap_x_pH` | pH shifts flat-band potential; interaction with Eg controls band bending |
| `bias_x_ionic` | Electric field in the double layer scales with ionic strength |
| `bg_x_overpot` | Combined material + electrochemical driving force |
| `pH_x_temp` | Arrhenius-like kinetics depend on both |
| `has_cocatalyst` | Binary: catalytic surface sites for H₂/O₂ evolution |
| `is_nanostructured` | Binary: increased surface area vs. flat film |

---

## Anti-leakage notes

STH is defined as:

```
STH (%) = (Jph × 1.23 V × η_Faradaic) / P_incident × 100
```

So STH is **almost deterministically** a function of Photocurrent.
If you include Photocurrent as a predictor for STH, your model is simply
learning `y ≈ 1.23 × x` and your R² will be artificially high (~0.95+).

**Solution:** `build_feature_matrix()` accepts an `exclude_cols` list.
The STH `TargetConfig` sets `exclude_feats=[TARGETS["Photocurrent"]]`.

---

## Hydrogen Evolution: why it's hard

1. **Sparse observations** — many papers report Jph but not HER.
2. **Reporting inconsistency** — different illumination intensities (AM1.5G vs. UV lamp) are mixed.
3. **Non-linear physics** — HER depends on surface kinetics, catalyst loading, and mass transport in ways not captured by scalar features.

**Improvements applied:**
- `log1p` transform to compress the tail and handle zeros
- Separate feature selection pass (the important features differ from Jph)
- 5-fold CV to get honest uncertainty estimates

**Further suggestions for thesis:**
- Collect illumination intensity as a feature
- Add catalyst loading (mg/cm²) if available
- Try a Poisson or Tweedie loss (XGBoost supports `objective='reg:tweedie'`)
- Consider a two-stage model: (1) classifier → reports HER?, (2) regressor → HER value

---

## Hyperparameter tuning

`RandomizedSearchCV` with 3-fold inner CV is used **inside** the 5-fold outer CV loop.
This is a **nested CV** pattern:

```
Outer 5-fold CV
  ├─ Fold 1: [train] → inner 3-fold search → best model → eval on [val]
  ├─ Fold 2: ...
  └─ Fold 5: ...
```

This avoids selection bias from tuning on the same data used to estimate generalization.

---

## Outputs

| File | Description |
|---|---|
| `cv_summary.csv` | Table of R² / MAE / RMSE for all models × targets |
| `cv_r2_comparison.png` | Bar chart comparing all models |
| `feat_importance_{target}.png` | Top-15 features for best model |
| `shap_{target}.png` | SHAP beeswarm (requires `pip install shap`) |
| `pred_vs_actual_{target}.png` | Scatter plot on held-out 20% |

---

## Extending the pipeline

```python
# Add a new model
from sklearn.svm import SVR
zoo["SVR"] = SVR(kernel="rbf")
PARAM_SPACES["SVR"] = {"C": [0.1, 1, 10, 100], "gamma": ["scale", "auto"]}

# Add a new target
TARGET_CONFIGS.append(TargetConfig(
    name="IPCE",
    col="IPCE (%)",
    transform=None,
    exclude_feats=[],
))

# Change feature selection to SelectKBest
selected_cols = select_features(X_df, y, method="kbest", k=20)
```
