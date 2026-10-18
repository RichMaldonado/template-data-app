import os
import sys
import time
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="Data App API Template",
    description="API REST y servidor estatico de alto desempeno para Data Apps",
    version="1.0.0"
)

# Compresion GZip para reducir payloads grandes (~13x)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

from .database import get_db_connection, get_sqlite_connection, DUCKDB_PATH, SQLITE_PATH
from .cache import cached_api_call
from .telemetry import track_event, DEFAULT_APP_ID
from . import queries
from . import crud_metas
from .schemas import MetaGerenciaCreate, MetaGerenciaResponse

@app.on_event("startup")
def on_startup():
    track_event(
        event_type="SESSION_START",
        event_target="Servidor Data App Iniciado",
        payload_json={"status": "online"}
    )

@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    path = request.url.path
    if path.startswith("/api/") and path != "/api/health":
        query_params = dict(request.query_params)
        
        # Categorización semántica de la acción para telemetría
        if request.method in ["POST", "PUT", "DELETE"]:
            event_type = "CRUD_MUTATION"
        elif any(k in query_params for k in ["ciclo", "gv", "sector", "nivel"]):
            event_type = "FILTER_CHANGE"
        else:
            event_type = "DATA_QUERY"
            
        track_event(
            app_id=DEFAULT_APP_ID,
            event_type=event_type,
            event_target=path,
            username=request.headers.get("x-user-id", "usuario_template"),
            role=request.headers.get("x-user-role", "analista"),
            nombre_gerencia=query_params.get("gv"),
            nombre_sector=query_params.get("sector"),
            session_id=request.headers.get("x-session-id", "sess_default"),
            payload_json=query_params,
            response_time_ms=duration_ms,
            status_code=response.status_code
        )
    return response


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "olap_duckdb_connected": os.path.exists(str(DUCKDB_PATH)),
        "oltp_sqlite_connected": os.path.exists(str(SQLITE_PATH))
    }

# ==============================================================================
# RUTAS ANALITICAS (OLAP - DuckDB + Cache por mtime)
# ==============================================================================
@app.get("/api/v1/panel-general/kpis")
@cached_api_call(str(DUCKDB_PATH))
def endpoint_panel_general_kpis(
    ciclo: int = Query(202601, description="Ciclo comercial en formato YYYYCC"),
    gv: Optional[str] = Query(None, description="Codigo o nombre de Gerencia")
):
    try:
        conn = get_db_connection()
        try:
            return queries.get_kpis_panel_general(conn, ciclo=ciclo, gv=gv)
        finally:
            conn.close()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/panel-general/tendencia")
@cached_api_call(str(DUCKDB_PATH))
def endpoint_panel_general_tendencia(
    gv: Optional[str] = Query(None, description="Codigo o nombre de Gerencia")
):
    try:
        conn = get_db_connection()
        try:
            return queries.get_tendencia_ciclos(conn, gv=gv)
        finally:
            conn.close()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# RUTAS CRUD TRANSACCIONALES (OLTP - SQLite Modo WAL)
# ==============================================================================
@app.get("/api/v1/crud/metas", response_model=List[MetaGerenciaResponse])
def endpoint_list_metas(
    ciclo: Optional[int] = Query(None, description="Filtrar por ciclo comercial YYYYCC"),
    gv: Optional[str] = Query(None, description="Filtrar por gerencia")
):
    conn = get_sqlite_connection()
    try:
        return crud_metas.list_metas(conn, ciclo=ciclo, gerencia=gv)
    finally:
        conn.close()

@app.post("/api/v1/crud/metas", response_model=MetaGerenciaResponse)
def endpoint_create_or_update_meta(meta_in: MetaGerenciaCreate):
    conn = get_sqlite_connection()
    try:
        return crud_metas.create_or_update_meta(conn, meta_in)
    finally:
        conn.close()

@app.delete("/api/v1/crud/metas/{meta_id}")
def endpoint_delete_meta(meta_id: int):
    conn = get_sqlite_connection()
    try:
        deleted = crud_metas.delete_meta(conn, meta_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Meta no encontrada")
        return {"status": "success", "id_eliminado": meta_id}
    finally:
        conn.close()

# Servir Frontend compilado en Produccion si existe
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static_assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))

