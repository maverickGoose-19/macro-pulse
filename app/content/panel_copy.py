"""
All static explanatory copy for dashboard panels and the glossary.
State label functions compute the colored badge text from live data.
"""


def curve_state_label(spread_10y2y: float, spread_10y3m: float) -> tuple[str, str]:
    """Returns (label_text, tailwind_color_classes)."""
    both_inverted = spread_10y2y < 0 and spread_10y3m < 0
    one_inverted = spread_10y2y < 0 or spread_10y3m < 0
    if both_inverted:
        return ("Inverted", "text-red-400 bg-red-950 border border-red-800")
    elif one_inverted:
        return ("Partially inverted", "text-amber-400 bg-amber-950 border border-amber-800")
    elif spread_10y2y < 0.5:
        return ("Flattening", "text-yellow-400 bg-yellow-950 border border-yellow-800")
    else:
        return ("Normal slope", "text-emerald-400 bg-emerald-950 border border-emerald-800")


def credit_state_label(hy_spread_zscore_1y: float) -> tuple[str, str]:
    if hy_spread_zscore_1y > 2.0:
        return ("Significantly stressed", "text-red-400 bg-red-950 border border-red-800")
    elif hy_spread_zscore_1y > 1.0:
        return ("Elevated", "text-amber-400 bg-amber-950 border border-amber-800")
    elif hy_spread_zscore_1y < -1.0:
        return ("Compressed", "text-sky-400 bg-sky-950 border border-sky-800")
    else:
        return ("Near normal", "text-emerald-400 bg-emerald-950 border border-emerald-800")


def inflation_state_label(cpi_yoy: float) -> tuple[str, str]:
    if cpi_yoy > 5.0:
        return ("High", "text-red-400 bg-red-950 border border-red-800")
    elif cpi_yoy > 3.0:
        return ("Elevated", "text-amber-400 bg-amber-950 border border-amber-800")
    elif cpi_yoy < 1.5:
        return ("Below target", "text-sky-400 bg-sky-950 border border-sky-800")
    else:
        return ("Near target", "text-emerald-400 bg-emerald-950 border border-emerald-800")


PANEL_COPY: dict[str, dict] = {
    "curve": {
        "title": "Yield Curve",
        "subtitle": "10-year minus 2-year and 3-month Treasury spreads",
        "what_you_see": (
            "This panel shows the spread between long-term and short-term Treasury yields — "
            "specifically the 10-year minus 2-year (10Y–2Y) and 10-year minus 3-month (10Y–3M). "
            "When long rates exceed short rates the curve has a positive slope; "
            "when short rates exceed long rates the curve is inverted."
        ),
        "why_it_matters": (
            "The yield curve shape reflects how the bond market is pricing growth and inflation "
            "expectations relative to current short-term rates. "
            "It is one of the most watched macro signals because of its track record as an economic "
            "leading indicator — though it is a descriptive signal, not a prediction."
        ),
        "how_to_read": [
            "Positive spread → long rates higher than short rates → typical steepening environment",
            "Zero crossing → curve is flat → short and long rates are roughly equal",
            "Negative spread → curve is inverted → short rates exceed long rates",
            "Red shading on the chart marks periods where both spreads are below zero",
            "The 1M delta shows how many basis points the spread moved in the last ~21 trading days",
            "10Y–3M and 10Y–2Y often diverge — watching both gives a fuller picture of curve shape",
        ],
        "caveats": (
            "Yield curve inversion has historically preceded recessions, but timing and causality are "
            "variable. This panel describes curve shape; it does not forecast outcomes."
        ),
        "source_note": "Source: FRED T10Y2Y, T10Y3M. Updated daily on business days.",
        "fred_url": "https://fred.stlouisfed.org/series/T10Y2Y",
    },
    "credit": {
        "title": "Credit Stress",
        "subtitle": "ICE BofA US High Yield Index option-adjusted spread",
        "what_you_see": (
            "This panel tracks the ICE BofA US High Yield Index Option-Adjusted Spread (OAS) — "
            "the extra yield investors demand to hold high-yield corporate bonds instead of "
            "equivalent-maturity Treasuries."
        ),
        "why_it_matters": (
            "Credit spreads widen when investors perceive more default risk or require higher "
            "compensation for illiquidity. They compress when risk appetite is high. "
            "Watching credit alongside rates reveals whether stress is concentrated in rate markets, "
            "credit markets, or both — a key divergence signal."
        ),
        "how_to_read": [
            "Higher OAS → investors demanding more compensation → tighter conditions for borrowers",
            "Lower OAS → compressed risk premium → easier credit conditions",
            "The 1-year rolling average line shows the recent baseline for context",
            "The z-score badge shows where today's spread sits within its 1-year distribution",
            "Divergence between an inverted curve and calm credit (or vice versa) is worth noting",
        ],
        "caveats": (
            "Spread levels vary significantly across cycles. The z-score is relative to the past year "
            "only — it does not capture whether the past year itself was elevated or compressed."
        ),
        "source_note": "Source: FRED BAMLH0A0HYM2 (ICE BofA). Updated daily.",
        "fred_url": "https://fred.stlouisfed.org/series/BAMLH0A0HYM2",
    },
    "inflation": {
        "title": "Inflation Context",
        "subtitle": "CPI year-over-year change and Fed funds rate",
        "what_you_see": (
            "This panel shows year-over-year percent change in the Consumer Price Index (CPI) — "
            "both headline (all items) and core CPI excluding food and energy. "
            "The Fed funds rate is overlaid to show the policy response in context."
        ),
        "why_it_matters": (
            "The Fed's dual mandate targets price stability (roughly 2% inflation) alongside maximum "
            "employment. CPI trajectory determines how much pressure the Fed is under to raise or hold "
            "rates. Comparing headline and core reveals whether inflation is driven by volatile commodity "
            "prices or embedded in broader consumption."
        ),
        "how_to_read": [
            "CPI YoY bars → annualized inflation rate for that calendar month",
            "Core CPI line → inflation ex-food and energy, considered more persistent",
            "Fed funds step line (right axis) → where the Fed set its benchmark rate",
            "When core stays elevated after headline falls, it may indicate stickier inflation",
            "Monthly data: each bar covers observations released ~2 weeks after month-end",
        ],
        "caveats": (
            "CPI is one of several inflation measures. PCE is the Fed's preferred gauge but is not "
            "shown here. This panel provides context; it does not model future policy moves."
        ),
        "source_note": "Source: FRED CPIAUCSL, CPILFESL (monthly), FEDFUNDS (monthly).",
        "fred_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
    },
    "comparison": {
        "title": "Historical Regime Matches",
        "subtitle": "Dates most similar to today across rates, credit, and inflation simultaneously",
        "what_you_see": (
            "This panel finds historical dates where the combination of curve shape, credit stress, "
            "inflation, and policy rate most closely resembled today's configuration. "
            "Each match includes a similarity score and a per-feature breakdown showing which "
            "dimensions drove the match."
        ),
        "why_it_matters": (
            "Looking at one series at a time can be misleading — the interesting question is whether "
            "the full configuration of signals has appeared before. Regime matching answers: "
            "'When have rates, credit, and inflation lined up like this simultaneously?' "
            "The feature delta table shows exactly which dimensions are similar and which diverge."
        ),
        "how_to_read": [
            "Similarity score → cosine similarity between today's feature vector and the historical date (0–1, higher = more similar)",
            "Feature delta columns → difference between the historical value and today's value",
            "Small delta → that dimension is similar; large delta → that dimension differs",
            "Expand any row to see the full feature-level breakdown",
            "Matches within 12 months of today are excluded to avoid near-date clustering",
            "High similarity means the signal configuration was structurally similar — not that outcomes repeat",
        ],
        "caveats": (
            "Regime matching is descriptive. It identifies structural similarities; it does not predict "
            "what happened next or imply the same outcome will follow."
        ),
        "source_note": "Computed from T10Y2Y, T10Y3M, BAMLH0A0HYM2, CPIAUCSL, FEDFUNDS.",
        "fred_url": "https://fred.stlouisfed.org",
    },
}

GLOSSARY: dict[str, str] = {
    "Yield Curve": "A line plotting Treasury yields across maturities. Shape (steep, flat, inverted) reflects market expectations about growth and inflation.",
    "Spread": "The difference between two yields or rates, expressed in percentage points or basis points (1 bp = 0.01%).",
    "Inversion": "When a shorter-maturity yield exceeds a longer-maturity yield, producing a negative spread.",
    "Option-Adjusted Spread (OAS)": "The spread above a risk-free rate for a bond, adjusted to remove the value of any embedded options.",
    "Z-Score": "How many standard deviations a value sits above or below its rolling mean. Positive = above average; negative = below average.",
    "Basis Point (bp)": "One hundredth of one percentage point. 100 bps = 1%.",
    "CPI": "Consumer Price Index — measures the average change in prices paid by urban consumers for a basket of goods and services.",
    "Core CPI": "CPI excluding food and energy prices, considered less volatile and more reflective of underlying inflation trends.",
    "Fed Funds Rate": "The target interest rate set by the Federal Reserve for overnight lending between banks. A primary policy tool.",
    "Regime": "A period characterized by a consistent configuration of macro signals (e.g., inverted curve + elevated credit stress + high inflation).",
    "Cosine Similarity": "A measure of similarity between two vectors ranging from 0 (completely dissimilar) to 1 (identical direction). Used for regime matching.",
    "OAS": "See Option-Adjusted Spread.",
}
