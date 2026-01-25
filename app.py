import streamlit as st
import pandas as pd
import numpy as np
import re
import os

# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(
    page_title="Sepsis Heterogeneity Score (SHScore)",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CSS STYLING (Fixed for Button & Fonts)
# ==========================================
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* 1. Fix Top Spacing to show Title */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 5rem !important;
    }

    /* 2. SUPER GREEN BUTTON FIX */
    /* Targeting the button more aggressively */
    div.stButton > button {
        background-color: #2e7d32 !important; /* Vivid Green */
        color: #ffffff !important;            /* White Text */
        border: 3px solid #1b5e20 !important; /* Dark Green Border */
        border-radius: 15px !important;
        padding: 15px 30px !important;
        font-size: 32px !important;           /* Huge Font */
        font-weight: 900 !important;          /* Extra Bold */
        height: auto !important;
        min-height: 90px !important;          /* Taller Button */
        width: 100% !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        margin-top: 40px !important;
        display: block !important;
        transition: all 0.3s ease !important;
    }
    
    /* Hover State */
    div.stButton > button:hover {
        background-color: #1b5e20 !important; /* Darker Green on Hover */
        border-color: #004d40 !important;
        color: #ffffff !important;
        transform: scale(1.02) !important;
    }
    
    /* Active/Clicked State */
    div.stButton > button:active, div.stButton > button:focus {
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        border: none !important;
        outline: none !important;
    }
    
    /* Force text inside button to be white and big */
    div.stButton > button p {
        font-size: 32px !important;
        color: white !important;
    }

    /* 3. Subgroup Options (Radio Buttons) - Bigger Font */
    div[role="radiogroup"] label p {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #333 !important;
    }
    div[role="radiogroup"] {
        gap: 20px;
    }
    div[role="radiogroup"] label {
        padding: 20px !important;
        background: #f8f9fa;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
    }

    /* 4. Input Labels (Variable Names) - Bigger Font */
    .stNumberInput label p {
        font-size: 28px !important;
        font-weight: 900 !important;
        color: #000 !important;
    }
    .stNumberInput input {
        font-size: 22px !important;
        min-height: 50px !important;
    }

    /* 5. Headers */
    .main-title {
        color: #1565c0;
        font-weight: 900;
        font-size: 55px;
        line-height: 1.1;
    }
    .sub-title {
        color: #546e7a;
        font-size: 24px;
        margin-bottom: 30px;
    }
    
    /* 6. Section Headers */
    .section-header {
        font-size: 36px;
        font-weight: 900;
        color: #1a237e;
        border-bottom: 5px solid #eceff1;
        padding-bottom: 15px;
        margin-bottom: 30px;
    }
    .subgroup-header {
        font-size: 28px;
        font-weight: 900;
        color: #000;
        margin-bottom: 15px;
    }

    /* 7. Containers */
    .card-container {
        background: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    
    .about-box {
        background-color: #e3f2fd;
        border-left: 10px solid #1565c0;
        padding: 30px;
        border-radius: 10px;
        margin-bottom: 40px;
    }
    .about-title {
        font-size: 28px; font-weight: 900; color: #0d47a1; margin-bottom: 10px;
    }
    .about-text {
        font-size: 20px; line-height: 1.5; color: #37474f;
    }

    /* 8. Right Side Modules */
    .reference-box {
        background: white;
        border: 3px solid #eee;
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 30px;
    }
    .ref-title { font-size: 28px; font-weight: 900; color: #333; margin-bottom: 20px; border-bottom: 2px solid #eee; }
    .ref-item { font-size: 22px; margin-bottom: 15px; display: flex; align-items: center; }
    .ref-dot { width: 25px; height: 25px; border-radius: 50%; margin-right: 15px; display: inline-block; }

    .placeholder-box {
        background: #f1f8e9;
        border: 4px dashed #a5d6a7;
        border-radius: 20px;
        min-height: 800px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 40px;
    }

    /* 9. Risk Result Cards */
    .risk-card-low { background: #e8f5e9; color: #1b5e20; border: 6px solid #2e7d32; }
    .risk-card-mid { background: #FFF9C4; color: #000; border: 6px solid #FBC02D; }
    .risk-card-high { background: #ffebee; color: #b71c1c; border: 6px solid #c62828; }

    /* 10. Abnormal Factor Box */
    .breakdown-box {
        background: white;
        border: 2px solid #eee;
        border-left-width: 12px;
        border-radius: 12px;
        padding: 30px;
        margin-top: 30px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. Data & Logic
# ==========================================
VAR_META = {
    "Age": {"unit": "years", "full": "Age"},
    "APSIII_score": {"unit": "pts", "full": "APSIII Score"},
    "Aniongap": {"unit": "mmol/L", "full": "Anion Gap"},
    "aniongap": {"unit": "mmol/L", "full": "Anion Gap"},
    "BUN": {"unit": "mg/dL", "full": "Blood Urea Nitrogen"},
    "DBP": {"unit": "mmHg", "full": "Diastolic BP"},
    "Fluid_amount": {"unit": "mL", "full": "Fluid Amount"},
    "Fluid Amount": {"unit": "mL", "full": "Fluid Amount"},
    "HCO3": {"unit": "mmol/L", "full": "Bicarbonate"},
    "HR": {"unit": "bpm", "full": "Heart Rate"},
    "K": {"unit": "mmol/L", "full": "Potassium"},
    "MCV": {"unit": "fL", "full": "Mean Corpuscular Volume"},
    "Mechnical_Ventilation": {"unit": "0=No, 1=Yes", "full": "Mech. Ventilation"},
    "Na": {"unit": "mmol/L", "full": "Sodium"},
    "RDW": {"unit": "%", "full": "Red Cell Distribution Width"},
    "RR": {"unit": "bpm", "full": "Respiratory Rate"},
    "SBP": {"unit": "mmHg", "full": "Systolic BP"},
    "SpO2": {"unit": "%", "full": "Oxygen Saturation"},
    "T": {"unit": "°C", "full": "Temperature"},
    "Urine": {"unit": "mL/24h", "full": "Urine Output"},
    "WBC": {"unit": "x10^9/L", "full": "White Blood Cells"},
    "Elixhauser_score": {"unit": "pts", "full": "Elixhauser Comorbidity"},
    "Weight": {"unit": "kg", "full": "Weight"}
}

GROUP_MAPPING = {
    "Global (General ICU)": "Global",
    "Renal Disease Subgroup": "Renal_Disease",
    "Liver Disease Subgroup": "Liver_Disease",
    "Immunodeficiency Subgroup": "Immunodeficiency_Disorder"
}

@st.cache_data
def load_rules(csv_path="SHScore_Compact_Rules.csv"):
    df = None
    if os.path.exists(csv_path):
        try: df = pd.read_csv(csv_path)
        except: pass
    if df is None:
        data = {
            "Variable": ["Age (years)", "APSIII_score (pts)", "BUN (mg/dL)", "Elixhauser_score (pts)", "HCO3 (mmol/L)", "HR (bpm)", "MCV (fL)", "Mechnical_Ventilation (0=No, 1=Yes)", "T (°C)", "WBC (x10^9/L)", "Weight (Kg)", "Aniongap (mmol/L)"],
            "Global": ["< 60 (0)\n>= 60 (6)", "< 50 (0)\n>= 50 (10)", "< 30 (0)\n>= 30 (1)", "< 5 (0)\n>= 5 (2)", "< 22 (3)\n>= 22 (0)", "> 100 (2)\n<= 100 (0)", "> 90 (2)\n<= 90 (0)", "1 (4)\n0 (0)", "> 38 (0)\n<= 38 (2)", "> 12 (1)\n<= 12 (0)", "> 100 (4)\n<= 100 (0)", "> 15 (5)\n<= 15 (0)"],
            "Renal_Disease": ["< 60 (0)\n>= 60 (5)"] * 12, "Liver_Disease": ["< 60 (0)\n>= 60 (4)"] * 12, "Immunodeficiency_Disorder": ["< 60 (0)\n>= 60 (7)"] * 12
        }
        for k in data.keys():
            if k != "Variable" and len(data[k]) < 12: data[k] = data[k] + ["N/A"] * (12 - len(data[k]))
        df = pd.DataFrame(data)

    df = df.rename(columns=lambda x: x.strip())
    df["Variable"] = df["Variable"].str.replace("fluid_amount", "Fluid Amount", case=False)
    df["Variable"] = df["Variable"].str.replace("aniongap", "Aniongap", case=False)
    
    id_vars = ["Variable"]; 
    if "Category" in df.columns: id_vars.append("Category")
    df_long = df.melt(id_vars=id_vars, var_name="Group", value_name="RuleString")
    df_long = df_long.dropna(subset=["RuleString"])
    return df_long[~df_long["RuleString"].isin(["", "N/A", "--"])]

def parse_rule_string(rule_str):
    rules = []
    rule_str = str(rule_str).replace("\r\n", "\n")
    for line in [x.strip() for x in rule_str.split("\n") if x.strip()]:
        try:
            points_match = re.search(r"\(([-0-9]+)\)", line)
            if not points_match: continue
            points = int(points_match.group(1))
            nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line.split('(')[0])]
            mn, mx = -float('inf'), float('inf')
            if ">=" in line: mn = nums[0] if nums else mn
            elif ">" in line: mn = nums[0] + 1e-9 if nums else mn
            elif "<=" in line: mx = nums[0] if nums else mx
            elif "<" in line: mx = nums[0] - 1e-9 if nums else mx
            elif "-" in line and len(nums) >= 2: mn, mx = nums[0], nums[1]
            elif "=" in line or (len(nums)==1): mn, mx = (nums[0], nums[0]) if nums else (mn, mx)
            rules.append({"min": mn, "max": mx, "points": points, "raw": line})
        except: continue
    return rules

def calculate_score(user_inputs, rules_df, selected_group):
    total_score = 0; details = []
    group_rules = rules_df[rules_df["Group"] == selected_group]
    for _, row in group_rules.iterrows():
        raw_var = row["Variable"]
        clean_var = re.sub(r"\(.*\)", "", raw_var).strip()
        input_key = None
        for k in user_inputs.keys():
            if k.lower() == clean_var.lower(): input_key = k; break
        if input_key and user_inputs[input_key] is not None:
            val = user_inputs[input_key]; parsed = parse_rule_string(row["RuleString"])
            points_added = 0; matched_rule = None
            for rule in parsed:
                if rule["min"] <= val <= rule["max"]:
                    points_added = rule["points"]; matched_rule = rule["raw"]
                    if points_added > 0: break 
            if points_added != 0:
                total_score += points_added
                details.append({"var": clean_var, "val": val, "points": points_added, "rule": matched_rule})
    logit = -3.8 + 0.085 * total_score
    prob = 1 / (1 + np.exp(-logit))
    return total_score, prob, details

# ==========================================
# 4. Main Layout
# ==========================================
st.markdown('<div class="main-title">Sepsis Heterogeneity Score (SHScore)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Mortality Risk Stratification for Sepsis Patients</div>', unsafe_allow_html=True)

# About Box (Pure Text)
st.markdown("""
<div class="about-box">
    <div class="about-title">📘 About SHScore</div>
    <div class="about-text">
        The <b>Sepsis Heterogeneity Score (SHScore)</b> is a novel, data-driven stratification tool developed using the <b>MIMIC-IV</b> database and externally validated within the <b>eICU</b> Collaborative Research Database. 
        <br><br>
        Recognizing the <b>clinical heterogeneity</b> arising from different underlying comorbidities, this model was trained using <b>dynamic time-series data</b> to capture physiological fluctuations often missed by static snapshots. It is specifically designed to predict <b>short-term (7-day) mortality risk</b> across diverse sepsis phenotypes (e.g., Renal, Liver, Immunodeficiency), demonstrating <b>superior predictive performance</b> compared to traditional scoring systems like SOFA and APACHE II.
    </div>
</div>
""", unsafe_allow_html=True)

rules_df = load_rules()
col_inputs, col_results = st.columns([1.1, 0.9], gap="large")

# === Left Column: Inputs ===
with col_inputs:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="subgroup-header">1. Patient Subgroup Profile</div>', unsafe_allow_html=True)
    selected_group_label = st.radio("Select profile:", options=list(GROUP_MAPPING.keys()), index=0, label_visibility="collapsed")
    selected_group = GROUP_MAPPING[selected_group_label]
    current_group_vars = rules_df[rules_df["Group"] == selected_group]["Variable"].unique()
    
    st.markdown("---")
    st.markdown('<div class="subgroup-header" style="margin-top:30px;">2. Clinical Variables</div>', unsafe_allow_html=True)
    
    user_inputs = {}
    with st.form("input_form"):
        input_cols = st.columns(2)
        sorted_vars = sorted(current_group_vars)
        for i, var_str in enumerate(sorted_vars):
            clean_name = re.sub(r"\(.*\)", "", var_str).strip()
            meta = None
            for k, v in VAR_META.items():
                if k.lower() == clean_name.lower(): meta = v; break
            label = clean_name
            if meta: label = f"{meta['full']} ({meta['unit']})"
            
            with input_cols[i % 2]:
                user_inputs[clean_name] = st.number_input(label, value=None, placeholder="--", step=0.1, key=f"in_{clean_name}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        # The Green Button
        submitted = st.form_submit_button("🚀 Calculate Risk Score")
    st.markdown('</div>', unsafe_allow_html=True)

# === Right Column: Results ===
with col_results:
    if submitted:
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        if score < 20:
            risk_class = "risk-card-low"; risk_label = "LOW RISK"; color_hex = "#2e7d32"
        elif score <= 35:
            risk_class = "risk-card-mid"; risk_label = "INTERMEDIATE RISK"; color_hex = "#FBC02D"
        else:
            risk_class = "risk-card-high"; risk_label = "HIGH RISK (SEPSIS SHOCK)"; color_hex = "#c62828"

        # 1. Risk Reference (Top)
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 20 pts:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>20 - 35 pts:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 35 pts:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Result Card
        st.markdown(f"""
        <div class="card-container {risk_class}" style="text-align: center; padding: 50px;">
            <div style="font-size: 24px; font-weight: 700; opacity: 0.8;">PREDICTED 7-DAY MORTALITY</div>
            <div style="font-size: 50px; font-weight: 900; margin: 20px 0; color: {color_hex};">{risk_label}</div>
            <div style="font-size: 100px; font-weight: 900; line-height: 1; margin-bottom: 30px;">{prob_percent:.1f}%</div>
            <div style="background: rgba(255,255,255,0.6); display: inline-block; padding: 15px 40px; border-radius: 50px; font-weight: bold; font-size: 30px;">
                SHScore: {score} pts
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. Abnormal Factors List (Fixed Logic)
        st.markdown(f"""
        <div class="breakdown-box" style="border-left-color: {color_hex};">
            <div style="color: {color_hex}; font-weight: 900; font-size: 32px; margin-bottom: 25px; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                🔍 Abnormal Risk Factors
            </div>
        </div>
        """, unsafe_allow_html=True)

        if details:
            for d in details:
                # Using columns for clean layout instead of HTML lists
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                with c1: st.markdown(f"<span style='font-size:24px; font-weight:bold; color:#333;'>{d['var']}</span>", unsafe_allow_html=True)
                with c2: st.markdown(f"<span style='font-size:22px; color:#555;'>Value: {d['val']}</span>", unsafe_allow_html=True)
                with c3: st.markdown(f"<span style='font-size:24px; font-weight:bold; color:{color_hex};'>+{d['points']} pts</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        else:
            st.success("✅ All clinical indicators are within the baseline range. (Score: 0)")

    else:
        # Initial State
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 20 pts:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>20 - 35 pts:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 35 pts:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="placeholder-box">
            <div style="font-size: 100px; margin-bottom: 30px;">👈</div>
            <h2 style="margin:0; font-weight:900; color:#558b2f; font-size: 45px;">Ready to Calculate</h2>
            <p style="margin-top: 30px; font-size:24px; max-width:80%;">
                Please enter clinical data in the <b>Configuration</b> panel to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)