-- ============================================
-- EV-Insight-Pro 数据分析查询脚本
-- 包含：品牌分析、地域分析、时间趋势、特征分析
-- ============================================

-- ========== 1. 品牌市场占有率分析 ==========
SELECT
    v.make AS brand,
    COUNT(*) AS total_vehicles,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_ev_registration), 2) AS market_share_pct,
    ROUND(AVG(v.base_msrp), 2) AS avg_msrp,
    ROUND(AVG(v.electric_range), 1) AS avg_range_miles,
    ROUND(AVG(v.car_age), 1) AS avg_car_age
FROM fact_ev_registration f
JOIN dim_vehicle v ON f.vehicle_id = v.vehicle_id
WHERE v.base_msrp > 0
GROUP BY v.make
ORDER BY total_vehicles DESC
LIMIT 20;

-- ========== 2. 品牌AI体验特征对比 ==========
SELECT
    af.make AS brand,
    COUNT(DISTINCT f.registration_id) AS vehicle_count,
    ROUND(AVG(af.battery_anxiety_mean), 2) AS battery_anxiety,
    ROUND(AVG(af.charging_convenience_mean), 2) AS charging_conv,
    ROUND(AVG(af.range_satisfaction_mean), 2) AS range_sat,
    ROUND(AVG(af.smart_driving_satisfaction_mean), 2) AS smart_driving,
    ROUND(AVG(af.interior_quality_mean), 2) AS interior_quality,
    ROUND(AVG(af.value_for_money_mean), 2) AS value_money,
    ROUND(AVG(af.after_sales_service_mean), 2) AS after_sales
FROM fact_ev_registration f
JOIN dim_ai_features af ON f.feature_id = af.feature_id
GROUP BY af.make
HAVING vehicle_count > 100
ORDER BY smart_driving DESC;

-- ========== 3. 地域分布分析（按州/县） ==========
SELECT
    g.state,
    g.county,
    COUNT(*) AS total_vehicles,
    ROUND(AVG(v.base_msrp), 2) AS avg_msrp,
    ROUND(AVG(v.electric_range), 1) AS avg_range,
    COUNT(DISTINCT v.make) AS brand_diversity
FROM fact_ev_registration f
JOIN dim_geography g ON f.geo_id = g.geo_id
JOIN dim_vehicle v ON f.vehicle_id = v.vehicle_id
WHERE v.base_msrp > 0
GROUP BY g.state, g.county
ORDER BY total_vehicles DESC
LIMIT 30;

-- ========== 4. 时间趋势分析（按车型年份） ==========
SELECT
    v.model_year,
    COUNT(*) AS vehicles_sold,
    ROUND(AVG(v.base_msrp), 2) AS avg_msrp,
    ROUND(AVG(v.electric_range), 1) AS avg_range,
    ROUND(AVG(CASE WHEN v.ev_type LIKE '%BEV%' THEN 1 ELSE 0 END) * 100, 1) AS bev_pct,
    COUNT(DISTINCT v.make) AS brand_count
FROM fact_ev_registration f
JOIN dim_vehicle v ON f.vehicle_id = v.vehicle_id
WHERE v.model_year >= 2010 AND v.base_msrp > 0
GROUP BY v.model_year
ORDER BY v.model_year;

-- ========== 5. 续航里程与价格关系分析 ==========
SELECT
    CASE
        WHEN v.electric_range = 0 THEN '0 (Unknown)'
        WHEN v.electric_range < 100 THEN '< 100 miles'
        WHEN v.electric_range < 200 THEN '100-200 miles'
        WHEN v.electric_range < 300 THEN '200-300 miles'
        ELSE '300+ miles'
    END AS range_group,
    COUNT(*) AS vehicle_count,
    ROUND(AVG(v.base_msrp), 2) AS avg_msrp,
    ROUND(MIN(v.base_msrp), 2) AS min_msrp,
    ROUND(MAX(v.base_msrp), 2) AS max_msrp
FROM fact_ev_registration f
JOIN dim_vehicle v ON f.vehicle_id = v.vehicle_id
WHERE v.base_msrp > 0
GROUP BY range_group
ORDER BY MIN(v.electric_range);

-- ========== 6. BEV vs PHEV 对比分析 ==========
SELECT
    CASE
        WHEN v.ev_type LIKE '%BEV%' THEN 'BEV (纯电动)'
        WHEN v.ev_type LIKE '%PHEV%' THEN 'PHEV (插电混动)'
        ELSE 'Other'
    END AS vehicle_type,
    COUNT(*) AS total_count,
    ROUND(AVG(v.base_msrp), 2) AS avg_msrp,
    ROUND(AVG(v.electric_range), 1) AS avg_range,
    ROUND(AVG(v.car_age), 1) AS avg_age,
    COUNT(DISTINCT v.make) AS brand_count
FROM fact_ev_registration f
JOIN dim_vehicle v ON f.vehicle_id = v.vehicle_id
WHERE v.base_msrp > 0
GROUP BY vehicle_type;

-- ========== 7. 品牌竞争力矩阵（市场份额 vs 平均价格） ==========
SELECT
    v.make AS brand,
    COUNT(*) AS total_vehicles,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_ev_registration WHERE base_msrp > 0), 2) AS market_share,
    ROUND(AVG(v.base_msrp), 0) AS avg_price,
    ROUND(AVG(v.electric_range), 0) AS avg_range,
    CASE
        WHEN AVG(v.base_msrp) > 60000 THEN 'Premium'
        WHEN AVG(v.base_msrp) > 35000 THEN 'Mid-range'
        ELSE 'Budget'
    END AS price_tier
FROM fact_ev_registration f
JOIN dim_vehicle v ON f.vehicle_id = v.vehicle_id
WHERE v.base_msrp > 0
GROUP BY v.make
HAVING total_vehicles > 50
ORDER BY market_share DESC;

-- ========== 8. 窗口函数：各品牌车型价格排名 ==========
SELECT
    make,
    model,
    model_year,
    base_msrp,
    electric_range,
    RANK() OVER (PARTITION BY make ORDER BY base_msrp DESC) AS price_rank_in_brand,
    DENSE_RANK() OVER (ORDER BY base_msrp DESC) AS overall_price_rank,
    ROUND(AVG(base_msrp) OVER (PARTITION BY make), 0) AS brand_avg_price,
    ROUND(base_msrp - AVG(base_msrp) OVER (PARTITION BY make), 0) AS price_vs_brand_avg
FROM dim_vehicle
WHERE base_msrp > 0
ORDER BY base_msrp DESC
LIMIT 50;

-- ========== 9. 同比增长分析（按年份） ==========
WITH yearly_stats AS (
    SELECT
        model_year,
        COUNT(*) AS vehicle_count,
        AVG(base_msrp) AS avg_msrp
    FROM dim_vehicle
    WHERE model_year >= 2015 AND base_msrp > 0
    GROUP BY model_year
)
SELECT
    curr.model_year,
    curr.vehicle_count,
    prev.vehicle_count AS prev_year_count,
    ROUND((curr.vehicle_count - prev.vehicle_count) * 100.0 / prev.vehicle_count, 1) AS yoy_growth_pct,
    ROUND(curr.avg_msrp, 0) AS avg_msrp,
    ROUND((curr.avg_msrp - prev.avg_msrp) * 100.0 / prev.avg_msrp, 1) AS price_yoy_pct
FROM yearly_stats curr
LEFT JOIN yearly_stats prev ON curr.model_year = prev.model_year + 1
ORDER BY curr.model_year;

-- ========== 10. AI特征与价格相关性（高分品牌） ==========
SELECT
    af.make,
    COUNT(*) AS sample_count,
    ROUND(AVG(v.base_msrp), 0) AS avg_price,
    ROUND(AVG(af.smart_driving_satisfaction_mean), 2) AS smart_driving_score,
    ROUND(AVG(af.interior_quality_mean), 2) AS interior_score,
    ROUND(AVG(af.battery_anxiety_mean), 2) AS battery_anxiety_score,
    CASE
        WHEN AVG(af.smart_driving_satisfaction_mean) >= 7 THEN '智驾领先'
        WHEN AVG(af.smart_driving_satisfaction_mean) >= 5 THEN '智驾主流'
        ELSE '智驾待提升'
    END AS smart_driving_tier
FROM fact_ev_registration f
JOIN dim_ai_features af ON f.feature_id = af.feature_id
JOIN dim_vehicle v ON f.vehicle_id = v.vehicle_id
WHERE v.base_msrp > 0
GROUP BY af.make
HAVING sample_count > 100
ORDER BY avg_price DESC;
