"""
EDA探索性数据分析模块
提供品牌分析、地域分析、时间趋势、相关性分析等功能
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import AI_FEATURE_COLUMNS, AI_FEATURE_NAMES_CN


class EDAAnalyzer:
    """EDA分析器"""

    def __init__(self, df=None):
        self.df = df
        self.results = {}

    def set_data(self, df):
        """设置分析数据"""
        self.df = df

    def brand_analysis(self, top_n=15):
        """品牌市场分析"""
        df = self.df[self.df["base_msrp"] > 0].copy()

        brand_stats = df.groupby("make").agg(
            total_vehicles=("vin", "count"),
            avg_msrp=("base_msrp", "mean"),
            median_msrp=("base_msrp", "median"),
            avg_range=("electric_range", "mean"),
            avg_car_age=("car_age", "mean"),
            model_count=("model", "nunique"),
        ).reset_index()

        brand_stats["market_share_pct"] = (
            brand_stats["total_vehicles"] / brand_stats["total_vehicles"].sum() * 100
        ).round(2)

        brand_stats = brand_stats.sort_values("total_vehicles", ascending=False).head(top_n)
        self.results["brand_analysis"] = brand_stats
        return brand_stats

    def geographic_analysis(self, top_n=20):
        """地域分布分析"""
        df = self.df[self.df["base_msrp"] > 0].copy()

        geo_stats = df.groupby(["state", "county"]).agg(
            total_vehicles=("vin", "count"),
            avg_msrp=("base_msrp", "mean"),
            avg_range=("electric_range", "mean"),
            brand_diversity=("make", "nunique"),
        ).reset_index()

        geo_stats = geo_stats.sort_values("total_vehicles", ascending=False).head(top_n)
        self.results["geographic_analysis"] = geo_stats
        return geo_stats

    def time_trend_analysis(self):
        """时间趋势分析"""
        df = self.df[
            (self.df["model_year"] >= 2010) & (self.df["base_msrp"] > 0)
        ].copy()

        yearly = df.groupby("model_year").agg(
            vehicles_sold=("vin", "count"),
            avg_msrp=("base_msrp", "mean"),
            avg_range=("electric_range", "mean"),
            brand_count=("make", "nunique"),
            bev_pct=("ev_type_short", lambda x: (x == "BEV").mean() * 100),
        ).reset_index()

        # 计算同比增长
        yearly["yoy_growth_pct"] = yearly["vehicles_sold"].pct_change() * 100
        yearly["price_yoy_pct"] = yearly["avg_msrp"].pct_change() * 100

        self.results["time_trend"] = yearly
        return yearly

    def range_price_analysis(self):
        """续航与价格关系分析"""
        df = self.df[self.df["base_msrp"] > 0].copy()

        range_price = df.groupby("range_group", observed=True).agg(
            vehicle_count=("vin", "count"),
            avg_msrp=("base_msrp", "mean"),
            min_msrp=("base_msrp", "min"),
            max_msrp=("base_msrp", "max"),
            avg_car_age=("car_age", "mean"),
        ).reset_index()

        self.results["range_price"] = range_price
        return range_price

    def bev_phev_comparison(self):
        """BEV vs PHEV对比"""
        df = self.df[self.df["base_msrp"] > 0].copy()

        comparison = df.groupby("ev_type_short").agg(
            total_count=("vin", "count"),
            avg_msrp=("base_msrp", "mean"),
            median_msrp=("base_msrp", "median"),
            avg_range=("electric_range", "mean"),
            avg_car_age=("car_age", "mean"),
            brand_count=("make", "nunique"),
        ).reset_index()

        self.results["bev_phev"] = comparison
        return comparison

    def ai_feature_analysis(self):
        """AI体验特征分析"""
        if "battery_anxiety_mean" not in self.df.columns:
            print("数据中无AI特征列")
            return None

        df = self.df[self.df["base_msrp"] > 0].copy()
        ai_cols = [c for c in AI_FEATURE_COLUMNS if c in df.columns]

        # 品牌AI特征对比
        brand_ai = df.groupby("make")[ai_cols].mean().reset_index()
        brand_ai["vehicle_count"] = df.groupby("make")["vin"].count().values
        brand_ai = brand_ai[brand_ai["vehicle_count"] > 100]
        brand_ai = brand_ai.sort_values("smart_driving_satisfaction_mean", ascending=False)

        # AI特征与价格相关性
        corr_data = df[["base_msrp"] + ai_cols].dropna()
        correlations = corr_data.corr()["base_msrp"].drop("base_msrp").sort_values(ascending=False)

        self.results["ai_feature_brand"] = brand_ai
        self.results["ai_feature_correlation"] = correlations
        return brand_ai, correlations

    def price_segment_analysis(self):
        """价格区间分析"""
        df = self.df[self.df["base_msrp"] > 0].copy()

        segment = df.groupby("price_range", observed=True).agg(
            vehicle_count=("vin", "count"),
            avg_range=("electric_range", "mean"),
            avg_car_age=("car_age", "mean"),
            brand_count=("make", "nunique"),
            bev_pct=("ev_type_short", lambda x: (x == "BEV").mean() * 100),
        ).reset_index()

        self.results["price_segment"] = segment
        return segment

    def generate_full_report(self):
        """生成完整EDA报告"""
        print("===== EDA 分析报告 =====\n")

        print("--- 1. 品牌分析 (Top 10) ---")
        brand = self.brand_analysis(10)
        print(brand[["make", "total_vehicles", "market_share_pct", "avg_msrp", "avg_range"]].to_string(index=False))

        print("\n--- 2. 时间趋势 ---")
        trend = self.time_trend_analysis()
        print(trend[["model_year", "vehicles_sold", "avg_msrp", "avg_range", "bev_pct"]].to_string(index=False))

        print("\n--- 3. BEV vs PHEV ---")
        bev = self.bev_phev_comparison()
        print(bev.to_string(index=False))

        print("\n--- 4. 价格区间分析 ---")
        segment = self.price_segment_analysis()
        print(segment.to_string(index=False))

        if "battery_anxiety_mean" in self.df.columns:
            print("\n--- 5. AI特征与价格相关性 ---")
            _, corr = self.ai_feature_analysis()
            for feature, corr_val in corr.items():
                cn_name = AI_FEATURE_NAMES_CN.get(feature, feature)
                print(f"  {cn_name}: {corr_val:.3f}")

        return self.results


if __name__ == "__main__":
    from data.data_cleaner import DataCleaner
    cleaner = DataCleaner()
    cleaner.load_raw_data()
    cleaner.load_ai_features()
    cleaner.clean_ev_data()
    df = cleaner.merge_ai_features()

    analyzer = EDAAnalyzer(df)
    analyzer.generate_full_report()
