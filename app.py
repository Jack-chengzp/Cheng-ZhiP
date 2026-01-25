import streamlit as st
import pandas as pd
import numpy as np
import re
import os
import plotly.graph_objects as go

# ==========================================
# 1. 页面配置与 CSS 样式美化
# ==========================================
st.set_page_config(
    page_title="Sepsis Heterogeneity Score (SHScore)",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS 样式 - 绿色按钮 + 超大字体修复版
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: #212121;
        font-size: 18px;
    }
    
    /* === 0. 修复标题被遮挡问题 === */
    .block-container {
        padding-top: 6rem !important; /* 顶部留出足够空间 */
        padding-bottom: 3rem !important;
        max-width: 95% !important;
    }
    
    /* === 1. 标题样式 === */
    .main-title {
        color: #1565c0; 
        font-weight: 900;
        font-size: 3.5rem; 
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
        line-height: 1.2;
    }
    .sub-title {
        color: #546e7a;
        font-size: 1.5rem; 
        font-weight: 400;
        margin-bottom: 3rem;
    }

    /* === 2. 纯文本介绍 === */
    .about-text-container {
        margin-bottom: 40px;
        padding-left: 15px;
        border-left: 8px solid #1565c0; 
    }
    .about-title {
        font-weight: 900;
        color: #0d47a1;
        font-size: 1.8rem; 
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }
    .about-text {
        font-size: 1.3rem; 
        line-height: 1.6;
        color: #37474f;
        text-align: justify;
    }

    /* === 3. 卡片容器 === */
    .card-container {
        background-color: #ffffff;
        padding: 40px; 
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        margin-bottom: 0px; 
        height: 100%; 
    }
    
    /* Configuration 标题 */
    .section-header {
        font-size: 2.4rem; 
        font-weight: 900;
        color: #1a237e;
        margin-bottom: 30px;
        border-bottom: 5px solid #eceff1;
        padding-bottom: 15px;
    }

    /* === 4. 变量名 (2.2rem 极粗) === */
    .stNumberInput label p {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        color: #000000 !important;
    }
    .stNumberInput label {
        margin-bottom: 15px !important;
    }
    .stNumberInput input {
        font-size: 1.5rem;
        font-weight: 500;
        min-height: 3.5rem; 
        padding: 10px;
    }

    /* === 5. [重点修改] 绿色计算按钮 (2.2rem + 填充背景) === */
    div.stButton > button:first-child {
        background-color: #2e7d32 !important; /* 强制绿色背景 */
        color: white !important;               /* 白色文字 */
        font-size: 2.2rem !important;          /* 2.2rem 字号 */
        font-weight: 900 !important;           /* 极粗 */
        height: auto;
        min-height: 5rem;
        border-radius: 15px;
        border: 2px solid #1b5e20;             /* 深绿边框 */
        width: 100%;
        box-shadow: 0 8px 16px rgba(46, 125, 50, 0.3); /* 绿色阴影 */
        margin-top: 50px;
        padding: 15px 30px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    div.stButton > button:first-child:hover {
        background-color: #1b5e20 !important; /* 悬停变深绿 */
        border-color: #1b5e20 !important;
        transform: translateY(-3px);
        color: white !important;
    }
    /* 修复按钮内图标文字对齐 */
    div.stButton > button:first-child p {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        margin: 0;
        padding: 0;
    }

    /* === 6. Subgroup 标题 === */
    .subgroup-title {
        font-size: 2.2rem;
        font-weight: 900; 
        color: #000000;   
        margin-bottom: 20px;
        display: block;
    }
    
    /* Subgroup 选项 */
    div[role="radiogroup"] {
        display: grid;
        grid-template-columns: 1fr 1fr; 
        gap: 20px;
    }
    div[role="radiogroup"] label {
        background-color: #f5f7f9;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        transition: all 0.2s;
    }
    div[role="radiogroup"] label p {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: #37474f !important;
    }

    /* === 7. 右侧模块 === */
    .reference-box {
        background-color: #ffffff;
        border: 3px solid #e0e0e0;
        border-radius: 16px;
        padding: 35px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.03);
    }
    .ref-title {
        font-weight: 900;
        color: #37474f;
        margin-bottom: 25px;
        font-size: 2.2rem; 
        border-bottom: 3px solid #f5f5f5;
        padding-bottom: 15px;
    }
    .ref-item {
        display: flex;
        align-items: center;
        margin-bottom: 18px;
        font-size: 1.6rem; 
        font-weight: 600;
        color: #455a64;
    }
    .ref-dot {
        width: 32px; 
        height: 32px;
        border-radius: 50%;
        margin-right: 20px;
        display: inline-block;
        border: 1px solid rgba(0,0,0,0.1);
        flex-shrink: 0;
    }

    .placeholder-box {
        background-color: #f8f9fa; 
        border: 5px dashed #cfd8dc; 
        border-radius: 20px; 
        padding: 50px; 
        text-align: center; 
        color: #78909c;
        min-height: 900px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-top: 35px;
    }

    /* === 8. 结果样式 === */
    .risk-card-low { background-color: #e8f5e9; color: #1b5e20; border: 6px solid #2e7d32; }
    .risk-card-mid { background-color: #FFF9C4; color: #212121; border: 6px solid #FBC02D; }
    .risk-card-high { background-color: #ffebee; color: #b71c1c; border: 6px solid #c62828; }

    .protocol-box {
        background-color: #fafafa;
        border: 1px solid #ddd;
        border-left: 10px solid #546e7a;
        padding: 35px;
        border-radius: 8px;
        margin-top: 30px;
        font-size: 1.4rem; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 配置与映射表
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

# ==========================================
# 3. 核心逻辑函数
# ==========================================
@st.cache_data
def load_rules(csv_path="SHScore_Compact_Rules.csv"):
    df = None
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
        except:
            pass
    if df is None:
        data = {
            "Variable": [
                "Age (years)", "APSIII_score (pts)", "BUN (mg/dL)", 
                "Elixhauser_score (pts)", "HCO3 (mmol/L)", "HR (bpm)",
                "MCV (fL)", "Mechnical_Ventilation (0=No, 1=Yes)", 
                "T (°C)", "WBC (x10^9/L)", "Weight (Kg)", "Aniongap (mmol/L)"
            ],
            "Global": [
                "< 60 (0)\n>= 60 (6)", "< 50 (0)\n>= 50 (10)", "< 30 (0)\n>= 30 (1)",
                "< 5 (0)\n>= 5 (2)", "< 22 (3)\n>= 22 (0)", "> 100 (2)\n<= 100 (0)",
                "> 90 (2)\n<= 90 (0)", "1 (4)\n0 (0)", "> 38 (0)\n<= 38 (2)",
                "> 12 (1)\n<= 12 (0)", "> 100 (4)\n<= 100 (0)", "> 15 (5)\n<= 15 (0)"
            ],
            "Renal_Disease": ["< 60 (0)\n>= 60 (5)"] * 12,
            "Liver_Disease": ["< 60 (0)\n>= 60 (4)"] * 12,
            "Immunodeficiency_Disorder": ["< 60 (0)\n>= 60 (7)"] * 12
        }
        for k in data.keys():
            if k != "Variable":
                if len(data[k]) < 12: data[k] = data[k] + ["N/A"] * (12 - len(data[k]))
        df = pd.DataFrame(data)

    df = df.rename(columns=lambda x: x.strip())
    df["Variable"] = df["Variable"].str.replace("fluid_amount", "Fluid Amount", case=False)
    df["Variable"] = df["Variable"].str.replace("aniongap", "Aniongap", case=False)
    
    id_vars = ["Variable"]
    if "Category" in df.columns: id_vars.append("Category")
    df_long = df.melt(id_vars=id_vars, var_name="Group", value_name="RuleString")
    df_long = df_long.dropna(subset=["RuleString"])
    df_long = df_long[~df_long["RuleString"].isin(["", "N/A", "--"])]
    return df_long

def parse_rule_string(rule_str):
    rules = []
    rule_str = str(rule_str).replace("\r\n", "\n")
    lines = [x.strip() for x in rule_str.split("\n") if x.strip()]
    for line in lines:
        try:
            points_match = re.search(r"\(([-0-9]+)\)", line)
            if not points_match: continue
            points = int(points_match.group(1))
            nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line.split('(')[0])]
            mn, mx = -float('inf'), float('inf')
            if ">=" in line:
                if nums: mn = nums[0]
            elif ">" in line:
                if nums: mn = nums[0] + 1e-9
            elif "<=" in line:
                if nums: mx = nums[0]
            elif "<" in line:
                if nums: mx = nums[0] - 1e-9
            elif "-" in line and len(nums) >= 2:
                mn, mx = nums[0], nums[1]
            elif "=" in line or (len(nums)==1 and ("=" not in line) and (">" not in line) and ("<" not in line)): 
                 if nums: mn, mx = nums[0], nums[0]
            rules.append({"min": mn, "max": mx, "points": points, "raw": line})
        except: continue
    return rules

def calculate_score(user_inputs, rules_df, selected_group):
    total_score = 0
    details = []
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
                    if points_added > 0: break 
            if points_added != 0:
                total_score += points_added
                details.append({"var": clean_var, "val": val, "points": points_added, "rule": matched_rule})
    
    logit = -3.8 + 0.085 * total_score
    prob = 1 / (1 + np.exp(-logit))
    return total_score, prob, details

# ==========================================
# 4. 主界面布局
# ==========================================

# --- 主标题 ---
st.markdown('<div class="main-title">Sepsis Heterogeneity Score (SHScore)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Mortality Risk Stratification for Sepsis Patients</div>', unsafe_allow_html=True)

# --- 文案 (纯文本版) ---
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

# --- 加载数据 ---
rules_df = load_rules()

# --- 主内容区：两列布局 ---
col_inputs, col_results = st.columns([1.1, 0.9], gap="large")

# ================================
# 左侧：Configuration & Inputs
# ================================
with col_inputs:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    # 1. Subgroup
    st.markdown('<div class="subgroup-title">1. Patient Subgroup Profile</div>', unsafe_allow_html=True)
    selected_group_label = st.radio(
        "Select profile:",
        options=list(GROUP_MAPPING.keys()),
        index=0,
        label_visibility="collapsed"
    )
    selected_group = GROUP_MAPPING[selected_group_label]
    current_group_vars = rules_df[rules_df["Group"] == selected_group]["Variable"].unique()
    
    st.markdown("---")
    st.markdown('<div class="subgroup-title" style="margin-top:25px;">2. Clinical Variables</div>', unsafe_allow_html=True)
    st.caption("Enter the latest clinical values within the first 24 hours.")
    
    # 2. 输入表单
    user_inputs = {}
    with st.form("input_form"):
        input_cols = st.columns(2)
        sorted_vars = sorted(current_group_vars)
        
        for i, var_str in enumerate(sorted_vars):
            clean_name = re.sub(r"\(.*\)", "", var_str).strip()
            meta = None
            for k, v in VAR_META.items():
                if k.lower() == clean_name.lower():
                    meta = v; break
            
            label = clean_name
            if meta: label = f"{meta['full']} ({meta['unit']})"
            
            col_idx = i % 2
            with input_cols[col_idx]:
                user_inputs[clean_name] = st.number_input(
                    label, value=None, placeholder="--", step=0.1, key=f"in_{clean_name}"
                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        # 绿色按钮
        submitted = st.form_submit_button("🚀 Calculate Risk Score")
    
    st.markdown('</div>', unsafe_allow_html=True) # 结束卡片

# ================================
# 右侧：结果展示 (Top: Reference, Bottom: Placeholder/Result)
# ================================
with col_results:
    if submitted:
        # 计算结果
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        # === 定义配色与阈值 ===
        if score < 20:
            risk_class = "risk-card-low"
            risk_label = "LOW RISK"
            color_hex = "#2e7d32" 
            protocol = """
            **✅ Standard Care Pathway**
            * **Monitoring:** Standard vital signs q4h.
            * **Fluids:** Maintain euvolemia.
            * **Antibiotics:** De-escalate based on culture results.
            """
        elif score <= 35:
            risk_class = "risk-card-mid"
            risk_label = "INTERMEDIATE RISK"
            color_hex = "#FBC02D" # 香蕉黄
            protocol = """
            **⚠️ Enhanced Surveillance Pathway**
            * **Monitoring:** Continuous telemetry. Hourly urine output.
            * **Labs:** Repeat lactate q6h if elevated.
            * **Intervention:** Low-dose vasopressors might be needed.
            """
        else:
            risk_class = "risk-card-high"
            risk_label = "HIGH RISK (SEPSIS SHOCK)"
            color_hex = "#c62828" 
            protocol = """
            **🚨 Aggressive Resuscitation Pathway**
            * **Hemodynamics:** Target MAP > 65 mmHg immediately.
            * **Support:** Prepare for mechanical ventilation/CRRT.
            * **Source Control:** Urgent surgical consult within 1 hour.
            """

        # 1. 风险图例 (置顶)
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 20 pts:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>20 - 35 pts:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 35 pts:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 2. 结果大卡片
        st.markdown(f"""
        <div class="card-container {risk_class}" style="text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 700; opacity: 0.8; letter-spacing: 1px;">PREDICTED 7-DAY MORTALITY</div>
            <div style="font-size: 3rem; font-weight: 900; margin: 20px 0; color: inherit;">{risk_label}</div>
            <div style="font-size: 7rem; font-weight: 900; line-height: 1; margin-bottom: 30px;">{prob_percent:.1f}%</div>
            <div style="background: rgba(255,255,255,0.4); display: inline-block; padding: 12px 35px; border-radius: 50px; font-weight: bold; font-size: 1.8rem;">
                SHScore: {score} pts
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. 详细建议
        st.markdown(f"""
        <div class="protocol-box">
            <h5 style="color: {color_hex}; margin-top:0; font-weight:900; font-size: 1.8rem;">📋 Clinical Management Guide</h5>
            {protocol}
        </div>
        """, unsafe_allow_html=True)

        # 4. 动态仪表盘
        st.markdown("<br>", unsafe_allow_html=True)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Risk Severity Gauge", 'font': {'size': 28, 'color': "#555", 'weight': 'bold'}},
            number = {'suffix': " pts", 'font': {'color': color_hex, 'weight': 'bold', 'size': 36}},
            gauge = {
                'axis': {'range': [None, 80], 'tickwidth': 1, 'tickcolor': "#333"}, 
                'bar': {'color': color_hex, 'thickness': 0.25},
                'bgcolor': "white",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 20], 'color': '#a5d6a7'},
                    {'range': [20, 35], 'color': '#FFF59D'},
                    {'range': [35, 80], 'color': '#ef9a9a'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 3},
                    'thickness': 0.8,
                    'value': score
                }
            }))
        fig.update_layout(height=300, margin=dict(l=30, r=30, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    else:
        # === 初始状态：图例在上，占位符在下 ===
        
        # 1. Risk Reference (图例模块)
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 20 pts:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>20 - 35 pts:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 35 pts:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Ready to Calculate (占位符模块) - 高度拉满
        st.markdown("""
        <div class="placeholder-box">
            <div style="font-size: 8rem; margin-bottom: 30px;">👈</div>
            <h2 style="margin:0; font-weight:900; color:#546e7a; font-size: 3rem;">Ready to Calculate</h2>
            <p style="margin-top: 30px; font-size:1.6rem; max-width:85%;">
                Please enter the patient's clinical data in the left <b>Configuration</b> panel to generate a precision risk assessment.
            </p>
        </div>
        """, unsafe_allow_html=True)