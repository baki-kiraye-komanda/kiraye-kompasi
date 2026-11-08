-- ============================================================
-- 03_budget_query.sql — Saytın əsas sorğusu: "Büdcəm hansı rayonlara çatır?"
-- Parametrlər (bind):
--   :budget  — bir nəfərin kirayəyə ayıra biləcəyi məbləğ (AZN/ay)
--               = xalis maaş − kirayədən sonra saxlamaq istədiyi məbləğ (saytda hesablanır)
--   :people  — kirayəni neçə nəfər bölür (1 və ya 2)
--   :rooms   — otaq qrupu ('1', '2', '3', '4', '5+')
-- Məntiq: elanın qiyməti nəfər sayına bölünür və büdcə ilə müqayisə olunur.
-- 10-dan az elanı olan rayonlar göstərilmir: az müşahidə ilə median etibarlı deyil.
-- ============================================================
SELECT district_name,
       COUNT(*)                                                       AS listings,
       SUM(CASE WHEN price_azn / :people <= :budget THEN 1 ELSE 0 END) AS fit_count,
       ROUND(100 * SUM(CASE WHEN price_azn / :people <= :budget THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                           AS fit_pct,
       ROUND(MEDIAN(price_azn))                                       AS median_flat_azn,
       ROUND(MEDIAN(price_azn) / :people)                             AS median_per_person_azn,
       ROUND(:budget - MEDIAN(price_azn) / :people)                   AS budget_gap_azn
FROM v_listing_current
WHERE rooms_group = :rooms
GROUP BY district_name
HAVING COUNT(*) >= 10
ORDER BY fit_pct DESC, median_per_person_azn
