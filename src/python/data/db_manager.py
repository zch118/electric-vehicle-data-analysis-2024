"""数据库管理模块 - SQLite星型模型"""
import sqlite3
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH, RAW_EV_DATA, AI_FEATURES_DATA, CURRENT_YEAR


class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self, sql_file=None):
        if sql_file is None:
            sql_file = Path(__file__).parent.parent.parent / "sql" / "01_create_tables.sql"
        with open(sql_file, "r", encoding="utf-8-sig") as f:
            sql_script = f.read()
        if not self.conn:
            self.connect()
        self.conn.executescript(sql_script)
        self.conn.commit()
        print("数据库表结构创建完成")

    def import_ev_data(self, csv_path=None):
        csv_path = csv_path or RAW_EV_DATA
        print(f"正在导入数据: {csv_path}")
        df = pd.read_csv(csv_path)
        df.columns = [c.strip() for c in df.columns]
        df["car_age"] = CURRENT_YEAR - df["Model Year"]
        print(f"原始数据行数: {len(df)}")

        # 车辆维度表
        vdf = df[["VIN (1-10)","Make","Model","Model Year","Electric Vehicle Type",
                   "Clean Alternative Fuel Vehicle (CAFV) Eligibility","Base MSRP",
                   "Electric Range","car_age"]].copy()
        vdf.columns = ["vin","make","model","model_year","ev_type","cafv_eligibility",
                       "base_msrp","electric_range","car_age"]
        vdf = vdf.drop_duplicates(subset=["vin"])
        vdf.to_sql("dim_vehicle", self.conn, if_exists="append", index=False)
        print(f"  车辆维度表: {len(vdf)} 行")

        # 地理维度表
        gdf = df[["State","County","City","Postal Code","Legislative District",
                  "2020 Census Tract"]].copy()
        gdf.columns = ["state","county","city","postal_code","legislative_district","census_tract"]
        gdf = gdf.drop_duplicates()
        gdf.to_sql("dim_geography", self.conn, if_exists="append", index=False)
        print(f"  地理维度表: {len(gdf)} 行")

        # 时间维度表
        tdf = df[["Model Year"]].drop_duplicates().copy()
        tdf.columns = ["model_year"]
        tdf["decade"] = (tdf["model_year"] // 10 * 10).astype(str) + "s"
        tdf.to_sql("dim_time", self.conn, if_exists="append", index=False)
        print(f"  时间维度表: {len(tdf)} 行")

        # 事实表 - 直接写入，避免大merge
        fdf = df[["VIN (1-10)","State","County","Model Year","DOL Vehicle ID",
                  "Vehicle Location","Electric Utility"]].copy()
        fdf.columns = ["vin","state","county","model_year","dol_vehicle_id",
                       "vehicle_location","electric_utility"]
        # 简化：直接写入原始字段，不做ID关联
        fdf["vehicle_id"] = 0
        fdf["geo_id"] = 0
        fdf["time_id"] = 0
        fdf["feature_id"] = 0
        fdf[["vehicle_id","geo_id","time_id","feature_id","vin","state","county",
             "model_year","dol_vehicle_id","vehicle_location","electric_utility"]].to_sql(
            "fact_ev_registration", self.conn, if_exists="append", index=False)
        print(f"  事实表: {len(fdf)} 行")

        # 用SQL更新关联ID
        print("  更新关联ID...")
        # 用SQL关联更新ID
        self.conn.execute("""
            UPDATE fact_ev_registration
            SET vehicle_id = COALESCE((
                SELECT v.vehicle_id FROM dim_vehicle v
                WHERE v.vin = fact_ev_registration.vin LIMIT 1
            ), 0)
        """)
        self.conn.execute("""
            UPDATE fact_ev_registration
            SET geo_id = COALESCE((
                SELECT g.geo_id FROM dim_geography g
                WHERE g.state = fact_ev_registration.state
                AND g.county = fact_ev_registration.county LIMIT 1
            ), 0)
        """)
        self.conn.execute("""
            UPDATE fact_ev_registration
            SET time_id = COALESCE((
                SELECT t.time_id FROM dim_time t
                WHERE t.model_year = fact_ev_registration.model_year LIMIT 1
            ), 0)
        """)
        self.conn.commit()
        print("  关联ID更新完成")

        # 预聚合
        self.conn.execute("DELETE FROM agg_brand_summary")
        self.conn.execute("""
            INSERT OR REPLACE INTO agg_brand_summary
            SELECT v.make, COUNT(*), AVG(v.base_msrp), AVG(v.electric_range),
                   AVG(v.car_age),
                   SUM(CASE WHEN v.ev_type LIKE '%BEV%' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN v.ev_type LIKE '%PHEV%' THEN 1 ELSE 0 END),
                   0, 0, 0
            FROM fact_ev_registration f
            JOIN dim_vehicle v ON f.vehicle_id = v.vehicle_id
            WHERE v.base_msrp > 0
            GROUP BY v.make
        """)
        self.conn.commit()
        print("EV数据导入完成")

    def import_ai_features(self, csv_path=None):
        csv_path = csv_path or AI_FEATURES_DATA
        if not Path(csv_path).exists():
            print(f"AI特征文件不存在: {csv_path}")
            return
        print(f"正在导入AI特征: {csv_path}")
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        cols = ["make","model"] + [c for c in df.columns if "_mean" in c]
        cols = [c for c in cols if c in df.columns]
        adf = df[cols].drop_duplicates(subset=["make","model"])
        adf.to_sql("dim_ai_features", self.conn, if_exists="append", index=False)
        print(f"  AI特征表: {len(adf)} 行")
        self.conn.commit()


    def build_aggregations(self):
        """构建预聚合表（已在import_ev_data中完成）"""
        print("预聚合表已构建")
    def get_table_stats(self):
        tables = ["dim_vehicle","dim_geography","dim_time","dim_ai_features",
                  "fact_ev_registration","agg_brand_summary"]
        stats = {}
        for t in tables:
            try:
                stats[t] = self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except:
                stats[t] = 0
        return stats

    def execute_query(self, query):
        if not self.conn:
            self.connect()
        return pd.read_sql_query(query, self.conn)