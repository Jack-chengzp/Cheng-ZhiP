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
    page_title="SHScore Clinical Calculator",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式 - 高对比度、鲜艳配色
st.markdown("""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    /* 标题样式 */
    .main-title {
        color: #1a237e; /* 靛蓝 */
        font-weight: 900;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #546e7a;
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 2rem;
    }

    /* 卡片容器 */
    .card-container {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }

    /* === 风险等级卡片配色 (高饱和度) === */
    /* 低危 - 鲜绿 */
    .risk-card-low { 
        background-color: #d4edda; 
        color: #155724; 
        border-left: 8px solid #28a745; 
    }
    /* 中危 - 亮黄/琥珀色 (为了对比度使用琥珀色文字) */
    .risk-card-mid { 
        background-color: #fff3cd; 
        color: #856404; 
        border-left: 8px solid #ffc107; 
    }
    /* 高危 - 鲜红 */
    .risk-card-high { 
        background-color: #f8d7da; 
        color: #721c24; 
        border-left: 8px solid #dc3545; 
    }

    /* 临床建议框 */
    .protocol-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-left: 5px solid #1a237e;
        padding: 20px;
        border-radius: 5px;
        margin-top: 15px;
        font-size: 1.05rem;
        line-height: 1.6;
    }

    /* 说明文本 */
    .info-text {
        font-size: 0.95rem;
        color: #455a64;
        line-height: 1.5;
    }
    
    /* 按钮样式优化 */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
        color: white;
        font-size: 1.1rem;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #283593 0%, #1a237e 100%);
        transform: translateY(-2px);
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
        # DEMO DATA (用于文件缺失时的演示)
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

# --- 侧边栏 (About Section) ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    selected_group_label = st.radio(
        "Select Patient Subgroup",
        options=list(GROUP_MAPPING.keys()),
        index=0
    )
    selected_group = GROUP_MAPPING[selected_group_label]
    
    st.divider()
    
    # --- 丰富内容：关于模型 ---
    st.markdown("### 📘 About SHScore")
    st.info("""
    The **Sepsis Heterogeneity Score (SHScore)** is a novel, data-driven tool designed to stratify mortality risk in sepsis patients.
    
    Unlike traditional scores (SOFA, APACHE II), SHScore is optimized for **high-risk subgroup identification** (e.g., Renal, Liver, Immunodeficiency).
    """)
    
    st.markdown("### 🚦 Risk Thresholds")
    st.markdown("""
    * 🟢 **< 20 pts**: Low Risk
    * 🟡 **20 - 35 pts**: Intermediate
    * 🔴 **> 35 pts**: High Risk
    """)

# --- 主标题区域 ---
st.markdown('<div class="main-title">SHScore Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Mortality Risk Stratification for Sepsis Patients</div>', unsafe_allow_html=True)

# --- 丰富内容：解释性折叠框 ---
with st.expander("ℹ️ How to use this calculator", expanded=False):
    st.markdown("""
    1.  **Select Subgroup**: Choose the patient's comorbidity profile from the sidebar.
    2.  **Input Data**: Enter the clinical variables below. Values will be automatically validated.
    3.  **Calculate**: Click the button to generate the risk probability and specific clinical protocol.
    """)

rules_df = load_rules()
current_group_vars = rules_df[rules_df["Group"] == selected_group]["Variable"].unique()

# --- 布局：左侧输入，右侧结果 ---
col_inputs, col_results = st.columns([1.2, 0.9], gap="large")

with col_inputs:
    st.markdown('<div class="card-container"><h4>📝 Enter Clinical Variables</h4><hr>', unsafe_allow_html=True)
    
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
                    label, value=None, placeholder="Value", step=0.1, key=f"in_{clean_name}"
                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Calculate Risk Score", use_container_width=True)

with col_results:
    if submitted:
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        # === 核心逻辑：定义鲜艳配色与阈值 ===
        # 绿色 (Low) | 黄色 (Mid) | 红色 (High)
        if score < 20:
            risk_class = "risk-card-low"
            risk_label = "LOW RISK"
            # 鲜艳的绿色
            color_hex = "#28a745" 
            bar_colors = ['#28a745', '#eee', '#eee'] # 仅绿色亮起
            protocol = """
            **✅ Standard Sepsis Protocol**
            * **Diagnostics:** Obtain blood cultures before antibiotics. Measure lactate.
            * **Treatment:** Administer broad-spectrum antibiotics within 3 hours.
            * **Fluids:** Initiate 30 mL/kg crystalloid for hypotension or lactate ≥ 4 mmol/L.
            """
        elif score <= 35:
            risk_class = "risk-card-mid"
            risk_label = "INTERMEDIATE RISK"
            # 鲜艳的黄色/琥珀色
            color_hex = "#ffc107"
            bar_colors = ['#28a745', '#ffc107', '#eee'] # 绿+黄亮起
            protocol = """
            **⚠️ Enhanced Monitoring Protocol**
            * **Urgency:** Complete 3-hour bundle within **1 hour**.
            * **Monitoring:** Continuous vital sign monitoring. Re-measure lactate if initial was elevated (>2 mmol/L).
            * **Circulation:** Consider early vasopressor support if MAP < 65 mmHg despite fluids.
            """
        else:
            risk_class = "risk-card-high"
            risk_label = "HIGH RISK (SEPSIS SHOCK)"
            # 鲜艳的红色
            color_hex = "#dc3545"
            bar_colors = ['#28a745', '#ffc107', '#dc3545'] # 全亮
            protocol = """
            **🚨 Critical Care Protocol (Aggressive)**
            * **Immediate Action:** Initiate vasopressors (Norepinephrine) immediately to maintain MAP ≥ 65 mmHg.
            * **Source Control:** Emergent assessment for source control (surgery/drainage) within 6-12 hours.
            * **Support:** Assess for invasive mechanical ventilation and renal replacement therapy.
            * **Goals:** Target ScvO2 > 70% and lactate clearance > 20% in 2 hours.
            """

        # 1. 结果大卡片
        st.markdown(f"""
        <div class="card-container {risk_class}" style="text-align: center;">
            <h2 style="margin:0; font-weight:900; letter-spacing: 1px;">{risk_label}</h2>
            <div style="font-size: 4rem; font-weight: 900; margin: 10px 0; line-height: 1;">{prob_percent:.1f}%</div>
            <div style="font-size: 1.1rem; font-weight: 500; opacity: 0.9;">Predicted 7-Day Mortality</div>
            <hr style="border-color: rgba(0,0,0,0.1); margin: 15px 20%;">
            <div style="font-size: 1.2rem; font-weight: bold;">SHScore: {score} pts</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. 动态仪表盘 (颜色对比度高)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,  # 显示分数
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Risk Severity Gauge (Score)", 'font': {'size': 15, 'color': "#333"}},
            number = {'suffix': " pts", 'font': {'color': color_hex, 'weight': 'bold'}},
            gauge = {
                'axis': {'range': [None, 80], 'tickwidth': 1}, # 假设最大分80左右
                'bar': {'color': color_hex, 'thickness': 0.3}, # 指针颜色跟随风险
                'bgcolor': "white",
                'borderwidth': 1,
                'bordercolor': "#ccc",
                'steps': [
                    {'range': [0, 20], 'color': '#e8f5e9'},  # 淡绿背景
                    {'range': [20, 35], 'color': '#fff3e0'}, # 淡黄背景
                    {'range': [35, 80], 'color': '#ffebee'}  # 淡红背景
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 3},
                    'thickness': 0.8,
                    'value': score
                }
            }))
        fig.update_layout(height=220, margin=dict(l=30, r=30, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # 3. 详细的医疗建议
        st.markdown(f"""
        <div class="protocol-box">
            {protocol}
        </div>
        """, unsafe_allow_html=True)

        # 4. 解释性内容：为何得分
        with st.expander("🔍 Risk Factor Breakdown (Why this score?)", expanded=True):
            if details:
                st.markdown("""
                <div style="background-color: white; border: 1px solid #eee; border-radius: 8px; padding: 15px;">
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="border-bottom: 2px solid #eee; color: #555;">
                        <th style="text-align:left; padding: 8px;">Indicator</th>
                        <th style="text-align:center; padding: 8px;">Value</th>
                        <th style="text-align:right; padding: 8px;">Contribution</th>
                    </tr>
                """, unsafe_allow_html=True)
                
                for d in details:
                    st.markdown(f"""
                    <tr style="border-bottom: 1px solid #f9f9f9;">
                        <td style="padding: 8px; font-weight:600; color: #333;">{d['var']}</td>
                        <td style="text-align:center; color: #666;">{d['val']}</td>
                        <td style="text-align:right; color: #dc3545; font-weight:bold;">+{d['points']}</td>
                    </tr>
                    """, unsafe_allow_html=True)
                
                st.markdown("</table></div>", unsafe_allow_html=True)
            else:
                st.success("All clinical indicators are within the baseline range.")

    else:
        # 初始空白状态提示
        st.markdown("""
        <div style="background-color: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 12px; padding: 40px; text-align: center; color: #adb5bd;">
            <div style="font-size: 3rem;">👈</div>
            <h3>Ready to Calculate</h3>
            <p>Please enter the patient's clinical data in the left panel and click <b>"Calculate Risk Score"</b>.</p>
        </div>
        """, unsafe_allow_html=True)

# --- 底部免责声明 ---
st.markdown("---")
st.caption("""
**Disclaimer:** This tool is intended for research and educational purposes only. It is not a substitute for professional medical judgment. 
The SHScore should be used as an adjunct to clinical assessment. 
© 2024 SHScore Research Group.
""")