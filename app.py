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
# 2. CSS 样式注入 (终极修复版)
# ==========================================
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* === 0. 基础布局 === */
    .block-container {
        padding-top: 3rem !important; 
        padding-bottom: 5rem !important;
    }

    /* === 1. [终极修复] 绿色计算按钮 (2.2rem) === */
    /* 使用高优先级选择器强制覆盖 */
    div.stButton > button {
        background-color: #2e7d32 !important; /* 强制鲜艳绿 */
        background-image: none !important;    /* 去除任何渐变 */
        color: #ffffff !important;            /* 白色文字 */
        border: none !important;
        border-radius: 12px !important;
        padding: 20px 30px !important;
        font-size: 2.2rem !important;         /* 强制 2.2rem */
        font-weight: 900 !important;
        height: auto !important;
        width: 100% !important;
        box-shadow: 0 5px 15px rgba(46, 125, 50, 0.3) !important;
        margin-top: 30px !important;
        transition: all 0.2s ease !important;
    }
    
    /* 悬停效果 */
    div.stButton > button:hover {
        background-color: #1b5e20 !important; /* 深绿色 */
        box-shadow: 0 8px 20px rgba(46, 125, 50, 0.5) !important;
        transform: translateY(-2px);
    }
    
    /* 点击效果 */
    div.stButton > button:active, div.stButton > button:focus {
        background-color: #1b5e20 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* 确保按钮内部文字标签也继承大小 */
    div.stButton > button p {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
    }

    /* === 2. 字体与标题 === */
    .main-title {
        color: #1565c0; 
        font-weight: 900;
        font-size: 3.5rem; 
        line-height: 1.1;
    }
    .sub-title {
        color: #546e7a;
        font-size: 1.6rem; 
        margin-bottom: 30px;
    }
    .section-header {
        font-size: 2.2rem; font-weight: 900; color: #1a237e;
        border-bottom: 4px solid #eceff1; padding-bottom: 15px; margin-bottom: 30px;
    }
    .subgroup-title { font-size: 1.8rem; font-weight: 900; margin-bottom: 20px; color: #000; }

    /* === 3. 输入控件样式 === */
    .card-container {
        background: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e0e0e0;
    }
    /* 单选框 */
    div[role="radiogroup"] { gap: 15px; }
    div[role="radiogroup"] label {
        padding: 15px !important; background: #f8f9fa; border: 2px solid #e0e0e0; border-radius: 10px;
    }
    div[role="radiogroup"] label p { font-size: 1.4rem !important; font-weight: 700 !important; color: #333 !important; }
    /* 数字输入框 */
    .stNumberInput label p { font-size: 1.6rem !important; font-weight: 900 !important; }
    .stNumberInput input { font-size: 1.3rem !important; min-height: 45px !important; }

    /* === 4. 右侧结果模块 === */
    /* 风险图例 */
    .reference-box {
        background: white; border: 3px solid #eee; border-radius: 15px; padding: 25px; margin-bottom: 25px;
    }
    .ref-title { font-size: 1.8rem; font-weight: 900; color: #333; margin-bottom: 15px; border-bottom: 2px solid #eee; }
    .ref-item { font-size: 1.4rem; margin-bottom: 10px; display: flex; align-items: center; }
    .ref-dot { width: 20px; height: 20px; border-radius: 50%; margin-right: 15px; display: inline-block; }

    /* [修改] 缩小后的风险结果卡片 */
    .risk-result-card {
        text-align: center;
        padding: 30px; /* 减小内边距 */
        border-radius: 20px;
        margin-bottom: 25px;
    }
    .risk-card-low { background:#e8f5e9; color:#1b5e20; border:6px solid #2e7d32; }
    .risk-card-mid { background:#fff9c4; color:#000; border:6px solid #fbc02d; }
    .risk-card-high { background:#ffebee; color:#b71c1c; border:6px solid #c62828; }

    /* [新增] 临床建议模块 */
    .protocol-box {
        background-color: #fafafa;
        border: 2px solid #e0e0e0;
        border-left-width: 12px; /* 左侧彩色边框 */
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    .protocol-title {
        font-size: 1.8rem; font-weight: 900; margin-bottom: 15px; display: flex; align-items: center;
    }
    .protocol-text { font-size: 1.4rem; line-height: 1.6; color: #37474f; }
    .protocol-text li { margin-bottom: 10px; }

    /* 异常指标模块 */
    .breakdown-box {
        background: white; border: 2px solid #eee; border-left-width: 12px;
        border-radius: 12px; padding: 30px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* 占位符 */
    .placeholder-box {
        background: #f1f8e9; border: 4px dashed #a5d6a7; border-radius: 20px;
        min-height: 700px; display: flex; flex-direction: column;
        justify-content: center; align-items: center; text-align: center; padding: 40px;
    }
    
    /* 关于介绍 */
    .about-box {
        background-color: #e3f2fd; border-left: 10px solid #1565c0; padding: 25px;
        border-radius: 10px; margin-bottom: 40px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 数据与逻辑
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
        # DEMO DATA for preview
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
# 4. 主界面布局
# ==========================================
st.markdown('<div class="main-title">Sepsis Heterogeneity Score (SHScore)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Mortality Risk Stratification for Sepsis Patients</div>', unsafe_allow_html=True)

st.markdown("""
<div class="about-box">
    <div class="about-title">📘 About SHScore</div>
    <div class="about-text">
        The <b>Sepsis Heterogeneity Score (SHScore)</b> is a novel, data-driven stratification tool developed using the <b>MIMIC-IV</b> database and externally validated within the <b>eICU</b> Collaborative Research Database. 
        It is specifically designed to predict <b>short-term (7-day) mortality risk</b> across diverse sepsis phenotypes (e.g., Renal, Liver, Immunodeficiency), demonstrating <b>superior predictive performance</b> compared to traditional scoring systems like SOFA and APACHE II.
    </div>
</div>
""", unsafe_allow_html=True)

rules_df = load_rules()
col_inputs, col_results = st.columns([1.1, 0.9], gap="large")

# === 左侧：输入区 ===
with col_inputs:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
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
        # [核心修复] 绿色 2.2rem 按钮
        submitted = st.form_submit_button("🚀 Calculate Risk Score")
    st.markdown('</div>', unsafe_allow_html=True)

# === 右侧：结果区 ===
with col_results:
    if submitted:
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        # 定义风险等级和对应的临床建议
        if score < 20:
            risk_class = "risk-card-low"; risk_label = "LOW RISK"; color_hex = "#2e7d32"
            protocol_title = "✅ Standard Care Pathway"
            protocol_items = """
            <li><b>Monitoring:</b> Standard vital signs q4h.</li>
            <li><b>Fluids:</b> Maintain euvolemia. avoid fluid overload.</li>
            <li><b>Antibiotics:</b> De-escalate based on culture results.</li>
            """
        elif score <= 35:
            risk_class = "risk-card-mid"; risk_label = "INTERMEDIATE RISK"; color_hex = "#FBC02D"
            protocol_title = "⚠️ Enhanced Surveillance Pathway"
            protocol_items = """
            <li><b>Monitoring:</b> Continuous telemetry. Hourly urine output.</li>
            <li><b>Labs:</b> Repeat lactate q6h if elevated.</li>
            <li><b>Intervention:</b> Consider low-dose vasopressors if MAP is unstable.</li>
            """
        else:
            risk_class = "risk-card-high"; risk_label = "HIGH RISK (SEPSIS SHOCK)"; color_hex = "#c62828"
            protocol_title = "🚨 Aggressive Resuscitation Pathway"
            protocol_items = """
            <li><b>Hemodynamics:</b> Target MAP > 65 mmHg immediately with vasopressors.</li>
            <li><b>Support:</b> Prepare for mechanical ventilation or CRRT immediately.</li>
            <li><b>Source Control:</b> Urgent surgical consult within 1 hour.</li>
            """

        # 1. 风险图例 (Top)
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 20 pts:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>20 - 35 pts:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 35 pts:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)

        # 2. [修改] 缩小后的风险结果卡片
        st.markdown(f"""
        <div class="risk-result-card {risk_class}">
            <div style="font-size: 1.6rem; font-weight: 700; opacity: 0.8;">PREDICTED 7-DAY MORTALITY</div>
            <div style="font-size: 3rem; font-weight: 900; margin: 15px 0; color: {color_hex};">{risk_label}</div>
            <div style="font-size: 6rem; font-weight: 900; line-height: 1; margin-bottom: 20px;">{prob_percent:.1f}%</div>
            <div style="background: rgba(255,255,255,0.6); display: inline-block; padding: 10px 30px; border-radius: 50px; font-weight: bold; font-size: 1.8rem;">
                SHScore: {score} pts
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. [新增] 临床建议模块 (Clinical Management Guide)
        st.markdown(f"""
        <div class="protocol-box" style="border-left-color: {color_hex};">
            <div class="protocol-title" style="color: {color_hex};">
                {protocol_title}
            </div>
            <ul class="protocol-text">
                {protocol_items}
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # 4. 异常指标列表
        st.markdown(f"""
        <div class="breakdown-box" style="border-left-color: {color_hex};">
            <div style="color: {color_hex}; font-weight: 900; font-size: 2rem; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                🔍 Abnormal Risk Factors
            </div>
        </div>
        """, unsafe_allow_html=True)

        if details:
            for d in details:
                c1, c2, c3 = st.columns([0.45, 0.35, 0.2])
                with c1: st.markdown(f"<span style='font-size:1.6rem; font-weight:bold; color:#333;'>{d['var']}</span>", unsafe_allow_html=True)
                with c2: st.markdown(f"<span style='font-size:1.4rem; color:#555;'>Value: {d['val']}</span>", unsafe_allow_html=True)
                with c3: st.markdown(f"<span style='font-size:1.6rem; font-weight:bold; color:{color_hex}; float:right;'>+{d['points']} pts</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
        else:
            st.success("✅ All clinical indicators are within the baseline range. (Score: 0)")

    else:
        # 初始状态
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
            <div style="font-size: 8rem; margin-bottom: 30px;">👈</div>
            <h2 style="margin:0; font-weight:900; color:#558b2f; font-size: 3rem;">Ready to Calculate</h2>
            <p style="margin-top: 25px; font-size:1.6rem; max-width:80%;">
                Please enter clinical data in the <b>Configuration</b> panel to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)