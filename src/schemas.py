import pandera.polars as pa
import polars as pl

# Định nghĩa Schema cho Polars DataFrame
finance_strict_schema = pa.DataFrameSchema({
    "Date": pa.Column(pl.Date, nullable=False),

    "Year": pa.Column(pl.Int64, nullable=False),

    "Symbol": pa.Column(pl.String, nullable=False),

    "Asset_Type": pa.Column(pl.String),

    "Open": pa.Column(
        pl.Float64,
        checks=pa.Check.gt(0)
    ),

    "High": pa.Column(
        pl.Float64,
        checks=pa.Check.gt(0)
    ),

    "Low": pa.Column(
        pl.Float64,
        checks=pa.Check.gt(0)
    ),

    "Close": pa.Column(
        pl.Float64,
        checks=pa.Check.gt(0)
    ),

    "Adj Close": pa.Column(
        pl.Float64,
        checks=pa.Check.gt(0)
    ),

    "Volume": pa.Column(
        pl.Int64,
        checks=pa.Check.ge(0)
    )
})