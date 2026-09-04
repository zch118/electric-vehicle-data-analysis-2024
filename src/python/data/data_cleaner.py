"""
数据清洗与预处理模块
负责原始数据的加载、清洗、特征工程
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RAW_EV_DATA, AI_FEATURES_DATA, CURRENT_YEAR, PROCESSED_DATA_DIR


class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        self.raw_df = None
        self.cleaned_df = None
        self.ai_df = None
        self.merged_df = None

    def load_raw_data(self, filepath=None):
        """加载原始EV数据"""
        filepath = filepath or RAW_EV_DATA
        self.raw_df = pd.read_csv(filepath)
        self.raw_df.columns = [c.strip() for c in self.raw_df.columns]
        print(f"原始数据加载: {self.raw_df.shape[0]} 行, {self.raw_df.shape[1]} 列")
        return self.raw_df

    def load_ai_features(self, filepath=None):
        """加载AI体验特征数据"""
        filepath = filepath or AI_FEATURES_DATA
        if Path(filepath).exists():
            self.ai_df = pd.read_csv(filepath, encoding="utf-8-sig")
            print(f"AI特征数据加载: {self.ai_df.shape[0]} 行")
        else:
            print(f"AI特征文件不存在: {filepath}")
        return self.ai_df

    def clean_ev_data(self):
        """清洗EV数据"""
        if self.raw_df is None:
            self.load_raw_data()

        df = self.raw_df.copy()

        # 1. 重命名列
        column_mapping = {
            "VIN (1-10)": "vin",
            "County": "county",
            "City": "city",
            "State": "state",
            "Postal Code": "postal_code",
            "Model Year": "model_year",
            "Make": "make",
            "Model": "model",
            "Electric Vehicle Type": "ev_type",
            "Clean Alternative Fuel Vehicle (CAFV) Eligibility": "cafv_eligibility",
            "Electric Range": "electric_range",
            "Base MSRP": "base_msrp",
            "Legislative District": "legislative_district",
            "DOL Vehicle ID": "dol_vehicle_id",
            "Vehicle Location": "vehicle_location",
            "Electric Utility": "electric_utility",
            "2020 Census Tract": "census_tract",
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        # 2. 处理MSRP为0的情况（视为缺失）
        df["base_msrp"] = df["base_msrp"].replace(0, np.nan)

        # 3. 处理续航为0的情况
        df["electric_range"] = df["electric_range"].replace(0, np.nan)

        # 4. 计算车龄
        df["car_age"] = CURRENT_YEAR - df["model_year"]

        # 5. 提取车辆类型简称
        df["ev_type_short"] = df["ev_type"].apply(
            lambda x: "BEV" if "BEV" in str(x) else ("PHEV" if "PHEV" in str(x) else "Other")
        )

        # 6. 价格区间分箱
        df["price_range"] = pd.cut(
            df["base_msrp"],
            bins=[0, 30000, 50000, 80000, float("inf")],
            labels=["Budget (<30k)", "Mid-range (30-50k)", "Premium (50-80k)", "Luxury (80k+)"]
        )

        # 7. 续航区间分箱
        df["range_group"] = pd.cut(
            df["electric_range"],
            bins=[0, 100, 200, 300, float("inf")],
            labels=["<100 miles", "100-200 miles", "200-300 miles", "300+ miles"]
        )

        # 8. 品牌标准化（大写）
        df["make"] = df["make"].str.upper().str.strip()

        self.cleaned_df = df
        print(f"数据清洗完成: {len(df)} 行")
        print(f"  有效价格记录: {df['base_msrp'].notna().sum()}")
        print(f"  有效续航记录: {df['electric_range'].notna().sum()}")
        return self.cleaned_df

    def merge_ai_features(self):
        """合并AI体验特征"""
        if self.cleaned_df is None:
            self.clean_ev_data()
        if self.ai_df is None:
            self.load_ai_features()

        if self.ai_df is None:
            print("无AI特征数据可合并")
            return self.cleaned_df

        # 按品牌型号合并
        ai_cols = ["make", "model"] + [c for c in self.ai_df.columns if "_mean" in c]
        ai_subset = self.ai_df[ai_cols].drop_duplicates(subset=["make", "model"])

        self.merged_df = self.cleaned_df.merge(
            ai_subset, on=["make", "model"], how="left"
        )
        print(f"AI特征合并完成: {len(self.merged_df)} 行")
        print(f"  匹配到AI特征的记录: {self.merged_df['battery_anxiety_mean'].notna().sum()}")
        return self.merged_df

    def save_cleaned_data(self, filename="cleaned_ev_data.csv"):
        """保存清洗后的数据"""
        output_path = PROCESSED_DATA_DIR / filename
        self.cleaned_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"清洗数据已保存: {output_path}")

    def save_merged_data(self, filename="ev_merged_full.csv"):
        """保存合并后的数据"""
        output_path = PROCESSED_DATA_DIR / filename
        self.merged_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"合并数据已保存: {output_path}")

    def get_data_quality_report(self):
        """生成数据质量报告"""
        if self.cleaned_df is None:
            self.clean_ev_data()

        df = self.cleaned_df
        report = {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
            "unique_brands": df["make"].nunique(),
            "unique_models": df["model"].nunique(),
            "year_range": f"{df['model_year'].min()} - {df['model_year'].max()}",
            "price_stats": df["base_msrp"].describe().to_dict(),
            "range_stats": df["electric_range"].describe().to_dict(),
        }
        return report


def run_cleaning_pipeline():
    """运行完整数据清洗流程"""
    cleaner = DataCleaner()
    cleaner.load_raw_data()
    cleaner.load_ai_features()
    cleaner.clean_ev_data()
    cleaner.merge_ai_features()
    cleaner.save_cleaned_data()
    cleaner.save_merged_data()

    report = cleaner.get_data_quality_report()
    print("\n===== 数据质量报告 =====")
    print(f"总记录数: {report['total_records']:,}")
    print(f"品牌数量: {report['unique_brands']}")
    print(f"型号数量: {report['unique_models']}")
    print(f"年份范围: {report['year_range']}")
    print(f"平均价格: ${report['price_stats']['mean']:,.0f}")
    print(f"平均续航: {report['range_stats']['mean']:.1f} 英里")

    return cleaner


if __name__ == "__main__":
    run_cleaning_pipeline()
