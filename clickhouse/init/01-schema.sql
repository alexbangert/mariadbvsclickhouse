CREATE TABLE IF NOT EXISTS PROFILEPRICE (
    PRICEID Int64, -- bigint(20)
    PRICE Float64, -- double
    CREATED DateTime, -- datetime
    PRICETYPE Int32, -- int(11)
    VAT Float64, -- double
    DEACTIVATED Nullable (DateTime), -- datetime DEFAULT NULL
    EXCHANGERATETOEURO Float64, -- double
    CURRENCY String, -- varchar(255)
    PROFILE_PROFILEID Nullable (Int64), -- bigint(20) DEFAULT NULL
    CREATOR_USERID Nullable (Int64), -- bigint(20) DEFAULT NULL
    COMPANY_COMPANYID Nullable (String), -- varchar(12) DEFAULT NULL
    PRICEVIEW_PRICEVIEWID Nullable (Int64), -- bigint(20) DEFAULT NULL
    METAINFOS_ID Nullable (Int64), -- bigint(20) DEFAULT NULL
    ATTENDANCEPRICE Nullable (Float64), -- double DEFAULT NULL
    PRICEWITHOUTATTENDANCE Nullable (Float64), -- double DEFAULT NULL
    ORIGIN_ID Int64, -- bigint(20)
    ORIGIN_TOOL String, -- varchar(255)
    ORIGIN_USERID Int64, -- bigint(20)
    ORIGIN_METAINFOS_ID Nullable (Int64), -- bigint(20) DEFAULT NULL
    MODIFIED Nullable (DateTime) -- datetime DEFAULT NULL
) ENGINE = MergeTree ()
ORDER BY
    (PRICEID) PRIMARY KEY (PRICEID);
