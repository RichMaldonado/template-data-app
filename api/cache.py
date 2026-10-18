import os
import functools
import logging
from cachetools import TTLCache

logger = logging.getLogger("api.cache")

# Limite estricto de 200 entradas en RAM con TTL de 300 segundos (5 minutos)
_api_cache = TTLCache(maxsize=200, ttl=300)
_cached_db_mtime = 0.0

def get_db_mtime(db_path: str) -> float:
    try:
        return os.path.getmtime(db_path) if os.path.exists(db_path) else 0.0
    except OSError:
        return 0.0

def check_db_invalidation(db_path: str):
    """
    Invalida la cache automaticamente si el archivo DuckDB ha sido modificado por el ETL.
    """
    global _cached_db_mtime, _api_cache
    current_mtime = get_db_mtime(db_path)
    if current_mtime != _cached_db_mtime:
        if _cached_db_mtime != 0.0:
            logger.info("Base de datos modificada. Invalidando cache analitico en memoria RAM.")
        _cached_db_mtime = current_mtime
        _api_cache.clear()

def cached_api_call(db_path: str):
    """
    Decorador para endpoints analiticos de FastAPI.
    Serializa los parametros de consulta y almacena en RAM con clave determinista.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_db_invalidation(db_path)
            params_str = "&".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
            cache_key = f"{func.__name__}:{params_str}"
            
            if cache_key in _api_cache:
                return _api_cache[cache_key]
                
            result = func(*args, **kwargs)
            _api_cache[cache_key] = result
            return result
        return wrapper
    return decorator
