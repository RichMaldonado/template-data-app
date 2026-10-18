import os
import json
import threading
import urllib.request
import sqlite3
from pathlib import Path

# Configuracion del endpoint y base de datos central de telemetria
TELEMETRY_ENDPOINT = os.getenv("TELEMETRY_ENDPOINT", "http://127.0.0.1:2000/api/v1/telemetry/ingest")
TELEMETRY_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../telemetry_dashboard_app/database/telemetry_master.db")
)
DEFAULT_APP_ID = "template_data_app"

def _send_http_async(payload: dict):
    """
    Envio HTTP asincrono en hilo desacoplado.
    Si el servidor central esta inactivo, aplica fallback directo a SQLite.
    """
    def _worker():
        try:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(TELEMETRY_ENDPOINT, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                pass
        except Exception:
            _write_direct_sqlite(payload)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def _write_direct_sqlite(payload: dict):
    """
    Escritura directa de contingencia en la base central SQLite en modo WAL.
    """
    if not os.path.exists(TELEMETRY_DB_PATH):
        return
    try:
        conn = sqlite3.connect(TELEMETRY_DB_PATH, timeout=2.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=2000;")
        
        p_json = json.dumps(payload.get("payload_json"), ensure_ascii=False) if payload.get("payload_json") else None
        cursor.execute(
            """
            INSERT INTO app_telemetry_events (
                app_id, session_id, username, role, nombre_gerencia, nombre_sector,
                event_type, event_target, payload_json, response_time_ms, status_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("app_id", DEFAULT_APP_ID),
                payload.get("session_id", "sess_default"),
                payload.get("username", "usuario_template"),
                payload.get("role", "analista"),
                payload.get("nombre_gerencia"),
                payload.get("nombre_sector"),
                payload.get("event_type", "DATA_QUERY"),
                payload.get("event_target"),
                p_json,
                payload.get("response_time_ms", 0),
                payload.get("status_code", 200)
            )
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def track_event(
    event_type: str = "DATA_QUERY",
    event_target: str = None,
    username: str = "usuario_template",
    role: str = "analista",
    nombre_gerencia: str = None,
    nombre_sector: str = None,
    session_id: str = "sess_default",
    payload_json: dict = None,
    response_time_ms: int = 0,
    status_code: int = 200,
    app_id: str = DEFAULT_APP_ID
):
    """
    Envia un evento de telemetria hacia telemetry_dashboard_app de forma no bloqueante.
    """
    payload = {
        "app_id": app_id,
        "session_id": session_id,
        "username": username,
        "role": role,
        "nombre_gerencia": nombre_gerencia,
        "nombre_sector": nombre_sector,
        "event_type": event_type,
        "event_target": event_target,
        "payload_json": payload_json or {},
        "response_time_ms": response_time_ms,
        "status_code": status_code
    }
    _send_http_async(payload)
