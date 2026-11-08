-- ============================================================
-- 01_schema.sql — Ulduz sxemi (star schema), Oracle
-- Fakt cədvəli: FACT_LISTING (hər sətir = bir snapshotda bir elan)
-- Ölçü cədvəlləri: DIM_DISTRICT, DIM_LOCATION, DIM_BUILDING_TYPE, SNAPSHOT
-- Kontekst cədvəlləri: SALARY_SECTOR (DSK: sahələr üzrə), SALARY_REGION (DSK: şəhər/rayon üzrə)
--
-- Niyə ulduz sxemi: Power BI üçün ən uyğun modeldir — filtrlər ölçü
-- cədvəllərindən fakt cədvəlinə bir istiqamətdə axır, DAX sadə qalır.
-- Niyə SNAPSHOT: hər həftəlik yeniləmə yeni snapshot olur, köhnələr silinmir,
-- beləliklə qiymətlərin zamanla dəyişməsini görmək mümkündür.
-- Vaxtlar Bakı vaxtı ilə (UTC+4) saxlanılır.
-- ============================================================

CREATE TABLE dim_district (
    district_id     NUMBER(6)          PRIMARY KEY,
    district_name   VARCHAR2(50 CHAR)  NOT NULL,
    is_baku_city    CHAR(1)            DEFAULT 'Y' NOT NULL CHECK (is_baku_city IN ('Y', 'N')),
    latitude        NUMBER(9,6),
    longitude       NUMBER(9,6)
);

CREATE TABLE dim_location (
    location_id     NUMBER(6)          PRIMARY KEY,
    location_name   VARCHAR2(100 CHAR) NOT NULL,
    location_type   VARCHAR2(20 CHAR)  NOT NULL
                    CHECK (location_type IN ('Metro', 'Rayon', 'Qəsəbə', 'Nişangah', 'Naməlum')),
    district_id     NUMBER(6)          REFERENCES dim_district (district_id)
);

CREATE TABLE dim_building_type (
    building_type_id NUMBER(2)         PRIMARY KEY,
    building_type    VARCHAR2(30 CHAR) NOT NULL
);

CREATE TABLE snapshot (
    snapshot_id     VARCHAR2(13)       PRIMARY KEY,           -- məs. 20261108_0130
    captured_at     TIMESTAMP          NOT NULL,              -- Bakı vaxtı
    source_url      VARCHAR2(200)      NOT NULL,
    rows_raw        NUMBER(10)         NOT NULL,
    rows_clean      NUMBER(10)         NOT NULL,
    rows_outlier    NUMBER(10)         NOT NULL,
    rows_duplicate  NUMBER(10)         DEFAULT 0 NOT NULL,
    loaded_at       TIMESTAMP          DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE TABLE fact_listing (
    snapshot_id      VARCHAR2(13)      NOT NULL REFERENCES snapshot (snapshot_id),
    listing_id       NUMBER(12)        NOT NULL,
    district_id      NUMBER(6)         NOT NULL REFERENCES dim_district (district_id),
    location_id      NUMBER(6)         REFERENCES dim_location (location_id),
    building_type_id NUMBER(2)         NOT NULL REFERENCES dim_building_type (building_type_id),
    rooms            NUMBER(2)         NOT NULL CHECK (rooms > 0),
    rooms_group      VARCHAR2(3)       NOT NULL CHECK (rooms_group IN ('1', '2', '3', '4', '5+')),
    area_m2          NUMBER(8,2)       NOT NULL CHECK (area_m2 > 0),
    floor            NUMBER(3),
    floors           NUMBER(3),
    price_azn        NUMBER(10,2)      NOT NULL CHECK (price_azn > 0),
    price_per_m2     NUMBER(10,2)      NOT NULL,
    has_repair       CHAR(1)           NOT NULL CHECK (has_repair IN ('Y', 'N')),
    has_bill_of_sale CHAR(1)           NOT NULL CHECK (has_bill_of_sale IN ('Y', 'N')),
    has_mortgage     CHAR(1)           NOT NULL CHECK (has_mortgage IN ('Y', 'N')),
    is_agency        CHAR(1)           NOT NULL CHECK (is_agency IN ('Y', 'N')),
    is_outlier       CHAR(1)           NOT NULL CHECK (is_outlier IN ('Y', 'N')),
    is_duplicate     CHAR(1)           DEFAULT 'N' NOT NULL CHECK (is_duplicate IN ('Y', 'N')),
    updated_at       TIMESTAMP,
    url              VARCHAR2(200)     NOT NULL,
    CONSTRAINT pk_fact_listing PRIMARY KEY (snapshot_id, listing_id)
);

CREATE INDEX ix_fact_snap_dist_rooms ON fact_listing (snapshot_id, district_id, rooms_group);

CREATE TABLE salary_sector (
    year            NUMBER(4)          NOT NULL,
    sector_name     VARCHAR2(200 CHAR) NOT NULL,
    avg_salary_azn  NUMBER(10,2)       NOT NULL CHECK (avg_salary_azn > 0),
    source_url      VARCHAR2(300)      NOT NULL,
    CONSTRAINT pk_salary_sector PRIMARY KEY (year, sector_name)
);

CREATE TABLE salary_region (
    year            NUMBER(4)          NOT NULL,
    region_name     VARCHAR2(200 CHAR) NOT NULL,
    avg_salary_azn  NUMBER(10,2)       NOT NULL CHECK (avg_salary_azn > 0),
    source_url      VARCHAR2(300)      NOT NULL,
    CONSTRAINT pk_salary_region PRIMARY KEY (year, region_name)
);
