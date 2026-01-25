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
    page_title="SHScore Sepsis Risk Calculator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    /* 引入 Google Fonts */
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* 标题样式 */
    .main-title {
        color: #00008B; /* 深蓝 */
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #7f8c8d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* 卡片容器样式 */
    .card-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border: 1px solid #f0f2f6;
    }
    
    /* 侧边栏样式优化 */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    /* 风险卡片样式 (深色系) */
    .risk-card-low { 
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
        color: #006400; /* 深绿 */
        border-left: 6px solid #006400; 
    }
    .risk-card-mid { 
        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%); 
        color: #856404; 
        border-left: 6px solid #ffc107; 
    }
    .risk-card-high { 
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%); 
        color: #8B0000; /* 深红 */
        border-left: 6px solid #8B0000; 
    }
    
    .protocol-box {
        background-color: #f0f4f8;
        border-left: 4px solid #00008B; /* 深蓝 */
        padding: 15px;
        border-radius: 4px;
        margin-top: 15px;
        color: #2c3e50;
    }
    
    /* 输入框标签微调 */
    .stNumberInput label {
        font-weight: 600;
        color: #34495e;
    }
    
    /* 按钮样式 */
    div.stButton > button:first-child {
        background-color: #00008B;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #0000CD;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 配置与映射表
# ==========================================
# 变量单位与全称映射 (已修正变量名为大写开头)
VAR_META = {
    "Age": {"unit": "years", "full": "Age"},
    "APSIII_score": {"unit": "pts", "full": "APSIII Score"},
    "Aniongap": {"unit": "mmol/L", "full": "Anion Gap"}, # 修正
    "aniongap": {"unit": "mmol/L", "full": "Anion Gap"}, # 兼容小写
    "BUN": {"unit": "mg/dL", "full": "Blood Urea Nitrogen"},
    "DBP": {"unit": "mmHg", "full": "Diastolic BP"},
    "Fluid_amount": {"unit": "mL", "full": "Fluid Amount"}, # 兼容旧名
    "Fluid Amount": {"unit": "mL", "full": "Fluid Amount"}, # 修正
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
    "Global": "Global",
    "Renal Disease": "Renal_Disease",
    "Liver Disease": "Liver_Disease",
    "Immunodeficiency Disease": "Immunodeficiency_Disorder"
}

# ==========================================
# 3. 核心逻辑函数
# ==========================================

@st.cache_data
def load_rules(csv_path="SHScore_Compact_Rules.csv"):
    """加载并解析规则 CSV，如果不存在则生成 Demo 数据"""
    df = None
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
        except:
            pass
            
    # 如果文件不存在，创建演示数据
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
        # 补全演示数据长度
        for k in data.keys():
            if k != "Variable":
                if len(data[k]) < 12: data[k] = data[k] + ["N/A"] * (12 - len(data[k]))
        df = pd.DataFrame(data)
        st.toast("⚠️ Loaded DEMO rules (CSV not found).", icon="ℹ️")

    # 数据清洗
    df = df.rename(columns=lambda x: x.strip())
    
    # 统一变量名 (修正 fluid_amount -> Fluid Amount 等)
    df["Variable"] = df["Variable"].str.replace("fluid_amount", "Fluid Amount", case=False)
    df["Variable"] = df["Variable"].str.replace("aniongap", "Aniongap", case=False)
    
    id_vars = ["Variable"]
    if "Category" in df.columns: id_vars.append("Category")
    
    df_long = df.melt(id_vars=id_vars, var_name="Group", value_name="RuleString")
    df_long = df_long.dropna(subset=["RuleString"])
    df_long = df_long[~df_long["RuleString"].isin(["", "N/A", "--"])]
    
    return df_long

def parse_rule_string(rule_str):
    """解析规则字符串"""
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
        except:
            continue
    return rules

def calculate_score(user_inputs, rules_df, selected_group):
    """计算总分"""
    total_score = 0
    details = []
    
    group_rules = rules_df[rules_df["Group"] == selected_group]
    
    for _, row in group_rules.iterrows():
        raw_var = row["Variable"]
        clean_var = re.sub(r"\(.*\)", "", raw_var).strip()
        
        input_key = None
        for k in user_inputs.keys():
            if k.lower() == clean_var.lower():
                input_key = k
                break
        
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

# --- 侧边栏 ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/medical-doctor.png", width=60)
    st.title("Configuration")
    
    selected_group_label = st.radio(
        "Select Patient Subgroup",
        options=list(GROUP_MAPPING.keys()),
        index=0
    )
    selected_group = GROUP_MAPPING[selected_group_label]
    
    st.info("💡 **Tips:** Enter values on the left. Press 'Calculate Risk' to see mortality prediction.")
    st.divider()
    st.caption("v2.1 | Deep Color Theme")

# --- 主标题区域 ---
st.markdown('<div class="main-title">SHScore Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">A Precision Stratification Tool for Sepsis Mortality Risk</div>', unsafe_allow_html=True)

rules_df = load_rules()
current_group_vars = rules_df[rules_df["Group"] == selected_group]["Variable"].unique()

# --- 输入表单区域 ---
col_inputs, col_results = st.columns([1.2, 0.8], gap="large")

with col_inputs:
    st.markdown('<div class="card-container"><h5>📝 Clinical Characteristics</h5><hr>', unsafe_allow_html=True)
    
    user_inputs = {}
    
    with st.form("input_form"):
        input_cols = st.columns(2)
        sorted_vars = sorted(current_group_vars)
        
        for i, var_str in enumerate(sorted_vars):
            clean_name = re.sub(r"\(.*\)", "", var_str).strip()
            
            # 查找元数据
            meta = None
            for k, v in VAR_META.items():
                if k.lower() == clean_name.lower():
                    meta = v
                    break
            
            label = clean_name
            if meta:
                label = f"{meta['full']} ({meta['unit']})"
            
            col_idx = i % 2
            with input_cols[col_idx]:
                user_inputs[clean_name] = st.number_input(
                    label, 
                    value=None, 
                    placeholder="Value",
                    step=0.1,
                    key=f"in_{clean_name}"
                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Calculate Risk", use_container_width=True)

# --- 结果展示区域 ---
with col_results:
    if submitted:
        score, prob, details = calculate_score(user_inputs, rules_df, selected_group)
        prob_percent = prob * 100
        
        # 判定风险等级 (使用深色系配色)
        if score < 20:
            risk_class = "risk-card-low"
            risk_label = "Low Risk"
            color_hex = "#006400" # Deep Green
            protocol = "✅ **Protocol:** Complete blood cultures, administer antibiotics, and initiate 30 ml/kg crystalloid fluid resuscitation within 3 hours."
        elif score <= 35:
            risk_class = "risk-card-mid"
            risk_label = "Intermediate Risk"
            color_hex = "#b8860b" # Dark Goldenrod
            protocol = "⚠️ **Protocol:** Synchronize cultures, antibiotics, and fluids within 1 hr. Consider vasopressors and implement lactate monitoring."
        else:
            risk_class = "risk-card-high"
            risk_label = "High Risk (Sepsis Shock)"
            color_hex = "#8B0000" # Deep Red
            protocol = "🚨 **Protocol:** Complete all bundle components within 1 hr. Initiate vasopressors, assess for intubation/source control."

        # 1. 结果卡片
        st.markdown(f"""
        <div class="card-container {risk_class}" style="text-align: center;">
            <h3 style="margin:0;">{risk_label}</h3>
            <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0;">{prob_percent:.1f}%</div>
            <div style="font-size: 1rem; opacity: 0.8;">Mortality Probability (7-Day)</div>
            <div style="margin-top: 10px; font-weight: bold; background: rgba(255,255,255,0.5); padding: 5px; border-radius: 5px;">Total Score: {score}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. 仪表盘 (Gauge Chart)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = prob_percent,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Risk Gauge", 'font': {'size': 14, 'color': "#00008B"}},
            number = {'suffix': "%", 'font': {'color': color_hex}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': color_hex},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 20], 'color': '#e8f5e9'},
                    {'range': [20, 50], 'color': '#fff8e1'},
                    {'range': [50, 100], 'color': '#ffebee'}],
            }))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # 3. 临床协议
        st.markdown(f"""
        <div class="protocol-box">
            {protocol}
        </div>
        """, unsafe_allow_html=True)

        # 4. 异常指标详情
        with st.expander("🔍 Risk Contributors (Abnormal Indicators)", expanded=True):
            if details:
                st.write("The following factors contributed to the score:")
                for d in details:
                    st.markdown(f"- **{d['var']}**: {d['val']} ➡️ `+{d['points']} pts`")
            else:
                st.success("No abnormal indicators found (Score 0).")

    else:
        st.info("👈 Please enter clinical values on the left.")
        st.markdown("""
        <div style="text-align: center; color: #ccc; padding: 40px; border: 2px dashed #ddd; border-radius: 10px;">
            <h3>Waiting for input...</h3>
        </div>
        """, unsafe_allow_html=True)