import sqlite3
from typing import List, Optional
from .schemas import MetaGerenciaCreate, MetaGerenciaUpdate

def list_metas(conn: sqlite3.Connection, ciclo: Optional[int] = None, gerencia: Optional[str] = None) -> List[dict]:
    query = "SELECT * FROM metas_gerencias WHERE 1=1"
    params = []
    if ciclo:
        query += " AND ciclo = ?"
        params.append(ciclo)
    if gerencia:
        query += " AND gerencia = ?"
        params.append(gerencia)
    query += " ORDER BY ciclo DESC, gerencia ASC"
    
    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def get_meta_by_id(conn: sqlite3.Connection, meta_id: int) -> Optional[dict]:
    cursor = conn.execute("SELECT * FROM metas_gerencias WHERE id = ?", (meta_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def create_or_update_meta(conn: sqlite3.Connection, meta_in: MetaGerenciaCreate) -> dict:
    cursor = conn.execute("""
    INSERT INTO metas_gerencias (ciclo, gerencia, meta_monto, meta_consultoras, observaciones, usuario_registro, actualizado_en)
    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(ciclo, gerencia) DO UPDATE SET
        meta_monto = excluded.meta_monto,
        meta_consultoras = excluded.meta_consultoras,
        observaciones = excluded.observaciones,
        usuario_registro = excluded.usuario_registro,
        actualizado_en = CURRENT_TIMESTAMP
    RETURNING *;
    """, (
        meta_in.ciclo,
        meta_in.gerencia,
        meta_in.meta_monto,
        meta_in.meta_consultoras,
        meta_in.observaciones,
        meta_in.usuario_registro
    ))
    row = cursor.fetchone()
    conn.commit()
    return dict(row) if row else {}

def delete_meta(conn: sqlite3.Connection, meta_id: int) -> bool:
    cursor = conn.execute("DELETE FROM metas_gerencias WHERE id = ?", (meta_id,))
    conn.commit()
    return cursor.rowcount > 0
