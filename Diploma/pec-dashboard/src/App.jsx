import { useState } from "react";
import "./index.css";

const API_URL = import.meta.env.VITE_API_URL;

const navItems = ["Dashboard", "Prediction", "Results", "About"];

const datasetInfo = {
  source: "Web of Science",
  materials: 24,
  experiments: 152,
  totalArticles: 400,
  usableRows: 357,
  train: 249,
  validation: 54,
  test: 54,
};

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

const initialForm = {
  material: "BiVO₄ (Bismuth Vanadate)",
  bandgap: "2.40",
  morphology: "Nanorods",
  nanostructure: "Heterojunction",
  cocatalyst: "None",
  electrolyte: "Na₂SO₄ (Sodium Sulfate)",
  ph: "7.0",
  lightIntensity: "100",
  appliedBias: "1.23",
  temperature: "298",
  thickness: "300",
  synthesisMethod: "Hydrothermal",
  photoelectrodeType: "photoanode",
  protectiveLayer: "TiO2",
};

function Sidebar({ activeTab, setActiveTab }) {
  const icons = {
    Dashboard: "≡",
    Prediction: "⚡",
    Results: "📊",
    About: "ⓘ",
  };

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
        <p>Source: {datasetInfo.source}</p>

        <div className="dataset-mini-grid">
          <div className="mini-stat">
            <span className="mini-value">{datasetInfo.materials}</span>
            <span className="mini-label">Materials</span>
          </div>
          <div className="mini-stat">
            <span className="mini-value">{datasetInfo.experiments}</span>
            <span className="mini-label">Experiments</span>
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
        <span>{value.toFixed(6)}</span>
      </div>
      <div className="feature-track">
        <div
          className="feature-fill"
          style={{ width: `${(value / max) * 100}%` }}
        />
      </div>
    </div>
  );
}

function confidenceColor(confidence) {
  if (confidence === "HIGH") return "#5ef0bf";
  if (confidence === "MEDIUM") return "#ffca28";
  if (confidence === "LOW") return "#ff8891";
  return "#93a1c3";
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

  // Strip unicode subscripts so "BiVO₄ (Bismuth Vanadate)" → "BiVO4"
  const cleanMaterial = (s) =>
    s.replace(/[₀₁₂₃₄₅₆₇₈₉]/g, d => "0123456789"["₀₁₂₃₄₅₆₇₈₉".indexOf(d)])
     .replace(/[²³]/g, d => d === "²" ? "2" : "3")
     .split("(")[0].trim();

  const cleanElectrolyte = (s) =>
    s.replace(/[₀₁₂₃₄₅₆₇₈₉]/g, d => "0123456789"["₀₁₂₃₄₅₆₇₈₉".indexOf(d)])
     .replace(/[²³]/g, d => d === "²" ? "2" : "3")
     .split("(")[0].trim();

  const runPrediction = async () => {
    try {
      setLoading(true);
      setError("");
      setErrorDetails([]);

      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material:            cleanMaterial(form.material),
          bandgap:             form.bandgap,
          morphology:          form.morphology,
          nanostructure:       form.nanostructure,
          cocatalyst:          form.cocatalyst,
          electrolyte:         cleanElectrolyte(form.electrolyte),
          pH:                  form.ph,
          bias:                form.appliedBias,
          light_intensity:     form.lightIntensity,
          temperature:         form.temperature,
          thickness:           form.thickness,
          synthesis_method:    form.synthesisMethod,
          photoelectrode_type: form.photoelectrodeType,
          protective_layer:    form.protectiveLayer,
          light_source:        "AM 1.5G",
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

  const displayedPhotocurrent = backendResult
    ? (backendResult.Photocurrent ?? 0)
    : 0;

  const displayedSTH = backendResult
    ? (backendResult.STH ?? 0)
    : 0;

  const displayedH2 = backendResult
    ? (backendResult.H2 ?? 0)
    : 0;

  const performanceClass = backendResult
    ? backendResult.performance_class
    : "LOW";

  const performanceWidth =
    displayedPhotocurrent >= 10
      ? 100
      : Math.max(10, displayedPhotocurrent * 10);

  const maxImportance = Math.max(...topFeatures.map((item) => item[1]));

  return (
    <div className="app-shell">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="main-panel">
        {error && (
          <div
            className="glass-card"
            style={{
              marginBottom: "18px",
              borderColor: "rgba(255,127,138,0.35)",
            }}
          >
            <p style={{ color: "#ff9aa3", margin: 0, fontWeight: 700 }}>{error}</p>

            {errorDetails.length > 0 && (
              <div style={{ marginTop: "12px", color: "#ffd5d9" }}>
                {errorDetails.map((item, idx) => (
                  <p key={idx} style={{ margin: "6px 0" }}>
                    • {item}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "Dashboard" && (
          <>
            <section className="hero-section">
              <h2>Machine Learning Prediction System</h2>
              <p>
                Predict photoelectrochemical water splitting performance using
                experimental parameters
              </p>
            </section>

            <section className="summary-grid">
              <SummaryCard
                icon="🧪"
                title="Total Experiments"
                value="156"
                subtitle="From scientific literature"
                accent="blue"
              />
              <SummaryCard
                icon="⚡"
                title="Average STH Efficiency"
                value="3.87%"
                subtitle="Across all materials"
                accent="green"
              />
              <SummaryCard
                icon="⭐"
                title="Best Performing"
                value="BiVO₄"
                subtitle="STH: 8.12% at 1.23 V vs RHE"
                accent="yellow"
              />
            </section>

            <section className="dashboard-grid">
              <div className="glass-card form-card">
                <div className="section-head">
                  <h3>Enter Experimental Parameters</h3>
                  <p>Input the material and conditions for prediction</p>
                </div>

                <div className="form-grid">
                  <label>
                    Material
                    <select name="material" value={form.material} onChange={handleChange}>
                      <option>BiVO₄ (Bismuth Vanadate)</option>
                      <option>Fe₂O₃ (Hematite)</option>
                      <option>WO₃</option>
                      <option>TiO₂</option>
                      <option>g-C₃N₄</option>
                    </select>
                  </label>

                  <label>
                    Bandgap (eV)
                    <select name="bandgap" value={form.bandgap} onChange={handleChange}>
                      <option>2.40</option>
                      <option>2.10</option>
                      <option>2.70</option>
                      <option>1.95</option>
                    </select>
                  </label>

                  <label>
                    Morphology
                    <select
                      name="morphology"
                      value={form.morphology}
                      onChange={handleChange}
                    >
                      <option>Nanorods</option>
                      <option>Nanosheets</option>
                      <option>Thin Film</option>
                      <option>Nanotubes</option>
                    </select>
                  </label>

                  <label>
                    Nanostructure
                    <select
                      name="nanostructure"
                      value={form.nanostructure}
                      onChange={handleChange}
                    >
                      <option>Heterojunction</option>
                      <option>Core-shell</option>
                      <option>Porous</option>
                      <option>Bulk</option>
                    </select>
                  </label>

                  <label>
                    Cocatalyst
                    <select
                      name="cocatalyst"
                      value={form.cocatalyst}
                      onChange={handleChange}
                    >
                      <option>None</option>
                      <option>NiFeOx</option>
                      <option>Co-Pi</option>
                      <option>Pt</option>
                    </select>
                  </label>

                  <label>
                    Electrolyte
                    <select
                      name="electrolyte"
                      value={form.electrolyte}
                      onChange={handleChange}
                    >
                      <option>Na₂SO₄ (Sodium Sulfate)</option>
                      <option>KOH</option>
                      <option>NaOH</option>
                      <option>H₂SO₄</option>
                    </select>
                  </label>

                  <label>
                    pH
                    <input name="ph" value={form.ph} onChange={handleChange} />
                  </label>

                  <label>
                    Light Intensity (mW/cm²)
                    <input
                      name="lightIntensity"
                      value={form.lightIntensity}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Temperature (K)
                    <input
                      name="temperature"
                      value={form.temperature}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Thickness (nm)
                    <input
                      name="thickness"
                      value={form.thickness}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Synthesis Method
                    <input
                      name="synthesisMethod"
                      value={form.synthesisMethod}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Photoelectrode Type
                    <input
                      name="photoelectrodeType"
                      value={form.photoelectrodeType}
                      onChange={handleChange}
                    />
                  </label>

                  <label className="full-width">
                    Applied Bias (V vs RHE)
                    <input
                      name="appliedBias"
                      value={form.appliedBias}
                      onChange={handleChange}
                    />
                  </label>

                  <label className="full-width">
                    Protective Layer
                    <input
                      name="protectiveLayer"
                      value={form.protectiveLayer}
                      onChange={handleChange}
                    />
                  </label>
                </div>

                <button
                  className="predict-btn"
                  onClick={runPrediction}
                  disabled={loading}
                >
                  {loading ? "Predicting..." : "🚀 Predict Performance"}
                </button>
              </div>

              <div className="glass-card result-panel">
                <div className="section-head">
                  <h3>Prediction Results</h3>
                  <p>
                    Estimated photoelectrochemical performance based on selected inputs
                  </p>
                </div>

                <div className="result-top-grid">
                  <div className="metric-box cyan">
                    <p>Photocurrent Density</p>
                    <h2>{displayedPhotocurrent}</h2>
                    <span>mA/cm²</span>
                    <small>ML prediction</small>
                  </div>

                  <div className="metric-box green">
                    <p>STH Efficiency</p>
                    <h2>{displayedSTH}%</h2>
                    <small>ML prediction</small>
                  </div>

                  <div className="metric-box" style={{ borderColor: "rgba(210,153,34,0.4)" }}>
                    <p>H₂ Evolution Rate</p>
                    <h2 style={{ color: "#d29922" }}>{displayedH2}</h2>
                    <span>µmol/h/cm²</span>
                    <small>ML prediction</small>
                  </div>
                </div>

                <div className="performance-box">
                  <h4>Performance Class</h4>
                  <div className="performance-row">
                    <div className="class-badge">{performanceClass}</div>
                    <div className="progress-track">
                      <div
                        className="progress-fill"
                        style={{ width: `${performanceWidth}%` }}
                      />
                    </div>
                  </div>
                  <p>
                    Predictions from separate RandomForest models trained for each target.
                  </p>
                </div>
              </div>
            </section>
          </>
        )}

        {activeTab === "Prediction" && (
          <section className="single-page">
            <div className="glass-card">
              <div className="section-head">
                <h3>Enter Experimental Parameters</h3>
                <p>Input the material and conditions for prediction</p>
              </div>

              <div className="form-grid">
                <label>
                  Material
                  <select name="material" value={form.material} onChange={handleChange}>
                    <option>BiVO₄ (Bismuth Vanadate)</option>
                    <option>Fe₂O₃ (Hematite)</option>
                    <option>WO₃</option>
                    <option>TiO₂</option>
                    <option>g-C₃N₄</option>
                  </select>
                </label>

                <label>
                  Bandgap (eV)
                  <select name="bandgap" value={form.bandgap} onChange={handleChange}>
                    <option>2.40</option>
                    <option>2.10</option>
                    <option>2.70</option>
                    <option>1.95</option>
                  </select>
                </label>

                <label>
                  Morphology
                  <select
                    name="morphology"
                    value={form.morphology}
                    onChange={handleChange}
                  >
                    <option>Nanorods</option>
                    <option>Nanosheets</option>
                    <option>Thin Film</option>
                    <option>Nanotubes</option>
                  </select>
                </label>

                <label>
                  Nanostructure
                  <select
                    name="nanostructure"
                    value={form.nanostructure}
                    onChange={handleChange}
                  >
                    <option>Heterojunction</option>
                    <option>Core-shell</option>
                    <option>Porous</option>
                    <option>Bulk</option>
                  </select>
                </label>

                <label>
                  Cocatalyst
                  <select
                    name="cocatalyst"
                    value={form.cocatalyst}
                    onChange={handleChange}
                  >
                    <option>None</option>
                    <option>NiFeOx</option>
                    <option>Co-Pi</option>
                    <option>Pt</option>
                  </select>
                </label>

                <label>
                  Electrolyte
                  <select
                    name="electrolyte"
                    value={form.electrolyte}
                    onChange={handleChange}
                  >
                    <option>Na₂SO₄ (Sodium Sulfate)</option>
                    <option>KOH</option>
                    <option>NaOH</option>
                    <option>H₂SO₄</option>
                  </select>
                </label>

                <label>
                  pH
                  <input name="ph" value={form.ph} onChange={handleChange} />
                </label>

                <label>
                  Light Intensity (mW/cm²)
                  <input
                    name="lightIntensity"
                    value={form.lightIntensity}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  Temperature (K)
                  <input
                    name="temperature"
                    value={form.temperature}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  Thickness (nm)
                  <input
                    name="thickness"
                    value={form.thickness}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  Synthesis Method
                  <input
                    name="synthesisMethod"
                    value={form.synthesisMethod}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  Photoelectrode Type
                  <input
                    name="photoelectrodeType"
                    value={form.photoelectrodeType}
                    onChange={handleChange}
                  />
                </label>

                <label className="full-width">
                  Applied Bias (V vs RHE)
                  <input
                    name="appliedBias"
                    value={form.appliedBias}
                    onChange={handleChange}
                  />
                </label>

                <label className="full-width">
                  Protective Layer
                  <input
                    name="protectiveLayer"
                    value={form.protectiveLayer}
                    onChange={handleChange}
                  />
                </label>
              </div>

              <div className="row-actions">
                <button className="secondary-btn" onClick={resetForm}>
                  Reset
                </button>
                <button
                  className="predict-btn slim"
                  onClick={runPrediction}
                  disabled={loading}
                >
                  {loading ? "Predicting..." : "Predict Performance"}
                </button>
              </div>
            </div>
          </section>
        )}

        {activeTab === "Results" && (
          <section className="results-grid">
            <div className="glass-card">
              <div className="section-head">
                <h3>Latest Model Output</h3>
              </div>

              <div className="info-stack">
                <div className="info-box">
                  <span>Material</span>
                  <strong>{form.material.split(" ")[0]}</strong>
                </div>
                <div className="info-box">
                  <span>Morphology / Structure</span>
                  <strong>
                    {form.morphology} / {form.nanostructure}
                  </strong>
                </div>
                <div className="info-box">
                  <span>Electrolyte / pH</span>
                  <strong>
                    {form.electrolyte.split(" ")[0]} / {form.ph}
                  </strong>
                </div>

                <button
                  className="secondary-btn wide"
                  onClick={() => setActiveTab("Prediction")}
                >
                  Edit Parameters
                </button>
              </div>
            </div>

            <div className="glass-card">
              <div className="section-head">
                <h3>Prediction Results</h3>
                <p>Estimated photoelectrochemical performance based on selected inputs</p>
              </div>

              <div className="result-top-grid">
                <div className="metric-box cyan">
                  <p>Photocurrent Density</p>
                  <h2>{displayedPhotocurrent}</h2>
                  <span>mA/cm²</span>
                  <small>ML prediction</small>
                </div>

                <div className="metric-box green">
                  <p>STH Efficiency</p>
                  <h2>{displayedSTH}%</h2>
                  <small>ML prediction</small>
                </div>

                <div className="metric-box" style={{ borderColor: "rgba(210,153,34,0.4)" }}>
                  <p>H₂ Evolution Rate</p>
                  <h2 style={{ color: "#d29922" }}>{displayedH2}</h2>
                  <span>µmol/h/cm²</span>
                  <small>ML prediction</small>
                </div>
              </div>

              <div className="performance-box">
                <h4>Performance Class: {performanceClass}</h4>
                <div className="performance-row">
                  <div className="class-badge">{performanceClass}</div>
                  <div className="progress-track">
                    <div
                      className="progress-fill"
                      style={{ width: `${performanceWidth}%` }}
                    />
                  </div>
                </div>
                <p>
                  Separate RandomForest models trained per target (PC, STH, H₂).
                </p>
              </div>
            </div>
          </section>
        )}

        {activeTab === "About" && (
          <section className="about-grid">
            <div className="glass-card about-text">
              <h2>About the Project</h2>
              <p>
                This interface demonstrates a concept for applying machine learning
                methods to predict the outcomes of physical experiments based on
                parameters extracted from scientific publications.
              </p>
              <p>
                In the diploma context, the dashboard represents a front-end layer for
                an experimental prediction system where literature-derived data can be
                structured, analyzed, and transformed into model-ready inputs.
              </p>
            </div>

            <div className="glass-card">
              <h2>Key Features</h2>
              <div className="key-features">
                <div className="key-item">Literature-based dataset structure</div>
                <div className="key-item">Experimental parameter input panel</div>
                <div className="key-item">Prediction results visualization</div>
                <div className="key-item">Confidence and uncertainty display</div>
                <div className="key-item">Train / validation / test split</div>
                <div className="key-item">Feature importance interpretation</div>
              </div>
            </div>

            <div className="glass-card full-span">
              <div className="section-head">
                <h3>Model Summary</h3>
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
                <FeatureBar
                  key={label}
                  label={label}
                  value={value}
                  max={maxImportance}
                />
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}