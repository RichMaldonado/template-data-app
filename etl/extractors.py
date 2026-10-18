import polars as pl
import random

def extract_ventas_simuladas(ciclo: int) -> pl.DataFrame:
    """
    Simulador de extraccion de datos para el template inicial.
    Reemplazar con Databricks SQL Connector o SQL Server (pyodbc).
    Retorna directamente un Polars DataFrame para maximo rendimiento.
    """
    gerencias = ["GV_NORTE", "GV_SUR", "GV_CENTRO", "GV_OCCIDENTE"]
    n_rows = 500
    
    data = {
        "ciclo": [ciclo] * n_rows,
        "codigo_consultora": [f"C_{random.randint(10000, 99999)}" for _ in range(n_rows)],
        "gerencia": [random.choice(gerencias) for _ in range(n_rows)],
        "monto_facturado": [round(random.uniform(500.0, 4500.0), 2) for _ in range(n_rows)],
        "items": [random.randint(1, 15) for _ in range(n_rows)]
    }
    return pl.DataFrame(data)
