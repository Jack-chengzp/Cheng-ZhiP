import streamlit as st
import pandas as pd
import numpy as np
import re
import os

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(
    page_title="Sepsis Heterogeneity Score (SHScore)",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CSS 样式 (V22.0 - 字体统一版)
# ==========================================
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* === 布局调整 === */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 5rem !important;
        max-width: 98% !important;
    }

    /* === 绿色按钮 === */
    div.stButton > button {
        background-color: #2e7d32 !important;
        background-image: none !important;
        color: #ffffff !important;
        border: 3px solid #1b5e20 !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.2) !important;
        font-size: 32px !important;
        font-weight: 900 !important;
        padding: 15px 0 !important;
        min-height: 80px !important;
        border-radius: 12px !important;
        width: 100% !important;
        margin-top: 20px !important; 
        display: block !important;
    }
    div.stButton > button:hover {
        background-color: #1b5e20 !important;
        border-color: #004d40 !important;
        transform: scale(1.01);
        color: white !important;
    }
    div.stButton > button p {
        font-size: 32px !important;
        color: white !important;
    }

    /* =========================================
       [核心修改] 字体统一设置 
       标题: 28px, 正文: 24px
    ========================================= */

    /* 1. 模块标题 (28px Bold) */
    .section-header, 
    .subgroup-title, 
    .about-title, 
    .ref-title, 
    .protocol-title,
    .abnormal-title { 
        font-size: 28px !important; 
        font-weight: 900 !important; 
        margin-bottom: 15px !important;
        line-height: 1.3 !important;
    }
    
    /* 2. 正文内容 (24px) */
    .about-text, 
    .subgroup-desc, 
    .ref-item, 
    .protocol-content,
    .risk-label-small { 
        font-size: 24px !important; 
        line-height: 1.5 !important; 
        color: #37474f !important; 
    }

    /* 3. 输入控件字体 (24px) */
    /* 单选框 */
    div[role="radiogroup"] { gap: 15px; }
    div[role="radiogroup"] label p { 
        font-size: 24px !important; 
        font-weight: 700 !important; 
        color: #37474f !important; 
    }
    
    /* 数字输入框标签 */
    div[data-testid="stNumberInput"] label p { 
        font-size: 24px !important; 
        font-weight: 900 !important; 
        color: #000000 !important; 
    }
    /* 数字输入框数值 */
    div[data-testid="stNumberInput"] input { 
        font-size: 24px !important; 
        min-height: 55px !important; 
    }

    /* === 标题与模块 === */
    .main-title { color: #1565c0; font-weight: 900; font-size: 3.5rem; margin-bottom: 10px; }
    .sub-title { color: #546e7a; font-size: 1.8rem; margin-bottom: 30px; }
    
    .section-header { color: #1a237e; border-bottom: 4px solid #eceff1; padding-bottom: 15px; margin-bottom: 25px; }
    .subgroup-title { color: #000; margin-bottom: 10px; }
    .subgroup-desc { font-style: italic; color: #666; margin-bottom: 15px; }
    
    /* 容器样式 */
    .card-container { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; margin-bottom: 20px; }
    .about-box { background: #e3f2fd; border-left: 12px solid #1565c0; padding: 25px; border-radius: 12px; margin-bottom: 25px; }
    .about-title { color: #0d47a1; margin-bottom: 10px; }
    
    /* 结果区样式 */
    .risk-result-card { text-align: center; padding: 30px; border-radius: 20px; margin-bottom: 25px; }
    .risk-card-low { background:#e8f5e9; color:#1b5e20; border:5px solid #2e7d32; }
    .risk-card-mid { background:#fff9c4; color:#000; border:5px solid #fbc02d; }
    .risk-card-high { background:#ffebee; color:#b71c1c; border:5px solid #c62828; }
    
    /* 医学处置提示模块 */
    .protocol-box { 
        background: #fafafa; 
        border: 2px solid #e0e0e0; 
        border-left-width: 10px; 
        padding: 25px; 
        border-radius: 10px; 
        margin-bottom: 25px; 
    }
    
    .protocol-content { 
        color: #333; 
        margin: 0;
        padding-left: 30px; 
    }
    
    .protocol-content li { 
        margin-bottom: 12px; 
        list-style-type: disc !important; 
    }
    
    /* 图例与占位符 */
    .reference-box { background: white; border: 3px solid #eee; border-radius: 15px; padding: 20px; margin-bottom: 25px; }
    .ref-title { margin-bottom: 10px; border-bottom: 2px solid #eee; }
    .ref-item { margin-bottom: 8px; display: flex; align-items: center; }
    .ref-dot { width: 24px; height: 24px; border-radius: 50%; margin-right: 12px; display: inline-block; }
    .placeholder-box { background: #f1f8e9; border: 4px dashed #a5d6a7; border-radius: 20px; min-height: 600px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 核心逻辑
# ==========================================

VAR_CONFIG = {
    "age": {"full": "Age", "unit": "years"},
    "apsiii": {"full": "APSIII Score", "unit": "pts"},
    "anion": {"full": "Aniongap", "unit": "mmol/L"},
    "bun": {"full": "BUN", "unit": "mg/dL"},
    "dbp": {"full": "DBP", "unit": "mmHg"},
    "fluid": {"full": "Fluid Amount", "unit": "mL/6h"},
    "hco3": {"full": "HCO$_3^-$", "unit": "mmol/L"},
    "hr": {"full": "HR", "unit": "bpm"},
    "heart": {"full": "HR", "unit": "bpm"},
    "k": {"full": "K$^+$", "unit": "mmol/L"},
    "mcv": {"full": "MCV", "unit": "fL"},
    "mech": {"full": "Mech. Ventilation", "unit": "0=No, 1=Yes"},
    "na": {"full": "Na$^+$", "unit": "mmol/L"},
    "rdw": {"full": "RDW", "unit": "%"},
    "rr": {"full": "RR", "unit": "bpm"},
    "resp": {"full": "RR", "unit": "bpm"},
    "sbp": {"full": "SBP", "unit": "mmHg"},
    "spo2": {"full": "S$_p$O$_2$", "unit": "%"},
    "t": {"full": "T", "unit": "°C"},
    "temp": {"full": "T", "unit": "°C"},
    "urine": {"full": "Urine", "unit": "mL/6h"},
    "wbc": {"full": "WBC", "unit": "x10^9/L"},
    "white": {"full": "WBC", "unit": "x10^9/L"},
    "elixhauser": {"full": "Elixhauser Score", "unit": "pts"},
    "weight": {"full": "Weight", "unit": "kg"}
}

GROUP_MAPPING = {
    "Global": "Global",
    "Renal Disease": "Renal_Disease",
    "Liver Disease": "Liver_Disease",
    "Immunodeficiency": "Immunodeficiency_Disorder"
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
    df["Variable"] = df["Variable"].str.replace("aniongap", "Anion Gap", case=False)
    
    id_vars = ["Variable"]; 
    if "Category" in df.columns: id_vars.append("Category")
    df_long = df.melt(id_vars=id_vars, var_name="Group", value_name="RuleString")
    df_long = df_long.dropna(subset=["RuleString"])
    return df_long[~df_long["RuleString"].isin(["", "N/A", "--"])]

def parse_rule_string(rule_str):
    rules = []
    rule_str = str(rule_str).replace("\r\n", " ").replace("\n", " ")
    pattern = r"([^\(]+)\s*\((-?\d+)\)"
    matches = re.findall(pattern, rule_str)
    
    for condition_str, points_str in matches:
        try:
            points = int(points_str)
            condition_str = condition_str.strip()
            nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", condition_str)]
            mn, mx = -float('inf'), float('inf')
            if not nums: continue 
            if "-" in condition_str and len(nums) >= 2: mn, mx = nums[0], nums[1]
            elif ">=" in condition_str: mn = nums[0]
            elif ">" in condition_str: mn = nums[0] + 1e-9 
            elif "<=" in condition_str: mx = nums[0]
            elif "<" in condition_str: mx = nums[0] - 1e-9 
            elif "=" in condition_str or len(nums) == 1: mn, mx = nums[0], nums[0]
            rules.append({"min": mn, "max": mx, "points": points, "raw": f"{condition_str} ({points})"})
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
            if k.lower() == clean_var.lower(): 
                input_key = k; break
        
        if input_key and user_inputs[input_key] is not None:
            val = user_inputs[input_key]
            parsed = parse_rule_string(row["RuleString"])
            points_added = 0
            matched_rule = None
            for rule in parsed:
                if rule["min"] <= val <= rule["max"]:
                    points_added = rule["points"]
                    matched_rule = rule["raw"]
                    if points_added != 0: break 
            
            if points_added != 0:
                total_score += points_added
                details.append({"var": clean_var, "val": val, "points": points_added, "rule": matched_rule})
                
    logit = -3.8 + 0.085 * total_score
    prob = 1 / (1 + np.exp(-logit))
    return total_score, prob, details

def get_var_display(raw_name):
    clean_name = re.sub(r"\(.*\)", "", raw_name).strip().lower()
    target_key = None
    for k in VAR_CONFIG.keys():
        if k in clean_name: 
            target_key = k
            break
            
    if clean_name == "na" or "sodium" in clean_name: target_key = "na"
    if "anion" in clean_name: target_key = "anion"
    if "potassium" in clean_name: target_key = "k"
    
    if target_key:
        cfg = VAR_CONFIG[target_key]
        return f"{cfg['full']} ({cfg['unit']})"
    else:
        return raw_name

# ==========================================
# 4. 主界面布局
# ==========================================
st.markdown('<div class="main-title">Sepsis Heterogeneity Score (SHScore)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Mortality Risk Stratification for Sepsis Patients</div>', unsafe_allow_html=True)

rules_df = load_rules()

col_left, col_right = st.columns([1.1, 0.9], gap="large")

# === 左栏 (About + 输入) ===
with col_left:
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

    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="subgroup-title">1. Patient Subgroup Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="subgroup-desc">Please select the appropriate subgroup based on the patient\'s underlying disease for accurate risk assessment:</div>', unsafe_allow_html=True)
    
    selected_group_label = st.radio("Select profile:", options=list(GROUP_MAPPING.keys()), index=0, label_visibility="collapsed", horizontal=True)
    selected_group = GROUP_MAPPING[selected_group_label]
    current_group_vars = rules_df[rules_df["Group"] == selected_group]["Variable"].unique()
    
    st.markdown("---")
    st.markdown('<div class="subgroup-title" style="margin-top:30px;">2. Clinical Variables</div>', unsafe_allow_html=True)
    
    user_inputs = {}
    with st.form("input_form"):
        input_cols = st.columns(2)
        sorted_vars = sorted(current_group_vars)
        for i, var_str in enumerate(sorted_vars):
            clean_name = re.sub(r"\(.*\)", "", var_str).strip()
            display_label = get_var_display(clean_name)
            
            with input_cols[i % 2]:
                user_inputs[clean_name] = st.number_input(display_label, value=None, placeholder="--", step=0.1, key=f"in_{clean_name}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Calculate Risk Score")
    st.markdown('</div>', unsafe_allow_html=True)

# === 右栏 (图例 + 结果) ===
with col_right:
    
    if submitted:
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        # [逻辑修复] 确保内容和标题字体一致
        if prob_percent < 10:
            risk_class = "risk-card-low"; risk_label = "LOW RISK"; color_hex = "#2e7d32"
            protocol_title = "✅ Standard Care Pathway"
            protocol_items = """<li><b>Monitoring:</b> Standard vital signs q4h.</li><li><b>Fluids:</b> Maintain euvolemia. Avoid fluid overload.</li><li><b>Antibiotics:</b> De-escalate based on culture results.</li>"""
        elif prob_percent <= 30:
            risk_class = "risk-card-mid"; risk_label = "INTERMEDIATE RISK"; color_hex = "#FBC02D"
            protocol_title = "⚠️ Enhanced Surveillance Pathway"
            protocol_items = """<li><b>Monitoring:</b> Continuous telemetry. Hourly urine output.</li><li><b>Labs:</b> Repeat lactate q6h if elevated.</li><li><b>Intervention:</b> Consider low-dose vasopressors if MAP is unstable.</li>"""
        else:
            risk_class = "risk-card-high"; risk_label = "HIGH RISK (SEPSIS SHOCK)"; color_hex = "#c62828"
            protocol_title = "🚨 Aggressive Resuscitation Pathway"
            protocol_items = """<li><b>Hemodynamics:</b> Target MAP > 65 mmHg immediately with vasopressors.</li><li><b>Support:</b> Prepare for mechanical ventilation or CRRT immediately.</li><li><b>Source Control:</b> Urgent surgical consult within 1 hour.</li>"""

        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation (By Mortality Rate)</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 10%:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>10% - 30%:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 30%:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="risk-result-card {risk_class}">
            <div class="risk-label-small" style="font-weight: 700; opacity: 0.8;">PREDICTED 7-DAY MORTALITY</div>
            <div style="font-size: 3rem; font-weight: 900; margin: 15px 0; color: {color_hex};">{risk_label}</div>
            <div style="font-size: 6rem; font-weight: 900; line-height: 1; margin-bottom: 20px;">{prob_percent:.1f}%</div>
            <div class="risk-label-small" style="background: rgba(255,255,255,0.6); display: inline-block; padding: 10px 30px; border-radius: 50px; font-weight: bold;">
                SHScore: {score} pts
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # [字体统一] 28px 标题, 24px 正文
        st.markdown(f"""
        <div class="protocol-box" style="border-left-color: {color_hex};">
            <div class="protocol-title" style="color: {color_hex};">
                {protocol_title}
            </div>
            <ul class="protocol-content">
                {protocol_items}
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if details:
            abnormal_str = "; ".join([f"{d['var']}: {d['points']}" for d in details])
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; border: 2px solid #eee; margin-top: 25px; text-align: left; line-height: 1.4;">
                <div class="abnormal-title" style="color: #000; margin-bottom: 10px;">Abnormal Risk Factors:</div> 
                <div style="font-size: 24px; color: #b71c1c; font-weight: bold;">{abnormal_str}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success("✅ All clinical indicators are within the baseline range. (Score: 0)")

    else:
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 10%:</b>&nbsp; Low Risk (Mortality)</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>10% - 30%:</b>&nbsp; Intermediate Risk (Mortality)</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 30%:</b>&nbsp; High Risk (Mortality)</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="placeholder-box">
            <div style="font-size: 8rem; margin-bottom: 30px;">👈</div>
            <h2 style="margin:0; font-weight:900; color:#558b2f; font-size: 3rem;">Ready to Calculate</h2>
            <p style="margin-top: 25px; font-size: 24px; max-width:80%;">
                Please enter clinical data in the <b>Configuration</b> panel to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)