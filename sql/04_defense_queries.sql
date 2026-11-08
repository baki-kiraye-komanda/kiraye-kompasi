-- ============================================================
-- 04_defense_queries.sql — Müdafiədə müəllim "SQL-də göstər" deyəndə işlədiləcək sorğular.
-- SQL Developer-də: BAKU_RENT bağlantısı -> bu faylı aç -> sorğunun üzərində Ctrl+Enter.
-- Hər sorğunun üstündə: nə göstərir və hansı SQL mövzusudur.
-- ============================================================

-- 1) Cədvəllərdə neçə sətir var? (COUNT, UNION ALL)
SELECT 'snapshot' AS cedvel, COUNT(*) AS setir FROM snapshot
UNION ALL SELECT 'fact_listing', COUNT(*) FROM fact_listing
UNION ALL SELECT 'dim_district', COUNT(*) FROM dim_district
UNION ALL SELECT 'dim_location', COUNT(*) FROM dim_location
UNION ALL SELECT 'dim_building_type', COUNT(*) FROM dim_building_type
UNION ALL SELECT 'salary_sector', COUNT(*) FROM salary_sector
UNION ALL SELECT 'salary_region', COUNT(*) FROM salary_region;

-- 2) Məlumat yolu tutuşur? Xam -> təmiz -> analiz (snapshot cədvəli)
--    analiz = təmiz − qeyri-adi qiymət − təkrar elan
SELECT snapshot_id, captured_at, rows_raw, rows_clean, rows_outlier, rows_duplicate,
       rows_clean - rows_outlier - rows_duplicate AS analiz_ucun
FROM snapshot ORDER BY captured_at;

-- 3) Eyni yoxlama birbaşa fakt cədvəlindən (CASE WHEN ilə şərti sayma)
SELECT COUNT(*)                                             AS temiz,
       SUM(CASE WHEN is_outlier   = 'Y' THEN 1 ELSE 0 END)  AS qeyri_adi,
       SUM(CASE WHEN is_duplicate = 'Y' THEN 1 ELSE 0 END)  AS tekrar,
       SUM(CASE WHEN is_outlier = 'N' AND is_duplicate = 'N' THEN 1 ELSE 0 END) AS analiz
FROM fact_listing
WHERE snapshot_id = (SELECT snapshot_id FROM v_latest_snapshot);

-- 4) Rayonlar üzrə median kirayə (GROUP BY, MEDIAN, PERCENTILE_CONT, HAVING)
SELECT district_name,
       COUNT(*)                                                      AS elan,
       ROUND(MEDIAN(price_azn))                                      AS median_azn,
       ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_azn)) AS p25,
       ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_azn)) AS p75
FROM v_listing_current
GROUP BY district_name
HAVING COUNT(*) >= 10
ORDER BY median_azn DESC;

-- 5) Ulduz sxemi: fakt + ölçü cədvəllərinin JOIN-i (view-suz, əl ilə)
SELECT d.district_name, b.building_type, f.rooms, f.area_m2, f.price_azn, f.url
FROM fact_listing f
JOIN dim_district d      ON d.district_id = f.district_id
JOIN dim_building_type b ON b.building_type_id = f.building_type_id
WHERE f.snapshot_id = (SELECT snapshot_id FROM v_latest_snapshot)
  AND f.is_outlier = 'N' AND f.is_duplicate = 'N'
FETCH FIRST 10 ROWS ONLY;

-- 6) Vasitəçi və mülkiyyətçi elanlarının qiyməti (insight: vasitəçi elanı daha bahadır)
SELECT CASE is_agency WHEN 'Y' THEN 'Vasitəçi' ELSE 'Mülkiyyətçi' END AS kim,
       COUNT(*) AS elan, ROUND(MEDIAN(price_azn)) AS median_azn
FROM v_listing_current
GROUP BY is_agency;

-- 7) Əsas sual: Bakıda median kirayə orta maaşın neçə faizidir? (alt sorğu, CROSS JOIN)
SELECT k.median_azn, m.avg_salary_azn AS baki_orta_maas, m.year AS maas_ili,
       ROUND(100 * k.median_azn / m.avg_salary_azn) AS kiraye_yuku_faiz
FROM (SELECT MEDIAN(price_azn) AS median_azn FROM v_listing_current WHERE is_baku_city = 'Y') k
CROSS JOIN (SELECT year, avg_salary_azn FROM salary_region
            WHERE region_name = 'Bakı şəhəri - cəmi'
              AND year = (SELECT MAX(year) FROM salary_region)) m;

-- 8) Rayonları ucuzdan bahaya sıralamaq (pəncərə funksiyası RANK)
SELECT district_name, rooms_group, median_azn,
       RANK() OVER (PARTITION BY rooms_group ORDER BY median_azn) AS ucuzluq_yeri
FROM v_district_stats
WHERE listings >= 10 AND rooms_group IN ('1', '2', '3')
ORDER BY rooms_group, ucuzluq_yeri;

-- 9) Təkrar elan nümunəsi: eyni mənzil, eyni qiymət, fərqli elan nömrəsi (R9 qaydası)
SELECT district_id, location_id, rooms, area_m2, floor, floors, price_azn,
       COUNT(*) AS nece_defe, MIN(listing_id) AS ilk_elan, MAX(listing_id) AS son_elan
FROM fact_listing
WHERE snapshot_id = (SELECT snapshot_id FROM v_latest_snapshot)
GROUP BY district_id, location_id, building_type_id, rooms, area_m2, floor, floors, price_azn
HAVING COUNT(*) > 1
ORDER BY nece_defe DESC
FETCH FIRST 10 ROWS ONLY;

-- 10) Keyfiyyət yoxlaması: boş (NULL) və məntiqsiz dəyərlər olmamalıdır
SELECT SUM(CASE WHEN price_azn IS NULL OR price_azn <= 0 THEN 1 ELSE 0 END) AS pis_qiymet,
       SUM(CASE WHEN area_m2   IS NULL OR area_m2   <= 0 THEN 1 ELSE 0 END) AS pis_sahe,
       SUM(CASE WHEN floor > floors THEN 1 ELSE 0 END)                    AS mertebe_xetasi,
       SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END)                AS yersiz
FROM fact_listing;

-- 11) Büdcə sorğusu (saytın əsas sorğusu) — 03_budget_query.sql faylındadır.
--     SQL Developer dəyər soruşacaq: budget=700, people=1, rooms=2
