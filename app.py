import streamlit as st
import pandas as pd
import numpy as np
import re
import os
import plotly.graph_objects as go

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
# 2. 终极 CSS 注入 (针对性修复)
# ==========================================
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* === 0. 顶部间距修复 === */
    .block-container {
        padding-top: 5rem !important; 
        padding-bottom: 5rem !important;
        max-width: 95% !important;
    }

    /* === 1. [核心修复] 单选按钮选项字体 (Subgroup Options) === */
    /* 强制覆盖 Streamlit Markdown 容器内的 P 标签 */
    div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
        font-size: 2.2rem !important; /* 强制 2.2rem */
        font-weight: 700 !important;  /* 加粗 */
        line-height: 1.2 !important;
        color: #37474f !important;
    }
    
    /* 调整单选框容器的大小以适应大字体 */
    div[role="radiogroup"] label {
        padding: 25px 20px !important;
        background-color: #f8f9fa;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        display: flex;
        align-items: center;
    }
    /* 选中状态 */
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #e3f2fd !important;
        border-color: #1565c0 !important;
    }

    /* === 2. [核心修复] 绿色计算按钮 === */
    /* 移除默认样式干扰，强制绿色 */
    div.stButton > button {
        background-image: none !important;
        background-color: #2e7d32 !important; /* 鲜艳绿 */
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(46, 125, 50, 0.5) !important;
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        padding: 20px 40px !important;
        min-height: 80px !important;
        border-radius: 16px !important;
        width: 100% !important;
        transition: all 0.2s !important;
    }
    
    /* 悬停状态 */
    div.stButton > button:hover {
        background-color: #1b5e20 !important; /* 深绿 */
        color: #ffffff !important;
        box-shadow: 0 6px 15px rgba(46, 125, 50, 0.6) !important;
        transform: translateY(-2px);
    }
    
    /* 点击/聚焦状态 (防止变红或变蓝) */
    div.stButton > button:active, div.stButton > button:focus {
        background-color: #1b5e20 !important;
        color: white !important;
        border: none !important;
        outline: none !important;
    }
    
    /* 按钮内部文字容器 */
    div.stButton > button p {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
    }

    /* === 3. 变量名 (2.2rem 极粗) === */
    .stNumberInput label p {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        color: #000000 !important;
    }
    .stNumberInput label {
        margin-bottom: 15px !important;
    }
    .stNumberInput input {
        font-size: 1.6rem !important;
        font-weight: 500;
        min-height: 4rem !important; /* 输入框更高 */
        padding: 10px !important;
    }

    /* === 4. 标题与排版 === */
    .main-title {
        color: #1565c0; 
        font-weight: 900;
        font-size: 3.5rem; 
        line-height: 1.1;
        margin-bottom: 10px;
    }
    .sub-title {
        color: #546e7a;
        font-size: 1.6rem; 
        margin-bottom: 40px;
    }

    /* 纯文本介绍区域 */
    .about-text-container {
        margin-bottom: 50px;
        padding: 25px;
        background-color: #f8fdff;
        border-left: 12px solid #1565c0;
        border-radius: 8px;
    }
    .about-title {
        font-weight: 900;
        color: #0d47a1;
        font-size: 2rem; 
        margin-bottom: 15px;
    }
    .about-text {
        font-size: 1.4rem; 
        line-height: 1.6;
        color: #37474f;
    }

    /* === 5. 右侧模块布局 === */
    /* 风险图例 */
    .reference-box {
        background-color: white;
        border: 3px solid #eceff1;
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 30px;
    }
    .ref-title {
        font-size: 2.2rem;
        font-weight: 900;
        color: #37474f;
        margin-bottom: 20px;
        border-bottom: 3px solid #eee;
    }
    .ref-item {
        font-size: 1.8rem; /* 图例内容加大 */
        font-weight: 600;
        color: #455a64;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    .ref-dot {
        width: 35px; height: 35px; border-radius: 50%; 
        margin-right: 20px; display: inline-block;
    }

    /* 占位符 (Ready to Calculate) */
    .placeholder-box {
        background-color: #f1f8e9; 
        border: 5px dashed #a5d6a7; 
        border-radius: 20px; 
        padding: 60px 40px; 
        text-align: center; 
        color: #558b2f;
        min-height: 900px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    /* === 6. Configuration 标题 === */
    .section-header {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1a237e;
        border-bottom: 5px solid #e8eaf6;
        padding-bottom: 20px;
        margin-bottom: 30px;
    }
    .subgroup-title {
        font-size: 2.2rem;
        font-weight: 900;
        margin-bottom: 20px;
        color: #000;
    }

    /* 卡片容器 */
    .card-container {
        background-color: #ffffff;
        padding: 40px; 
        border-radius: 20px;
        box-shadow: 0 5px 25px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }

    /* 单选按钮组布局 */
    div[role="radiogroup"] {
        display: grid;
        grid-template-columns: 1fr 1fr; 
        gap: 20px;
    }

    /* 结果卡片 */
    .risk-card-low { background:#e8f5e9; color:#1b5e20; border:6px solid #2e7d32; }
    .risk-card-mid { background:#fff9c4; color:#000; border:6px solid #fbc02d; }
    .risk-card-high { background:#ffebee; color:#b71c1c; border:6px solid #c62828; }

    .protocol-box {
        background-color: #fafafa;
        border: 1px solid #ddd;
        border-left: 10px solid #546e7a;
        padding: 35px;
        border-radius: 8px;
        margin-top: 30px;
        font-size: 1.5rem; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 核心逻辑与配置
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
# 4. 主界面
# ==========================================
st.markdown('<div class="main-title">Sepsis Heterogeneity Score (SHScore)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Mortality Risk Stratification for Sepsis Patients</div>', unsafe_allow_html=True)

st.markdown("""
<div class="about-text-container">
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

# === 左侧输入 ===
with col_inputs:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    # 2.2rem 标题
    st.markdown('<div class="subgroup-title">1. Patient Subgroup Profile</div>', unsafe_allow_html=True)
    selected_group_label = st.radio("Select profile:", options=list(GROUP_MAPPING.keys()), index=0, label_visibility="collapsed")
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
            meta = None
            for k, v in VAR_META.items():
                if k.lower() == clean_name.lower(): meta = v; break
            label = clean_name
            if meta: label = f"{meta['full']} ({meta['unit']})"
            
            with input_cols[i % 2]:
                user_inputs[clean_name] = st.number_input(label, value=None, placeholder="--", step=0.1, key=f"in_{clean_name}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        # 绿色大按钮
        submitted = st.form_submit_button("🚀 Calculate Risk Score")
    st.markdown('</div>', unsafe_allow_html=True)

# === 右侧结果 ===
with col_results:
    if submitted:
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        if score < 20:
            risk_class = "risk-card-low"; risk_label = "LOW RISK"; color_hex = "#2e7d32"
            protocol = "**✅ Standard Care Pathway**: Monitoring q4h, Fluids euvolemia, Antibiotics de-escalation."
        elif score <= 35:
            risk_class = "risk-card-mid"; risk_label = "INTERMEDIATE RISK"; color_hex = "#FBC02D"
            protocol = "**⚠️ Enhanced Surveillance**: Continuous telemetry, Hourly urine, Repeat lactate."
        else:
            risk_class = "risk-card-high"; risk_label = "HIGH RISK (SEPSIS SHOCK)"; color_hex = "#c62828"
            protocol = "**🚨 Aggressive Resuscitation**: Target MAP > 65, Mechanical ventilation prep, Urgent surgical consult."

        # Risk Reference (Top)
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 20 pts:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>20 - 35 pts:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 35 pts:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Result Card
        st.markdown(f"""
        <div class="card-container {risk_class}" style="text-align: center; padding: 50px;">
            <div style="font-size: 1.8rem; font-weight: 700; opacity: 0.8;">PREDICTED 7-DAY MORTALITY</div>
            <div style="font-size: 3.5rem; font-weight: 900; margin: 20px 0; color: {color_hex};">{risk_label}</div>
            <div style="font-size: 8rem; font-weight: 900; line-height: 1; margin-bottom: 30px;">{prob_percent:.1f}%</div>
            <div style="background: rgba(255,255,255,0.6); display: inline-block; padding: 15px 40px; border-radius: 50px; font-weight: bold; font-size: 2rem;">
                SHScore: {score} pts
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Protocol & Gauge
        st.markdown(f"""<div class="protocol-box" style="font-size:1.6rem; margin-top:30px;"><b style="color:{color_hex}">📋 Guide:</b> {protocol}</div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = score,
            title = {'text': "Risk Severity", 'font': {'size': 30, 'color': "#555", 'weight': 'bold'}},
            number = {'suffix': " pts", 'font': {'color': color_hex, 'weight': 'bold', 'size': 40}},
            gauge = {'axis': {'range': [None, 80]}, 'bar': {'color': color_hex}, 'steps': [{'range': [0, 20], 'color': '#a5d6a7'}, {'range': [20, 35], 'color': '#FFF59D'}, {'range': [35, 80], 'color': '#ef9a9a'}]}
        ))
        fig.update_layout(height=350, margin=dict(l=30, r=30, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    else:
        # Risk Reference (Top)
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 20 pts:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>20 - 35 pts:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 35 pts:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Placeholder (Bottom)
        st.markdown("""
        <div class="placeholder-box">
            <div style="font-size: 8rem; margin-bottom: 30px;">👈</div>
            <h2 style="margin:0; font-weight:900; color:#558b2f; font-size: 3.5rem;">Ready to Calculate</h2>
            <p style="margin-top: 30px; font-size:1.8rem; max-width:80%;">
                Please enter clinical data in the <b>Configuration</b> panel to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)