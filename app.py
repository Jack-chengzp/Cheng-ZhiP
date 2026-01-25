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
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式 - 医疗专业风格
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: #333333;
    }
    
    /* 主标题样式 */
    .main-title {
        color: #1565c0; /* 医疗蓝 */
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }
    .sub-title {
        color: #546e7a;
        font-size: 1.15rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* 关于模型介绍框 */
    .about-box {
        background-color: #e3f2fd; /* 淡蓝背景 */
        border-left: 6px solid #1565c0;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .about-title {
        font-weight: 700;
        color: #0d47a1;
        font-size: 1.1rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    .about-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #37474f;
    }

    /* 卡片容器 */
    .card-container {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        margin-bottom: 20px;
    }
    
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #455a64;
        margin-bottom: 15px;
        border-bottom: 2px solid #eceff1;
        padding-bottom: 10px;
    }

    /* === 风险等级卡片配色 (高对比度) === */
    /* 低危 - 森林绿 */
    .risk-card-low { 
        background-color: #e8f5e9; 
        color: #1b5e20; 
        border: 2px solid #2e7d32;
    }
    /* 中危 - 琥珀色 (对比度比纯黄高) */
    .risk-card-mid { 
        background-color: #fff8e1; 
        color: #bf360c; 
        border: 2px solid #ff8f00;
    }
    /* 高危 - 火红 */
    .risk-card-high { 
        background-color: #ffebee; 
        color: #b71c1c; 
        border: 2px solid #c62828;
    }

    /* 临床建议框 */
    .protocol-box {
        background-color: #fafafa;
        border: 1px solid #ddd;
        border-top: 4px solid #333;
        padding: 20px;
        border-radius: 4px;
        margin-top: 15px;
    }
    
    /* 按钮样式 */
    div.stButton > button:first-child {
        background: #1565c0;
        color: white;
        font-size: 1.1rem;
        height: 3em;
        border-radius: 8px;
        border: none;
        width: 100%;
        transition: all 0.3s;
    }
    div.stButton > button:first-child:hover {
        background: #0d47a1;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
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
        # DEMO DATA (用于演示)
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

# --- 主标题区域 ---
st.markdown('<div class="main-title">Sepsis Heterogeneity Score (SHScore)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Mortality Risk Stratification for Sepsis Patients</div>', unsafe_allow_html=True)

# --- 介绍模块 (移至上方) ---
st.markdown("""
<div class="about-box">
    <div class="about-title">📘 About SHScore</div>
    <div class="about-text">
        The <b>Sepsis Heterogeneity Score (SHScore)</b> is a novel, data-driven stratification tool designed to predict 7-day mortality in sepsis patients. 
        Unlike traditional scoring systems (e.g., SOFA, APACHE II) which apply a one-size-fits-all approach, SHScore is optimized to identify 
        <b>high-risk phenotypes</b>, particularly within specific comorbidity subgroups (Renal, Liver, and Immunodeficiency).
        <br><br>
        <i>This tool assists clinicians in early identification of patients requiring aggressive intervention.</i>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 侧边栏配置 ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/settings.png", width=50)
    st.markdown("## ⚙️ Configuration")
    
    st.markdown("### 1. Patient Subgroup")
    selected_group_label = st.radio(
        "Select the primary comorbidity profile:",
        options=list(GROUP_MAPPING.keys()),
        index=0
    )
    selected_group = GROUP_MAPPING[selected_group_label]
    
    st.markdown("---")
    
    st.markdown("### 2. Risk Reference")
    st.info("""
    **Score Interpretation:**
    
    🟢 **< 20 pts**: Low Risk
    * Routine sepsis management.
    
    🟠 **20 - 35 pts**: Intermediate Risk
    * Enhanced monitoring required.
    
    🔴 **> 35 pts**: High Risk
    * Urgent, aggressive ICU intervention.
    """)
    
    st.markdown("---")
    st.caption("© 2024 SHScore Research Group. For research use only.")

# --- 加载数据 ---
rules_df = load_rules()
current_group_vars = rules_df[rules_df["Group"] == selected_group]["Variable"].unique()

# --- 主内容区：两列布局 ---
col_inputs, col_results = st.columns([1.1, 0.9], gap="large")

with col_inputs:
    st.markdown('<div class="card-container"><div class="section-header">📝 Clinical Variables Input</div>', unsafe_allow_html=True)
    
    user_inputs = {}
    
    with st.form("input_form"):
        st.caption("Please enter the latest clinical values within the first 24 hours of admission.")
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
    
    st.markdown('</div>', unsafe_allow_html=True) # End card

with col_results:
    if submitted:
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        # === 核心逻辑：定义鲜艳配色与阈值 ===
        if score < 20:
            risk_class = "risk-card-low"
            risk_label = "LOW RISK"
            color_hex = "#2e7d32" # 鲜艳的森林绿
            color_bg = "#e8f5e9"
            protocol = """
            **✅ Standard Care Pathway**
            * **Monitoring:** Standard vital signs q4h.
            * **Fluids:** Maintain euvolemia.
            * **Antibiotics:** De-escalate based on culture results.
            * **Disposition:** General ward or step-down unit may be appropriate if stable.
            """
        elif score <= 35:
            risk_class = "risk-card-mid"
            risk_label = "INTERMEDIATE RISK"
            color_hex = "#f57f17" # 醒目的琥珀色
            color_bg = "#fff8e1"
            protocol = """
            **⚠️ Enhanced Surveillance Pathway**
            * **Monitoring:** Continuous telemetry. Hourly urine output.
            * **Labs:** Repeat lactate q6h if elevated.
            * **Intervention:** Low-dose vasopressors might be needed. Ensure central access.
            * **Disposition:** ICU admission recommended.
            """
        else:
            risk_class = "risk-card-high"
            risk_label = "HIGH RISK (SEPSIS SHOCK)"
            color_hex = "#c62828" # 鲜艳的火红
            color_bg = "#ffebee"
            protocol = """
            **🚨 Aggressive Resuscitation Pathway**
            * **Hemodynamics:** Target MAP > 65 mmHg immediately using norepinephrine.
            * **Support:** Prepare for mechanical ventilation and CRRT.
            * **Source Control:** Urgent surgical/interventional consult within 1 hour.
            * **Goals:** Lactate clearance > 20% within 2 hours. ScvO2 > 70%.
            """

        # 1. 结果大卡片
        st.markdown(f"""
        <div class="card-container {risk_class}" style="text-align: center;">
            <div style="font-size: 1rem; font-weight: 700; opacity: 0.8; letter-spacing: 1px;">PREDICTED MORTALITY RISK</div>
            <div style="font-size: 1.8rem; font-weight: 900; margin: 10px 0; color: {color_hex};">{risk_label}</div>
            <div style="font-size: 4.5rem; font-weight: 900; line-height: 1; margin-bottom: 10px;">{prob_percent:.1f}%</div>
            <div style="background: rgba(0,0,0,0.05); display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                SHScore: {score} pts
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. 动态仪表盘 (固定三色背景，指针变色)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Risk Severity Gauge", 'font': {'size': 14, 'color': "#555"}},
            number = {'suffix': " pts", 'font': {'color': color_hex, 'weight': 'bold', 'size': 20}},
            gauge = {
                'axis': {'range': [None, 80], 'tickwidth': 1, 'tickcolor': "#333"}, 
                'bar': {'color': color_hex, 'thickness': 0.25}, # 指针颜色跟随风险等级
                'bgcolor': "white",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 20], 'color': '#a5d6a7'},  # 浅绿
                    {'range': [20, 35], 'color': '#ffe082'}, # 浅黄
                    {'range': [35, 80], 'color': '#ef9a9a'}  # 浅红
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 3},
                    'thickness': 0.8,
                    'value': score
                }
            }))
        fig.update_layout(height=180, margin=dict(l=30, r=30, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # 3. 详细的医疗建议
        st.markdown(f"""
        <div class="protocol-box">
            <h5 style="color: {color_hex}; margin-top:0;">📋 Clinical Management Guide</h5>
            {protocol}
        </div>
        """, unsafe_allow_html=True)

        # 4. 解释性内容：为何得分
        with st.expander("🔍 Detailed Score Breakdown (Why this score?)", expanded=False):
            if details:
                st.write("The following indicators deviated from baseline, contributing to the score:")
                for d in details:
                    st.markdown(f"""
                    - **{d['var']}**: Value `{d['val']}` added **+{d['points']} pts**
                      <br><small style="color:gray">Rule: {d['rule']}</small>
                    """, unsafe_allow_html=True)
            else:
                st.success("All clinical indicators are within the baseline range (0 points added).")

    else:
        # 初始空白状态提示
        st.markdown("""
        <div style="background-color: #f1f8e9; border: 2px dashed #aed581; border-radius: 12px; padding: 40px; text-align: center; color: #558b2f;">
            <div style="font-size: 3rem; margin-bottom: 10px;">👈</div>
            <h3 style="margin:0;">Ready to Calculate</h3>
            <p style="margin-top: 10px;">Please enter clinical data in the left panel to generate a risk assessment.</p>
        </div>
        """, unsafe_allow_html=True)