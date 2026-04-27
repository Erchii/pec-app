import { useState } from "react";
import "./index.css";

const API_URL = import.meta.env.VITE_API_URL;

const navItems = ["Dashboard", "Prediction", "Results", "About"];

const modelMetrics = {
  linearRegression: {
    validation: { mae: 10.078, rmse: 30.8279, r2: -20.9079 },
    test: { mae: 18.2108, rmse: 70.5412, r2: -165.2584 },
  },
  randomForest: {
    validation: { mae: 2.0658, rmse: 4.4518, r2: 0.5431 },
    test: { mae: 2.337, rmse: 4.9406, r2: 0.1844 },
  },
};

const topFeatures = [
  ["Cocatalyst_Ru15 (molecular catalyst)", 0.204409],
  ["Material System_Polymeric carbon nitride (CN)", 0.188878],
  ["Synthesis Method_dipping and thermal treatment", 0.169247],
  ["Synthesis Method_One-pot Hydrothermal", 0.052814],
  ["Bandgap (eV)", 0.051966],
  ["Material System_Silicon", 0.031997],
  ["Cocatalyst_NiFe", 0.027731],
  ["Applied Bias (V vs RHE)", 0.01047],
];

const MATERIALS = [
  "BiVO4","TiO2","Fe2O3","WO3","ZnO","g-C3N4","CdS","Cu2O","GaN","InGaN",
  "Silicon","Ta3N5","TaON","SrTiO3","BaTiO3","NiO","CuBi2O4","CuFeO2",
  "Bi2WO6","SnO2","MoS2","CdSe","ZnFe2O4","LaFeO3","CuO",
];

const ELECTROLYTES = [
  "KOH","NaOH","Na2SO4","H2SO4","HCl","Na2SO3","KPi","PBS",
  "0.1 M KOH","0.5 M Na2SO4","1 M NaOH","0.5 M H2SO4",
  "Na2SO4/Na2SO3","KH2PO4","K2HPO4",
];

const COCATALYSTS = [
  "None","Pt","RuO2","IrO2","Co-Pi","FeOOH","NiFeOx","NiOx",
  "MnOx","CoOx","Au","Ag","CoPi","NiFe-LDH","FeOOH/Co-Pi",
  "Rh","MoS2","WS2","Ni","Cu",
];

const MORPHOLOGIES = [
  "Thin Film","Nanorod","Nanowire","Nanosheet","Nanoparticle","Nanotube",
  "Nanoporous","Nanodot","Nanoflower","Bulk","Mesoporous","Hollow sphere",
  "Nanoplatelets","Quantum dot","Core-shell",
];

const NANOSTRUCTURES = [
  "Heterojunction","Core-shell","Porous","Bulk","Type-II heterojunction",
  "Z-scheme","p-n junction","Homojunction","Quantum dot sensitized",
  "Nanocomposite","Single crystal","Polycrystalline",
];

const SYNTHESIS_METHODS = [
  "Hydrothermal","Solvothermal","Sol-gel","Electrodeposition",
  "Chemical vapor deposition","Atomic layer deposition","Spray pyrolysis",
  "Co-precipitation","Thermal oxidation","Screen printing","Doctor blade",
  "Spin coating","Dip coating","Electrospinning","One-pot Hydrothermal",
];

const initialForm = {
  material: "BiVO4",
  bandgap: "2.4",
  morphology: "Thin Film",
  nanostructure: "Heterojunction",
  cocatalyst: "None",
  electrolyte: "Na2SO4",
  ph: "7.0",
  lightIntensity: "100",
  appliedBias: "1.23",
  temperature: "298",
  thickness: "300",
  synthesisMethod: "Hydrothermal",
  photoelectrodeType: "photoanode",
  protectiveLayer: "",
};

function Sidebar({ activeTab, setActiveTab }) {
  const icons = { Dashboard: "≡", Prediction: "⚡", Results: "📊", About: "ⓘ" };
  return (
    <aside className="sidebar">
      <div className="logo-block">
        <div className="logo-icon">✦</div>
        <div>
          <h1 className="logo-title">PEC-ML</h1>
          <p className="logo-subtitle">Prediction System</p>
        </div>
      </div>
      <nav className="nav-list">
        {navItems.map((item) => (
          <button
            key={item}
            className={`nav-btn ${activeTab === item ? "active" : ""}`}
            onClick={() => setActiveTab(item)}
          >
            <span className="nav-icon">{icons[item]}</span>
            <span>{item}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-divider" />
      <div className="dataset-card">
        <h3>Dataset Info</h3>
        <p>Source: Web of Science + Literature</p>
        <div className="dataset-mini-grid">
          <div className="mini-stat">
            <span className="mini-value">676</span>
            <span className="mini-label">Rows</span>
          </div>
          <div className="mini-stat">
            <span className="mini-value">25+</span>
            <span className="mini-label">Materials</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

function SummaryCard({ icon, title, value, subtitle, accent = "blue" }) {
  return (
    <div className={`glass-card summary-card ${accent}`}>
      <div className="summary-icon">{icon}</div>
      <div>
        <p className="card-label">{title}</p>
        <h3 className="summary-value">{value}</h3>
        <p className="card-muted">{subtitle}</p>
      </div>
    </div>
  );
}

function FeatureBar({ label, value, max }) {
  return (
    <div className="feature-row">
      <div className="feature-row-top">
        <span>{label}</span>
        <span>{value.toFixed(4)}</span>
      </div>
      <div className="feature-track">
        <div className="feature-fill" style={{ width: `${(value / max) * 100}%` }} />
      </div>
    </div>
  );
}

function DatalistInput({ id, name, value, onChange, list, placeholder, type = "text", min, max, step }) {
  const listId = `dl-${name}`;
  return (
    <>
      <input
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        list={listId}
        placeholder={placeholder}
        type={type}
        min={min}
        max={max}
        step={step}
        autoComplete="off"
      />
      <datalist id={listId}>
        {list.map((opt) => <option key={opt} value={opt} />)}
      </datalist>
    </>
  );
}

function PredictionForm({ form, handleChange, runPrediction, resetForm, loading, compact }) {
  return (
    <div className="form-grid">
      {/* Required fields */}
      <label>
        Material *
        <DatalistInput name="material" value={form.material} onChange={handleChange}
          list={MATERIALS} placeholder="e.g. BiVO4" />
      </label>

      <label>
        Electrolyte *
        <DatalistInput name="electrolyte" value={form.electrolyte} onChange={handleChange}
          list={ELECTROLYTES} placeholder="e.g. Na2SO4" />
      </label>

      <label>
        pH *
        <input name="ph" type="number" value={form.ph} onChange={handleChange}
          min="0" max="14" step="0.1" />
      </label>

      <label>
        Applied Bias (V vs RHE) *
        <input name="appliedBias" type="number" value={form.appliedBias} onChange={handleChange}
          min="-2" max="5" step="0.01" />
      </label>

      {/* Optional fields */}
      <label>
        Bandgap (eV)
        <input name="bandgap" type="number" value={form.bandgap} onChange={handleChange}
          min="0.5" max="6.0" step="0.01" placeholder="e.g. 2.4" />
      </label>

      <label>
        Light Intensity (mW/cm²)
        <input name="lightIntensity" type="number" value={form.lightIntensity} onChange={handleChange}
          min="0" max="2000" step="1" />
      </label>

      <label>
        Temperature (K)
        <input name="temperature" type="number" value={form.temperature} onChange={handleChange}
          min="200" max="1500" step="1" />
      </label>

      <label>
        Thickness (nm)
        <input name="thickness" type="number" value={form.thickness} onChange={handleChange}
          min="0" max="100000" step="1" />
      </label>

      <label>
        Morphology
        <DatalistInput name="morphology" value={form.morphology} onChange={handleChange}
          list={MORPHOLOGIES} placeholder="e.g. Thin Film" />
      </label>

      <label>
        Nanostructure
        <DatalistInput name="nanostructure" value={form.nanostructure} onChange={handleChange}
          list={NANOSTRUCTURES} placeholder="e.g. Heterojunction" />
      </label>

      <label>
        Cocatalyst
        <DatalistInput name="cocatalyst" value={form.cocatalyst} onChange={handleChange}
          list={COCATALYSTS} placeholder="e.g. None" />
      </label>

      <label>
        Synthesis Method
        <DatalistInput name="synthesisMethod" value={form.synthesisMethod} onChange={handleChange}
          list={SYNTHESIS_METHODS} placeholder="e.g. Hydrothermal" />
      </label>

      <label>
        Photoelectrode Type
        <select name="photoelectrodeType" value={form.photoelectrodeType} onChange={handleChange}>
          <option value="photoanode">Photoanode</option>
          <option value="photocathode">Photocathode</option>
        </select>
      </label>

      <label>
        Protective Layer
        <input name="protectiveLayer" value={form.protectiveLayer} onChange={handleChange}
          placeholder="e.g. TiO2 (optional)" />
      </label>

      <div className={compact ? "" : "row-actions full-width"} style={compact ? { gridColumn: "1/-1", marginTop: "12px" } : {}}>
        {!compact && (
          <button className="secondary-btn" onClick={resetForm}>Reset</button>
        )}
        <button className={compact ? "predict-btn" : "predict-btn slim"} onClick={runPrediction} disabled={loading}>
          {loading ? "Predicting…" : "🚀 Predict Performance"}
        </button>
      </div>
    </div>
  );
}

function ResultsDisplay({ backendResult, performanceWidth }) {
  if (!backendResult) return null;

  const fmt = (v) => v != null ? Number(v).toFixed(3) : "—";
  const fmtPct = (v) => v != null ? (v * 100).toFixed(0) + "%" : "";
  const score = backendResult.performance_score ?? 0;
  const perfClass = backendResult.performance_class ?? "—";
  const perfColor = perfClass === "HIGH" ? "#5ef0bf" : perfClass === "MEDIUM" ? "#ffca28" : "#ff8891";

  return (
    <>
      <div className="result-top-grid">
        <div className="metric-box cyan">
          <p>Photocurrent Density</p>
          <h2>{fmt(backendResult.Photocurrent?.value)}</h2>
          <span>mA/cm²</span>
          <small>Confidence: {fmtPct(backendResult.Photocurrent?.confidence)}</small>
        </div>
        <div className="metric-box green">
          <p>STH Efficiency</p>
          <h2>{fmt(backendResult.STH?.value)}%</h2>
          <small>Confidence: {fmtPct(backendResult.STH?.confidence)}</small>
        </div>
        <div className="metric-box" style={{ borderColor: "rgba(210,153,34,0.4)" }}>
          <p>H₂ Evolution Rate</p>
          <h2 style={{ color: "#d29922" }}>{fmt(backendResult.H2?.value)}</h2>
          <span>µmol/h/cm²</span>
          <small>Confidence: {fmtPct(backendResult.H2?.confidence)}</small>
        </div>
      </div>
      <div className="performance-box">
        <h4>Performance Class: <span style={{ color: perfColor }}>{perfClass}</span> — Score: {score.toFixed(1)}/100</h4>
        <div className="performance-row">
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${performanceWidth}%`, background: perfColor }} />
          </div>
        </div>
        <p style={{ marginTop: "8px", fontSize: "12px", color: "#8b949e" }}>
          XGBoost + RandomForest ensemble · percentile-based thresholds
        </p>
      </div>
    </>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("Dashboard");
  const [form, setForm] = useState(initialForm);
  const [backendResult, setBackendResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [errorDetails, setErrorDetails] = useState([]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const resetForm = () => {
    setForm(initialForm);
    setBackendResult(null);
    setError("");
    setErrorDetails([]);
  };

  const runPrediction = async () => {
    try {
      setLoading(true);
      setError("");
      setErrorDetails([]);

      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material:            form.material,
          electrolyte:         form.electrolyte,
          pH:                  parseFloat(form.ph),
          bias:                parseFloat(form.appliedBias),
          light_source:        "AM 1.5G",
          bandgap:             form.bandgap ? parseFloat(form.bandgap) : undefined,
          light_intensity:     form.lightIntensity ? parseFloat(form.lightIntensity) : undefined,
          temperature:         form.temperature ? parseFloat(form.temperature) : undefined,
          thickness:           form.thickness ? parseFloat(form.thickness) : undefined,
          morphology:          form.morphology || undefined,
          nanostructure:       form.nanostructure || undefined,
          cocatalyst:          form.cocatalyst || undefined,
          synthesis_method:    form.synthesisMethod || undefined,
          photoelectrode_type: form.photoelectrodeType || undefined,
          protective_layer:    form.protectiveLayer || undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok || data.status === "error") {
        setErrorDetails(data.details || []);
        throw new Error(data.message || "Prediction failed");
      }

      setBackendResult(data);
      setActiveTab("Results");
    } catch (err) {
      setError(err.message || "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  };

  const performanceWidth = backendResult?.performance_score ?? 0;
  const maxImportance = Math.max(...topFeatures.map((item) => item[1]));

  return (
    <div className="app-shell">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="main-panel">
        {error && (
          <div className="glass-card" style={{ marginBottom: "18px", borderColor: "rgba(255,127,138,0.35)" }}>
            <p style={{ color: "#ff9aa3", margin: 0, fontWeight: 700 }}>{error}</p>
            {errorDetails.length > 0 && (
              <div style={{ marginTop: "12px", color: "#ffd5d9" }}>
                {errorDetails.map((item, idx) => (
                  <p key={idx} style={{ margin: "6px 0" }}>• {item}</p>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "Dashboard" && (
          <>
            <section className="hero-section">
              <h2>Machine Learning Prediction System</h2>
              <p>Predict photoelectrochemical water splitting performance using experimental parameters</p>
            </section>

            <section className="summary-grid">
              <SummaryCard icon="🧪" title="Dataset Size" value="676" subtitle="rows after augmentation" accent="blue" />
              <SummaryCard icon="⚡" title="Best CV R²" value="0.557" subtitle="STH · XGBoost" accent="green" />
              <SummaryCard icon="⭐" title="Best Performing" value="BiVO₄" subtitle="Most studied material" accent="yellow" />
            </section>

            <section className="dashboard-grid">
              <div className="glass-card form-card">
                <div className="section-head">
                  <h3>Quick Predict</h3>
                  <p>Enter parameters and click Predict</p>
                </div>
                <PredictionForm
                  form={form} handleChange={handleChange}
                  runPrediction={runPrediction} resetForm={resetForm}
                  loading={loading} compact={true}
                />
              </div>

              <div className="glass-card result-panel">
                <div className="section-head">
                  <h3>Prediction Results</h3>
                  <p>Estimated photoelectrochemical performance</p>
                </div>
                {backendResult
                  ? <ResultsDisplay backendResult={backendResult} performanceWidth={performanceWidth} />
                  : <p style={{ color: "#8b949e" }}>Run a prediction to see results here.</p>
                }
              </div>
            </section>
          </>
        )}

        {activeTab === "Prediction" && (
          <section className="single-page">
            <div className="glass-card">
              <div className="section-head">
                <h3>Full Prediction Form</h3>
                <p>Required fields marked * · optional fields use training-data defaults if left empty</p>
              </div>
              <PredictionForm
                form={form} handleChange={handleChange}
                runPrediction={runPrediction} resetForm={resetForm}
                loading={loading} compact={false}
              />
            </div>
          </section>
        )}

        {activeTab === "Results" && (
          <section className="results-grid">
            <div className="glass-card">
              <div className="section-head"><h3>Input Summary</h3></div>
              <div className="info-stack">
                <div className="info-box"><span>Material</span><strong>{form.material}</strong></div>
                <div className="info-box"><span>Electrolyte</span><strong>{form.electrolyte}</strong></div>
                <div className="info-box"><span>pH / Bias</span><strong>{form.ph} / {form.appliedBias} V</strong></div>
                <div className="info-box"><span>Bandgap</span><strong>{form.bandgap || "auto"} eV</strong></div>
                <div className="info-box"><span>Morphology</span><strong>{form.morphology || "—"}</strong></div>
                <div className="info-box"><span>Cocatalyst</span><strong>{form.cocatalyst || "—"}</strong></div>
                <button className="secondary-btn wide" onClick={() => setActiveTab("Prediction")}>
                  Edit Parameters
                </button>
              </div>
            </div>

            <div className="glass-card">
              <div className="section-head">
                <h3>Prediction Results</h3>
                <p>Estimated photoelectrochemical performance based on selected inputs</p>
              </div>
              {backendResult
                ? <ResultsDisplay backendResult={backendResult} performanceWidth={performanceWidth} />
                : <p style={{ color: "#8b949e" }}>No prediction yet — go to Prediction tab first.</p>
              }
            </div>
          </section>
        )}

        {activeTab === "About" && (
          <section className="about-grid">
            <div className="glass-card about-text">
              <h2>About the Project</h2>
              <p>
                ML-powered prediction system for photoelectrochemical (PEC) water splitting.
                Predicts Photocurrent Density, Solar-to-Hydrogen Efficiency, and H₂ Evolution Rate
                from material and experimental parameters.
              </p>
              <p style={{ marginTop: "12px" }}>
                Dataset: 676 rows (529 original + 147 synthetic) from scientific literature.
                Models: XGBoost + RandomForest ensemble with 5-fold cross-validation.
              </p>
            </div>

            <div className="glass-card">
              <h2>Model Performance (CV R²)</h2>
              <div className="key-features">
                <div className="key-item">Photocurrent Density — XGBoost R²=0.445</div>
                <div className="key-item">STH Efficiency — XGBoost R²=0.557</div>
                <div className="key-item">H₂ Evolution Rate — XGBoost R²=0.364</div>
                <div className="key-item">20 physics-informed features</div>
                <div className="key-item">Percentile-based classification (HIGH/MEDIUM/LOW)</div>
                <div className="key-item">Confidence score per prediction</div>
              </div>
            </div>

            <div className="glass-card full-span">
              <div className="section-head">
                <h3>Model Comparison</h3>
                <p>Regression results from the current PEC dataset</p>
              </div>
              <div className="model-summary-grid">
                <div className="model-summary-card">
                  <h4>Linear Regression</h4>
                  <p>Validation R²: {modelMetrics.linearRegression.validation.r2}</p>
                  <p>Test R²: {modelMetrics.linearRegression.test.r2}</p>
                  <p className="danger-text">Too simple for nonlinear PEC relationships</p>
                </div>
                <div className="model-summary-card">
                  <h4>Random Forest</h4>
                  <p>Validation R²: {modelMetrics.randomForest.validation.r2}</p>
                  <p>Test R²: {modelMetrics.randomForest.test.r2}</p>
                  <p className="success-text">Best current model for this dataset</p>
                </div>
              </div>
            </div>
          </section>
        )}

        <section className="bottom-section">
          <div className="glass-card">
            <div className="section-head">
              <h3>Top Feature Importance</h3>
              <p>Random Forest feature ranking</p>
            </div>
            <div className="feature-list">
              {topFeatures.map(([label, value]) => (
                <FeatureBar key={label} label={label} value={value} max={maxImportance} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
