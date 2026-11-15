-- ============================================================
-- 03_budget_query.sql — Layihənin əsas sualı SQL dilində: "Büdcəm hansı rayonlara çatır?"
--
-- Eyni qayda üç yerdə eynidir:
--   * burada (SQL)                — müdafiədə bazadan birbaşa göstərmək üçün
--   * Power BI: 'Büdcəyə uyğun elan' ölçüsü (DAX)
--   * sayt: app/core.py -> compute()  (sayt bazaya qoşulmur, eyni qaydanı CSV üzərində tətbiq edir)
--
-- Parametrlər (SQL Developer işə salanda dəyər soruşur; məs. budget = 415, people = 1, rooms = 2):
--   :budget  — bir nəfərin kirayəyə ayırdığı aylıq məbləğ, AZN (saytda: maaş × kirayəyə ayrılan pay)
--   :people  — kirayəni neçə nəfər bölür
--   :rooms   — otaq qrupu ('1', '2', '3', '4', '5+')
--
-- Məntiq: mənzilin qiyməti nəfər sayına bölünür və bir nəfərin büdcəsi ilə müqayisə olunur.
-- 30-dan az elanı olan rayonlar göstərilmir: az elanla median etibarlı deyil (saytda və Power BI-da da belədir).
-- ============================================================
SELECT district_name,                                                                  -- rayon
       COUNT(*)                                                       AS listings,     -- bu rayonda neçə elan var
       SUM(CASE WHEN price_azn / :people <= :budget THEN 1 ELSE 0 END) AS fit_count,   -- neçəsi büdcəyə sığır
       ROUND(100 * SUM(CASE WHEN price_azn / :people <= :budget THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                           AS fit_pct,      -- sığanların payı, %
       ROUND(MEDIAN(price_azn))                                       AS median_flat_azn,        -- mənzilin tipik qiyməti
       ROUND(MEDIAN(price_azn) / :people)                             AS median_per_person_azn,  -- adambaşına düşən
       ROUND(:budget - MEDIAN(price_azn) / :people)                   AS budget_gap_azn          -- müsbət: çatır, mənfi: çatmır
FROM v_listing_current            -- təmiz, unikal elanlar (son snapshot)
WHERE rooms_group = :rooms        -- yalnız seçilmiş otaq sayı
GROUP BY district_name            -- hər rayon üçün bir sətir
HAVING COUNT(*) >= 30             -- az elanlı rayonlar çıxarılır
ORDER BY fit_pct DESC, median_per_person_azn   -- ən əlçatan rayon yuxarıda
