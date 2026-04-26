"""
PEC Dataset Expansion Script
=============================
Strategy:
  1. Fill bandgap from known material literature values
  2. Fill pH from electrolyte composition
  3. Fill temperature (default 298 K for lab conditions)
  4. Fill light intensity for standard AM 1.5G illumination rows
  5. Estimate STH from Jph using physics: STH(%) = Jph × 1.23 / Pin × FE × 100
  6. Estimate H2 from Jph using Faraday's law: H2 = Jph × 18.64 × FE
  7. Add literature-based synthetic rows for common PEC materials

All estimated/synthetic values are tagged in 'Data_Source' column:
  'original'   — unchanged from source
  'estimated'  — physics-derived from measured Jph
  'synthetic'  — new rows based on published material ranges
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
IN_PATH  = Path("/Users/custom/files/pec_dataset.csv")
OUT_PATH = Path("/Users/custom/files/pec_dataset_expanded.csv")

# ── 1. Known bandgaps (eV) by material keyword ────────────────────────────────
# Values from well-established PEC literature / semiconducting property tables

BANDGAP_MAP = {
    # Titanates
    "tio2":        (3.2, 3.2),   # anatase dominant in PEC
    "rutile":      (3.0, 3.0),
    "anatase":     (3.2, 3.2),
    # Vanadates
    "bivo4":       (2.4, 2.5),
    # Iron oxides
    "fe2o3":       (2.0, 2.2),
    "alpha-fe2o3": (2.1, 2.1),
    "feooh":       (2.0, 2.2),
    "fe2tio5":     (2.2, 2.3),
    # Tungstates
    "wo3":         (2.6, 2.8),
    "bi2wo6":      (2.7, 2.8),
    "bi2moo6":     (2.6, 2.8),
    # Zinc compounds
    "zno":         (3.2, 3.4),
    "znfe2o4":     (1.9, 2.1),
    "znse":        (2.6, 2.7),
    # Copper compounds
    "cu2o":        (1.9, 2.1),
    "cuo":         (1.4, 1.7),
    "cubiO4":      (1.5, 1.8),
    "cubi2o4":     (1.5, 1.7),
    "cufe2o4":     (1.6, 1.9),
    # Nitrides / oxynitrides
    "gan":         (3.4, 3.4),
    "ta3n5":       (2.0, 2.1),
    "tao n":       (2.4, 2.5),
    "ingaN":       (2.0, 3.0),
    "latan":       (2.0, 2.1),
    # Carbon nitride
    "g-c3n4":      (2.6, 2.8),
    "c3n4":        (2.6, 2.8),
    "graphitic":   (2.7, 2.7),
    # Chalcogenides
    "cds":         (2.4, 2.4),
    "cdse":        (1.7, 1.7),
    "ws2":         (1.8, 2.0),
    "mos2":        (1.8, 1.9),
    "nis2":        (0.4, 0.5),
    "bi2s3":       (1.3, 1.4),
    "sb2s3":       (1.7, 1.8),
    "ni-sns2":     (0.5, 0.7),
    # Silicon
    "silicon":     (1.1, 1.1),
    "n-si":        (1.1, 1.1),
    "p-si":        (1.1, 1.1),
    "a-si":        (1.6, 1.8),   # amorphous
    "si":          (1.1, 1.1),
    # Bismuth compounds
    "bi2o3":       (2.5, 2.9),
    "bifeo3":      (2.3, 2.7),
    "bioi":        (1.8, 1.9),
    "bi2fe4o9":    (2.0, 2.2),
    # Stannates
    "sno2":        (3.5, 3.8),
    "batio3":      (3.0, 3.2),
    # Gallates / phosphates
    "gap":         (2.3, 2.3),
    "gaas":        (1.4, 1.4),
    "inp":         (1.3, 1.3),
    # Others
    "cofe2o4":     (1.3, 1.6),
    "nife2o4":     (1.6, 1.9),
    "graphene":    (0.0, 0.1),
    "rgo":         (0.0, 0.1),
    "reduced graphene": (0.0, 0.1),
}

def _fill_bandgap(material: str, current_bg) -> float:
    if pd.notna(current_bg):
        try:
            return float(current_bg)
        except (ValueError, TypeError):
            pass
    if pd.isna(material):
        return np.nan
    m_lower = str(material).lower()
    for key, (lo, hi) in BANDGAP_MAP.items():
        if key in m_lower:
            return round(RNG.uniform(lo, hi), 2)
    return np.nan


# ── 2. pH from electrolyte ────────────────────────────────────────────────────

def _fill_ph(electrolyte: str, current_ph) -> float:
    if pd.notna(current_ph):
        try:
            v = float(current_ph)
            if 0 <= v <= 14:
                return v
        except (ValueError, TypeError):
            pass
    if pd.isna(electrolyte):
        return np.nan
    e = str(electrolyte).lower()
    if any(x in e for x in ["koh", "naoh", "lioh"]):
        return round(RNG.uniform(13.0, 14.0), 1)
    if any(x in e for x in ["h2so4", "hcl", "hno3", "h3po4"]):
        return round(RNG.uniform(0.0, 1.5), 1)
    if any(x in e for x in ["na2so4", "k2so4", "mgso4"]):
        return round(RNG.uniform(5.8, 7.2), 1)
    if any(x in e for x in ["pbs", "phosphate buffer saline"]):
        return round(RNG.uniform(7.0, 7.5), 1)
    if any(x in e for x in ["kpi", "potassium phosphate", "k2hpo4", "kh2po4"]):
        return round(RNG.uniform(6.5, 7.5), 1)
    if any(x in e for x in ["kbi", "potassium borate", "borate"]):
        return round(RNG.uniform(8.8, 9.5), 1)
    if any(x in e for x in ["na2hpo4", "phosphate"]):
        return round(RNG.uniform(6.5, 8.0), 1)
    if any(x in e for x in ["khco3", "nabicarbonate", "bicarbonate"]):
        return round(RNG.uniform(8.0, 9.0), 1)
    if any(x in e for x in ["neutral", "water"]):
        return 7.0
    return np.nan


# ── 3. Light intensity for AM 1.5G ───────────────────────────────────────────

_AM15_KEYWORDS = {
    "am 1.5g", "am1.5g", "am 1.5", "am1.5",
    "simulated solar", "solar simulator", "solar simulation",
    "1 sun", "1sun", "simulated sunlight", "solar illumination",
}

def _fill_light_intensity(illum_type: str, current_val) -> float:
    if pd.notna(current_val):
        try:
            v = float(current_val)
            if v > 0:
                return v
        except (ValueError, TypeError):
            pass
    if pd.isna(illum_type):
        return np.nan
    t = str(illum_type).lower().strip()
    if any(kw in t for kw in _AM15_KEYWORDS):
        return 100.0
    return np.nan


# ── 4. STH from Jph (physics formula) ────────────────────────────────────────

def _estimate_sth(jph: float, pin: float, bias: float) -> float:
    """
    STH (%) = Jph × 1.23 / Pin × FE × 100
    Valid approximation when:
      - Pin in mW/cm²
      - Jph in mA/cm²
      - Faradaic efficiency assumed 0.75–0.98 (add noise)
    For bias ≠ 0 this becomes ABPE, but we still use it as a
    physics-consistent estimate with reduced FE range.
    """
    if jph <= 0 or pin <= 0:
        return np.nan
    # Faradaic efficiency: slightly lower when biased (cathodic losses)
    if abs(bias) > 0.1:
        fe = RNG.uniform(0.55, 0.85)
    else:
        fe = RNG.uniform(0.75, 0.98)
    sth = jph * 1.23 / pin * fe * 100.0
    # Add small multiplicative noise (±8%) to reflect real measurement variability
    sth *= RNG.uniform(0.92, 1.08)
    return round(float(np.clip(sth, 0.01, 30.0)), 3)


# ── 5. H2 from Jph (Faraday's law) ───────────────────────────────────────────

def _estimate_h2(jph: float) -> float:
    """
    H2 (µmol/h/cm²) = Jph (mA/cm²) × 3600 / (2 × 96485) × 1000 × FE
                     ≈ Jph × 18.64 × FE
    Faradaic efficiency FE ~ 0.6–0.95 depending on catalyst quality.
    """
    if jph <= 0:
        return np.nan
    fe = RNG.uniform(0.60, 0.95)
    h2 = jph * 18.64 * fe
    h2 *= RNG.uniform(0.88, 1.12)
    return round(float(np.clip(h2, 0.01, 5000.0)), 2)


# ── 6. Main filling function ──────────────────────────────────────────────────

def fill_existing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Data_Source"] = "original"

    filled_bg = filled_ph = filled_temp = filled_pin = filled_sth = filled_h2 = 0

    for idx in df.index:
        row = df.loc[idx]

        # Bandgap
        new_bg = _fill_bandgap(row.get("Material System"), row.get("Bandgap (eV)"))
        if pd.notna(new_bg) and pd.isna(row.get("Bandgap (eV)")):
            df.at[idx, "Bandgap (eV)"] = new_bg
            df.at[idx, "Data_Source"] = "estimated"
            filled_bg += 1

        # pH
        new_ph = _fill_ph(row.get("Electrolyte"), row.get("pH"))
        if pd.notna(new_ph) and pd.isna(row.get("pH")):
            df.at[idx, "pH"] = new_ph
            if df.at[idx, "Data_Source"] == "original":
                df.at[idx, "Data_Source"] = "estimated"
            filled_ph += 1

        # Temperature (standard lab = 298 K if not specified)
        if pd.isna(row.get("Temperature (K)")):
            df.at[idx, "Temperature (K)"] = 298.0
            if df.at[idx, "Data_Source"] == "original":
                df.at[idx, "Data_Source"] = "estimated"
            filled_temp += 1

        # Light intensity for AM 1.5G rows
        new_pin = _fill_light_intensity(row.get("Illumination Type"), row.get("Light Intensity (mW/cm²)"))
        if pd.notna(new_pin) and pd.isna(row.get("Light Intensity (mW/cm²)")):
            df.at[idx, "Light Intensity (mW/cm²)"] = new_pin
            if df.at[idx, "Data_Source"] == "original":
                df.at[idx, "Data_Source"] = "estimated"
            filled_pin += 1

        # Re-read updated light intensity
        pin = df.at[idx, "Light Intensity (mW/cm²)"]
        jph_raw = row.get("Photocurrent Density (mA/cm²)")
        bias_raw = row.get("Applied Bias (V vs RHE)")

        try:
            jph = float(jph_raw)
        except (TypeError, ValueError):
            jph = np.nan
        try:
            bias = float(bias_raw) if pd.notna(bias_raw) else 0.0
        except (TypeError, ValueError):
            bias = 0.0
        try:
            pin_f = float(pin)
        except (TypeError, ValueError):
            pin_f = np.nan

        # STH estimate
        if pd.isna(row.get("STH Efficiency (%)")) and pd.notna(jph) and jph > 0:
            if pd.notna(pin_f):
                new_sth = _estimate_sth(jph, pin_f, bias)
            else:
                # Assume 100 mW/cm² for standard illumination
                new_sth = _estimate_sth(jph, 100.0, bias)
            if pd.notna(new_sth):
                df.at[idx, "STH Efficiency (%)"] = new_sth
                if df.at[idx, "Data_Source"] == "original":
                    df.at[idx, "Data_Source"] = "estimated"
                filled_sth += 1

        # H2 estimate
        if pd.isna(row.get("Hydrogen Evolution Rate (µmol h⁻¹ cm⁻²)")) and pd.notna(jph) and jph > 0:
            new_h2 = _estimate_h2(jph)
            if pd.notna(new_h2):
                df.at[idx, "Hydrogen Evolution Rate (µmol h⁻¹ cm⁻²)"] = new_h2
                if df.at[idx, "Data_Source"] == "original":
                    df.at[idx, "Data_Source"] = "estimated"
                filled_h2 += 1

    print(f"  Filled bandgap:        {filled_bg}")
    print(f"  Filled pH:             {filled_ph}")
    print(f"  Filled temperature:    {filled_temp}")
    print(f"  Filled light intensity:{filled_pin}")
    print(f"  Estimated STH:         {filled_sth}")
    print(f"  Estimated H2:          {filled_h2}")
    return df


# ── 7. Synthetic rows based on published PEC literature ranges ────────────────

# Each entry: (material, bandgap, electrolyte, pH, illum, pin,
#              jph_range, bias, cocatalyst, nanostructure, morphology,
#              synth_method, pe_type, notes)
# Jph ranges sourced from review papers:
#   - Dias et al., Chem Soc Rev 2016 (Fe2O3, WO3, BiVO4)
#   - Tamirat et al., Nanoscale Horiz 2016 (Fe2O3)
#   - Kim & Choi, Solar Energy Materials 2014 (BiVO4)
#   - Turner et al., MRS Bulletin 2011 (GaN, Si tandems)

SYNTHETIC_TEMPLATES = [
    # ── BiVO4 variants ────────────────────────────────────────────────────────
    ("BiVO4", 2.4, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.8, 3.5), 1.23,
     "None", "nanoparticle", "nanoparticle", "spin coating", "photoanode",
     "W-doped BiVO4"),
    ("BiVO4", 2.4, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (1.5, 4.5), 1.23,
     "FeOOH", "nanoparticle", "nanoparticle", "electrodeposition", "photoanode",
     "BiVO4 with FeOOH overlayer"),
    ("BiVO4", 2.4, "0.1 M KPi", 7.0, "AM 1.5G", 100.0, (2.0, 6.0), 1.23,
     "NiOOH", "nanostructure", "nanoporous", "electrodeposition", "photoanode",
     "BiVO4 with NiOOH cocatalyst"),
    ("BiVO4", 2.4, "1 M KBi", 9.2, "AM 1.5G", 100.0, (1.8, 5.5), 1.23,
     "CoOx", "thin film", "thin film", "spray pyrolysis", "photoanode",
     "BiVO4 with CoOx"),
    ("BiVO4", 2.5, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (2.5, 7.0), 1.23,
     "NiCo2O4", "nanostructure", "nanostructured", "hydrothermal", "photoanode",
     "Mo-doped BiVO4 with NiCo2O4"),
    ("BiVO4", 2.4, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (3.0, 7.5), 1.23,
     "Pt", "nanoporous", "nanoporous", "electrodeposition", "photoanode",
     "Nanoporous BiVO4 with Pt"),
    ("BiVO4", 2.4, "0.1 M Na2SO4", 6.8, "AM 1.5G", 100.0, (1.2, 4.0), 1.23,
     "None", "thin film", "thin film", "chemical bath deposition", "photoanode",
     "Plain BiVO4 thin film"),
    ("WO3/BiVO4", 2.5, "0.1 M KPi", 7.0, "AM 1.5G", 100.0, (2.0, 5.0), 1.23,
     "CoOx", "nanostructure", "bilayer", "electrodeposition", "photoanode",
     "WO3/BiVO4 heterojunction"),
    ("WO3/BiVO4", 2.5, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (3.0, 6.5), 1.23,
     "NiOx", "nanostructure", "bilayer", "hydrothermal", "photoanode",
     "WO3/BiVO4 with NiOx"),

    # ── Fe2O3 / hematite variants ─────────────────────────────────────────────
    ("Fe2O3", 2.1, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.3, 1.5), 1.23,
     "None", "nanorod", "nanorod", "hydrothermal", "photoanode",
     "Pristine hematite nanorod"),
    ("Fe2O3", 2.1, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.5, 2.5), 1.23,
     "IrO2", "nanorod", "nanorod", "hydrothermal", "photoanode",
     "Hematite with IrO2 cocatalyst"),
    ("Fe2O3", 2.1, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.8, 3.0), 1.23,
     "CoOx", "nanoparticle", "nanoparticle", "spray pyrolysis", "photoanode",
     "Ti-doped Fe2O3 with CoOx"),
    ("Fe2O3", 2.1, "1 M KOH", 14.0, "AM 1.5G", 100.0, (0.4, 2.0), 1.23,
     "None", "nanotube", "nanotube", "anodization", "photoanode",
     "Fe2O3 nanotube array"),
    ("alpha-Fe2O3", 2.1, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.6, 2.8), 1.23,
     "CoFeOx", "nanostructure", "dendritic", "APCVD", "photoanode",
     "Dendritic alpha-Fe2O3"),
    ("alpha-Fe2O3", 2.1, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (1.0, 4.0), 1.23,
     "Ga2O3", "thin film", "thin film", "ALD", "photoanode",
     "ALD Fe2O3 with Ga2O3 passivation"),

    # ── TiO2 variants ─────────────────────────────────────────────────────────
    ("TiO2", 3.2, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (0.3, 1.2), 0.0,
     "None", "nanorod", "nanorod", "hydrothermal", "photoanode",
     "TiO2 nanorod in H2SO4"),
    ("TiO2", 3.2, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.5, 2.0), 0.0,
     "Pt", "nanotube", "nanotube", "anodization", "photoanode",
     "TiO2 nanotube with Pt"),
    ("TiO2", 3.0, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.2, 0.8), 0.0,
     "None", "thin film", "thin film", "sol-gel", "photoanode",
     "N-doped TiO2 thin film"),
    ("TiO2", 3.2, "1 M KOH", 14.0, "AM 1.5G", 100.0, (0.5, 1.8), 0.0,
     "RuO2", "nanoparticle", "nanoparticle", "sol-gel", "photoanode",
     "TiO2 nanoparticle with RuO2"),
    ("TiO2/Fe2O3", 2.6, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.8, 2.5), 1.23,
     "None", "nanostructure", "bilayer", "spray pyrolysis", "photoanode",
     "TiO2/Fe2O3 heterojunction"),

    # ── WO3 variants ──────────────────────────────────────────────────────────
    ("WO3", 2.7, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (1.5, 4.5), 1.23,
     "None", "nanoplate", "nanoplate", "hydrothermal", "photoanode",
     "WO3 nanoplate in H2SO4"),
    ("WO3", 2.7, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (2.0, 5.5), 1.23,
     "RuO2", "nanorod", "nanorod", "hydrothermal", "photoanode",
     "WO3 nanorod with RuO2"),
    ("WO3", 2.7, "1 M HClO4", 0.0, "AM 1.5G", 100.0, (1.0, 3.0), 1.23,
     "None", "thin film", "thin film", "sputtering", "photoanode",
     "WO3 thin film in HClO4"),
    ("WO3", 2.6, "0.1 M H2SO4", 1.0, "AM 1.5G", 100.0, (2.5, 6.0), 1.23,
     "Pt", "nanowire", "nanowire", "CVD", "photoanode",
     "WO3 nanowire with Pt"),

    # ── ZnO variants ──────────────────────────────────────────────────────────
    ("ZnO", 3.3, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.5, 2.5), 0.0,
     "None", "nanorod", "nanorod", "hydrothermal", "photoanode",
     "ZnO nanorod array"),
    ("ZnO", 3.3, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.3, 1.5), 0.0,
     "CdS", "nanorod", "nanorod", "CBD", "photoanode",
     "ZnO/CdS core-shell nanorod"),
    ("ZnO", 3.2, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.8, 3.0), 0.0,
     "Au", "nanoparticle", "nanoparticle", "chemical bath deposition", "photoanode",
     "Au-decorated ZnO nanoparticle"),

    # ── Cu2O variants ─────────────────────────────────────────────────────────
    ("Cu2O", 2.0, "1 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.5, 3.5), 0.0,
     "None", "thin film", "thin film", "electrodeposition", "photocathode",
     "Cu2O photocathode"),
    ("Cu2O", 2.0, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (1.0, 5.0), 0.0,
     "Pt", "thin film", "thin film", "electrodeposition", "photocathode",
     "Cu2O with ALD TiO2 + Pt"),
    ("Cu2O", 2.0, "1 M KOH", 14.0, "AM 1.5G", 100.0, (0.8, 4.0), 0.0,
     "RuOx", "nanostructure", "nanostructured", "electrodeposition", "photocathode",
     "Cu2O with RuOx protection"),

    # ── GaN-based ─────────────────────────────────────────────────────────────
    ("GaN", 3.4, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (5.0, 18.0), 0.0,
     "Pt", "nanowire", "nanowire", "MBE", "photoanode",
     "GaN nanowire with Pt"),
    ("GaN", 3.4, "1 M HBr", 0.5, "AM 1.5G", 100.0, (8.0, 22.0), 0.0,
     "RuO2", "nanostructure", "nanostructured", "MOCVD", "photoanode",
     "InGaN nanowire with Rh/Cr2O3 cocatalyst"),
    ("GaN", 3.4, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (10.0, 20.0), 0.0,
     "NiCoOx", "nanowire", "nanowire", "MBE", "photoanode",
     "GaN nanowire WxS1-x passivation"),

    # ── Ta3N5 variants ────────────────────────────────────────────────────────
    ("Ta3N5", 2.1, "1 M KOH", 14.0, "AM 1.5G", 100.0, (0.3, 2.0), 1.0,
     "CoOx", "thin film", "thin film", "nitridation", "photoanode",
     "Ta3N5 with CoOx cocatalyst"),
    ("Ta3N5", 2.1, "1 M KOH", 14.0, "AM 1.5G", 100.0, (0.5, 3.5), 1.0,
     "IrO2", "nanorod", "nanorod", "hydrothermal+nitridation", "photoanode",
     "Ta3N5 nanorod with IrO2"),
    ("Ta3N5", 2.1, "1 M KOH", 14.0, "AM 1.5G", 100.0, (0.4, 2.5), 1.0,
     "Ni(OH)2", "nanoparticle", "nanoparticle", "nitridation", "photoanode",
     "Ta3N5 with Ni(OH)2"),

    # ── Silicon-based ─────────────────────────────────────────────────────────
    ("Silicon", 1.1, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (10.0, 30.0), 0.0,
     "Pt", "nanostructure", "nanowire", "wet etching", "photocathode",
     "n+p-Si with Pt nanoparticle"),
    ("n-Si", 1.1, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (8.0, 25.0), 0.0,
     "MoS2", "nanostructure", "nanostructured", "chemical etching", "photocathode",
     "n-Si with MoS2 electrocatalyst"),
    ("a-Si", 1.7, "0.1 M H2SO4", 1.0, "AM 1.5G", 100.0, (5.0, 18.0), 0.0,
     "CoP", "thin film", "thin film", "PECVD", "photocathode",
     "a-Si:H tandem with CoP"),

    # ── g-C3N4 ────────────────────────────────────────────────────────────────
    ("g-C3N4", 2.7, "0.1 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.1, 1.0), 0.0,
     "None", "thin film", "thin film", "thermal condensation", "photoanode",
     "g-C3N4 film"),
    ("g-C3N4", 2.7, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.3, 2.0), 0.0,
     "Pt", "nanostructure", "nanosheets", "exfoliation", "photoanode",
     "g-C3N4 nanosheets with Pt"),
    ("g-C3N4/ZnO", 2.8, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.5, 2.5), 0.0,
     "None", "nanocomposite", "nanocomposite", "hydrothermal", "photoanode",
     "g-C3N4/ZnO heterostructure"),

    # ── BiFeO3 / perovskites ──────────────────────────────────────────────────
    ("BiFeO3", 2.5, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.1, 0.8), 1.23,
     "None", "thin film", "thin film", "sol-gel", "photoanode",
     "BiFeO3 thin film"),
    ("BaTiO3/Cu2O", 3.1, "0.1 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.1, 0.5), 1.23,
     "None", "nanocomposite", "nanocomposite", "co-precipitation", "photoanode",
     "BaTiO3/Cu2O heterojunction"),

    # ── CuO ───────────────────────────────────────────────────────────────────
    ("CuO", 1.5, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.2, 1.5), 0.0,
     "None", "nanorod", "nanorod", "hydrothermal", "photocathode",
     "CuO nanorod photocathode"),
    ("CuO", 1.5, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.5, 2.5), 0.0,
     "Pt", "nanoparticle", "nanoparticle", "chemical bath deposition", "photocathode",
     "CuO with Pt cocatalyst"),

    # ── Fe2TiO5 / mixed oxides ─────────────────────────────────────────────────
    ("Fe2TiO5", 2.2, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.2, 1.0), 1.23,
     "None", "nanostructure", "nanostructured", "hydrothermal", "photoanode",
     "Fe2TiO5 pseudobrookite"),
    ("ZnFe2O4", 2.0, "1 M NaOH", 13.5, "AM 1.5G", 100.0, (0.1, 0.8), 1.23,
     "None", "nanoparticle", "nanoparticle", "co-precipitation", "photoanode",
     "ZnFe2O4 spinel"),
    ("WO3/BiVO4", 2.5, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (2.5, 6.0), 1.23,
     "FeOOH/NiOOH", "bilayer", "bilayer", "electrodeposition", "photoanode",
     "WO3/BiVO4 with dual FeOOH/NiOOH"),

    # ── Chalcogenide photocathodes ────────────────────────────────────────────
    ("CuInS2", 1.5, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (5.0, 18.0), 0.0,
     "Pt", "thin film", "thin film", "electrodeposition", "photocathode",
     "CuInS2 photocathode"),
    ("CdTe", 1.5, "0.5 M H2SO4", 0.3, "AM 1.5G", 100.0, (8.0, 22.0), 0.0,
     "Pt", "thin film", "thin film", "CBD", "photocathode",
     "CdTe photocathode"),
    ("CuGaSe2", 1.7, "0.1 M H2SO4", 1.0, "AM 1.5G", 100.0, (3.0, 12.0), 0.0,
     "Pt", "thin film", "thin film", "co-evaporation", "photocathode",
     "CuGaSe2 photocathode"),

    # ── Bi-based narrow-gap ───────────────────────────────────────────────────
    ("BiOI", 1.85, "0.1 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.5, 2.5), 1.23,
     "None", "nanoplate", "nanoplate", "solvothermal", "photoanode",
     "BiOI nanoplate"),
    ("Bi2MoO6", 2.7, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0, (0.1, 0.8), 1.23,
     "None", "nanoplate", "nanoplate", "hydrothermal", "photoanode",
     "Bi2MoO6 nanoplate"),
]

# Additional doping variants for high-coverage materials
BIVO4_DOPINGS = [
    ("Mo-doped", 2.4, (2.0, 5.0)),
    ("W-doped",  2.45, (1.5, 4.5)),
    ("Co-doped", 2.4, (1.0, 3.5)),
    ("Sn-doped", 2.42, (1.8, 4.0)),
    ("Nb-doped", 2.43, (2.0, 4.8)),
    ("Zr-doped", 2.41, (1.5, 3.8)),
]

FE2O3_DOPINGS = [
    ("Ti-doped",  2.1, (0.5, 2.5)),
    ("Sn-doped",  2.1, (0.4, 2.0)),
    ("Pt-doped",  2.1, (0.6, 2.8)),
    ("Si-doped",  2.1, (0.5, 2.2)),
    ("Mn-doped",  2.1, (0.3, 1.5)),
]


def _make_synthetic_row(template: tuple, row_id: int) -> dict:
    (material, bandgap, electrolyte, ph, illum, pin,
     jph_range, bias, cocatalyst, nanostructure, morphology,
     synth_method, pe_type, notes) = template

    jph = float(RNG.uniform(*jph_range))
    # Small jitter on bandgap (±0.05 eV measurement uncertainty)
    bg  = round(bandgap + float(RNG.uniform(-0.05, 0.05)), 2)
    # pH jitter ±0.3
    ph_v = round(ph + float(RNG.uniform(-0.3, 0.3)), 1)
    ph_v = max(0.0, min(14.0, ph_v))
    # Light intensity jitter ±2%
    pin_v = round(pin * float(RNG.uniform(0.98, 1.02)), 1)
    # Temperature: mostly 298 ± 3 K
    temp = round(float(RNG.uniform(295, 301)), 0)

    sth = _estimate_sth(jph, pin_v, bias)
    h2  = _estimate_h2(jph)

    return {
        "№":                      10000 + row_id,
        "Publication ID":         f"synthetic_{row_id:04d}",
        "Year":                   int(RNG.integers(2015, 2024)),
        "Title":                  f"Synthetic entry: {notes}",
        "Material System":        material,
        "Composition / Doping":   notes,
        "Bandgap (eV)":           bg,
        "Synthesis Method":       synth_method,
        "Morphology":             morphology,
        "Nanostructure":          nanostructure,
        "Cocatalyst":             cocatalyst,
        "Protective Layer":       np.nan,
        "Photoelectrode Type":    pe_type,
        "Thickness (nm)":         np.nan,
        "Electrolyte":            electrolyte,
        "pH":                     ph_v,
        "Illumination Type":      illum,
        "Wavelength (nm)":        np.nan,
        "Light Intensity (mW/cm²)": pin_v,
        "Applied Bias (V vs RHE)": bias,
        "Temperature (K)":        temp,
        "Photocurrent Density (mA/cm²)": round(jph, 3),
        "Onset Potential (V)":    np.nan,
        "STH Efficiency (%)":     sth,
        "ABPE (%)":               np.nan,
        "Hydrogen Evolution Rate (µmol h⁻¹ cm⁻²)": h2,
        "Stability Time (h)":     np.nan,
        "Units Normalized":       "Yes",
        "Performance Class":      np.nan,
        "Notes":                  f"[SYNTHETIC] {notes}",
        "Data_Source":            "synthetic",
    }


def build_synthetic_rows() -> pd.DataFrame:
    rows = []
    rid = 1

    # From SYNTHETIC_TEMPLATES: 2 jitter copies per template
    for template in SYNTHETIC_TEMPLATES:
        for _ in range(2):
            rows.append(_make_synthetic_row(template, rid))
            rid += 1

    # BiVO4 doping variants
    for doping, bg, jph_range in BIVO4_DOPINGS:
        for cocatalyst in ["FeOOH", "NiOOH", "CoOx", "None"]:
            template = (
                "BiVO4", bg, "0.5 M Na2SO4", 6.8, "AM 1.5G", 100.0,
                jph_range, 1.23, cocatalyst, "nanoparticle", "nanoparticle",
                "electrodeposition", "photoanode", f"BiVO4 {doping} with {cocatalyst}",
            )
            rows.append(_make_synthetic_row(template, rid))
            rid += 1

    # Fe2O3 doping variants
    for doping, bg, jph_range in FE2O3_DOPINGS:
        for cocatalyst in ["CoOx", "IrO2", "None"]:
            template = (
                "Fe2O3", bg, "1 M NaOH", 13.5, "AM 1.5G", 100.0,
                jph_range, 1.23, cocatalyst, "nanorod", "nanorod",
                "spray pyrolysis", "photoanode", f"Fe2O3 {doping} with {cocatalyst}",
            )
            rows.append(_make_synthetic_row(template, rid))
            rid += 1

    print(f"  Generated {len(rows)} synthetic rows")
    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

_NUMERIC_COLS = [
    "Bandgap (eV)", "pH", "Temperature (K)", "Light Intensity (mW/cm²)",
    "Applied Bias (V vs RHE)", "Photocurrent Density (mA/cm²)",
    "STH Efficiency (%)", "Hydrogen Evolution Rate (µmol h⁻¹ cm⁻²)",
    "Thickness (nm)", "ABPE (%)", "Stability Time (h)", "Wavelength (nm)",
    "Onset Potential (V)",
]

def main():
    print(f"[1/4] Loading {IN_PATH}")
    df = pd.read_csv(IN_PATH)
    print(f"      Original: {df.shape[0]} rows × {df.shape[1]} cols")

    # Force numeric columns to float so we can assign float values
    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add Data_Source column
    df["Data_Source"] = "original"

    print("\n[2/4] Filling existing rows with physics estimates...")
    df_filled = fill_existing(df)

    print("\n[3/4] Generating synthetic rows from literature ranges...")
    df_synth = build_synthetic_rows()

    print("\n[4/4] Combining and saving...")
    df_all = pd.concat([df_filled, df_synth], ignore_index=True)

    # Final stats
    sth_count = df_all["STH Efficiency (%)"].notna().sum()
    h2_count  = df_all["Hydrogen Evolution Rate (µmol h⁻¹ cm⁻²)"].notna().sum()
    pc_count  = df_all["Photocurrent Density (mA/cm²)"].notna().sum()
    bg_count  = df_all["Bandgap (eV)"].notna().sum()

    print(f"\n  Total rows:          {len(df_all)}")
    print(f"  Photocurrent filled: {pc_count} ({pc_count/len(df_all)*100:.0f}%)")
    print(f"  STH filled:          {sth_count} ({sth_count/len(df_all)*100:.0f}%)")
    print(f"  H2 filled:           {h2_count} ({h2_count/len(df_all)*100:.0f}%)")
    print(f"  Bandgap filled:      {bg_count} ({bg_count/len(df_all)*100:.0f}%)")

    print("\n  Data_Source breakdown:")
    print(df_all["Data_Source"].value_counts().to_string())

    df_all.to_csv(OUT_PATH, index=False)
    print(f"\n  Saved → {OUT_PATH}")


if __name__ == "__main__":
    main()
