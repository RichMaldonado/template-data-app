import os
import sys
import json
import duckdb
from pathlib import Path
from extractors import extract_ventas_simuladas
from transformers import transform_ventas

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "etl" / "config.json"

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_pipeline():
    """
    Orquestador incremental de ETL:
    - Solo actualiza los ciclos comerciales activos definidos en config.json
    - Registro directo Zero-Copy Polars -> DuckDB
    """
    config = load_config()
    db_path = BASE_DIR / config["database"]["path"]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    active_cycles = config["commercial"]["active_cycles"]
    print(f"Iniciando pipeline ETL para ciclos activos: {active_cycles}")
    
    conn = duckdb.connect(str(db_path))
    try:
        # Asegurar tabla base
        conn.execute("""
        CREATE TABLE IF NOT EXISTS fact_ventas (
            ciclo BIGINT,
            codigo_consultora VARCHAR,
            gerencia VARCHAR,
            monto_facturado DOUBLE,
            items BIGINT,
            ticket_promedio_item DOUBLE
        )
        """)
        
        for ciclo in active_cycles:
            print(f"Extrayendo ciclo {ciclo}...")
            raw_df = extract_ventas_simuladas(ciclo)
            clean_df = transform_ventas(raw_df)
            
            # Registro en DuckDB sin copiar en disco
            conn.register("temp_clean_df", clean_df)
            
            # Actualizacion incremental (DELETE ciclo activo + INSERT)
            conn.execute(f"DELETE FROM fact_ventas WHERE ciclo = {ciclo}")
            conn.execute("INSERT INTO fact_ventas SELECT * FROM temp_clean_df")
            print(f"Ciclo {ciclo} cargado con exito ({len(clean_df)} filas).")
            
        print("ETL completado exitosamente.")
    finally:
        conn.close()

if __name__ == "__main__":
    run_pipeline()
