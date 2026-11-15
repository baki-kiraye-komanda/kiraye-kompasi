-- ============================================================
-- 04_defense_queries.sql — Müdafiədə müəllim "SQL-də göstər" deyəndə işlədiləcək sorğular.
-- SQL Developer-də: BAKU_RENT bağlantısı -> bu faylı aç -> kursoru sorğunun üzərinə qoy -> Ctrl+Enter.
-- Hər sorğunun üstündə: nə göstərir və hansı SQL mövzusudur.
-- ============================================================

-- 1) Cədvəllərdə neçə sətir var? (COUNT, UNION ALL)
--    UNION ALL bir neçə sorğunun nəticəsini alt-alta birləşdirir.
SELECT 'snapshot' AS cedvel, COUNT(*) AS setir FROM snapshot
UNION ALL SELECT 'fact_listing', COUNT(*) FROM fact_listing
UNION ALL SELECT 'dim_district', COUNT(*) FROM dim_district
UNION ALL SELECT 'dim_location', COUNT(*) FROM dim_location
UNION ALL SELECT 'dim_building_type', COUNT(*) FROM dim_building_type
UNION ALL SELECT 'salary_sector', COUNT(*) FROM salary_sector
UNION ALL SELECT 'salary_region', COUNT(*) FROM salary_region;

-- 2) Hər toplamanın (snapshot) "pasportu": nə vaxt toplandı, neçə sətir idi, neçəsi işarələndi
SELECT snapshot_id, captured_at,
       rows_raw,        -- saytdan toplanan
       rows_clean,      -- səhv sətirlər silindikdən sonra (R1–R7)
       rows_outlier,    -- qeyri-adi qiymət və otaq kirayəsi kimi işarələnən (R8, R10)
       rows_duplicate   -- təkrar elan kimi işarələnən (R9)
FROM snapshot
ORDER BY captured_at;

-- 3) Məlumat yolu tutuşur? Təmiz -> analiz (CASE WHEN ilə şərti sayma), son snapshot üçün.
--    Bəzi elanlar HƏM qeyri-adi, HƏM təkrardır, ona görə:
--    analiz = temiz − qeyri_adi − tekrar + her_ikisi
SELECT COUNT(*)                                             AS temiz,
       SUM(CASE WHEN is_outlier   = 'Y' THEN 1 ELSE 0 END)  AS qeyri_adi,
       SUM(CASE WHEN is_duplicate = 'Y' THEN 1 ELSE 0 END)  AS tekrar,
       SUM(CASE WHEN is_outlier = 'Y' AND is_duplicate = 'Y' THEN 1 ELSE 0 END) AS her_ikisi,
       SUM(CASE WHEN is_outlier = 'N' AND is_duplicate = 'N' THEN 1 ELSE 0 END) AS analiz
FROM fact_listing
WHERE snapshot_id = (SELECT snapshot_id FROM v_latest_snapshot);   -- alt sorğu: yalnız son snapshot

-- 4) Rayonlar üzrə median kirayə (GROUP BY, MEDIAN, PERCENTILE_CONT, HAVING)
SELECT district_name,
       COUNT(*)                                                      AS elan,
       ROUND(MEDIAN(price_azn))                                      AS median_azn,   -- ortadakı qiymət
       ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_azn)) AS p25,          -- elanların 25%-i bundan ucuzdur
       ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_azn)) AS p75           -- elanların 75%-i bundan ucuzdur
FROM v_listing_current
GROUP BY district_name
HAVING COUNT(*) >= 30          -- HAVING: qruplaşdırmadan SONRA süzür (az elanlı rayonlar çıxır)
ORDER BY median_azn DESC;

-- 5) Ulduz sxemi: fakt + ölçü cədvəllərinin JOIN-i (view-suz, əl ilə)
--    Fakt cədvəlində yalnız kodlar (ID) var; adlar ölçü cədvəllərindən JOIN ilə gətirilir.
SELECT d.district_name, b.building_type, f.rooms, f.area_m2, f.price_azn, f.url
FROM fact_listing f
JOIN dim_district d      ON d.district_id = f.district_id
JOIN dim_building_type b ON b.building_type_id = f.building_type_id
WHERE f.snapshot_id = (SELECT snapshot_id FROM v_latest_snapshot)
  AND f.is_outlier = 'N' AND f.is_duplicate = 'N'
FETCH FIRST 10 ROWS ONLY;      -- yalnız ilk 10 sətir (nümunə üçün)

-- 6) Vasitəçi və mülkiyyətçi elanlarının qiyməti (insight: vasitəçi elanı daha bahadır)
SELECT CASE is_agency WHEN 'Y' THEN 'Vasitəçi' ELSE 'Mülkiyyətçi' END AS kim,
       COUNT(*) AS elan,
       ROUND(MEDIAN(price_azn))       AS median_azn,
       ROUND(MEDIAN(price_per_m2), 1) AS median_1m2_azn   -- 1 m² qiyməti: mənzilin ölçüsündən asılı olmayan müqayisə
FROM v_listing_current
GROUP BY is_agency;

-- 7) ƏSAS SUAL: Bakı şəhərində median kirayə orta maaşın neçə faizidir? (alt sorğu, CROSS JOIN)
--    Hər otaq qrupu üçün bir sətir. "2" sətri — layihənin baş rəqəmidir (dashboard və saytdakı ilə eyni).
SELECT k.rooms_group                                    AS otaq,
       k.median_azn,
       m.avg_salary_azn                                 AS baki_orta_maas,
       m.year                                           AS maas_ili,
       ROUND(100 * k.median_azn / m.avg_salary_azn)     AS kiraye_yuku_faiz,     -- norma: 30%-ə qədər
       ROUND(k.median_azn / 0.30)                       AS normaya_sigan_maas    -- kirayə 30% olsun deyə lazım olan maaş
FROM (SELECT rooms_group, MEDIAN(price_azn) AS median_azn      -- alt sorğu 1: Bakı şəhəri üzrə median, otaq sayına görə
      FROM v_listing_current
      WHERE is_baku_city = 'Y'
      GROUP BY rooms_group) k
CROSS JOIN (SELECT year, avg_salary_azn FROM salary_region    -- alt sorğu 2: Bakıda son ilin orta maaşı (1 sətir)
            WHERE region_name = 'Bakı şəhəri - cəmi'
              AND year = (SELECT MAX(year) FROM salary_region)) m
ORDER BY k.rooms_group;

-- 8) Rayonları ucuzdan bahaya sıralamaq (pəncərə funksiyası RANK)
--    PARTITION BY: hər otaq qrupu üçün sıralama ayrıca aparılır.
SELECT district_name, rooms_group, listings, median_azn,
       RANK() OVER (PARTITION BY rooms_group ORDER BY median_azn) AS ucuzluq_yeri
FROM v_district_stats
WHERE listings >= 30 AND rooms_group IN ('1', '2', '3')
ORDER BY rooms_group, ucuzluq_yeri;

-- 9) Təkrar elan nümunəsi: eyni mənzil, eyni qiymət, fərqli elan nömrəsi (R9 qaydası)
--    8 sahənin hamısı eyni olan elanlar bir qrupa düşür; qrupda 1-dən çox elan varsa — təkrardır.
SELECT district_id, location_id, rooms, area_m2, floor, floors, price_azn,
       COUNT(*) AS nece_defe, MIN(listing_id) AS ilk_elan, MAX(listing_id) AS son_elan
FROM fact_listing
WHERE snapshot_id = (SELECT snapshot_id FROM v_latest_snapshot)
GROUP BY district_id, location_id, building_type_id, rooms, area_m2, floor, floors, price_azn
HAVING COUNT(*) > 1
ORDER BY nece_defe DESC
FETCH FIRST 10 ROWS ONLY;

-- 10) Keyfiyyət yoxlaması: boş (NULL) və məntiqsiz dəyərlər olmamalıdır — bütün sütunlar 0 çıxmalıdır
SELECT SUM(CASE WHEN price_azn IS NULL OR price_azn <= 0 THEN 1 ELSE 0 END) AS pis_qiymet,
       SUM(CASE WHEN area_m2   IS NULL OR area_m2   <= 0 THEN 1 ELSE 0 END) AS pis_sahe,
       SUM(CASE WHEN floor > floors THEN 1 ELSE 0 END)                    AS mertebe_xetasi,
       SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END)                AS yersiz
FROM fact_listing;

-- 11) Qiymət zamanla necə dəyişir? (pəncərə funksiyası LAG)
--     Hər toplamada "2 otaqlı, Bakı şəhəri" medianı və əvvəlki toplama ilə fərqi.
--     LAG: əvvəlki sətrin dəyərini gətirir (burada — əvvəlki snapshotun medianı).
SELECT snapshot_id, captured_at, listings, median_azn,
       median_azn - LAG(median_azn) OVER (ORDER BY captured_at) AS evvelki_ile_ferq
FROM v_market_trend
WHERE is_baku_city = 'Y' AND rooms_group = '2'
ORDER BY captured_at;

-- 12) Büdcə sorğusu ("büdcəm hansı rayonlara çatır?") — 03_budget_query.sql faylındadır.
--     SQL Developer dəyər soruşacaq: budget=415, people=1, rooms=2
