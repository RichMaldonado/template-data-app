import os
import sys
import sqlite3
import duckdb
from pathlib import Path
import logging

logger = logging.getLogger("api.database")

BASE_DIR = Path(__file__).resolve().parent.parent
DUCKDB_PATH = BASE_DIR / "etl" / "database" / "analitica.duckdb"
SQLITE_PATH = BASE_DIR / "data" / "transaccional.db"

# Asegurar existencia del directorio data
SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# MOTOR ANALITICO (OLAP): DuckDB
# ==============================================================================
def get_db_connection() -> duckdb.DuckDBPyConnection:
    """
    Obtiene conexion a DuckDB en modo solo lectura.
    Configura pragmas de eficiencia en memoria RAM y concurrencia.
    """
    db_file = str(DUCKDB_PATH)
    if not os.path.exists(db_file):
        logger.error(f"Base de datos analitica no encontrada en {db_file}")
        raise FileNotFoundError(f"Base de datos analitica no encontrada en {db_file}. Ejecute el ETL primero.")

    conn = duckdb.connect(db_file, read_only=True)
    conn.execute("PRAGMA threads=4")
    conn.execute("PRAGMA preserve_insertion_order=false")
    return conn

# ==============================================================================
# MOTOR TRANSACCIONAL / CRUD (OLTP): SQLite con modo WAL y Timeout
# ==============================================================================
def get_sqlite_connection() -> sqlite3.Connection:
    """
    Obtiene conexion transaccional SQLite optimizada para concurrencia:
    - Modo WAL (Write-Ahead Logging) para lecturas y escrituras simultaneas.
    - Timeout de 30 segundos ante bloqueos concurrentes.
    - Claves foraneas activas para integridad referencial.
    """
    conn = sqlite3.connect(str(SQLITE_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
    """
    Inicializa las tablas CRUD base si no existen.
    Ejemplo: gestion de metas operativas y notas por ciclo/gerencia.
    """
    conn = get_sqlite_connection()
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS metas_gerencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciclo INTEGER NOT NULL,
            gerencia TEXT NOT NULL,
            meta_monto REAL NOT NULL,
            meta_consultoras INTEGER NOT NULL,
            observaciones TEXT,
            usuario_registro TEXT DEFAULT 'admin',
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ciclo, gerencia)
        );
        """)
        conn.commit()
    finally:
        conn.close()

# Inicializar tablas CRUD al importar modulo
init_sqlite_db()
