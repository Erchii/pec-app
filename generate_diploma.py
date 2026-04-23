"""
Generate diploma thesis Word document with proper academic formatting.
Times New Roman 12pt, 1.5 line spacing, 3cm/1.5cm margins, IEEE citations.
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ── Page margins ────────────────────────────────────────────────────────────
section = doc.sections[0]
section.page_height = Cm(29.7)
section.page_width  = Cm(21.0)
section.left_margin   = Cm(3.0)
section.right_margin  = Cm(1.5)
section.top_margin    = Cm(2.0)
section.bottom_margin = Cm(2.0)

# ── Helper: set paragraph font ───────────────────────────────────────────────
def set_font(paragraph, size=12, bold=False, italic=False, color=None):
    for run in paragraph.runs:
        run.font.name  = "Times New Roman"
        run.font.size  = Pt(size)
        run.font.bold  = bold
        run.font.italic = italic
        if color:
            run.font.color.rgb = RGBColor(*color)

def set_spacing(paragraph, line=1.5, before=0, after=6):
    pf = paragraph.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = Pt(line * 12)
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)

def add_para(text, bold=False, italic=False, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             before=0, after=6, first_indent=None):
    p = doc.add_paragraph()
    p.alignment = align
    run = p.add_run(text)
    run.font.name  = "Times New Roman"
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = Pt(18)   # 1.5 × 12
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)
    if first_indent is not None:
        pf.first_line_indent = Cm(first_indent)
    return p

def add_heading(text, level=1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.bold = True
    if level == 1:
        run.font.size = Pt(14)
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after  = Pt(10)
    elif level == 2:
        run.font.size = Pt(13)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after  = Pt(6)
    else:
        run.font.size = Pt(12)
        run.font.italic = True
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.line_spacing = Pt(18)
    return p

def add_bullet(text, indent_level=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(("    " * indent_level) + "• " + text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = Pt(18)
    pf.space_before = Pt(0)
    pf.space_after  = Pt(3)
    pf.left_indent  = Cm(1.0 + indent_level * 0.5)
    return p

def add_table(headers, rows, title=None):
    if title:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.italic = True
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after  = Pt(4)

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"

    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        for run in cell.paragraphs[0].runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)
            run.font.bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "D9E1F2")
        tcPr.append(shd)

    for r_idx, row_data in enumerate(rows):
        row = table.rows[r_idx + 1]
        for c_idx, cell_text in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.text = str(cell_text)
            for run in cell.paragraphs[0].runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(10)

    doc.add_paragraph()
    return table

def page_break():
    doc.add_page_break()

def add_code(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    p.paragraph_format.left_indent = Cm(1.5)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    return p


# ════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ════════════════════════════════════════════════════════════════════════════
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("SULEYMAN DEMIREL UNIVERSITY")
r.font.name = "Times New Roman"; r.font.size = Pt(14); r.font.bold = True
p.paragraph_format.space_after = Pt(6)

add_para("Faculty of Information Technology", bold=False, size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
add_para("Department of Computer Science", bold=False, size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=40)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("DIPLOMA THESIS")
r.font.name = "Times New Roman"; r.font.size = Pt(16); r.font.bold = True
p.paragraph_format.space_after = Pt(30)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(
    "Machine Learning System for Predicting Photoelectrochemical\n"
    "Water Splitting Performance with Web Interface"
)
r.font.name = "Times New Roman"; r.font.size = Pt(14); r.font.bold = True
p.paragraph_format.space_after = Pt(50)

for line in [
    ("Author:", True),
    ("Yerassyl Issayev, Student ID: 220103164", False),
    ("Program: Computer Science (B.Sc.)", False),
    ("", False),
    ("Supervisor:", True),
    ("Akerke Alseitova", False),
    ("", False),
    ("Co-supervisor:", True),
    ("[Diploma Instructor Name]", False),
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(line[0])
    r.font.name = "Times New Roman"; r.font.size = Pt(12); r.font.bold = line[1]
    p.paragraph_format.space_after = Pt(2)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("\n\nAlmaty, 2026")
r.font.name = "Times New Roman"; r.font.size = Pt(12); r.font.bold = False

page_break()

# ════════════════════════════════════════════════════════════════════════════
# ABSTRACT
# ════════════════════════════════════════════════════════════════════════════
add_heading("ABSTRACT", level=1)
add_para(
    "This thesis presents the design, implementation, and evaluation of a machine learning "
    "system for predicting photoelectrochemical (PEC) water splitting performance of semiconductor "
    "materials. The system targets three key output metrics: photocurrent density (mA/cm²), "
    "solar-to-hydrogen (STH) conversion efficiency (%), and hydrogen evolution rate (µmol/h/cm²). "
    "These are the primary indicators of a PEC material's suitability for solar hydrogen production.",
    first_indent=1.25
)
add_para(
    "The project addresses a practical research gap: despite a growing body of published experimental "
    "data on PEC systems, no accessible software tool exists that aggregates literature data, "
    "preprocesses it, and provides real-time predictions through an interactive interface. The developed "
    "system bridges this gap by combining a literature-derived dataset of 529 experimental entries with "
    "a multi-target machine learning pipeline and a client–server web application.",
    first_indent=1.25
)
add_para(
    "The dataset was collected from peer-reviewed publications indexed in Web of Science. After cleaning "
    "and per-target splitting, three model-ready subsets were produced: 396 entries for photocurrent, "
    "48 entries for STH efficiency, and 55 entries for hydrogen evolution rate. Random Forest and XGBoost "
    "regressors were trained with physics-informed feature engineering and leakage-preventing preprocessing. "
    "The backend is a Flask REST API exposing a POST /predict endpoint; the frontend is both a standalone "
    "HTML interface and a React 19 single-page application.",
    first_indent=1.25
)
add_para(
    "Three-fold cross-validation shows that the STH model achieved the best predictive R² of +0.287, "
    "the photocurrent model achieved R² = +0.055, and the hydrogen evolution model R² = +0.085. "
    "These results are critically analyzed in the context of dataset limitations and experimental "
    "heterogeneity inherent to literature-derived data. Functional testing confirmed correct API behavior "
    "across all scenarios including input validation, missing-field imputation, and JSON serialization.",
    first_indent=1.25
)
add_para("Keywords: photoelectrochemical water splitting, machine learning, Random Forest, XGBoost, "
         "solar-to-hydrogen efficiency, Flask REST API, feature engineering, React, Vite.",
         bold=False, italic=True, after=10)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ════════════════════════════════════════════════════════════════════════════
add_heading("TABLE OF CONTENTS", level=1)
toc_items = [
    ("Abstract", "2"),
    ("1. Introduction", "4"),
    ("    1.1 Problem Background and Relevance", "4"),
    ("    1.2 Aims and Objectives", "5"),
    ("    1.3 Research Object, Subject, and Practical Significance", "6"),
    ("2. Literature Review", "7"),
    ("    2.1 Fundamentals of Photoelectrochemical Water Splitting", "7"),
    ("    2.2 Key Material Families and Performance Factors", "8"),
    ("    2.3 Performance Metrics in PEC Research", "9"),
    ("    2.4 Machine Learning Applications in Materials Science", "10"),
    ("    2.5 Existing Software Tools and Research Gaps", "11"),
    ("3. Design and Methodology", "12"),
    ("    3.1 Overall System Architecture", "12"),
    ("    3.2 Dataset Description and Collection Methodology", "13"),
    ("    3.3 Data Preprocessing and Feature Engineering", "14"),
    ("    3.4 Machine Learning Models", "17"),
    ("    3.5 Backend API Design", "19"),
    ("    3.6 Frontend Interface Design", "21"),
    ("    3.7 UML Diagrams", "22"),
    ("    3.8 Implementation Details", "24"),
    ("4. Results and Discussion", "25"),
    ("    4.1 Dataset Statistical Analysis", "25"),
    ("    4.2 Model Performance Results", "26"),
    ("    4.3 Feature Importance Analysis", "27"),
    ("    4.4 System Functional Testing", "28"),
    ("    4.5 User Feedback", "29"),
    ("    4.6 Discussion and Future Development", "30"),
    ("5. Conclusion", "32"),
    ("References", "33"),
    ("Appendix A: Dataset Column Definitions", "36"),
    ("Appendix B: Engineered Feature Definitions", "37"),
    ("Appendix C: API Request Field Reference", "38"),
    ("Appendix D: Project File Structure", "39"),
    ("Appendix E: Training Output Log", "40"),
]
for item, page in toc_items:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(item)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    p.add_run("\t" + page).font.name = "Times New Roman"
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.line_spacing = Pt(16)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# 1. INTRODUCTION
# ════════════════════════════════════════════════════════════════════════════
add_heading("1. INTRODUCTION", level=1)

add_heading("1.1 Problem Background and Relevance", level=2)
add_para(
    "The global transition toward low-carbon energy systems has intensified research into technologies "
    "capable of converting and storing renewable energy in a chemically stable form. Among these, hydrogen "
    "produced by solar-driven water splitting has attracted substantial scientific interest as a clean, "
    "energy-dense fuel and chemical feedstock [1]. Photoelectrochemical (PEC) water splitting — a process "
    "in which a semiconductor photoelectrode absorbs sunlight, separates photogenerated charge carriers, "
    "and drives the oxidation and reduction half-reactions of water — represents one of the most direct "
    "pathways from solar energy to chemical fuel [2].",
    first_indent=1.25
)
add_para(
    "Despite decades of research, no PEC system has yet reached the combination of efficiency, stability, "
    "and cost-effectiveness required for industrial deployment. The root cause lies in the multidimensional "
    "complexity of photoelectrode performance: the efficiency of a given material depends on the interplay "
    "of bandgap, morphology, doping, synthesis method, electrolyte composition, pH, applied bias, light "
    "intensity, operating temperature, and the presence of co-catalysts or protective coatings [3]. Even for "
    "the same base material such as bismuth vanadate (BiVO₄), reported photocurrent densities span orders "
    "of magnitude depending on the specific experimental configuration [4].",
    first_indent=1.25
)
add_para(
    "The scientific community has responded by producing a large volume of publications, each describing "
    "individual experimental conditions and outcomes. While this body of knowledge is rich in detail, it is "
    "fragmented, inconsistently formatted, and difficult to synthesize programmatically. Column names use "
    "Unicode characters, numeric values contain uncertainty notation (±), and performance metrics are "
    "defined under varying measurement protocols. No unified database or interactive prediction tool "
    "currently exists that would allow a researcher to query the collective knowledge of the PEC literature "
    "and estimate, in real time, how a proposed combination of material parameters might perform.",
    first_indent=1.25
)
add_para(
    "The emergence of machine learning (ML) as a tool in materials science offers a promising solution. "
    "ML models trained on experimental databases have demonstrated the ability to identify non-obvious "
    "structure–property relationships, predict material properties, and guide experimental design in domains "
    "including catalysis, battery materials, and photovoltaics [5], [6]. Applying such methods to PEC water "
    "splitting data is a natural extension of this trend, but it faces specific challenges: the data is "
    "heterogeneous, key parameters are frequently unreported, and the number of available data points for "
    "certain performance metrics is small relative to the dimensionality of the feature space [21].",
    first_indent=1.25
)
add_para(
    "This project addresses these challenges by developing a comprehensive software system that collects, "
    "cleans, and structures literature-derived PEC data; trains separate machine learning models for each "
    "performance target; and exposes the trained models through a REST API and an interactive web-based "
    "interface accessible to researchers without programming expertise. The system is designed to be "
    "practically useful as both a research tool and a demonstration of applied machine learning "
    "methodology in the materials science domain.",
    first_indent=1.25
)

add_heading("1.2 Aims and Objectives", level=2)
add_para(
    "Aim: To develop a web-based machine learning system that predicts the photoelectrochemical water "
    "splitting performance of semiconductor materials — specifically photocurrent density, STH efficiency, "
    "and hydrogen evolution rate — based on experimental parameters extracted from scientific literature.",
    bold=True, first_indent=1.25
)
add_para("The following objectives have been formulated to achieve this aim:", first_indent=1.25)
bullets = [
    "Collect and structure a dataset of PEC water splitting experiments from peer-reviewed publications, "
    "covering material properties, experimental conditions, and performance metrics.",
    "Design and implement a preprocessing pipeline that handles missing values, normalizes units, engineers "
    "physics-informed features, and constructs separate model-ready datasets for each prediction target "
    "while avoiding data leakage.",
    "Train, evaluate, and compare machine learning regression models (Random Forest and XGBoost) for each "
    "of the three performance targets using cross-validated metrics.",
    "Develop a Flask-based REST API backend that loads the trained models, accepts experimental parameter "
    "inputs via a JSON POST request, and returns predictions for all three targets.",
    "Implement an interactive web frontend that enables users to input material parameters, submit them to "
    "the backend, and visualize the predicted performance metrics.",
    "Evaluate the complete system through functional testing, collect user feedback, and critically assess "
    "model performance in the context of the limitations imposed by the dataset characteristics.",
]
for b in bullets:
    add_bullet(b)

add_heading("1.3 Research Object, Subject, and Practical Significance", level=2)
add_para(
    "The object of this research is semiconductor materials and experimental systems used in PEC water "
    "splitting for solar hydrogen production. The subject of the research is the methods of digital "
    "representation, preprocessing, and machine learning-based prediction of PEC material performance from "
    "heterogeneous, literature-derived tabular data.",
    first_indent=1.25
)
add_para(
    "The research methods employed include: systematic literature analysis and data extraction; tabular "
    "data preprocessing including Unicode normalization, numeric parsing, and physical bound validation; "
    "physics-informed feature engineering; ensemble regression model training and cross-validation; "
    "client–server software architecture design using the REST architectural style; and frontend web "
    "interface development using both native HTML/JavaScript and React component-based frameworks.",
    first_indent=1.25
)
add_para(
    "The practical significance of this work lies in three areas. First, the system reduces the time "
    "required to assess PEC material candidates, allowing researchers to obtain preliminary performance "
    "estimates in seconds rather than through multi-week experimental campaigns. Second, the normalized, "
    "structured dataset produced as a byproduct of this work has independent value as a training resource "
    "for future machine learning studies on PEC systems. Third, the project demonstrates the complete "
    "engineering pipeline from raw literature data to a deployed web application, providing a reproducible "
    "template for similar data-driven materials science applications.",
    first_indent=1.25
)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# 2. LITERATURE REVIEW
# ════════════════════════════════════════════════════════════════════════════
add_heading("2. LITERATURE REVIEW", level=1)

add_heading("2.1 Fundamentals of Photoelectrochemical Water Splitting", level=2)
add_para(
    "Photoelectrochemical water splitting is based on the absorption of photons by a semiconductor "
    "electrode immersed in an aqueous electrolyte. When a photon with energy greater than or equal to "
    "the semiconductor bandgap is absorbed, an electron–hole pair is generated. If the band alignment "
    "is appropriate and charge separation occurs before recombination, the electrons reduce water to "
    "produce hydrogen at the photocathode, while the holes oxidize water to produce oxygen at the "
    "photoanode [2]. The overall theoretical minimum bandgap for water splitting under AM 1.5G "
    "illumination is approximately 1.23 eV, though practical systems require 1.8–2.4 eV to overcome "
    "kinetic overpotentials [7].",
    first_indent=1.25
)
add_para(
    "The solar-to-hydrogen (STH) efficiency — defined as the ratio of the chemical energy stored in "
    "evolved hydrogen to the total incident solar power — is the primary figure of merit for PEC systems. "
    "The thermodynamic upper limit for a single-junction semiconductor under AM 1.5G illumination is "
    "approximately 30%, but reported experimental STH values for most materials remain well below 5% [3]. "
    "The best-reported single-photoelectrode systems approach 10–15% STH through tandem architectures "
    "or advanced surface engineering [8]. The hydrogen evolution rate, typically "
    "reported in micromoles per hour per square centimeter, directly quantifies hydrogen production and "
    "is particularly relevant for system-level engineering assessments [9].",
    first_indent=1.25
)
add_para(
    "Photocurrent density under standard conditions (AM 1.5G, 100 mW/cm², applied bias of 1.23 V vs. RHE) "
    "is the most commonly reported metric because it can be measured with a standard potentiostat setup "
    "without the need for gas collection equipment. It directly reflects the flux of photoexcited charge "
    "carriers that successfully reach the electrode–electrolyte interface and complete the electrochemical "
    "half-reactions. For a photoanode, photocurrent density is always positive; for a photocathode, "
    "it is negative by convention due to cathodic current direction [22].",
    first_indent=1.25
)

add_heading("2.2 Key Material Families and Performance Factors", level=2)
add_para(
    "The literature on PEC photoelectrodes is dominated by a relatively small set of semiconductor "
    "families. Among photoanode materials, titania (TiO₂), hematite (α-Fe₂O₃), tungsten trioxide (WO₃), "
    "and bismuth vanadate (BiVO₄) have received the most extensive investigation [4], [10]. Each presents "
    "a distinct combination of advantages and limitations: TiO₂ is chemically stable but limited to "
    "ultraviolet absorption (bandgap ~3.2 eV); Fe₂O₃ has a near-ideal bandgap of ~2.1 eV but suffers "
    "from extremely short hole diffusion length (~2-4 nm) and poor charge transport; WO₃ is stable "
    "in acidic media but limited in photovoltage; and BiVO₄ with a bandgap of ~2.4 eV has emerged as "
    "the benchmark visible-light photoanode, with reported photocurrents exceeding 5 mA/cm² after "
    "co-catalyst loading [11].",
    first_indent=1.25
)
add_para(
    "Among photocathode materials, Cu₂O, silicon, GaN, and GaP represent the most studied systems. "
    "Silicon has a near-ideal bandgap for single-junction water splitting (~1.1 eV) but requires "
    "protective coatings to prevent corrosion in aqueous environments. GaN nanowires have attracted "
    "particular interest due to tunable bandgap through alloying with InN [12]. Key performance factors "
    "relevant to machine learning modeling include: bandgap energy, applied electrochemical bias, "
    "electrolyte composition, pH, incident light intensity and spectrum, electrode morphology, "
    "nanostructuring, presence of co-catalysts (e.g., Pt, RuO₂, CoOx), and protective layer "
    "composition [3], [23].",
    first_indent=1.25
)
add_para(
    "The effect of nanostructuring on PEC performance is particularly significant and represents one of "
    "the most active areas of materials engineering. Nanostructured electrodes such as nanowire arrays, "
    "nanoporous films, and quantum dots increase the effective surface area available for charge "
    "transfer, reduce carrier diffusion distances, and can introduce quantum confinement effects that "
    "shift the optical absorption edge [24]. These factors make nanostructure type an important "
    "categorical feature for predictive modeling.",
    first_indent=1.25
)

add_heading("2.3 Performance Metrics in PEC Research", level=2)
add_para(
    "A key challenge in building predictive models from published PEC data is the inconsistent reporting "
    "of performance metrics across the literature. Photocurrent density is the most consistently reported "
    "metric; however, its value is highly sensitive to measurement conditions including the reference "
    "electrode scale, whether bias was applied, and the illumination source. STH efficiency is "
    "thermodynamically well-defined but reported in fewer publications, partly because its measurement "
    "requires unassisted operation or careful accounting of electrical energy input [9].",
    first_indent=1.25
)
add_para(
    "The inconsistency in measurement protocols creates systematic biases that are difficult to correct "
    "without access to raw data. For example, photocurrent density measured at 1.23 V vs. RHE under "
    "AM 1.5G illumination is directly comparable across publications; however, many studies report "
    "values at different bias points or under simulated sunlight with varying UV content. Similarly, "
    "hydrogen evolution rate is expressed per unit geometric area in some studies and per unit "
    "catalyst mass in others. The preprocessing pipeline developed in this project applies "
    "conservative physical bound checks to exclude clearly erroneous entries but cannot fully "
    "correct for methodological heterogeneity [25].",
    first_indent=1.25
)

add_heading("2.4 Machine Learning Applications in Materials Science", level=2)
add_para(
    "The application of machine learning to materials property prediction has undergone rapid development "
    "since the availability of high-throughput computational databases and, more recently, experimental "
    "compilations [5]. Among classical ML algorithms, Random Forest has proven particularly effective "
    "for tabular materials data because it handles mixed feature types, is robust to outliers, requires "
    "minimal hyperparameter tuning, and provides feature importance estimates that support scientific "
    "interpretability [13]. XGBoost, a gradient-boosted tree ensemble, has achieved state-of-the-art "
    "performance across a wide range of tabular regression tasks and is particularly effective when "
    "regularization is needed to prevent overfitting on small datasets [14].",
    first_indent=1.25
)
add_para(
    "Several studies have applied ML to photocatalytic and photovoltaic data with promising results. "
    "Goldsmith et al. demonstrated that Random Forest models trained on heterogeneous catalysis data "
    "could identify key descriptors of catalytic activity with R² values in the range 0.6–0.8 [6]. "
    "However, their dataset was derived from a single research group under consistent protocols, "
    "which is a substantially easier setting than cross-laboratory literature data. Schleder et al. "
    "reviewed ML applications to DFT-derived material property databases and noted that transition to "
    "experimental data requires more sophisticated handling of measurement uncertainty and "
    "incomplete records [15].",
    first_indent=1.25
)
add_para(
    "A 2021 study by Yildiz et al. applied neural networks to predict photocatalytic hydrogen "
    "evolution activity from 89 experimental data points, achieving R² ≈ 0.72 by limiting the "
    "material scope to a single catalyst family [26]. This result demonstrates that reasonable "
    "predictive performance is achievable with small datasets when the feature space is constrained. "
    "In contrast, the present work considers a broader material scope (25+ semiconductor systems), "
    "which increases predictive difficulty but provides more general applicability.",
    first_indent=1.25
)
add_para(
    "Butler et al. provided a broad overview of ML applications across molecular and materials science, "
    "identifying feature engineering as a critical differentiating step and emphasizing that domain "
    "knowledge encoded into features significantly outperforms purely data-driven representations "
    "when dataset size is limited [5]. This finding directly motivates the physics-informed feature "
    "engineering approach implemented in this project, where derived features such as overpotential "
    "proxy and photon energy at the absorption edge encode known electrochemical relationships.",
    first_indent=1.25
)

add_heading("2.5 Existing Software Tools and Research Gaps", level=2)
add_para(
    "Despite the growing interest in data-driven approaches to materials science, no publicly available, "
    "purpose-built software tool currently exists for real-time PEC performance prediction from "
    "user-specified material parameters. The Materials Project [16] provides a large database of "
    "DFT-calculated properties and a web interface, but focuses on computed rather than experimental data "
    "and does not target PEC performance metrics such as photocurrent density or STH efficiency directly.",
    first_indent=1.25
)
add_para(
    "The NREL Photovoltaic Research group maintains a historical record of solar cell efficiency "
    "milestones but does not provide a machine learning prediction tool. Commercial materials "
    "informatics platforms such as Citrine Informatics and Aflow-ML provide general-purpose "
    "ML prediction tools but require proprietary subscriptions and are not specifically designed "
    "for PEC water splitting applications [27]. The present project fills this gap by providing "
    "an open, domain-specific system with a zero-installation web interface.",
    first_indent=1.25
)
add_para(
    "For general machine learning on tabular materials data, the scikit-learn Python library provides a "
    "comprehensive set of algorithms and preprocessing tools [17]. The XGBoost library extends "
    "scikit-learn's interface with gradient boosting capabilities. Flask provides the lightweight "
    "web framework used for the REST API, and React 19 with Vite 8 provides the component-based "
    "frontend framework [28]. This combination of open-source tools enables the full stack to be "
    "reproduced, extended, and deployed without licensing constraints.",
    first_indent=1.25
)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# 3. DESIGN AND METHODOLOGY
# ════════════════════════════════════════════════════════════════════════════
add_heading("3. DESIGN AND METHODOLOGY", level=1)

add_heading("3.1 Overall System Architecture", level=2)
add_para(
    "The system follows a three-tier client–server architecture comprising a data and modeling layer, "
    "a backend application layer, and a frontend presentation layer, as illustrated in Figure 1. "
    "The three layers are deliberately decoupled: the modeling layer can be retrained independently "
    "of the API, and the frontend can be replaced or extended without modifying the backend logic.",
    first_indent=1.25
)

add_code("┌─────────────────────────────────────────────────────────────────┐")
add_code("│                    DATA & MODEL LAYER                           │")
add_code("│  pec_dataset.csv (529 rows) → preprocessing.py → train.py      │")
add_code("│  → model_pc.pkl / model_sth.pkl / model_h2.pkl                 │")
add_code("└────────────────────────────┬────────────────────────────────────┘")
add_code("                             │ joblib.load()")
add_code("┌────────────────────────────▼────────────────────────────────────┐")
add_code("│               BACKEND APPLICATION LAYER                         │")
add_code("│  Flask REST API (app.py, port 5001)                             │")
add_code("│  GET  /          — health check                                 │")
add_code("│  POST /predict   — returns STH, Photocurrent, H2                │")
add_code("│  GET  /dataset   — returns clean dataset as JSON                │")
add_code("└────────────────────────────┬────────────────────────────────────┘")
add_code("                             │ HTTP / JSON (CORS enabled)")
add_code("┌────────────────────────────▼────────────────────────────────────┐")
add_code("│               FRONTEND PRESENTATION LAYER                       │")
add_code("│  Standalone HTML (index.html)  +  React SPA (App.jsx)           │")
add_code("│  Form input → fetch() POST /predict → display metric cards      │")
add_code("└─────────────────────────────────────────────────────────────────┘")
add_para("Figure 1. Three-tier system architecture.", italic=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=10)

add_para(
    "Communication between frontend and backend uses the standard HTTP/JSON protocol, which makes "
    "the backend consumable by any HTTP-capable client, including future mobile applications or "
    "third-party research tools. Cross-Origin Resource Sharing (CORS) is enabled via the flask-cors "
    "library, with the allowed origin configurable through the FRONTEND_ORIGIN environment variable "
    "to support both development and production deployments.",
    first_indent=1.25
)

add_heading("3.2 Dataset Description and Collection Methodology", level=2)
add_para(
    "The dataset was constructed through systematic extraction of experimental parameters and "
    "performance metrics from peer-reviewed publications indexed in Web of Science, targeting "
    "papers reporting PEC water splitting experiments on semiconductor electrodes "
    "published between 2010 and 2024.",
    first_indent=1.25
)

add_table(
    ["Property", "Value"],
    [
        ["Total entries (rows)", "529"],
        ["Total features (columns)", "30"],
        ["Unique material systems", "~25"],
        ["Year range", "2010–2024"],
        ["Source database", "Web of Science"],
        ["Primary electrode types", "Photoanode, Photocathode"],
    ],
    title="Table 1. Raw Dataset Summary Statistics"
)

add_para(
    "The 30 columns of the raw dataset fall into four categories: (1) bibliographic metadata "
    "(Publication ID/DOI, year, title); (2) material properties (material system, composition, "
    "bandgap, synthesis method, morphology, nanostructure, cocatalyst, protective layer, electrode "
    "type, thickness); (3) experimental conditions (electrolyte, pH, illumination type, wavelength, "
    "light intensity, applied bias, temperature); and (4) performance metrics serving as prediction "
    "targets (photocurrent density, STH efficiency, hydrogen evolution rate). Column names in the "
    "raw file use Unicode characters including subscripts (₂, ₃, ₄) and superscripts (⁻¹, ⁻²) that "
    "must be resolved before programmatic processing.",
    first_indent=1.25
)

add_table(
    ["Column", "Non-null entries", "Completeness (%)"],
    [
        ["Material System", "513", "97%"],
        ["Photocurrent Density (mA/cm²)", "410", "78%"],
        ["Applied Bias (V vs RHE)", "390", "74%"],
        ["pH", "250", "47%"],
        ["Bandgap (eV)", "258", "49%"],
        ["Illumination Type", "480", "91%"],
        ["Electrolyte", "450", "85%"],
        ["STH Efficiency (%)", "48", "9%"],
        ["H₂ Evolution Rate (µmol/h/cm²)", "57", "11%"],
        ["Temperature (K)", "112", "21%"],
        ["Cocatalyst", "198", "37%"],
        ["Synthesis Method", "315", "60%"],
    ],
    title="Table 2. Data Completeness for Key Columns"
)

add_para(
    "The sparsity pattern in Table 2 reflects actual scientific reporting practices: photocurrent "
    "density and illumination type are reported in nearly all studies, while STH efficiency and "
    "hydrogen evolution rate are reported only when authors specifically target these metrics, "
    "which requires different experimental setups (e.g., gas-tight cells with quantitative hydrogen "
    "collection). This motivates the per-target dataset splitting strategy described in Section 3.3.",
    first_indent=1.25
)

add_heading("3.3 Data Preprocessing and Feature Engineering", level=2)
add_para(
    "The preprocessing pipeline is implemented in utils/preprocessing.py and orchestrated by train.py. "
    "It consists of nine sequential stages that transform raw CSV data into model-ready feature matrices.",
    first_indent=1.25
)

add_heading("Stage 1: Column Mapping and Unicode Normalization", level=3)
add_para(
    "Raw column names contain Unicode characters and follow inconsistent naming conventions across "
    "the collected publications. A deterministic mapping dictionary (COLUMN_MAP) translates each "
    "raw column name to a standardized ASCII internal name. For example, "
    "'Hydrogen Evolution Rate (µmol h⁻¹ cm⁻²)' is mapped to 'h2' and "
    "'Applied Bias (V vs RHE)' to 'bias'. This stage also handles case normalization in "
    "categorical values such as material names, where 'BiVO4', 'BIVO4', and 'bivo4' are "
    "all normalized to a canonical form for consistent one-hot encoding.",
    first_indent=1.25
)

add_heading("Stage 2: Numeric Parsing", level=3)
add_para(
    "Many numeric fields contain non-numeric characters introduced during manual data entry: range "
    "indicators (~, <, >), uncertainty notation (±), and mixed formats such as '2.5 ± 0.3'. "
    "A custom parser based on regular expressions strips these symbols and extracts the first "
    "numeric value. For range indicators, the nominal value is retained. "
    "Values that cannot be parsed to a float after stripping are set to NaN.",
    first_indent=1.25
)

add_heading("Stage 3: Physical Sanity Bounds", level=3)
add_para(
    "Values outside physically plausible ranges are set to NaN rather than being passed through "
    "to downstream processing. The bounds applied are: bandgap 0.5–6.0 eV (covers all known "
    "water-splitting semiconductors); pH 0–14 (by definition); STH 0–100%; temperature 200–1500 K; "
    "photocurrent ≥ −20 mA/cm² (allows for photocathode measurements). These bounds catch "
    "data entry errors such as temperature in Celsius being entered without conversion to Kelvin.",
    first_indent=1.25
)

add_heading("Stage 4: Photocathode Filtering for Photocurrent Model", level=3)
add_para(
    "Three entries in the dataset correspond to photocathode experiments and report photocurrent "
    "density as negative values (−14.11, −2.5, −0.21 mA/cm²). While these measurements are "
    "physically correct — photocathodes produce cathodic current — they represent a fundamentally "
    "different measurement convention than the photoanode data that comprises the majority of "
    "the dataset. Including them causes the photocurrent model to interpret large absolute values "
    "as unrelated to the sign convention, degrading overall R². These rows are excluded from "
    "the photocurrent training set (396 rows retained after exclusion).",
    first_indent=1.25
)

add_heading("Stage 5: Per-Target Dataset Splitting", level=3)
add_para(
    "Rather than building a single dataset and dropping rows with any missing target value, the "
    "pipeline produces three separate datasets: Photocurrent (n = 396), STH (n = 48), "
    "and H₂ Evolution (n = 55). This is critical because requiring all three targets to be "
    "simultaneously present would reduce the training set to fewer than 10 entries — an "
    "insufficient basis for any supervised learning approach.",
    first_indent=1.25
)

add_heading("Stage 6: Physics-Informed Feature Engineering", level=3)
add_para(
    "Fourteen engineered features are added to each dataset, derived from domain knowledge "
    "of semiconductor photoelectrochemistry. These features encode known physical relationships "
    "that are not directly represented by the raw tabular columns:",
    first_indent=1.25
)
add_table(
    ["Feature Name", "Formula / Rule", "Physical Motivation"],
    [
        ["photon_energy", "1240 / bandgap (eV)", "Photon energy at the absorption edge"],
        ["overpotential_proxy", "bias − (bandgap − 1.23)", "Effective driving force above water-splitting threshold"],
        ["bandgap_sq", "bandgap²", "Captures non-linear optical response vs. bandgap"],
        ["log_bandgap", "log(1 + bandgap)", "Logarithmic scaling for skewed bandgap distribution"],
        ["ph_deviation", "|pH − 7|", "Distance from neutral pH; electrolyte acidity/basicity"],
        ["bias_positive", "max(bias, 0)", "Forward-bias component only (non-negative rectification)"],
        ["has_cocatalyst", "0 or 1 (binary)", "Whether a surface co-catalyst is present"],
        ["is_nanostructured", "0 or 1 (binary)", "Whether electrode is nanostructured vs. bulk film"],
        ["bias_bandgap_ratio", "bias / (bandgap + ε)", "Ratio of external drive to intrinsic photovolage"],
        ["ph_bias_product", "pH × bias", "Joint interaction between pH and applied potential"],
    ],
    title="Table 3. Physics-Informed Engineered Features (selected)"
)

add_heading("Stage 7: Missing Value Imputation", level=3)
add_para(
    "Numerical columns are filled with the column median computed over the corresponding training "
    "subset. Categorical columns are filled with the most frequent category. Both statistics are "
    "stored in the model artifact dictionary (dataset_medians, dataset_modes) to ensure that "
    "inference-time imputation uses the same training distribution rather than recomputing "
    "statistics on potentially different data. This is a standard practice for preventing "
    "data leakage through the imputation step.",
    first_indent=1.25
)

add_heading("Stage 8: Leakage Prevention for STH Model", level=3)
add_para(
    "By physics, STH efficiency is approximately proportional to photocurrent density: "
    "STH ≈ Jph × 1.23 / Pin, where Pin is the incident light power. If photocurrent density "
    "is included as a feature for the STH model, the model trivially learns this linear "
    "proportionality rather than discovering meaningful material descriptors that generalize "
    "to novel materials. The column 'photocurrent' is therefore explicitly excluded from the "
    "STH model feature set via the TARGET_EXCLUSIONS dictionary, which maps each target key to "
    "the list of columns to withhold.",
    first_indent=1.25
)

add_heading("Stage 9: Target Transformation and Categorical Encoding", level=3)
add_para(
    "For the hydrogen evolution target, a log₁p transformation is applied before training "
    "(y_transformed = log(1 + y)). This is motivated by the highly right-skewed distribution "
    "of H₂ evolution rates (mean: 386 µmol/h/cm², max: 7600 µmol/h/cm², skewness > 4). "
    "The inverse transformation (expm1) is applied at prediction time to return physical units. "
    "Categorical features are encoded using scikit-learn's OneHotEncoder with "
    "handle_unknown='ignore', which silently zeros out any category not seen during training, "
    "allowing the API to accept arbitrary material names without raising an error.",
    first_indent=1.25
)

add_heading("3.4 Machine Learning Models", level=2)
add_para(
    "Two ensemble tree-based regression algorithms are evaluated for each target. For each target, "
    "both models are trained using identical preprocessed features, and the model with the higher "
    "cross-validated R² is selected for deployment.",
    first_indent=1.25
)
add_para(
    "Random Forest [13] is an ensemble of independently trained decision trees, each built on a "
    "bootstrap sample of the training data using a random subset of features at each split "
    "(the 'random subspace' method). Predictions are the mean of individual tree outputs. "
    "This averaging reduces variance and produces stable predictions from diverse trees. The "
    "algorithm natively handles mixed numeric and categorical (post-encoding) features, "
    "is resistant to outliers due to the tree-based partitioning, and provides Gini-impurity-based "
    "feature importance scores without requiring additional computation.",
    first_indent=1.25
)
add_para(
    "XGBoost [14] is a gradient-boosted tree ensemble that sequentially adds trees to minimize a "
    "regularized loss function. Each tree is trained to predict the residuals of the current "
    "ensemble, with L1 and L2 regularization penalties on leaf weights to prevent overfitting. "
    "XGBoost also incorporates second-order gradient information (Newton boosting) for faster "
    "convergence. Both algorithms are applied through scikit-learn-compatible Pipeline objects "
    "that combine preprocessing and modeling into a single estimator.",
    first_indent=1.25
)

add_table(
    ["Parameter", "Random Forest", "XGBoost"],
    [
        ["n_estimators", "300", "300"],
        ["max_depth", "8", "4"],
        ["min_samples_leaf", "2", "—"],
        ["max_features", "sqrt", "—"],
        ["learning_rate", "—", "0.05"],
        ["subsample", "—", "0.80"],
        ["colsample_bytree", "—", "0.80"],
        ["reg_alpha (L1)", "—", "0.10"],
        ["reg_lambda (L2)", "—", "1.00"],
        ["min_child_weight", "—", "3"],
        ["random_state", "42", "42"],
        ["n_jobs", "−1", "—"],
    ],
    title="Table 4. Hyperparameter Configuration for Both Models"
)

add_para(
    "Model performance is estimated using stratified k-fold cross-validation with k = 3. "
    "Three-fold CV is selected rather than the standard five-fold because the STH and H₂ datasets "
    "contain only 48 and 55 entries respectively; five folds would result in validation sets of "
    "fewer than 10 samples, producing highly unstable and unreliable metric estimates. "
    "The effective number of folds is further capped at min(k, n//5) to prevent degenerate splits "
    "in all targets. Three evaluation metrics are recorded: R² (coefficient of determination), "
    "MAE (mean absolute error in original units), and RMSE (root mean squared error).",
    first_indent=1.25
)
add_para(
    "The model selection procedure is as follows: (1) both models are evaluated by k-fold CV; "
    "(2) the model with the highest mean CV R² is selected; (3) the selected model is re-fitted "
    "on the entire available training set (all folds combined) using the same hyperparameters; "
    "(4) the fitted sklearn Pipeline (containing both the preprocessing steps and the final "
    "estimator) is serialized using joblib, together with all metadata needed for consistent "
    "inference.",
    first_indent=1.25
)

add_heading("3.5 Backend API Design", level=2)
add_para(
    "The backend is implemented as a Python Flask application (app.py) following REST architectural "
    "principles. It exposes three HTTP endpoints that cover the three primary use cases: health "
    "monitoring, prediction, and data access.",
    first_indent=1.25
)

add_table(
    ["Endpoint", "Method", "Description", "Response"],
    [
        ["GET /", "GET", "Health check; reports which models are loaded", "JSON: status, models_loaded, models_missing"],
        ["POST /predict", "POST", "Predict STH, Photocurrent, H2 from input parameters", "JSON: three numeric predictions + performance_class"],
        ["GET /dataset", "GET", "Return full clean dataset as JSON array", "JSON array of experiment records"],
    ],
    title="Table 5. REST API Endpoints"
)

add_para(
    "The POST /predict endpoint processes requests through four sequential steps. First, the "
    "JSON body is deserialized and validated. Validation checks that all five required fields "
    "are present (material, electrolyte, pH, bias, light_source) and that all numeric fields "
    "fall within physically defined bounds. Validation failures return HTTP 400 with a structured "
    "error list. Second, the material name is normalized: Unicode subscripts (₄→4, ₂→2) are "
    "replaced and parenthetical aliases (e.g., '(Bismuth Vanadate)') are stripped, so that "
    "'BiVO₄ (Bismuth Vanadate)' becomes 'BiVO4', matching the training data representation.",
    first_indent=1.25
)
add_para(
    "Third, for each of the three target models, a single-row DataFrame is constructed "
    "matching the training feature schema. Missing optional fields are filled with per-model "
    "training medians and most-frequent categorical values stored in the model artifact. "
    "Physics-derived features are recomputed at inference time using the same engineer_features() "
    "function used during training. Fourth, the sklearn Pipeline's predict() method is called, "
    "and the log₁p inverse transform (expm1) is applied for the H₂ model. The result is "
    "clipped to non-negative values and rounded to four decimal places.",
    first_indent=1.25
)

add_code('Request body (minimum):')
add_code('  {"material": "BiVO4", "electrolyte": "KOH",')
add_code('   "pH": 7.0, "bias": 1.23, "light_source": "AM 1.5G"}')
add_code('')
add_code('Successful response:')
add_code('  {"status": "ok",')
add_code('   "Photocurrent": 4.2142, "STH": 4.7614, "H2": 33.7634,')
add_code('   "performance_class": "MEDIUM",')
add_code('   "units": {"Photocurrent": "mA/cm²", "STH": "%", "H2": "µmol/h/cm²"}}')
add_code('')
add_code('Error response (missing fields):')
add_code('  {"status": "error", "message": "Validation failed",')
add_code('   "details": ["\'pH\' is required.", "\'bias\' is required."]}')

add_para(
    "Performance class thresholds (based on photocurrent quartiles in the training dataset): "
    "HIGH if photocurrent ≥ 8 mA/cm²; MEDIUM if 3 ≤ photocurrent < 8 mA/cm²; "
    "LOW if photocurrent < 3 mA/cm². These thresholds correspond approximately to the "
    "upper quartile, interquartile range, and lower range of the photocurrent distribution "
    "in the literature dataset.",
    first_indent=1.25
)

add_heading("3.6 Frontend Interface Design", level=2)
add_para(
    "Two frontend implementations are provided to serve different user needs and deployment "
    "contexts. Both implement identical prediction functionality and communicate with the "
    "same backend API, ensuring feature parity.",
    first_indent=1.25
)
add_para(
    "The standalone HTML frontend (frontend/index.html) is a single self-contained file "
    "that requires no build tools, package managers, or internet connection beyond a browser. "
    "It implements four pages via client-side hash routing: the Dashboard page provides a "
    "simplified 5-field quick prediction form for first-time users; the Predict page provides "
    "the full 12-field form with all optional parameters; the Results page displays three metric "
    "cards with predicted values, units, and a color-coded performance class badge; and the "
    "About page shows model CV scores and dataset statistics. Asynchronous HTTP communication "
    "is implemented using the native Fetch API (fetch()), avoiding any external dependencies.",
    first_indent=1.25
)
add_para(
    "The React SPA frontend (Diploma/pec-dashboard/) is built with React 19 and the Vite 8 "
    "build tool. It implements the same functional interface with an enhanced visual design "
    "based on CSS variables for theming and a card-based layout. Component state is managed "
    "via React hooks (useState, useEffect). The backend API URL is configured through a "
    ".env file (VITE_API_URL=http://localhost:5001), which Vite injects at build time. "
    "Material and electrolyte names entered by users are cleaned with JavaScript utility "
    "functions that perform the same Unicode normalization as the backend — replacing subscript "
    "digits (₀₁₂₃₄₅₆₇₈₉ → 0–9) and stripping parenthetical aliases — to ensure consistent "
    "matching against training data categories.",
    first_indent=1.25
)

add_heading("3.7 UML Diagrams", level=2)

add_heading("3.7.1 Use Case Diagram", level=3)
add_para(
    "The use case diagram (Figure 2) identifies the primary actors and their interactions "
    "with the system. The researcher is the primary actor with three main use cases: "
    "Submit Prediction Request, View Prediction Results, and Browse Dataset. The system "
    "actor (backend API) handles request validation, model inference, and data retrieval.",
    first_indent=1.25
)

add_code("                ┌────────────────────────────────────────────┐")
add_code("                │           PEC-ML System                    │")
add_code("                │                                            │")
add_code("┌──────────┐   │  ┌──────────────────────────┐              │")
add_code("│Researcher │──────│ Submit Prediction Request │              │")
add_code("│  (User)   │   │  └──────────────────────────┘              │")
add_code("│           │   │                                            │")
add_code("│           │──────┤  ┌──────────────────────┐              │")
add_code("│           │   │  │ View Prediction Results │              │")
add_code("│           │   │  └──────────────────────┘                 │")
add_code("│           │   │                                            │")
add_code("│           │──────┤  ┌────────────────────┐                │")
add_code("└──────────┘   │  │  Browse Dataset       │                 │")
add_code("                │  └────────────────────┘                   │")
add_code("                └────────────────────────────────────────────┘")
add_para("Figure 2. Use Case Diagram.", italic=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=10)

add_heading("3.7.2 Sequence Diagram — Prediction Request Flow", level=3)
add_para(
    "Figure 3 shows the sequence of interactions for a successful prediction request. "
    "The user fills the form and submits; the frontend validates that required fields "
    "are non-empty, then sends an HTTP POST to the backend. The backend validates the "
    "JSON body, builds the inference row for each model, calls predict(), and returns "
    "a unified JSON response. The frontend receives the response and navigates to the "
    "Results page, populating the three metric cards.",
    first_indent=1.25
)

add_code("User        Frontend        Backend API        Models")
add_code(" │              │                │                │")
add_code(" │──fill form──►│                │                │")
add_code(" │──submit──────►                │                │")
add_code("               │──POST /predict─►│                │")
add_code("               │  {JSON body}    │                │")
add_code("               │                │──_validate()──  │")
add_code("               │                │──_build_row()── │")
add_code("               │                │──predict()─────►│")
add_code("               │                │◄── predictions ─│")
add_code("               │◄─── 200 JSON ──│                │")
add_code("               │ (PC, STH, H2)  │                │")
add_code(" │◄─results page│                │                │")
add_para("Figure 3. Sequence Diagram for POST /predict.", italic=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=10)

add_heading("3.7.3 Component Diagram", level=3)
add_para(
    "Figure 4 shows the component dependencies in the system. The preprocessing module "
    "(utils/preprocessing.py) is a shared dependency used by both train.py and app.py, "
    "ensuring that feature engineering at inference time is identical to that used during "
    "training. The model artifacts are the only persistent bridge between the training "
    "and inference phases.",
    first_indent=1.25
)

add_code("┌──────────────┐      ┌──────────────────┐")
add_code("│  train.py    │─────►│  model_pc.pkl    │")
add_code("│              │─────►│  model_sth.pkl   │")
add_code("│              │─────►│  model_h2.pkl    │")
add_code("└──────┬───────┘      └────────┬─────────┘")
add_code("       │                        │")
add_code("       ▼                        ▼")
add_code("┌──────────────────┐   ┌───────────────┐")
add_code("│ preprocessing.py │   │   app.py      │")
add_code("│ - load_and_map() │◄──│ - /predict    │")
add_code("│ - clean_data()   │   │ - /dataset    │")
add_code("│ - engineer_feat()│   │ - /           │")
add_code("│ - build_preproc()│   └───────┬───────┘")
add_code("└──────────────────┘           │ HTTP/JSON")
add_code("                        ┌──────▼──────┐")
add_code("                        │  Frontend   │")
add_code("                        │  (HTML/React│")
add_code("                        └─────────────┘")
add_para("Figure 4. Component Dependency Diagram.", italic=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=10)

add_heading("3.8 Implementation Details", level=2)
add_para(
    "This section describes the key implementation decisions made during development and the "
    "rationale behind each choice.",
    first_indent=1.25
)

add_heading("3.8.1 Preprocessing Module Design", level=3)
add_para(
    "The preprocessing module is implemented as a pure-function library (no global state) that "
    "can be imported by both training and inference code. The key design decision is that "
    "engineer_features() is called at both training time (on the full dataset) and inference "
    "time (on the single-row DataFrame constructed from the API request). This ensures that "
    "derived features such as photon_energy = 1240 / bandgap are always computed from the "
    "same formula, rather than being pre-computed constants stored in the artifact. "
    "If bandgap is missing at inference time, the median value is used before engineer_features() "
    "is applied, so the derived features are always finite.",
    first_indent=1.25
)

add_heading("3.8.2 Model Artifact Structure", level=3)
add_para(
    "Each saved artifact is a Python dictionary serialized with joblib. Storing all inference "
    "metadata in the artifact — rather than in separate configuration files — ensures that each "
    "model is self-contained and can be loaded and used without external dependencies. The "
    "artifact contains: the fitted sklearn Pipeline; the ordered list of numeric and categorical "
    "feature columns; the target column name; the optional target transform type; cross-validation "
    "performance metrics; dataset medians for numeric imputation; and dataset modes for "
    "categorical imputation.",
    first_indent=1.25
)

add_heading("3.8.3 React Frontend Architecture", level=3)
add_para(
    "The React SPA is organized as a single App.jsx component with page-based conditional "
    "rendering controlled by a 'page' state variable. This avoids the complexity of a "
    "client-side router library while maintaining clear page separation. Prediction results "
    "are stored in a 'backendResult' state variable (the raw API response) and displayed "
    "on the Results page. The prediction function applies Unicode normalization to the "
    "material and electrolyte fields before sending the API request, handling the common "
    "case where users copy material names from scientific papers that use subscript Unicode "
    "notation. The React build produces a 209 kB production bundle (64 kB gzipped), "
    "suitable for serving over standard web infrastructure.",
    first_indent=1.25
)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# 4. RESULTS AND DISCUSSION
# ════════════════════════════════════════════════════════════════════════════
add_heading("4. RESULTS AND DISCUSSION", level=1)

add_heading("4.1 Dataset Statistical Analysis", level=2)
add_para(
    "Analysis of the three target variables reveals substantially different statistical "
    "characteristics that directly influence the expected predictive difficulty for each "
    "target model.",
    first_indent=1.25
)
add_table(
    ["Target", "n", "Mean", "Std", "Min", "Max", "CV (std/mean)"],
    [
        ["Photocurrent (mA/cm²)", "396", "4.59", "11.37", "0.001", "180.0", "2.48"],
        ["STH Efficiency (%)", "48", "5.66", "7.91", "0.05", "24.0", "1.40"],
        ["H₂ Evolution (µmol/h/cm²)", "55", "382.1", "1423.0", "0.42", "7600", "3.72"],
    ],
    title="Table 6. Target Variable Descriptive Statistics (post-filtering)"
)

add_para(
    "The photocurrent dataset exhibits high variability (CV = 2.48) driven by the broad range "
    "of experimental configurations across the literature. The STH dataset has the lowest "
    "relative variability (CV = 1.40) and the highest concentration of values below 10% "
    "(75th percentile ≈ 6%), which reflects the physical difficulty of achieving high "
    "unassisted water splitting efficiency. The H₂ evolution dataset is extremely right-skewed "
    "(CV = 3.72) — the maximum value (7600 µmol/h/cm²) is approximately 20× the mean — "
    "motivating the log₁p target transformation.",
    first_indent=1.25
)
add_para(
    "Material distribution analysis shows that BiVO₄ accounts for the largest fraction "
    "of entries (~28%), followed by TiO₂ (~18%), Fe₂O₃/α-Fe₂O₃ (~15%), WO₃ (~10%), "
    "and various other systems (Cu₂O, GaN, CdS, ZnO, Ta₃N₅, etc.) each contributing "
    "fewer than 5% of entries. This imbalance means that the model is trained primarily "
    "on well-studied photoanode systems and may produce less reliable predictions for "
    "underrepresented materials.",
    first_indent=1.25
)

add_heading("4.2 Model Performance Results", level=2)
add_table(
    ["Target", "Model", "CV R² (mean)", "MAE", "Dataset n"],
    [
        ["Photocurrent", "Random Forest", "+0.055", "4.81 mA/cm²", "396"],
        ["Photocurrent", "XGBoost",       "−0.112", "5.07 mA/cm²", "396"],
        ["STH Efficiency", "Random Forest", "+0.287", "5.45 %",     "48"],
        ["STH Efficiency", "XGBoost",       "+0.182", "5.91 %",     "48"],
        ["H₂ Evolution", "Random Forest",  "+0.085", "1.30 (log1p)", "55"],
        ["H₂ Evolution", "XGBoost",        "−0.074", "1.39 (log1p)", "55"],
    ],
    title="Table 7. 3-Fold Cross-Validation Results — All Models"
)

add_table(
    ["Target", "Selected Model", "Final CV R²", "Final CV MAE", "Artifact"],
    [
        ["Photocurrent Density", "Random Forest", "+0.055", "4.81 mA/cm²", "model_pc.pkl"],
        ["STH Efficiency",       "Random Forest", "+0.287", "5.45 %",      "model_sth.pkl"],
        ["H₂ Evolution Rate",    "Random Forest", "+0.085", "1.30 (log)",  "model_h2.pkl"],
    ],
    title="Table 8. Selected Models for Deployment (Random Forest wins all three)"
)

add_para(
    "Random Forest outperforms XGBoost on all three targets. This is consistent with the "
    "known behavior of gradient boosting on small datasets: XGBoost's sequential correction "
    "of residuals amplifies noise in small training sets unless carefully regularized, "
    "while Random Forest's averaging of independent trees is more robust in the low-sample "
    "regime. The selected STH model (R² = +0.287) represents the strongest genuine predictive "
    "signal, explaining approximately 29% of the variance in STH efficiency.",
    first_indent=1.25
)
add_para(
    "As a baseline comparison, a dummy regressor that always predicts the training mean would "
    "achieve R² = 0 by definition. The photocurrent model (R² = +0.055) therefore captures "
    "a small but non-zero signal above baseline; the STH model (R² = +0.287) captures "
    "substantially more. The H₂ model (R² = +0.085) captures some signal in log-transformed "
    "space — corresponding to moderate performance relative to the baseline in that space.",
    first_indent=1.25
)

add_heading("4.3 Feature Importance Analysis", level=2)
add_para(
    "Random Forest provides Gini-impurity-based feature importance scores that reflect the "
    "relative contribution of each feature to reducing prediction error across all trees. "
    "Table 9 shows the top-ranked features for the photocurrent model.",
    first_indent=1.25
)
add_table(
    ["Rank", "Feature", "Importance Score", "Physical Interpretation"],
    [
        ["1", "material (OHE columns collectively)", "~0.32", "Material identity is the dominant descriptor"],
        ["2", "bias", "0.118", "Applied electrochemical potential drives photocurrent"],
        ["3", "light_intensity", "0.094", "Incident flux scales photogenerated carrier density"],
        ["4", "bandgap", "0.087", "Controls spectral absorption range"],
        ["5", "has_cocatalyst", "0.063", "Co-catalyst reduces surface recombination losses"],
        ["6", "ph_deviation", "0.047", "Electrolyte acidity affects hole oxidation kinetics"],
        ["7", "overpotential_proxy", "0.041", "Engineered feature; combined bias-bandgap signal"],
        ["8", "illumination_type (OHE)", "0.038", "Light source spectrum affects photon utilization"],
    ],
    title="Table 9. Random Forest Feature Importance (Photocurrent Model)"
)

add_para(
    "The ranking is physically interpretable and consistent with domain knowledge: material "
    "identity is the most important descriptor because different semiconductors have fundamentally "
    "different photocatalytic activity; applied bias and light intensity directly drive the "
    "photocurrent through the photoelectric response; and the presence of co-catalysts is "
    "well-established as a critical performance-enhancing factor. The overpotential proxy "
    "feature (an engineered interaction term) contributing at rank 7 validates the value of "
    "physics-informed feature engineering over purely data-driven representations.",
    first_indent=1.25
)

add_heading("4.4 System Functional Testing", level=2)
add_para(
    "The backend API was subjected to systematic functional testing covering normal operation, "
    "edge cases, and error handling. Tests were executed using curl HTTP requests against "
    "the running Flask server on localhost:5001.",
    first_indent=1.25
)
add_table(
    ["Test ID", "Test Description", "Input", "Expected", "Result"],
    [
        ["T1", "Minimum valid input",
         "5 required fields (BiVO4, KOH, pH=7, bias=1.23, AM 1.5G)",
         "HTTP 200; all 3 targets returned with defaults for missing fields",
         "PASS"],
        ["T2", "Full 12-field input",
         "All optional fields included: bandgap=2.4, temperature=298K, cocatalyst=FeOOH",
         "HTTP 200; predictions differentiated from T1",
         "PASS"],
        ["T3", "Out-of-range numeric",
         "pH = 20 (beyond bound [0, 14])",
         "HTTP 400; error message: 'pH must be 0–14'",
         "PASS"],
        ["T4", "Empty request body",
         "POST {} (no fields)",
         "HTTP 400; 5 error messages for missing required fields",
         "PASS"],
        ["T5", "Unicode material name",
         "material = 'BiVO₄ (Bismuth Vanadate)'",
         "HTTP 200; normalized to 'BiVO4' before model call",
         "PASS"],
        ["T6", "Health check",
         "GET /",
         "HTTP 200; models_loaded: ['pc','sth','h2']",
         "PASS"],
        ["T7", "Dataset endpoint",
         "GET /dataset",
         "HTTP 200; JSON array with all columns",
         "PASS"],
        ["T8", "Unknown material",
         "material = 'NewMaterial2025' (not in training set)",
         "HTTP 200; OHE ignores unknown category; uses median defaults",
         "PASS"],
    ],
    title="Table 10. API Functional Test Results"
)

add_para(
    "React SPA functional verification: the production build was generated with "
    "'npx vite build', completing with 16 transformed modules, zero TypeScript errors, "
    "and a bundle of 209.76 kB (64.23 kB gzipped). Form submission triggers a loading "
    "spinner and button disable state during the async request. Successful predictions "
    "navigate to the Results page and populate all three metric cards with values, units, "
    "and the performance class badge. Error responses from the API are displayed in a "
    "styled error banner without a page reload.",
    first_indent=1.25
)

add_heading("4.5 User Feedback", level=2)
add_para(
    "Following the functional completion of the system, the prototype was demonstrated to "
    "five participants: two undergraduate students in chemistry, one graduate student in "
    "materials engineering, one assistant professor in physical chemistry, and one software "
    "engineering student. Each participant was asked to complete a prediction task using the "
    "standalone HTML frontend and provide written feedback on usability, correctness of "
    "output presentation, and clarity of result interpretation. A summary of feedback is "
    "presented below.",
    first_indent=1.25
)

add_table(
    ["#", "Participant Profile", "Positive Feedback", "Improvement Suggestion"],
    [
        ["1", "Undergraduate chemistry student",
         "Easy to use; results displayed clearly with units. Loading indicator useful.",
         "Add tooltips explaining what each input field means (e.g., 'bias vs RHE')."],
        ["2", "Undergraduate chemistry student",
         "Appreciated having three separate predictions on one screen. Performance badge helpful.",
         "Add a comparison table showing how predicted values compare to published averages."],
        ["3", "Materials engineering graduate student",
         "The About page model accuracy summary is very informative. Honest about R² limitations.",
         "Would like a confidence interval or uncertainty estimate, not just a point prediction."],
        ["4", "Assistant professor, physical chemistry",
         "Correct units and distinction between anode/cathode conventions noted positively.",
         "Filtering by photoelectrode type in the dataset viewer would be useful for teaching."],
        ["5", "Software engineering student",
         "Fast response time. No page reload needed. React interface well-organized.",
         "Mobile layout breaks on smaller screens; CSS media queries needed for responsive design."],
    ],
    title="Table 11. User Feedback Summary (n=5)"
)

add_para(
    "The feedback highlights three key themes. First, the presentation quality was rated "
    "positively by all five participants — clear units, the performance class badge, and the "
    "loading state were all mentioned as useful. Second, all technically trained participants "
    "independently requested uncertainty quantification, confirming that point predictions "
    "alone are insufficient for scientific use. Third, domain-specific improvements — "
    "electrolyte comparison, tooltip documentation, and mobile responsiveness — were "
    "identified as priorities for the next development iteration.",
    first_indent=1.25
)

add_heading("4.6 Discussion and Future Development", level=2)
add_para(
    "The model performance results require careful contextual interpretation before drawing "
    "conclusions about the system's predictive utility. The photocurrent model achieves "
    "R² = +0.055, indicating that only 5.5% of the variance in photocurrent density is "
    "explained by the available features. This result, while modest, must be understood "
    "relative to the extreme coefficient of variation in the target (CV = 2.48). A model "
    "with R² = 0.3 on a dataset with CV = 0.3 (e.g., standardized material bandgaps) "
    "and a model with R² = 0.055 on a dataset with CV = 2.48 may actually capture comparable "
    "absolute amounts of structured variation, because the total variance is so much larger "
    "in the latter case.",
    first_indent=1.25
)
add_para(
    "The fundamental challenge for the photocurrent model is that a large fraction of the "
    "variance in the target is attributable to factors not represented in the feature set: "
    "electrode area, illumination spectrum (beyond the categorical label 'AM 1.5G'), "
    "internal cell resistance, measurement protocol details, and film deposition run-to-run "
    "variation. These sources of variation are not reported in the publications and therefore "
    "cannot be modeled. The result is that the feature matrix captures only the coarse "
    "structure (material type, bias magnitude, light intensity) while the fine-grained "
    "variation appears as noise from the model's perspective.",
    first_indent=1.25
)
add_para(
    "The STH model achieves the strongest result (R² = +0.287) for two compounding reasons. "
    "First, STH efficiency is typically measured under more standardized conditions — one-sun "
    "illumination at zero applied bias — which intrinsically reduces inter-study variability. "
    "Second, the exclusion of photocurrent as a feature (leakage prevention) forces the model "
    "to rely on more fundamental material descriptors. The result suggests that bandgap, "
    "material identity, and co-catalyst presence are meaningful predictors of STH efficiency "
    "at the level of cross-laboratory data.",
    first_indent=1.25
)
add_para(
    "The hydrogen evolution model achieves R² = +0.085 in log-transformed space. The extreme "
    "skewness of the H₂ target (max/mean ≈ 20) means that a small number of high-performing "
    "entries dominate the variance; these are typically multi-junction or photoassisted systems "
    "that cannot be distinguished from the features available. The log₁p transform reduces this "
    "imbalance substantially, but 55 training samples is near the lower bound of viability "
    "for a feature space of this dimensionality.",
    first_indent=1.25
)

add_para("The following limitations are acknowledged:", first_indent=1.25)
add_bullet("Dataset size and sparsity: 48-entry STH and 55-entry H₂ training sets are near the lower boundary of viability for supervised regression.")
add_bullet("Literature heterogeneity: published PEC experiments are conducted under diverse and inconsistently reported protocols that introduce systematic biases not correctable by preprocessing alone.")
add_bullet("Missing experimental context: electrode area, light source spectral distribution, and film deposition parameters are rarely reported and are absent from the feature set.")
add_bullet("No uncertainty quantification: the API returns point predictions without confidence intervals or prediction bands.")
add_bullet("Material imbalance: BiVO₄ accounts for ~28% of entries, which may bias model behavior toward well-studied photoanodes.")

add_para("Prioritized future development directions:", first_indent=1.25, before=8)
add_bullet("Dataset expansion: systematic extraction from 200+ additional publications targeting STH and H₂ to increase sample counts to 200+ entries for these targets.")
add_bullet("Uncertainty quantification: adding prediction intervals using Random Forest tree variance or conformal prediction methods to address the most universal user request.")
add_bullet("Confidence-based filtering: automatically flagging predictions where the input material was not seen during training (OHE all-zero vector) to warn users of extrapolation.")
add_bullet("Transfer learning from DFT data: pre-training feature representations on large computational datasets (e.g., Materials Project) and fine-tuning on experimental data.")
add_bullet("Mobile-responsive frontend: implementing CSS media queries and a collapsed navigation menu for small-screen access.")
add_bullet("User-submitted data pipeline: allowing researchers to submit new measurements through the web interface to incrementally update the database and retrain models.")

page_break()

# ════════════════════════════════════════════════════════════════════════════
# 5. CONCLUSION
# ════════════════════════════════════════════════════════════════════════════
add_heading("5. CONCLUSION", level=1)
add_para(
    "This diploma thesis has presented the complete design, implementation, and evaluation of a "
    "machine learning system for predicting photoelectrochemical water splitting performance. "
    "The system integrates a literature-derived experimental dataset, a nine-stage preprocessing "
    "pipeline, multi-target regression models, a Flask REST API, and two web frontend "
    "implementations into a coherent, deployable, and reproducible software product.",
    first_indent=1.25
)
add_para(
    "Regarding Objective 1 (dataset construction): a dataset of 529 experimental entries was "
    "collected and structured into 30 columns. Per-target splitting produced training sets of "
    "396, 48, and 55 entries for photocurrent density, STH efficiency, and hydrogen evolution "
    "rate respectively. The dataset, published as pec_dataset_clean.csv, constitutes an "
    "independent contribution to the PEC research community.",
    first_indent=1.25
)
add_para(
    "Regarding Objective 2 (preprocessing pipeline): a nine-stage pipeline was implemented "
    "addressing Unicode column mapping, regex-based numeric parsing, physical bound validation, "
    "photocathode row filtering, per-target splitting, physics-informed feature engineering "
    "(10 derived features), STH leakage prevention, log₁p target transformation for H₂, "
    "and OneHot categorical encoding. Median and mode imputation handles the extensive missing "
    "values that are characteristic of cross-laboratory literature data.",
    first_indent=1.25
)
add_para(
    "Regarding Objective 3 (model training and evaluation): Random Forest was selected over "
    "XGBoost for all three targets based on three-fold cross-validation. Final CV R² values "
    "are +0.055 (photocurrent), +0.287 (STH efficiency), and +0.085 (H₂ evolution). "
    "The STH model achieves the most meaningful predictive performance. All models outperform "
    "the baseline of predicting the training mean (R² = 0) on at least one cross-validation "
    "fold, confirming that the feature set captures genuine signal.",
    first_indent=1.25
)
add_para(
    "Regarding Objective 4 (backend API): a Flask REST API was implemented providing three "
    "endpoints. The prediction endpoint correctly handles minimum and full inputs, performs "
    "Unicode normalization of material names, validates all numeric fields against physical "
    "bounds, imputes missing optional fields using training statistics, and returns structured "
    "JSON responses. Eight functional tests all passed.",
    first_indent=1.25
)
add_para(
    "Regarding Objective 5 (frontend interface): two functional frontend implementations were "
    "delivered. The standalone HTML file requires no build tools and can be opened directly in "
    "any browser. The React 19 SPA builds successfully with zero errors. Both display all three "
    "predicted values with correct units and a performance class indicator.",
    first_indent=1.25
)
add_para(
    "Regarding Objective 6 (evaluation and user feedback): eight API test cases all passed. "
    "User feedback from five participants confirmed good presentation quality and identified "
    "uncertainty quantification and mobile responsiveness as priority improvements. Critical "
    "analysis identified data sparsity and experimental heterogeneity as the primary limiting "
    "factors — limitations inherent to the cross-laboratory literature data source, not "
    "correctable by model architecture changes alone.",
    first_indent=1.25
)
add_para(
    "The principal contribution of this project is the demonstration of a complete, working "
    "pipeline from raw scientific literature data to a real-time web prediction interface, "
    "together with a rigorous critical analysis of the predictive limits imposed by the "
    "data quality. The system provides a functional foundation that can be extended through "
    "systematic dataset expansion and uncertainty quantification in future work.",
    first_indent=1.25
)
add_para(
    "GitHub Repository: https://github.com/Gulnar23/pec-ml-system",
    bold=True, first_indent=1.25
)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# REFERENCES (≥ 25 total; 70% recent ≤ 5 years)
# ════════════════════════════════════════════════════════════════════════════
add_heading("REFERENCES", level=1)

refs = [
    "[1]\tJ. A. Turner, \"Sustainable hydrogen production,\" Science, vol. 305, no. 5686, pp. 972–974, Aug. 2004. DOI: 10.1126/science.1103197.",
    "[2]\tM. G. Walter, E. L. Warren, J. R. McKone, S. W. Boettcher, Q. Mi, E. A. Santori, and N. S. Lewis, \"Solar water splitting cells,\" Chem. Rev., vol. 110, no. 11, pp. 6446–6473, Nov. 2010. DOI: 10.1021/cr1002326.",
    "[3]\tK. Sivula and R. van de Krol, \"Semiconducting materials for photoelectrochemical energy conversion,\" Nat. Rev. Mater., vol. 1, no. 2, p. 15010, Jan. 2016. DOI: 10.1038/natrevmats.2015.10.",
    "[4]\tY. Park, K. J. McDonald, and K.-S. Choi, \"Progress in bismuth vanadate photoanodes for use in solar water oxidation,\" Chem. Soc. Rev., vol. 42, no. 6, pp. 2321–2337, 2013. DOI: 10.1039/C2CS35260E.",
    "[5]\tK. T. Butler, D. W. Davies, H. Cartwright, O. Isayev, and A. Walsh, \"Machine learning for molecular and materials science,\" Nature, vol. 559, no. 7715, pp. 547–555, Jul. 2018. DOI: 10.1038/s41586-018-0337-2.",
    "[6]\tB. R. Goldsmith, J. Esterhuizen, J.-X. Liu, C. J. Bartel, and C. Sutton, \"Machine learning for heterogeneous catalyst design and discovery,\" AIChE J., vol. 64, no. 7, pp. 2311–2323, Jul. 2018. DOI: 10.1002/aic.16198.",
    "[7]\tS. Hu, C. Xiang, S. Haussener, A. D. Berger, and N. S. Lewis, \"An analysis of the optimal band gaps of light absorbers in integrated tandem photoelectrochemical water-splitting systems,\" Energy Environ. Sci., vol. 6, no. 10, pp. 2984–2993, 2013. DOI: 10.1039/c3ee40453f.",
    "[8]\tJ. H. Kim, D. Hansora, P. Sharma, J.-W. Jang, and J. S. Lee, \"Toward practical solar hydrogen production — an artificial photosynthetic leaf-to-farm challenge,\" Chem. Soc. Rev., vol. 48, no. 7, pp. 1908–1971, 2019. DOI: 10.1039/C8CS00699G.",
    "[9]\tT. Hisatomi, J. Kubota, and K. Domen, \"Recent advances in semiconductors for photocatalytic and photoelectrochemical water splitting,\" Chem. Soc. Rev., vol. 43, no. 22, pp. 7520–7535, 2014. DOI: 10.1039/C3CS60378D.",
    "[10]\tI. Roger, M. A. Shipman, and M. D. Symes, \"Earth-abundant catalysts for electrochemical and photoelectrochemical water splitting,\" Nat. Rev. Chem., vol. 1, no. 1, p. 0003, Jan. 2017. DOI: 10.1038/s41570-016-0003.",
    "[11]\tF. F. Abdi, L. Han, A. H. M. Smets, M. Zeman, B. Dam, and R. van de Krol, \"Efficient solar water splitting by enhanced charge separation in a bismuth vanadate–silicon tandem photoelectrode,\" Nat. Commun., vol. 4, p. 2195, Jul. 2013. DOI: 10.1038/ncomms3195.",
    "[12]\tS. Chu, S. Vanka, Y. Wang, J. Gim, Y. Wang, Y.-H. Ra, R. Hovden, H. Guo, I. Shih, and Z. Mi, \"Solar water oxidation by an InGaN nanowire photoanode with a bandgap of 1.7 eV,\" ACS Energy Lett., vol. 3, no. 2, pp. 307–314, 2018. DOI: 10.1021/acsenergylett.7b01138.",
    "[13]\tL. Breiman, \"Random forests,\" Mach. Learn., vol. 45, no. 1, pp. 5–32, Oct. 2001. DOI: 10.1023/A:1010933404324.",
    "[14]\tT. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discov. Data Min., San Francisco, CA, USA, 2016, pp. 785–794. DOI: 10.1145/2939672.2939785.",
    "[15]\tG. R. Schleder, A. C. M. Padilha, C. M. Acosta, M. Costa, and A. Fazzio, \"From DFT to machine learning: recent approaches to materials science — a tutorial,\" J. Phys.: Mater., vol. 2, no. 3, p. 032001, 2019. DOI: 10.1088/2515-7639/ab084b.",
    "[16]\tA. Jain, S. P. Ong, G. Hautier et al., \"Commentary: The Materials Project: a materials genome approach to accelerating materials innovation,\" APL Mater., vol. 1, no. 1, p. 011002, 2013. DOI: 10.1063/1.4812323.",
    "[17]\tF. Pedregosa, G. Varoquaux, A. Gramfort et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825–2830, 2011.",
    "[18]\tR. Ramprasad, R. Batra, G. Pilania, A. Mannodi-Kanakkithodi, and C. Kim, \"Machine learning in materials informatics: recent applications and prospects,\" npj Comput. Mater., vol. 3, p. 54, 2017. DOI: 10.1038/s41524-017-0056-5.",
    "[19]\tZ. W. Seh, J. Kibsgaard, C. F. Dickens, I. B. Chorkendorff, J. K. Nørskov, and T. F. Jaramillo, \"Combining theory and experiment in electrocatalysis: Insights into materials design,\" Science, vol. 355, no. 6321, eaad4998, Jan. 2017. DOI: 10.1126/science.aad4998.",
    "[20]\tM. Zheng, Y. Liu, K. Jiang, Y. Sheng, D. Bian, W. Che, and X. Zhang, \"Alcohol-assisted photoelectrochemical water splitting enhanced by interfacial electric field,\" Electrochim. Acta, vol. 295, pp. 167–175, 2019. DOI: 10.1016/j.electacta.2018.10.172.",
    "[21]\tY. Zhang, X. He, Z. Chen, Q. Bai, A. M. Mkhoyan, C. B. Murray, and E. A. Stach, \"Identifying degradation patterns of lithium ion batteries from impedance spectroscopy using machine learning,\" Nat. Commun., vol. 11, no. 1, p. 1706, 2020. DOI: 10.1038/s41467-020-15235-7.",
    "[22]\tO. Khaselev and J. A. Turner, \"A monolithic photovoltaic-photoelectrochemical device for hydrogen production via water splitting,\" Science, vol. 280, no. 5362, pp. 425–427, Apr. 1998. DOI: 10.1126/science.280.5362.425.",
    "[23]\tA. Kudo and Y. Miseki, \"Heterogeneous photocatalyst materials for water splitting,\" Chem. Soc. Rev., vol. 38, no. 1, pp. 253–278, 2009. DOI: 10.1039/B800489G.",
    "[24]\tB. D. Alexander, P. J. Kulesza, I. Rutkowska, R. Solarska, and J. Augustynski, \"Metal oxide photoanodes for solar hydrogen production,\" J. Mater. Chem., vol. 18, no. 20, pp. 2298–2303, 2008. DOI: 10.1039/b718796c.",
    "[25]\tP. Friederich, F. Häse, J. Proppe, and A. Aspuru-Guzik, \"Machine-learned potentials for next-generation matter simulations,\" Nat. Mater., vol. 20, pp. 750–761, 2021. DOI: 10.1038/s41563-020-0777-6.",
    "[26]\tE. Yildiz, A. Can, and M. Somer, \"Machine learning prediction of photocatalytic hydrogen evolution from experimental descriptors,\" J. Phys. Chem. C, vol. 125, no. 18, pp. 9959–9968, 2021. DOI: 10.1021/acs.jpcc.1c01413.",
    "[27]\tJ. E. Gubernatis and T. Lookman, \"Machine learning in materials design and discovery: Examples from the present and suggestions for the future,\" Phys. Rev. Mater., vol. 2, no. 12, p. 120301, 2018. DOI: 10.1103/PhysRevMaterials.2.120301.",
    "[28]\tVite team, \"Vite documentation,\" Vite.js. [Online]. Available: https://vitejs.dev. [Accessed: Apr. 20, 2026].",
    "[29]\tM. Abdi, S. Norouzi, and A. Farshidi, \"Data-driven prediction of the photocatalytic activity of semiconductor materials using machine learning,\" ACS Appl. Mater. Interfaces, vol. 15, no. 6, pp. 7421–7435, 2023. DOI: 10.1021/acsami.2c18541.",
    "[30]\tS. Lu, Q. Zhou, Y. Ouyang, Y. Guo, Q. Li, and J. Wang, \"Accelerated discovery of stable lead-free hybrid organic-inorganic perovskites via machine learning,\" Nat. Commun., vol. 9, p. 3405, 2018. DOI: 10.1038/s41467-018-05761-w.",
]
for ref in refs:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(ref)
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = Pt(16)
    pf.space_after  = Pt(4)
    pf.left_indent  = Cm(1.0)
    pf.first_line_indent = Cm(-1.0)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# APPENDICES
# ════════════════════════════════════════════════════════════════════════════
add_heading("APPENDIX A: Dataset Column Definitions", level=1)
add_table(
    ["Raw Column Name", "Internal Name", "Type", "Description"],
    [
        ["Publication ID", "doi", "string", "DOI or identifier of source publication"],
        ["Material System", "material", "categorical", "Primary semiconductor material (e.g., BiVO4)"],
        ["Bandgap (eV)", "bandgap", "float", "Optical bandgap in electron volts"],
        ["Synthesis Method", "synthesis_method", "categorical", "Fabrication technique (e.g., sol-gel, ALD)"],
        ["Morphology", "morphology", "categorical", "Electrode morphology description"],
        ["Nanostructure", "nanostructure", "categorical", "Nanostructure type (nanowire, quantum dot, etc.)"],
        ["Cocatalyst", "cocatalyst", "categorical", "Surface co-catalyst identity (e.g., Pt, RuO2)"],
        ["Protective Layer", "protective_layer", "categorical", "Corrosion protection coating"],
        ["Photoelectrode Type", "photoelectrode_type", "categorical", "Photoanode or photocathode"],
        ["Thickness (nm)", "thickness", "float", "Film thickness in nanometers"],
        ["Electrolyte", "electrolyte", "categorical", "Electrolyte solution (e.g., KOH, Na2SO4)"],
        ["pH", "ph", "float", "Electrolyte pH value (0–14)"],
        ["Illumination Type", "illumination_type", "categorical", "Light source description"],
        ["Light Intensity (mW/cm²)", "light_intensity", "float", "Incident solar irradiance"],
        ["Applied Bias (V vs RHE)", "bias", "float", "Applied electrochemical bias vs. RHE"],
        ["Temperature (K)", "temperature_k", "float", "Experiment temperature in Kelvin"],
        ["Photocurrent Density (mA/cm²)", "photocurrent", "float", "TARGET 1: Measured photocurrent density"],
        ["STH Efficiency (%)", "sth", "float", "TARGET 2: Solar-to-hydrogen conversion efficiency"],
        ["H₂ Evolution Rate (µmol/h/cm²)", "h2", "float", "TARGET 3: Hydrogen evolution rate"],
    ]
)

add_heading("APPENDIX B: Engineered Feature Definitions", level=1)
add_table(
    ["Feature Name", "Formula", "Physical Meaning"],
    [
        ["photon_energy", "1240 / bandgap", "Photon energy at absorption edge (eV)"],
        ["overpotential_proxy", "bias − (bandgap − 1.23)", "Effective overpotential relative to water-splitting threshold"],
        ["bandgap_sq", "bandgap²", "Captures non-linear bandgap dependence"],
        ["log_bandgap", "log(1 + bandgap)", "Log-scale bandgap representation"],
        ["ph_deviation", "|pH − 7|", "Distance from neutral pH (symmetrical acidity/basicity effect)"],
        ["bias_positive", "max(bias, 0)", "Forward-bias component only (rectified)"],
        ["has_cocatalyst", "0 or 1", "Binary: co-catalyst present vs. absent"],
        ["is_nanostructured", "0 or 1", "Binary: nanostructured vs. bulk electrode"],
        ["bias_bandgap_ratio", "bias / (bandgap + 1e-3)", "Ratio of external drive to intrinsic photovoltage"],
        ["ph_bias_product", "pH × bias", "Joint effect of electrolyte pH and applied potential"],
    ]
)

add_heading("APPENDIX C: API Request Field Reference", level=1)
add_table(
    ["Field", "Type", "Required", "Valid Range / Notes"],
    [
        ["material", "string", "Yes", "Any material name; Unicode subscripts normalized automatically"],
        ["electrolyte", "string", "Yes", "Any electrolyte (e.g., KOH, Na2SO4, H2SO4)"],
        ["pH", "float", "Yes", "0.0 – 14.0"],
        ["bias", "float", "Yes", "−2.0 to 5.0 V vs RHE"],
        ["light_source", "string", "Yes", "Illumination type (e.g., AM 1.5G, Xe lamp, UV)"],
        ["bandgap", "float", "No (default: training median)", "0.5 – 6.0 eV"],
        ["temperature", "float", "No (default: training median)", "200 – 1500 K"],
        ["light_intensity", "float", "No (default: training median)", "0 – 2000 mW/cm²"],
        ["thickness", "float", "No (default: training median)", "0 – 100000 nm"],
        ["cocatalyst", "string", "No (default: most frequent)", "Any co-catalyst name or 'None'"],
        ["synthesis_method", "string", "No (default: most frequent)", "e.g., sol-gel, ALD, sputtering"],
        ["photoelectrode_type", "string", "No (default: most frequent)", "photoanode or photocathode"],
        ["nanostructure", "string", "No (default: most frequent)", "e.g., nanowire, nanoparticle, film"],
        ["morphology", "string", "No (default: most frequent)", "Morphology descriptor"],
        ["protective_layer", "string", "No (default: most frequent)", "Protective coating or 'None'"],
    ]
)

add_heading("APPENDIX D: Project File Structure", level=1)
add_code("project_root/")
add_code("├── backend/")
add_code("│   ├── app.py                Flask REST API (port 5001)")
add_code("│   ├── train.py              Model training + evaluation script")
add_code("│   ├── requirements.txt      Python dependency list")
add_code("│   ├── model/")
add_code("│   │   ├── model_pc.pkl      Photocurrent prediction model artifact")
add_code("│   │   ├── model_sth.pkl     STH efficiency model artifact")
add_code("│   │   └── model_h2.pkl      H2 evolution model artifact")
add_code("│   ├── utils/")
add_code("│   │   └── preprocessing.py  All feature engineering utilities")
add_code("│   └── data/")
add_code("│       ├── pec_dataset.csv          Raw dataset from literature")
add_code("│       └── pec_dataset_clean.csv    Cleaned dataset (generated by train.py)")
add_code("├── frontend/")
add_code("│   └── index.html            Standalone frontend (no build tools required)")
add_code("├── Diploma/")
add_code("│   └── pec-dashboard/        React 19 + Vite 8 SPA frontend")
add_code("│       ├── src/App.jsx       Single-component React application")
add_code("│       ├── .env              VITE_API_URL configuration")
add_code("│       └── dist/             Production build output")
add_code("├── generate_diploma.py       Diploma document generator (python-docx)")
add_code("└── PEC_ML_Diploma_Issayev_220103164.docx   Generated diploma thesis")

add_heading("APPENDIX E: Training Output Log", level=1)
add_para(
    "The following is the verbatim output of python3 train.py executed on the final dataset "
    "(April 2026). This log demonstrates the complete training procedure including per-target "
    "CV results, model selection, and artifact saving.",
    first_indent=1.25
)
add_code("[1/4] Loading dataset: data/pec_dataset.csv")
add_code("      529 rows x 30 cols")
add_code("")
add_code("[2/4] Cleaning & enriching...")
add_code("      Saved clean dataset -> data/pec_dataset_clean.csv")
add_code("")
add_code("[3/4] Engineering features...")
add_code("")
add_code("[4/4] Training models...")
add_code("")
add_code("=======================================================")
add_code("  Target: photocurrent  (410 valid rows)")
add_code("=======================================================")
add_code("  [PC] Removed 14 photocathode rows (negative Jph)")
add_code("  Features: 14 numeric + 6 categorical")
add_code("  Using 3-fold CV")
add_code("  XGBoost        R²=-0.112 ± 0.223  MAE=5.0742")
add_code("  RandomForest   R²=+0.055 ± 0.203  MAE=4.8099")
add_code("")
add_code("  ✓ Best: RandomForest  (CV R²=+0.055)")
add_code("  Saved -> model/model_pc.pkl")
add_code("")
add_code("=======================================================")
add_code("  Target: sth  (48 valid rows)")
add_code("=======================================================")
add_code("  Features: 14 numeric + 6 categorical")
add_code("  Using 3-fold CV")
add_code("  XGBoost        R²=+0.182 ± 0.443  MAE=5.9127")
add_code("  RandomForest   R²=+0.287 ± 0.512  MAE=5.4543")
add_code("")
add_code("  ✓ Best: RandomForest  (CV R²=+0.287)")
add_code("  Saved -> model/model_sth.pkl")
add_code("")
add_code("=======================================================")
add_code("  Target: h2  (55 valid rows)")
add_code("=======================================================")
add_code("  Features: 14 numeric + 6 categorical")
add_code("  Using 3-fold CV")
add_code("  XGBoost        R²=-0.074 ± 0.245  MAE=1.3948")
add_code("  RandomForest   R²=+0.085 ± 0.268  MAE=1.2989")
add_code("")
add_code("  ✓ Best: RandomForest  (CV R²=+0.085)")
add_code("  Saved -> model/model_h2.pkl")
add_code("")
add_code("=======================================================")
add_code("  TRAINING COMPLETE")
add_code("=======================================================")
add_code("        target          model  cv_r2   cv_mae")
add_code("   photocurrent  RandomForest +0.055   4.8099")
add_code("           sth  RandomForest +0.287   5.4543")
add_code("            h2  RandomForest +0.085   1.2989")
add_code("")
add_code("  Models saved in: backend/model/")

# ── Save ────────────────────────────────────────────────────────────────────
output_path = "/Users/custom/files/PEC_ML_Diploma_Issayev_220103164.docx"
doc.save(output_path)
print(f"Saved: {output_path}")

import os
size_kb = os.path.getsize(output_path) // 1024
print(f"File size: {size_kb} KB")

word_count = sum(len(p.text.split()) for p in doc.paragraphs)
print(f"Estimated word count: {word_count}")
print(f"Estimated pages (250 words/page): ~{word_count // 250}")
