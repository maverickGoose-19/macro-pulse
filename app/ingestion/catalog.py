from dataclasses import dataclass


@dataclass(frozen=True)
class SeriesDef:
    fred_id: str
    name: str
    units: str
    frequency: str        # "daily" | "monthly"
    category: str         # "rates" | "credit" | "inflation" | "policy"
    typical_lag_days: int
    source_url: str


SERIES_CATALOG: list[SeriesDef] = [
    SeriesDef(
        "T10Y2Y", "10Y-2Y Treasury Spread", "Percent", "daily", "rates", 1,
        "https://fred.stlouisfed.org/series/T10Y2Y",
    ),
    SeriesDef(
        "T10Y3M", "10Y-3M Treasury Spread", "Percent", "daily", "rates", 1,
        "https://fred.stlouisfed.org/series/T10Y3M",
    ),
    SeriesDef(
        "DGS10", "10-Year Treasury Rate", "Percent", "daily", "rates", 1,
        "https://fred.stlouisfed.org/series/DGS10",
    ),
    SeriesDef(
        "DGS2", "2-Year Treasury Rate", "Percent", "daily", "rates", 1,
        "https://fred.stlouisfed.org/series/DGS2",
    ),
    SeriesDef(
        "DGS3MO", "3-Month Treasury Rate", "Percent", "daily", "rates", 1,
        "https://fred.stlouisfed.org/series/DGS3MO",
    ),
    SeriesDef(
        "FEDFUNDS", "Federal Funds Effective Rate", "Percent", "monthly", "policy", 5,
        "https://fred.stlouisfed.org/series/FEDFUNDS",
    ),
    SeriesDef(
        "BAMLH0A0HYM2", "ICE BofA HY Index OAS", "Percent", "daily", "credit", 1,
        "https://fred.stlouisfed.org/series/BAMLH0A0HYM2",
    ),
    SeriesDef(
        "CPIAUCSL", "CPI All Items SA", "Index 1982=100", "monthly", "inflation", 14,
        "https://fred.stlouisfed.org/series/CPIAUCSL",
    ),
    SeriesDef(
        "CPILFESL", "Core CPI ex Food & Energy", "Index 1982=100", "monthly", "inflation", 14,
        "https://fred.stlouisfed.org/series/CPILFESL",
    ),
]

SERIES_BY_ID: dict[str, SeriesDef] = {s.fred_id: s for s in SERIES_CATALOG}
