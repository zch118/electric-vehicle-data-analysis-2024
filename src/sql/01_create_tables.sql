-- EV-Insight-Pro 数据库建表脚本 (星型模型)
CREATE TABLE IF NOT EXISTS dim_vehicle (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT, make TEXT, model TEXT, model_year INTEGER,
    ev_type TEXT, cafv_eligibility TEXT, base_msrp REAL,
    electric_range INTEGER, car_age INTEGER
);
CREATE TABLE IF NOT EXISTS dim_geography (
    geo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT, county TEXT, city TEXT, postal_code TEXT,
    legislative_district INTEGER, census_tract TEXT
);
CREATE TABLE IF NOT EXISTS dim_time (
    time_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_year INTEGER, decade TEXT, year_group TEXT
);
CREATE TABLE IF NOT EXISTS dim_ai_features (
    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT, model TEXT,
    battery_anxiety_mean REAL, charging_convenience_mean REAL,
    range_satisfaction_mean REAL, smart_driving_satisfaction_mean REAL,
    interior_quality_mean REAL, value_for_money_mean REAL,
    after_sales_service_mean REAL
);
CREATE TABLE IF NOT EXISTS fact_ev_registration (
    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER DEFAULT 0,
    geo_id INTEGER DEFAULT 0,
    time_id INTEGER DEFAULT 0,
    feature_id INTEGER DEFAULT 0,
    vin TEXT, state TEXT, county TEXT, model_year INTEGER,
    dol_vehicle_id TEXT, vehicle_location TEXT, electric_utility TEXT
);
CREATE TABLE IF NOT EXISTS agg_brand_summary (
    make TEXT PRIMARY KEY, total_vehicles INTEGER, avg_msrp REAL,
    avg_range REAL, avg_car_age REAL, bev_count INTEGER, phev_count INTEGER,
    avg_battery_anxiety REAL, avg_smart_driving REAL, avg_interior_quality REAL
);
CREATE INDEX IF NOT EXISTS idx_vehicle_make ON dim_vehicle(make);
CREATE INDEX IF NOT EXISTS idx_geo_state ON dim_geography(state);
CREATE INDEX IF NOT EXISTS idx_fact_vehicle ON fact_ev_registration(vehicle_id);