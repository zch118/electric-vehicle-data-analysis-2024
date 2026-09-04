"""
EV-Insight-Pro 配置管理模块
集中管理项目路径、数据参数、分析配置、可视化主题等全局配置
"""

from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
DB_PATH = DATABASE_DIR / "ev_analysis.db"
REPORTS_DIR = PROJECT_ROOT / "reports"
EXCEL_REPORT_DIR = REPORTS_DIR / "excel"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DASHBOARD_PATH = DASHBOARD_DIR / "index.html"
SRC_DIR = PROJECT_ROOT / "src"
SQL_DIR = SRC_DIR / "sql"
DOCS_DIR = PROJECT_ROOT / "docs"
IMG_DIR = PROJECT_ROOT / "img"

RAW_EV_DATA = RAW_DATA_DIR / "Electric_Vehicle_Population_Data.csv"
AI_FEATURES_DATA = PROCESSED_DATA_DIR / "ev_with_ai_features_real.csv"
CLEANED_DATA = PROCESSED_DATA_DIR / "ev_cleaned.csv"
EXCEL_REPORT_PATH = EXCEL_REPORT_DIR / "EV_Analysis_Report.xlsx"

CURRENT_YEAR = 2024
RANDOM_SEED = 42
TOP_N_BRANDS = 15
TOP_N_MODELS = 20

AI_FEATURE_COLUMNS = [
    "battery_anxiety_mean",
    "charging_convenience_mean",
    "range_satisfaction_mean",
    "smart_driving_satisfaction_mean",
    "interior_quality_mean",
    "value_for_money_mean",
    "after_sales_service_mean",
]

AI_FEATURE_NAMES_CN = {
    "battery_anxiety_mean": "电池焦虑指数",
    "charging_convenience_mean": "充电便利性",
    "range_satisfaction_mean": "续航满意度",
    "smart_driving_satisfaction_mean": "智能驾驶满意度",
    "interior_quality_mean": "内饰品质",
    "value_for_money_mean": "性价比感知",
    "after_sales_service_mean": "售后服务体验",
}

PRICE_RANGES = [
    {"name": "Budget (<30k)", "min": 0, "max": 30000},
    {"name": "Mid-range (30-50k)", "min": 30000, "max": 50000},
    {"name": "Premium (50-80k)", "min": 50000, "max": 80000},
    {"name": "Luxury (80k+)", "min": 80000, "max": float("inf")},
]

CAR_AGE_BINS = [0, 2, 5, 8, 11, 100]
CAR_AGE_LABELS = ["0-2年", "3-5年", "6-8年", "9-11年", "12年以上"]

CHART_COLORS = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#06B6D4"]

EXCEL_THEME = {
    "header_fill": "1E293B",
    "header_font": "FFFFFF",
    "subheader_fill": "334155",
    "accent_fill": "2563EB",
    "font_name": "Microsoft YaHei",
}

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

def ensure_dirs():
    directories = [
        DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, DATABASE_DIR,
        REPORTS_DIR, EXCEL_REPORT_DIR, DASHBOARD_DIR, SRC_DIR,
        SQL_DIR, DOCS_DIR, IMG_DIR,
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)

ensure_dirs()

class Config:
    PROJECT_ROOT = PROJECT_ROOT
    DATA_DIR = DATA_DIR
    RAW_DATA_DIR = RAW_DATA_DIR
    PROCESSED_DATA_DIR = PROCESSED_DATA_DIR
    DATABASE_DIR = DATABASE_DIR
    REPORTS_DIR = REPORTS_DIR
    EXCEL_REPORT_DIR = EXCEL_REPORT_DIR
    DASHBOARD_DIR = DASHBOARD_DIR
    DASHBOARD_PATH = DASHBOARD_PATH
    SQL_DIR = SQL_DIR
    DOCS_DIR = DOCS_DIR
    RAW_EV_DATA = RAW_EV_DATA
    AI_FEATURES_DATA = AI_FEATURES_DATA
    CLEANED_DATA = CLEANED_DATA
    DB_PATH = DB_PATH
    EXCEL_REPORT_PATH = EXCEL_REPORT_PATH
    CURRENT_YEAR = CURRENT_YEAR
    RANDOM_SEED = RANDOM_SEED
    TOP_N_BRANDS = TOP_N_BRANDS
    AI_FEATURE_COLUMNS = AI_FEATURE_COLUMNS
    AI_FEATURE_NAMES_CN = AI_FEATURE_NAMES_CN
    PRICE_RANGES = PRICE_RANGES
    CAR_AGE_BINS = CAR_AGE_BINS
    CAR_AGE_LABELS = CAR_AGE_LABELS
    CHART_COLORS = CHART_COLORS
    EXCEL_THEME = EXCEL_THEME
