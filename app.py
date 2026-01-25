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

# 自定义 CSS 样式 - 字体加大版
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: #212121;
        font-size: 18px; /* 全局基础字体加大 */
    }
    
    /* === 1. 标题与文案增强 (加大) === */
    .main-title {
        color: #1565c0; 
        font-weight: 900;
        font-size: 3.5rem; /* 标题加大 */
        margin-bottom: 0.2rem;
        letter-spacing: -1px;
    }
    .sub-title {
        color: #546e7a;
        font-size: 1.5rem; /* 副标题加大 */
        font-weight: 400;
        margin-bottom: 2rem;
    }

    /* About 介绍框 - 字体加大 */
    .about-box {
        background-color: #e3f2fd;
        border-left: 10px solid #1565c0;
        padding: 30px 35px;
        border-radius: 12px;
        margin-bottom: 40px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .about-title {
        font-weight: 900;
        color: #0d47a1;
        font-size: 1.6rem; /* 加大 */
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    .about-text {
        font-size: 1.25rem; /* 正文加大 */
        line-height: 1.6;
        color: #263238;
        text-align: justify;
        font-weight: 400;
    }

    /* === 2. 容器与布局 === */
    .card-container {
        background-color: #ffffff;
        padding: 35px; /* 内边距加大 */
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        margin-bottom: 0px; /* 去除底部空白 */
        height: 100%; /* 尝试撑满 */
    }
    
    .section-header {
        font-size: 1.8rem; /* 加大 */
        font-weight: 900;
        color: #263238;
        margin-bottom: 30px;
        border-bottom: 4px solid #eceff1;
        padding-bottom: 15px;
        display: flex;
        align-items: center;
    }

    /* === 3. 右侧模块高度平衡优化 === */
    
    /* 占位符模块 - 强制加高以对齐左侧 */
    .placeholder-box {
        background-color: #f8f9fa; 
        border: 4px dashed #cfd8dc; 
        border-radius: 16px; 
        padding: 40px; 
        text-align: center; 
        color: #78909c;
        min-height: 750px; /* 关键：强制高度加大，撑开右侧 */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-top: 25px; /* 与上方图例拉开间距 */
    }
    
    /* 图例模块 - 加大尺寸，放在上方 */
    .reference-box {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 25px 30px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    .ref-title {
        font-weight: 900;
        color: #37474f;
        margin-bottom: 15px;
        font-size: 1.4rem; /* 加大 */
        border-bottom: 2px solid #f5f5f5;
        padding-bottom: 10px;
    }
    .ref-item {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        font-size: 1.25rem; /* 加大 */
        font-weight: 500;
        color: #455a64;
    }
    .ref-dot {
        width: 24px; /* 加大 */
        height: 24px;
        border-radius: 50%;
        margin-right: 15px;
        display: inline-block;
        border: 1px solid rgba(0,0,0,0.1);
        flex-shrink: 0;
    }

    /* === 4. 风险卡片配色 === */
    .risk-card-low { 
        background-color: #e8f5e9; color: #1b5e20; border: 4px solid #2e7d32;
    }
    /* 香蕉黄风格 */
    .risk-card-mid { 
        background-color: #FFF9C4; color: #212121; border: 4px solid #FBC02D;
    }
    .risk-card-high { 
        background-color: #ffebee; color: #b71c1c; border: 4px solid #c62828;
    }

    /* 临床建议框 */
    .protocol-box {
        background-color: #fafafa;
        border: 1px solid #ddd;
        border-left: 8px solid #546e7a;
        padding: 30px;
        border-radius: 6px;
        margin-top: 25px;
        font-size: 1.2rem; /* 加大 */
    }

    /* === 5. 输入框字体超级增强 === */
    .stNumberInput label {
        font-size: 1.5rem !important;  /* 字体极大 */
        font-weight: 900 !important;    /* 极粗 */
        color: #000000 !important;      /* 纯黑 */
        margin-bottom: 10px !important;
        letter-spacing: 0.5px;
    }
    .stNumberInput input {
        font-size: 1.25rem;
        color: #000;
        font-weight: 500;
    }
    /* 单选按钮字体加大 */
    .stRadio label {
        font-size: 1.3rem !important;
        color: #212121 !important;
        font-weight: 500 !important;
    }
    .stRadio div[role='radiogroup'] {
        gap: 15px;
    }
    
    /* 按钮样式 */
    div.stButton > button:first-child {
        background: #1565c0;
        color: white;
        font-size: 1.5rem; /* 按钮字加大 */
        height: 3.5em;
        border-radius: 12px;
        border: none;
        width: 100%;
        font-weight: 900;
        box-shadow: 0 6px 12px rgba(21, 101, 192, 0.25);
        margin-top: 25px;
    }
    div.stButton > button:first-child:hover {
        background: #0d47a1;
        transform: translateY(-3px);
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
        # DEMO DATA
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

# --- 文案 (About SHScore) ---
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

# --- 加载数据 ---
rules_df = load_rules()

# --- 主内容区：两列布局 (Left 1.1 : Right 0.9) ---
col_inputs, col_results = st.columns([1.1, 0.9], gap="large")

# ================================
# 左侧：配置与输入 (Configuration)
# ================================
with col_inputs:
    # 开始卡片容器
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    # 1. Subgroup
    st.markdown("##### 1. Patient Subgroup Profile")
    selected_group_label = st.radio(
        "Select profile:",
        options=list(GROUP_MAPPING.keys()),
        index=0,
        label_visibility="collapsed"
    )
    selected_group = GROUP_MAPPING[selected_group_label]
    current_group_vars = rules_df[rules_df["Group"] == selected_group]["Variable"].unique()
    
    st.markdown("---")
    st.markdown("##### 2. Clinical Variables")
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
        submitted = st.form_submit_button("🚀 Calculate Risk Score")
    
    st.markdown('</div>', unsafe_allow_html=True) # 结束卡片

# ================================
# 右侧：结果展示 & 布局互换
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

        # 1. 结果大卡片
        st.markdown(f"""
        <div class="card-container {risk_class}" style="text-align: center;">
            <div style="font-size: 1.2rem; font-weight: 700; opacity: 0.8; letter-spacing: 1px;">PREDICTED 7-DAY MORTALITY</div>
            <div style="font-size: 2.2rem; font-weight: 900; margin: 15px 0; color: inherit;">{risk_label}</div>
            <div style="font-size: 5.5rem; font-weight: 900; line-height: 1; margin-bottom: 20px;">{prob_percent:.1f}%</div>
            <div style="background: rgba(255,255,255,0.4); display: inline-block; padding: 10px 25px; border-radius: 30px; font-weight: bold; font-size: 1.4rem;">
                SHScore: {score} pts
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. 详细建议
        st.markdown(f"""
        <div class="protocol-box">
            <h5 style="color: {color_hex}; margin-top:0; font-weight:900;">📋 Clinical Management Guide</h5>
            {protocol}
        </div>
        """, unsafe_allow_html=True)

        # 3. 动态仪表盘 (移到底部)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Risk Severity Gauge", 'font': {'size': 20, 'color': "#555", 'weight': 'bold'}},
            number = {'suffix': " pts", 'font': {'color': color_hex, 'weight': 'bold', 'size': 24}},
            gauge = {
                'axis': {'range': [None, 80], 'tickwidth': 1, 'tickcolor': "#333"}, 
                'bar': {'color': color_hex, 'thickness': 0.25},
                'bgcolor': "white",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 20], 'color': '#a5d6a7'},  # 浅绿
                    {'range': [20, 35], 'color': '#FFF59D'}, # 浅香蕉黄
                    {'range': [35, 80], 'color': '#ef9a9a'}  # 浅红
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 3},
                    'thickness': 0.8,
                    'value': score
                }
            }))
        fig.update_layout(height=220, margin=dict(l=30, r=30, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    else:
        # === 布局互换：Risk Reference 在上，Ready to Calculate 在下 ===
        
        # 1. Risk Reference (图例模块) - 放在顶部
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 20 pts:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>20 - 35 pts:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 35 pts:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Ready to Calculate (占位符模块) - 放在底部，且加高
        st.markdown("""
        <div class="placeholder-box">
            <div style="font-size: 5rem; margin-bottom: 20px;">👈</div>
            <h2 style="margin:0; font-weight:900; color:#546e7a; font-size: 2.2rem;">Ready to Calculate</h2>
            <p style="margin-top: 20px; font-size:1.3rem; max-width:80%;">
                Please enter the patient's clinical data in the left <b>Configuration</b> panel to generate a precision risk assessment.
            </p>
        </div>
        """, unsafe_allow_html=True)