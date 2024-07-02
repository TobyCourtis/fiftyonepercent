GRANT ALL PRIVILEGES ON DATABASE fiftyonepercent_database TO databaseuser;

CREATE TABLE CANDLESTICK
(
    candlestickID            SERIAL PRIMARY KEY,
    openTime                 bigint,
    open                     varchar(255),
    high                     varchar(255),
    low                      varchar(255),
    close                    varchar(255),
    volume                   varchar(255),
    closeTime                bigint,
    quoteAssetVolume         varchar(255),
    numberOfTrades           bigint,
    takerBuyBaseAssetVolume  varchar(255),
    takerBuyQuoteAssetVolume varchar(255),
    ignore                   varchar(255),
    candleTimeframe          varchar(255)
);

select *
from CANDLESTICK
LIMIT 10;