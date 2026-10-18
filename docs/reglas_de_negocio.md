# Reglas de Negocio Estandarizadas para Data Apps

## 1. Jerarquia Temporal Comercial

El nucleo analitico de todas las data apps se estructura bajo la siguiente jerarquia estricta:

* **Ano comercial**
* **Periodo comercial:** Cada ano comercial se divide en exactamente 2 periodos.
* **Ciclo comercial:** Cada periodo comercial se compone de 9 ciclos. Cada ano comercial contiene un total de **18 ciclos comerciales**.
* **Formato Estandar:** Toda referencia a ciclos en bases de datos, APIs y frontend se realiza exclusivamente en formato **`YYYYCC`** (ejemplo: `202601`, `202602`, `202618`).

---

## 2. Convenciones de Datos y Persistencia Flexible (Opcional)

El framework permite seleccionar la estrategia de base de datos segun el objetivo del proyecto:

1. **Modo Solo OLAP (DuckDB):** Para dashboards analiticos de solo lectura.
   * La API debe conectarse siempre con `read_only=True` para garantizar lectura concurrente sin bloqueos.
   * Se deben activar los pragmas `PRAGMA threads=4` y `PRAGMA preserve_insertion_order=false`.
2. **Modo Solo OLTP (SQLite):** Para herramientas puramente operativas o formularios CRUD.
   * Es obligatorio configurar SQLite en **Modo WAL (`PRAGMA journal_mode=WAL;`)** y con un **`timeout=30.0`** segundos en la conexion para evitar errores de bloqueo.
3. **Modo Hibrido (OLAP + OLTP):** Coexistencia de DuckDB para analitica masiva y SQLite para transacciones y parametrizacion de usuarios.
4. **Eficiencia en RAM:** Todo analisis o transformacion tabular pesada debe priorizar Polars sobre Pandas.
5. **Cargas Incrementales:** Los pipelines ETL no deben recrear tablas completas; deben filtrar y actualizar exclusivamente los ciclos comerciales activos (`WHERE ciclo IN (...)`).

---

## 3. Trazabilidad y Consultas SQL por Grafico / Widget

Para garantizar la auditoria, consistencia y mantenimiento de la informacion en toda Data App:

1. **Consulta SQL Asociada Obligatoria:** Todo grafico, tarjeta de KPI o componente de visualizacion debe contar con una consulta SQL explicita y asociada. Esto aplica tanto a:
   * La consulta analitica en backend (`api/queries/`) sobre la base analitica local (DuckDB).
   * La consulta SQL de extraccion en el pipeline ETL (`etl/consultas/*.sql`) que alimenta los datos crudos.
2. **Rastreabilidad Estricta a Fuentes de Informacion:** Cada metrica y grafico debe registrar su linaje completo hasta su origen primario:
   * **Databricks:** Catalogo, esquema, tabla fisica/vista o query delta (ej. `sandbox.planeamiento_mexico.*`, `product.*`, `platform.*`).
   * **SQL Server / Fuentes Relacionales:** Servidor, base de datos, esquema y tabla (via ODBC / pyodbc).
   * **Reportes Locales / Archivos:** Ruta, formato (Excel, CSV, Parquet) y periodicidad de actualizacion.
3. **Registro en Diccionario de Metricas:** Es mandatorio que cada entrada en `docs/metricas_diccionario.json` declare explicitamente:
   * `fuente_origen`: Origen primario (Databricks, SQL Server o Reporte local).
   * `archivo_sql_origen`: Archivo SQL de extraccion asociado.
   * `tabla_destino`: Tabla analitica local (DuckDB / fact table).
   * `formula`: Logica de agregacion SQL.

---

## 4. Modularizacion Obligatoria de Consultas SQL por Panel (api/queries/)

Queda estrictamente prohibido embeber sentencias o bloques extensos de SQL dentro de `api/main.py`. La arquitectura de backend debe seguir una separacion estricta por paneles analiticos:

1. **Directorio Dedicado:** Todas las consultas analiticas del backend deben residir obligatoriamente en `api/queries/`.
2. **Un Archivo por Panel:** Debe crearse un archivo Python separado por cada panel que conforme la Data App (ej. `api/queries/panel_general.py`, `api/queries/panel_detalle.py`, etc.).
3. **Modulos Comunes:** Logicas transversales de filtrado (ej. funciones constructoras de WHERE) deben ubicarse en `api/queries/common.py`.
4. **Exportacion Centralizada:** El archivo `api/queries/__init__.py` debe importar y exponer los modulos de consulta para su consumo unificado en la API.
5. **Rol de `api/main.py`:** El archivo principal debe actuar unica y exclusivamente como controlador HTTP:
   * Definicion de rutas (`@app.get`, `@app.post`).
   * Validacion y tipado de parametros de entrada con Pydantic / FastAPI Query.
   * Aplicacion de decoradores de cache (`@cached_api_call`) y middlewares de telemetria.
   * Invocacion a las funciones del modulo `api/queries/<panel>.py` correspondiente.
   * Formateo y serializacion de la respuesta JSON o streaming CSV.
