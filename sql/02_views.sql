-- ============================================================
-- 02_views.sql — Analitik görünüşlər (view). Hər yükləmədə yenidən yaradılır.
-- Niyə view: hesablama qaydası bir yerdə (Oracle-da) saxlanılır.
-- Power BI, sayt və müdafiə sorğuları eyni qaydadan istifadə edir,
-- buna görə rəqəmlər hər yerdə eyni çıxır.
-- ============================================================

-- Ən son snapshot
CREATE OR REPLACE VIEW v_latest_snapshot AS
SELECT snapshot_id, captured_at, rows_raw, rows_clean, rows_outlier, rows_duplicate
FROM snapshot
WHERE captured_at = (SELECT MAX(captured_at) FROM snapshot);

-- Son snapshotun analiz üçün elanları: qeyri-adi qiymətlər və otaq kirayəsi (R8, R10) və təkrar elanlar (R9) çıxarılıb
CREATE OR REPLACE VIEW v_listing_current AS
SELECT f.snapshot_id,
       f.listing_id,
       d.district_id,
       d.district_name,
       d.is_baku_city,
       NVL(l.location_name, 'Naməlum') AS location_name,
       NVL(l.location_type, 'Naməlum') AS location_type,
       b.building_type,
       f.rooms,
       f.rooms_group,
       f.area_m2,
       f.floor,
       f.floors,
       f.price_azn,
       f.price_per_m2,
       f.has_repair,
       f.has_bill_of_sale,
       f.is_agency,
       f.updated_at,
       f.url
FROM fact_listing f
JOIN v_latest_snapshot s  ON s.snapshot_id = f.snapshot_id
JOIN dim_district d       ON d.district_id = f.district_id
JOIN dim_building_type b  ON b.building_type_id = f.building_type_id
LEFT JOIN dim_location l  ON l.location_id = f.location_id
WHERE f.is_outlier = 'N'
  AND f.is_duplicate = 'N';

-- Rayon x otaq sayı üzrə statistika (son snapshot).
-- Median: qiymətlərin ortası; çox baha və ya çox ucuz elanlar onu orta hesab kimi "çəkmir".
-- P25-P75: elanların orta 50%-nin qiymət intervalı.
CREATE OR REPLACE VIEW v_district_stats AS
SELECT district_name,
       is_baku_city,
       rooms_group,
       COUNT(*)                                                    AS listings,
       ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_azn))  AS p25_azn,
       ROUND(MEDIAN(price_azn))                                        AS median_azn,
       ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_azn))  AS p75_azn,
       ROUND(MEDIAN(price_per_m2), 1)                                  AS median_azn_per_m2,
       ROUND(MEDIAN(area_m2))                                          AS median_area_m2
FROM v_listing_current
GROUP BY district_name, is_baku_city, rooms_group;

-- Zaman üzrə dinamika: hər snapshot üçün rayon x otaq medianı
CREATE OR REPLACE VIEW v_price_trend AS
SELECT s.snapshot_id,
       s.captured_at,
       d.district_name,
       f.rooms_group,
       COUNT(*)                  AS listings,
       ROUND(MEDIAN(f.price_azn)) AS median_azn
FROM fact_listing f
JOIN snapshot s     ON s.snapshot_id = f.snapshot_id
JOIN dim_district d ON d.district_id = f.district_id
WHERE f.is_outlier = 'N'
  AND f.is_duplicate = 'N'
GROUP BY s.snapshot_id, s.captured_at, d.district_name, f.rooms_group;
