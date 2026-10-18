import polars as pl
import duckdb

def get_kpis_panel_general(conn: duckdb.DuckDBPyConnection, ciclo: int, gv: str = None) -> dict:
    """
    Ejemplo de consulta analitica modularizada retornando datos procesados.
    Zero-copy interoperabilidad DuckDB -> Polars.
    """
    where_clauses = [f"ciclo = {ciclo}"]
    if gv:
        where_clauses.append(f"gerencia = '{gv}'")
    where_sql = " AND ".join(where_clauses)

    query = f"""
    SELECT 
        COUNT(DISTINCT codigo_consultora) AS total_consultoras,
        SUM(monto_facturado) AS venta_total,
        AVG(monto_facturado) AS ticket_promedio
    FROM fact_ventas
    WHERE {where_sql}
    """
    try:
        df = conn.execute(query).pl()
        if not df.is_empty():
            return df.to_dicts()[0]
    except Exception as e:
        # Retorno seguro en caso de tabla no inicializada en el template
        return {
            "total_consultoras": 0,
            "venta_total": 0.0,
            "ticket_promedio": 0.0,
            "error": str(e)
        }
    return {"total_consultoras": 0, "venta_total": 0.0, "ticket_promedio": 0.0}

def get_tendencia_ciclos(conn: duckdb.DuckDBPyConnection, gv: str = None) -> list:
    where_sql = f"WHERE gerencia = '{gv}'" if gv else ""
    query = f"""
    SELECT 
        ciclo,
        SUM(monto_facturado) as venta,
        COUNT(DISTINCT codigo_consultora) as activas
    FROM fact_ventas
    {where_sql}
    GROUP BY ciclo
    ORDER BY ciclo ASC
    """
    try:
        df = conn.execute(query).pl()
        return df.to_dicts()
    except Exception:
        return []
