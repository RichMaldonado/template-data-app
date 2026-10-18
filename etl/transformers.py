import polars as pl

def transform_ventas(df: pl.DataFrame) -> pl.DataFrame:
    """
    Transformaciones vectoriales con Polars optimizadas en memoria.
    """
    if df.is_empty():
        return df

    return df.with_columns([
        pl.col("monto_facturado").cast(pl.Float64),
        (pl.col("monto_facturado") / pl.col("items")).alias("ticket_promedio_item")
    ])
