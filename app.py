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
# 2. CSS 样式 (V13.0)
# ==========================================
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* === 0. 顶部布局 === */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 5rem !important;
        max-width: 98% !important;
    }

    /* === 1. [核心] 绿色计算按钮 === */
    div.stButton > button {
        background-color: #2e7d32 !important; /* 鲜艳绿 */
        background-image: none !important;
        color: #ffffff !important;
        border: 3px solid #1b5e20 !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.2) !important;
        font-size: 32px !important; /* 字体加大 */
        font-weight: 900 !important;
        padding: 15px 0 !important;
        min-height: 80px !important;
        border-radius: 12px !important;
        width: 100% !important;
        margin-top: 35px !important;
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

    /* === 2. 字体强制扩大 (24px) === */
    .about-text { font-size: 24px !important; line-height: 1.5 !important; color: #37474f !important; }
    
    /* 单选框 */
    div[role="radiogroup"] label p { font-size: 24px !important; font-weight: 700 !important; color: #263238 !important; }
    div[role="radiogroup"] label { padding: 15px !important; background: #f8f9fa; border: 2px solid #cfd8dc; border-radius: 10px; }

    /* 输入框 */
    div[data-testid="stNumberInput"] label p { font-size: 24px !important; font-weight: 900 !important; color: #000000 !important; }
    div[data-testid="stNumberInput"] input { font-size: 22px !important; min-height: 55px !important; }

    /* === 3. 标题与模块 === */
    .main-title { color: #1565c0; font-weight: 900; font-size: 3.5rem; margin-bottom: 10px; }
    .sub-title { color: #546e7a; font-size: 1.8rem; margin-bottom: 30px; }
    .section-header { font-size: 2.4rem; font-weight: 900; color: #1a237e; border-bottom: 4px solid #eceff1; padding-bottom: 15px; margin-bottom: 25px; }
    .subgroup-title { font-size: 2.2rem; font-weight: 900; color: #000; margin-bottom: 15px; }

    /* === 4. 容器 === */
    .card-container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; }
    .about-box { background: #e3f2fd; border-left: 12px solid #1565c0; padding: 30px; border-radius: 12px; margin-bottom: 40px; }
    .about-title { font-size: 2.4rem; font-weight: 900; color: #0d47a1; margin-bottom: 15px; }

    /* === 5. 右侧模块 === */
    .reference-box { background: white; border: 3px solid #eee; border-radius: 15px; padding: 25px; margin-bottom: 25px; }
    .ref-title { font-size: 2.0rem; font-weight: 900; margin-bottom: 15px; border-bottom: 2px solid #eee; }
    .ref-item { font-size: 1.6rem; margin-bottom: 10px; display: flex; align-items: center; }
    .ref-dot { width: 25px; height: 25px; border-radius: 50%; margin-right: 15px; display: inline-block; }

    .risk-result-card { text-align: center; padding: 30px; border-radius: 20px; margin-bottom: 25px; }
    .risk-card-low { background:#e8f5e9; color:#1b5e20; border:5px solid #2e7d32; }
    .risk-card-mid { background:#fff9c4; color:#000; border:5px solid #fbc02d; }
    .risk-card-high { background:#ffebee; color:#b71c1c; border:5px solid #c62828; }

    .protocol-box { background: #fafafa; border: 2px solid #e0e0e0; border-left-width: 10px; padding: 25px; border-radius: 10px; margin-bottom: 25px; }
    .protocol-title { font-size: 2.0rem; font-weight: 900; margin-bottom: 10px; }
    
    .breakdown-box { background: white; border: 2px solid #eee; border-left-width: 10px; border-radius: 10px; padding: 25px; margin-top: 25px; }
    
    .placeholder-box { background: #f1f8e9; border: 4px dashed #a5d6a7; border-radius: 20px; min-height: 800px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 核心逻辑与数据
# ==========================================

# [关键修改] 变量元数据：使用 LaTeX 规范化学式，并修正显示名称
# full 字段中的 LaTeX 代码会被 Streamlit 自动渲染
VAR_META = {
    "Age": {"unit": "years", "full": "Age"},
    "APSIII_score": {"unit": "pts", "full": "APSIII_score"}, 
    "Aniongap": {"unit": "mmol/L", "full": "Aniongap"},     
    "aniongap": {"unit": "mmol/L", "full": "Aniongap"},
    "BUN": {"unit": "mg/dL", "full": "BUN"},                
    "DBP": {"unit": "mmHg", "full": "DBP"},                
    
    # [修改] Fluid_amount -> Fluid Amount
    "Fluid_amount": {"unit": "mL", "full": "Fluid Amount"}, 
    "Fluid Amount": {"unit": "mL", "full": "Fluid Amount"},
    
    # [修改] HCO3 -> HCO3- (3下标, -上标)
    "HCO3": {"unit": "mmol/L", "full": "HCO$_3^-$"},            
    
    "HR": {"unit": "bpm", "full": "HR"},                   
    
    # [修改] K -> K+ (+上标)
    "K": {"unit": "mmol/L", "full": "K$^+$"},                  
    
    "MCV": {"unit": "fL", "full": "MCV"},                  
    "Mechnical_Ventilation": {"unit": "0=No, 1=Yes", "full": "Mechnical_Ventilation"}, 
    
    # [修改] Na -> Na+ (+上标)
    "Na": {"unit": "mmol/L", "full": "Na$^+$"},                
    
    "RDW": {"unit": "%", "full": "RDW"},                   
    "RR": {"unit": "bpm", "full": "RR"},                   
    "SBP": {"unit": "mmHg", "full": "SBP"},                
    
    # [修改] SpO2 -> SpO2 (p下标, 2下标)
    "SpO2": {"unit": "%", "full": "S$_p$O$_2$"},                 
    
    "T": {"unit": "°C", "full": "T"},                      
    "Urine": {"unit": "mL/6h", "full": "Urine"},           
    "WBC": {"unit": "x10^9/L", "full": "WBC"},              
    "Elixhauser_score": {"unit": "pts", "full": "Elixhauser_score"}, 
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
        # Fallback Data (Variables aligned with CSV style)
        data = {
            "Variable": ["Age (years)", "APSIII_score (pts)", "BUN (mg/dL)", "Elixhauser_score (pts)", "HCO3 (mmol/L)", "HR (bpm)", "MCV (fL)", "Mechnical_Ventilation (0=No, 1=Yes)", "T (°C)", "WBC (x10^9/L)", "Weight (Kg)", "Aniongap (mmol/L)"],
            "Global": ["< 60 (0)\n>= 60 (6)", "< 50 (0)\n>= 50 (10)", "< 30 (0)\n>= 30 (1)", "< 5 (0)\n>= 5 (2)", "< 22 (3)\n>= 22 (0)", "> 100 (2)\n<= 100 (0)", "> 90 (2)\n<= 90 (0)", "1 (4)\n0 (0)", "> 38 (0)\n<= 38 (2)", "> 12 (1)\n<= 12 (0)", "> 100 (4)\n<= 100 (0)", "> 15 (5)\n<= 15 (0)"],
            "Renal_Disease": ["< 60 (0)\n>= 60 (5)"] * 12, "Liver_Disease": ["< 60 (0)\n>= 60 (4)"] * 12, "Immunodeficiency_Disorder": ["< 60 (0)\n>= 60 (7)"] * 12
        }
        for k in data.keys():
            if k != "Variable" and len(data[k]) < 12: data[k] = data[k] + ["N/A"] * (12 - len(data[k]))
        df = pd.DataFrame(data)

    df = df.rename(columns=lambda x: x.strip())
    # 标准化变量名 (确保代码逻辑能匹配到VAR_META的键)
    df["Variable"] = df["Variable"].str.replace("fluid_amount", "Fluid Amount", case=False)
    df["Variable"] = df["Variable"].str.replace("aniongap", "Aniongap", case=False)
    
    id_vars = ["Variable"]; 
    if "Category" in df.columns: id_vars.append("Category")
    df_long = df.melt(id_vars=id_vars, var_name="Group", value_name="RuleString")
    df_long = df_long.dropna(subset=["RuleString"])
    return df_long[~df_long["RuleString"].isin(["", "N/A", "--"])]

def parse_rule_string(rule_str):
    rules = []
    # 移除换行，统一成一行处理
    rule_str = str(rule_str).replace("\r\n", " ").replace("\n", " ")
    
    # 正则表达式：查找所有 (数字) 结尾的片段
    pattern = r"([^\(]+)\s*\((-?\d+)\)"
    matches = re.findall(pattern, rule_str)
    
    for condition_str, points_str in matches:
        try:
            points = int(points_str)
            condition_str = condition_str.strip()
            
            # 提取条件中的所有数字
            nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", condition_str)]
            
            mn, mx = -float('inf'), float('inf')
            
            if not nums:
                continue 
                
            # 解析条件逻辑
            if "-" in condition_str and len(nums) >= 2:
                mn, mx = nums[0], nums[1]
            elif ">=" in condition_str:
                mn = nums[0]
            elif ">" in condition_str:
                mn = nums[0] + 1e-9 
            elif "<=" in condition_str:
                mx = nums[0]
            elif "<" in condition_str:
                mx = nums[0] - 1e-9 
            elif "=" in condition_str or len(nums) == 1:
                mn, mx = nums[0], nums[0]
                
            rules.append({"min": mn, "max": mx, "points": points, "raw": f"{condition_str} ({points})"})
            
        except:
            continue
            
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

# ==========================================
# 4. 主界面布局
# ==========================================
st.markdown('<div class="main-title">Sepsis Heterogeneity Score (SHScore)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Mortality Risk Stratification for Sepsis Patients</div>', unsafe_allow_html=True)

# --- About ---
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
            
            # 使用 VAR_META 中定义的简写名称 (含 LaTeX)
            label = clean_name
            if meta: label = f"{meta['full']} ({meta['unit']})"
            
            with input_cols[i % 2]:
                user_inputs[clean_name] = st.number_input(label, value=None, placeholder="--", step=0.1, key=f"in_{clean_name}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Green Button
        submitted = st.form_submit_button("🚀 Calculate Risk Score")
    st.markdown('</div>', unsafe_allow_html=True)

# === Right Column: Results ===
with col_results:
    if submitted:
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        # Risk Logic based on Mortality Rate
        if prob_percent < 10:
            risk_class = "risk-card-low"; risk_label = "LOW RISK"; color_hex = "#2e7d32"
            protocol_title = "✅ Standard Care Pathway"
            protocol_list = """
- **Monitoring:** Standard vital signs q4h.
- **Fluids:** Maintain euvolemia. avoid fluid overload.
- **Antibiotics:** De-escalate based on culture results.
"""
        elif prob_percent <= 30:
            risk_class = "risk-card-mid"; risk_label = "INTERMEDIATE RISK"; color_hex = "#FBC02D"
            protocol_title = "⚠️ Enhanced Surveillance Pathway"
            protocol_list = """
- **Monitoring:** Continuous telemetry. Hourly urine output.
- **Labs:** Repeat lactate q6h if elevated.
- **Intervention:** Consider low-dose vasopressors if MAP is unstable.
"""
        else:
            risk_class = "risk-card-high"; risk_label = "HIGH RISK (SEPSIS SHOCK)"; color_hex = "#c62828"
            protocol_title = "🚨 Aggressive Resuscitation Pathway"
            protocol_list = """
- **Hemodynamics:** Target MAP > 65 mmHg immediately with vasopressors.
- **Support:** Prepare for mechanical ventilation or CRRT immediately.
- **Source Control:** Urgent surgical consult within 1 hour.
"""

        # 1. Risk Interpretation
        st.markdown("""
        <div class="reference-box">
            <div class="ref-title">🚦 Risk Score Interpretation (By Mortality Rate)</div>
            <div class="ref-item"><span class="ref-dot" style="background:#2e7d32;"></span> <b>&lt; 10%:</b>&nbsp; Low Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#FBC02D;"></span> <b>10% - 30%:</b>&nbsp; Intermediate Risk</div>
            <div class="ref-item"><span class="ref-dot" style="background:#c62828;"></span> <b>&gt; 30%:</b>&nbsp; High Risk</div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Risk Result Card
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
        
        # 3. Clinical Guide (Markdown)
        st.markdown(f"""
        <div class="protocol-box" style="border-left-color: {color_hex};">
            <div class="protocol-title" style="color: {color_hex};">
                {protocol_title}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(protocol_list)

        # 4. Abnormal Risk Factors
        st.markdown(f"""
        <div class="breakdown-box" style="border-left-color: {color_hex};">
            <div style="color: {color_hex}; font-weight: 900; font-size: 2rem; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                🔍 Abnormal Risk Factors
            </div>
        </div>
        """, unsafe_allow_html=True)

        if details:
            for d in details:
                # [修正] 结果展示区也应用变量名简写
                display_name = d['var']
                for k, v in VAR_META.items():
                    if k.lower() == d['var'].lower(): 
                        display_name = v['full']
                        break
                
                c1, c2, c3 = st.columns([0.45, 0.35, 0.2])
                with c1: st.markdown(f"<span style='font-size:1.6rem; font-weight:bold; color:#333;'>{display_name}</span>", unsafe_allow_html=True)
                with c2: st.markdown(f"<span style='font-size:1.4rem; color:#555;'>Value: {d['val']}</span>", unsafe_allow_html=True)
                with c3: st.markdown(f"<span style='font-size:1.6rem; font-weight:bold; color:{color_hex}; float:right;'>+{d['points']} pts</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
        else:
            st.success("✅ All clinical indicators are within the baseline range. (Score: 0)")

    else:
        # Initial Placeholder
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
            <p style="margin-top: 25px; font-size:1.6rem; max-width:80%;">
                Please enter clinical data in the <b>Configuration</b> panel to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)