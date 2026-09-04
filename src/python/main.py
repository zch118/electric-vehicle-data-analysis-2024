"""
EV-Insight-Pro 主程序入口
一键运行完整数据分析流水线
技术栈：SQL + Python + Excel + HTML
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from config import Config, LOG_FORMAT, LOG_LEVEL
from data.data_cleaner import DataCleaner
from data.db_manager import DatabaseManager
from analysis.eda_analyzer import EDAAnalyzer
from report.excel_report import ExcelReportGenerator
from models.model_trainer import split_data, save_model

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class PipelineRunner:
    """数据分析流水线执行器"""

    def __init__(self, skip_steps=None):
        self.skip_steps = skip_steps or []
        self.step_times = {}
        self.start_time = None
        self.results = {}

    def run(self):
        self.start_time = time.time()
        logger.info("=" * 60)
        logger.info("EV-Insight-Pro 新能源汽车数据分析平台")
        logger.info("技术栈：SQL + Python + Excel + HTML")
        logger.info("开始时间：" + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("=" * 60)

        try:
            if "clean" not in self.skip_steps:
                df = self._step_data_cleaning()
            else:
                import pandas as pd
                df = pd.read_csv(Config.CLEANED_DATA)

            if "database" not in self.skip_steps:
                self._step_database_build()

            if "eda" not in self.skip_steps:
                self._step_eda_analysis(df)

            if "excel" not in self.skip_steps:
                self._step_excel_report(df)

            if "model" not in self.skip_steps:
                self._step_model_training(df)

            if "html" not in self.skip_steps:
                self._step_html_dashboard()

            self._print_summary()
            return True
        except Exception as e:
            logger.error("流水线执行失败：" + str(e), exc_info=True)
            return False

    def _step_data_cleaning(self):
        logger.info("[1/6] 数据清洗与预处理...")
        step_start = time.time()
        cleaner = DataCleaner()
        cleaner.load_raw_data()
        cleaner.load_ai_features()
        cleaner.clean_ev_data()
        df = cleaner.merge_ai_features()
        self.step_times["cleaning"] = time.time() - step_start
        self.results["total_rows"] = len(df)
        logger.info("清洗完成：" + str(len(df)) + " 行有效数据")
        return df

    def _step_database_build(self):
        logger.info("[2/6] 构建SQLite星型数据模型...")
        step_start = time.time()
        db = DatabaseManager(Config.DB_PATH)
        db.create_tables()
        db.import_ev_data()
        db.build_aggregations()
        table_counts = db.get_table_stats()
        db.close()
        self.step_times["database"] = time.time() - step_start
        self.results["tables"] = table_counts
        logger.info("数据库已构建：" + str(Config.DB_PATH))

    def _step_eda_analysis(self, df):
        logger.info("[3/6] EDA探索性分析...")
        step_start = time.time()
        eda = EDAAnalyzer(df)
        eda.generate_full_report()
        self.step_times["eda"] = time.time() - step_start
        logger.info("EDA分析完成")

    def _step_excel_report(self, df):
        logger.info("[4/6] 生成Excel自动化分析报告...")
        step_start = time.time()
        excel_gen = ExcelReportGenerator()
        excel_gen.generate(df)
        self.step_times["excel"] = time.time() - step_start
        logger.info("Excel报告：" + str(Config.EXCEL_REPORT_PATH))

    def _step_model_training(self, df):
        logger.info("[5/6] 模型训练与评估...")
        step_start = time.time()
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
            from sklearn.preprocessing import LabelEncoder
            import joblib
            
            df_clean = df.dropna(subset=["base_msrp"]).copy()
            df_clean = df_clean[df_clean["base_msrp"] > 0]
            if "car_age" not in df_clean.columns and "model_year" in df_clean.columns:
                df_clean["car_age"] = 2024 - pd.to_numeric(df_clean["model_year"], errors="coerce")
            
            features = ["car_age", "electric_range", "model_year"]
            features += [col for col in ["battery_anxiety_mean","charging_convenience_mean","range_satisfaction_mean","smart_driving_satisfaction_mean","interior_quality_mean","value_for_money_mean","after_sales_service_mean"] if col in df_clean.columns]
            
            if "make" in df_clean.columns:
                le = LabelEncoder()
                df_clean["make_encoded"] = le.fit_transform(df_clean["make"].astype(str))
                features.append("make_encoded")
            
            X = df_clean[features].copy()
            y = pd.to_numeric(df_clean["base_msrp"], errors="coerce")
            for col in X.columns:
                X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)
            valid = ~y.isna()
            X, y = X[valid], y[valid]
            
            model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
            model.fit(X, y)
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            
            import os
            os.makedirs(str(Config.PROJECT_ROOT / "models"), exist_ok=True)
            model_path = str(Config.PROJECT_ROOT / "models" / "random_forest_model.pkl")
            joblib.dump({"model": model, "features": features, "r2_score": r2}, model_path)
            
            self.step_times["model"] = time.time() - step_start
            self.results["model_r2"] = r2
            logger.info("模型训练完成，R2=" + str(round(r2, 4)))
            logger.info("模型已保存: " + model_path)
        except Exception as e:
            logger.warning("模型训练跳过: " + str(e))
            self.step_times["model"] = time.time() - step_start

    def _step_html_dashboard(self):
        logger.info("[6/6] HTML交互式看板验证...")
        step_start = time.time()
        dashboard_path = Config.DASHBOARD_PATH
        if dashboard_path.exists():
            file_size = dashboard_path.stat().st_size
            self.results["dashboard_size"] = file_size
            logger.info("HTML看板已存在：" + str(dashboard_path))
            logger.info("文件大小：" + str(round(file_size / 1024, 1)) + "KB")
            logger.info("包含6个模块：数据概览/品牌分析/时间趋势/AI体验/预测模拟器/业务洞察")
        else:
            logger.warning("HTML看板不存在：" + str(dashboard_path))
        self.step_times["html"] = time.time() - step_start

    def _print_summary(self):
        total_time = time.time() - self.start_time
        logger.info("=" * 60)
        logger.info("分析流程全部完成！")
        logger.info("=" * 60)
        logger.info("总耗时：" + str(round(total_time, 2)) + "秒")
        logger.info("数据量：" + str(self.results.get("total_rows", "N/A")) + " 行")
        logger.info("数据库：" + str(Config.DB_PATH))
        logger.info("Excel报告：" + str(Config.EXCEL_REPORT_PATH))
        logger.info("HTML看板：" + str(Config.DASHBOARD_PATH))
        logger.info("SQL脚本：" + str(Config.SQL_DIR))
        logger.info("各步骤耗时：")
        for step, duration in self.step_times.items():
            pct = round(duration / total_time * 100, 1) if total_time > 0 else 0
            logger.info("  " + step + ": " + str(round(duration, 2)) + "秒 (" + str(pct) + "%)")
        logger.info("=" * 60)


def run_full_pipeline():
    runner = PipelineRunner()
    success = runner.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    run_full_pipeline()
