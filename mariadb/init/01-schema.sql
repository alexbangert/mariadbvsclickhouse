CREATE TABLE IF NOT EXISTS PROFILEPRICE (
    `PRICEID` bigint(20) NOT NULL AUTO_INCREMENT,
    `PRICE` double NOT NULL,
    `CREATED` datetime NOT NULL,
    `PRICETYPE` int(11) NOT NULL,
    `VAT` double NOT NULL,
    `DEACTIVATED` datetime DEFAULT NULL,
    `EXCHANGERATETOEURO` double NOT NULL,
    `CURRENCY` varchar(255) NOT NULL,
    `PROFILE_PROFILEID` bigint(20) DEFAULT NULL,
    `CREATOR_USERID` bigint(20) DEFAULT NULL,
    `COMPANY_COMPANYID` varchar(12) DEFAULT NULL,
    `PRICEVIEW_PRICEVIEWID` bigint(20) DEFAULT NULL,
    `METAINFOS_ID` bigint(20) DEFAULT NULL,
    `ATTENDANCEPRICE` double DEFAULT NULL,
    `PRICEWITHOUTATTENDANCE` double DEFAULT NULL,
    `ORIGIN_ID` bigint(20) NOT NULL,
    `ORIGIN_TOOL` varchar(255) NOT NULL,
    `ORIGIN_USERID` bigint(20) NOT NULL,
    `ORIGIN_METAINFOS_ID` bigint(20) DEFAULT NULL,
    `MODIFIED` datetime DEFAULT NULL,
    PRIMARY KEY (`PRICEID`),
    UNIQUE KEY `PRICEID` (`PRICEID`),
    UNIQUE KEY `ORIGIN` (`ORIGIN_TOOL`, `ORIGIN_ID`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb3 COLLATE = utf8mb3_general_ci;
