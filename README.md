# Framework Canónico para Data Apps (Monolito Modular Lean)

Plantilla arquitectónica y estándar de desarrollo para crear aplicaciones analíticas de alto rendimiento, bajo consumo de RAM y despliegue simple en Windows/PM2.

---

## 1. Arquitectura del Proyecto

```
Template-Data-App/
│
├── api/                             # Capa Backend / API REST
│   ├── main.py                      # Endpoints FastAPI analíticos y CRUD, compresión GZip
│   ├── database.py                  # Conectores Duales: DuckDB (OLAP) + SQLite WAL con timeout (CRUD)
│   ├── schemas.py                   # Esquemas Pydantic V2 para validación transaccional
│   ├── crud_metas.py                # Operaciones CRUD para SQLite
│   ├── cache.py                     # TTLCache en memoria RAM con invalidación por mtime
│   ├── telemetry.py                 # Registro unificado de telemetría y latencias
│   ├── queries/                     # Consultas analíticas modularizadas por panel
│   │   ├── __init__.py
│   │   └── panel_general.py         # Extracción analítica con Polars Zero-Copy
│   ├── requirements.txt             # Dependencias del backend
│   └── pm2_api.json                 # Configuración de daemon PM2 para la API
│
├── data/                            # Almacén de Base de Datos Transaccional (OLTP)
│   └── transaccional.db             # Base SQLite con modo WAL y timeout de 30s
│
├── frontend/                        # Capa Cliente SPA (Vite + Alpine.js + Tailwind + ECharts)
│   ├── package.json                 # Dependencias frontend optimizadas
│   ├── vite.config.js               # Bundler con code splitting (chunks de echarts y alpine)
│   ├── tailwind.config.js           # Paleta corporativa con soporte dark mode
│   ├── postcss.config.js            # Pipeline PostCSS
│   ├── index.html                   # Layout canónico: Sidebar > Paneles > Widgets (Cards) > Tabs + Modal
│   └── src/
│       ├── main.js                  # Entrypoint e inicialización de Alpine
│       ├── api.js                   # Cliente HTTP con descarte de nulos y soporte GET/POST/DELETE
│       ├── store.js                 # Store global reactivo de filtros, modales y CRUD
│       ├── components/
│       │   ├── charts.js            # Wrappers de visualización con Apache ECharts
│       │   └── exporter.js          # Exportador institucional de widgets a PNG (HiDPI 2x)
│       └── styles/
│           └── main.css             # Directivas de Tailwind y estilos base
│
├── etl/                             # Pipeline de Ingesta y Transformación de Datos (OLAP)
│   ├── run_etl.py                   # Orquestador con carga incremental por ciclo activo
│   ├── extractors.py                # Extractores modulares (Databricks, SQL Server o Mock)
│   ├── transformers.py              # Transformaciones vectoriales con Polars
│   ├── config.json                  # Parámetros y ciclos comerciales activos
│   ├── pm2_etl.json                 # Tarea periódica de actualización con cron PM2
│   └── database/
│       └── analitica.duckdb         # Base de datos analítica columnar embebida (DuckDB)
│
├── docs/                            # Documentación y Diccionarios
│   ├── metricas_diccionario.json    # Catálogo de métricas que alimenta el modal de los widgets
│   ├── especificacion_widgets_png.md# Especificación del Card, Tabs y exportador PNG
│   └── reglas_de_negocio.md         # Jerarquía temporal de 18 ciclos (YYYYCC)
│
├── compilar_frontend.bat            # Compila la SPA hacia frontend/dist
├── ejecutar_etl.bat                 # Ejecuta el pipeline ETL de forma manual
├── reiniciar_aplicacion.bat         # Recompila frontend y reinicia/inicia la app (PM2 o ventana local)
├── reiniciar_app.bat                # Alias para reiniciar_aplicacion.bat
└── ecosystem.config.json            # Manifiesto PM2 unificado
```

---

## 2. Stack Tecnológico Estandarizado y Modos de Persistencia (Opcionales)

El framework es modular y desacoplado, permitiendo configurar el motor de persistencia según las necesidades del proyecto:

| Modo de Arquitectura | Motor Utilizado | Caso de Uso Principal |
| :--- | :--- | :--- |
| **1. Solo OLAP (Analítica Pura)** | **DuckDB** (`analitica.duckdb`) | Dashboards de solo lectura, monitoreo de métricas, agregaciones masivas sobre millones de filas con alta velocidad y bajo consumo de RAM. |
| **2. Solo OLTP (Transaccional / CRUD)** | **SQLite** (`data/transaccional.db` con Modo WAL) | Aplicaciones de formularios, captura de datos, parametrización, inventarios pequeños o paneles operativos con altas, bajas y modificaciones frecuentes. |
| **3. Híbrido (OLAP + OLTP)** | **DuckDB + SQLite WAL** | Aplicaciones analíticas completas que combinan lectura masiva de KPIs con captura transaccional de metas, notas operativas o auditoría. |

### Reglas de Configuración por Motor:
* **DuckDB (OLAP):** Se conecta siempre en modo `read_only=True` desde la API con pragmas `threads=4` y `preserve_insertion_order=false`. Se actualiza exclusivamente mediante pipelines ETL con Polars.
* **SQLite (OLTP):** Si se utiliza para operaciones CRUD, es obligatorio configurarlo en **Modo WAL (`PRAGMA journal_mode=WAL;`)**, `synchronous=NORMAL`, `foreign_keys=ON` y con parámetro de **`timeout=30.0`** para garantizar concurrencia sin bloqueos de archivo.
* **Backend:** Python + FastAPI + Uvicorn + Pydantic V2.
* **Frontend:** Vite + Alpine.js + Tailwind CSS + Apache ECharts.
* **Gestión de Procesos:** PM2 (`pm2-windows-startup`).

---

## 3. Jerarquía y Layout de Interfaz (Estándar Canónico)

El layout está optimizado para maximizar el área útil del canvas, eliminando sidebars izquierdos permanentes y consolidando el control en una cabecera modular y un panel deslizante:

1. **Header Modular en 3 Filas:**
   * **Fila 1 (`h-14` / 56px):** Branding institucional, título de la aplicación, badge de última actualización ETL, botón para abrir el drawer de filtros (`Filtros Comerciales`) y botón de refresco (`Actualizar`).
   * **Fila 2 (`py-2` / ~36-38px):** Barra contextual de **Filtros Activos** con chips interactivos clickeables (Ciclo `YYYYCC`, GV) y acceso directo a edición/restablecimiento.
   * **Fila 3 (`py-1.5` / ~36-38px):** Navegación horizontal de **Paneles / Tabs** (`panelActivo`) para alternar fluidamente entre módulos analíticos sin recargar la página.
2. **Sidebar Drawer Lateral Derecho (Filtros Globales):**
   * Panel deslizante flotante (`w-80` a `w-84`, z-index 50) con backdrop difuminado.
   * Selector principal de **Ciclo Comercial (`YYYYCC`)** en primera posición (18 ciclos comerciales al año).
   * Filtros jerárquicos (Gerencia de Ventas, Sector, Canales).
   * Botones de confirmación: "Aplicar y Cerrar" y "Restablecer a Valores Predeterminados".
   * Tarjeta inferior con estatus y metadatos del ETL.
   * *(Ver especificación completa en [docs/guia_layout_frontend.md](file:///C:/Users/339302/Documents/Template-Data-App/docs/guia_layout_frontend.md))*.
3. **Paneles (`panelActivo`):**
   * Vistas de alto nivel (ej. *Visión General*, *Detalle Operativo*).
4. **Widgets (Cards Autónomas):**
   * Cada métrica o análisis se aloja en un card independiente.
   * **Header del Widget:**
     * Título destacado y subtítulo.
     * **Detonador de Información `(i)`:** Abre el modal contextual con la definición, fórmula matemática, regla de negocio y origen de datos desde `docs/metricas_diccionario.json`.
     * **Tabs Internos del Widget (`tabWidget`):** Permiten alternar entre diferentes perspectivas del mismo tema dentro de la tarjeta (ej. *Diagrama / Gráfico* vs *Matriz Histórica / Tabla*).
     * **Botón de Descarga PNG:** Genera y descarga una imagen institucional en alta resolución (HiDPI 2x) que incluye:
       - Nombre de la Data App origen y fecha de captura.
       - Título y subtítulo del widget.
       - Contenido del gráfico.
       - Resumen de los filtros activos al momento de la descarga.
4. **Modal Centralizado:**
   * Un único componente en el DOM que se llena dinámicamente según la métrica seleccionada.

---

## 4. Guía Rápida de Uso

### Paso 1: Inicializar la Base de Datos con el ETL
Ejecutar el script por lotes o el orquestador Python:
```cmd
ejecutar_etl.bat
```
Esto creará el archivo `etl/database/analitica.duckdb` e insertará los registros iniciales para los ciclos configurados en `etl/config.json`.

### Paso 2: Instalar Dependencias del Backend
```cmd
cd api
pip install -r requirements.txt
cd ..
```

### Paso 3: Compilar o Desarrollar el Frontend
* **Modo Desarrollo con HMR:**
  ```cmd
  cd frontend
  npm install
  npm run dev
  ```
* **Modo Producción:**
  ```cmd
  compilar_frontend.bat
  ```
  Esto generará la carpeta `frontend/dist/`, la cual es servida directamente por FastAPI en el puerto `8000`.

### Paso 4: Levantar y Persistir con PM2
Para desplegar la aplicación como servicio persistente en Windows:
```cmd
pm2 start ecosystem.config.json
pm2 save
```
La aplicación estará disponible en `http://localhost:8000`.

---

## 5. Estrategias de Optimización Clave

1. **Memoria RAM:**
   * Transformaciones en Polars con tipado estricto.
   * `PRAGMA preserve_insertion_order=false` en DuckDB.
   * `TTLCache` con tope máximo de entradas (200) para no sobrecargar el heap de Python.
2. **Caché con Invalidación Reactiva:**
   * La caché del backend evalúa el `mtime` de `analitica.duckdb`. Si el ETL corre y modifica el archivo, la caché en memoria se invalida de forma automática e inmediata.
4. **Telemetría y Adopción Centralizada (`telemetry_dashboard_app`):**
   * Integración nativa no bloqueante mediante hilo daemon (`threading.Thread`).
   * Envío HTTP a `http://127.0.0.1:2000/api/v1/telemetry/ingest` con fallback automático a SQLite WAL (`telemetry_master.db`).
   * Cero impacto en tiempo de respuesta del usuario final ante caídas del servidor central.
   * Auto-descubrimiento en el panel central con solo definir `DEFAULT_APP_ID`.
5. **Trazabilidad Estricta y SQL por Gráfico:**
   * Todo gráfico debe contar con una consulta SQL asociada (consulta analítica en `api/queries/` y extracción en `etl/consultas/`).
   * Linaje rastreable hasta su fuente de información original (Databricks, SQL Server o reportes locales), documentado en `docs/metricas_diccionario.json` y consultable interactivamente en el modal de cada widget.

6. **Modularizacion de Consultas SQL por Panel (api/queries/):**
   * Prohibicion estricta de SQL embebido en api/main.py.
   * Las consultas analiticas deben residir de forma obligatoria y aislada en archivos independientes dentro de api/queries/, estructurados segun los paneles que compongan la aplicacion (ej. panel_general.py, panel_detalle.py).
   * api/main.py se restringe a definir endpoints, validar esquemas, gestionar cache/telemetria y serializar respuestas, delegando las consultas a su respectivo modulo en api/queries/.
