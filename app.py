import streamlit as st
import pandas as pd
import numpy as np
import re
import os
import plotly.graph_objects as go

# ==========================================
# 1. 页面配置与 CSS 样式 (高对比度版)
# ==========================================
st.set_page_config(
    page_title="SHScore Sepsis Risk Calculator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 鲜艳配色定义
COLOR_LOW = "#00aa00"    # 鲜绿
COLOR_MID = "#ff9900"    # 鲜橙/金黄
COLOR_HIGH = "#ff0000"   # 鲜红
COLOR_NAVY = "#000066"   # 深藏蓝 (标题用)

st.markdown(f"""
<style>
    @import url('https://gs.jurieo.com/gemini/fonts-googleapis/css2?family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Roboto', sans-serif;
    }}
    
    /* 标题增强 */
    .main-title {{
        color: {COLOR_NAVY};
        font-weight: 900;
        font-size: 2.8rem;
        margin-bottom: 0px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .sub-title {{
        color: #555;
        font-size: 1.2rem;
        margin-bottom: 30px;
        font-weight: 500;
    }}

    /* 卡片容器 */
    .card-container {{
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }}
    
    /* 风险卡片 (高对比度) */
    .risk-card-low {{ 
        background-color: #e6fffa; 
        border: 2px solid {COLOR_LOW};
        color: {COLOR_LOW};
    }}
    .risk-card-mid {{ 
        background-color: #fff8e1; 
        border: 2px solid {COLOR_MID};
        color: {COLOR_MID};
    }}
    .risk-card-high {{ 
        background-color: #ffebee; 
        border: 2px solid {COLOR_HIGH};
        color: {COLOR_HIGH};
    }}
    
    /* 协议框 */
    .protocol-box {{
        background-color: #f8f9fa;
        border-left: 6px solid {COLOR_NAVY};
        padding: 20px;
        border-radius: 4px;
        margin-top: 20px;
        color: #333;
        font-size: 1.05rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    
    /* 侧边栏说明文字 */
    .sidebar-text {{
        font-size: 0.9rem;
        color: #444;
        line-height: 1.5;
    }}
    
    /* 按钮样式 */
    div.stButton > button:first-child {{
        background-color: {COLOR_NAVY};
        color: white;
        height: 3em;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 8px;
        border: 2px solid {COLOR_NAVY};
    }}
    div.stButton > button:first-child:hover {{
        background-color: white;
        color: {COLOR_NAVY};
        border: 2px solid {COLOR_NAVY};
    }}
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
    "RDW": {"unit": "%", "full": "RDW"},
    "RR": {"unit": "bpm", "full": "Respiratory Rate"},
    "SBP": {"unit": "mmHg", "full": "Systolic BP"},
    "SpO2": {"unit": "%", "full": "Oxygen Saturation"},
    "T": {"unit": "°C", "full": "Temperature"},
    "Urine": {"unit": "mL/24h", "full": "Urine Output"},
    "WBC": {"unit": "x10^9/L", "full": "White Blood Cells"},
    "Elixhauser_score": {"unit": "pts", "full": "Elixhauser"},
    "Weight": {"unit": "kg", "full": "Weight"}
}

GROUP_MAPPING = {
    "Global (General Sepsis)": "Global",
    "Renal Disease Subgroup": "Renal_Disease",
    "Liver Disease Subgroup": "Liver_Disease",
    "Immunodeficiency Subgroup": "Immunodeficiency_Disorder"
}

# ==========================================
# 3. 核心逻辑函数 (保持不变)
# ==========================================
@st.cache_data
def load_rules(csv_path="SHScore_Compact_Rules.csv"):
    df = None
    if os.path.exists(csv_path):
        try: df = pd.read_csv(csv_path)
        except: pass
            
    if df is None:
        # Demo Data
        data = {
            "Variable": ["Age (years)", "APSIII_score (pts)", "BUN (mg/dL)", "Elixhauser_score (pts)", "HCO3 (mmol/L)", "HR (bpm)", "MCV (fL)", "Mechnical_Ventilation (0=No, 1=Yes)", "T (°C)", "WBC (x10^9/L)", "Weight (Kg)", "Aniongap (mmol/L)"],
            "Global": ["< 60 (0)\n>= 60 (6)", "< 50 (0)\n>= 50 (10)", "< 30 (0)\n>= 30 (1)", "< 5 (0)\n>= 5 (2)", "< 22 (3)\n>= 22 (0)", "> 100 (2)\n<= 100 (0)", "> 90 (2)\n<= 90 (0)", "1 (4)\n0 (0)", "> 38 (0)\n<= 38 (2)", "> 12 (1)\n<= 12 (0)", "> 100 (4)\n<= 100 (0)", "> 15 (5)\n<= 15 (0)"],
            "Renal_Disease": ["< 60 (0)\n>= 60 (5)"] * 12, "Liver_Disease": ["< 60 (0)\n>= 60 (4)"] * 12, "Immunodeficiency_Disorder": ["< 60 (0)\n>= 60