# Directrices de Desarrollo para Data Apps

## 1. Modularizacion Estricta de Consultas SQL (Backend)

* **Prohibicion de SQL Embebido:** Queda estrictamente prohibido colocar bloques extensos de sentencias SQL dentro de `api/main.py`.
* **Directorio Obligatorio `api/queries/`:** Todas las consultas analiticas deben residir en `api/queries/`, organizadas en un archivo `.py` independiente por cada panel analitico de la aplicacion (ej. `panel_general.py`, `panel_detalle.py`, etc.).
* **Filtros y Helpers Comunes:** Funciones transversales de armado dinamico de WHERE o utilidades de query deben alojarse en `api/queries/common.py`.
* **Exposicion Unificada:** `api/queries/__init__.py` debe exponer los modulos y helpers para su consumo en la API.
* **Responsabilidad de `api/main.py`:** Se limita a definicion de rutas FastAPI, validacion de parametros, gestion de cache/telemetria y formateo de respuestas.

## 2. Calidad de Codigo y Rendimiento

* **Prohibicion de Emojis:** Queda estrictamente prohibido el uso de emojis en cualquier contexto del desarrollo.
* **Eficiencia en RAM:** Se debe priorizar el uso de Polars sobre Pandas para transformaciones tabulares.
* **DuckDB (OLAP):** Conexion siempre en modo `read_only=True`, con pragmas `threads=4` y `preserve_insertion_order=false`.
* **SQLite (OLTP/CRUD):** Conexion obligatoria con Modo WAL (`PRAGMA journal_mode=WAL;`) y `timeout=30.0`.
* **Unidades Temporales:** Ciclos comerciales en formato estricto `YYYYCC` (18 ciclos comerciales por ano).

## 3. Estandar Canonico de Layout Frontend (Header y Sidebar)

* **Prohibicion de Sidebar Izquierdo Permanente:** Queda prohibido colocar sidebars fijos a la izquierda que reduzcan el ancho util de pantalla para tablas y graficos.
* **Header Canónico en 3 Filas (Alturas Controladas y Fijas):**
  * **Fila 1 (Principal / Branding / Acciones) - Altura fija `h-14` (56px):**
    * Izquierda: Isotipo/Logo + Titulo de la aplicacion + Subtitulo/perimetro + Indicador de carga analitica (`animate-pulse`).
    * Derecha: Badge de actualizacion ETL (dot verde pulsante + timestamp) + Boton principal "Filtros Comerciales" (`@click="isSidebarOpen = true"`) + Boton "Actualizar".
  * **Fila 2 (Barra de Filtros Activos) - Altura `py-2` (~36-38px):**
    * Izquierda: Etiqueta en mayusculas `FILTROS ACTIVOS:`.
    * Centro: Chips interactivos clickeables (`@click="isSidebarOpen = true"`) con valor actual de Ciclo (`YYYYCC`), GV y filtros secundarios.
    * Derecha: Boton `Editar Filtros` y boton opcional `Restablecer`.
  * **Fila 3 (Navegacion de Paneles / Tabs) - Altura `py-1.5` a `py-2` (~36-38px):**
    * Navegacion horizontal entre paneles o modulos principales (`panelActivo`), con botones tipo pastilla interactivos y cambio reactivo de panel.
* **Estrategia de Filtros Globales (Sidebar Drawer Lateral Derecho):**
  * Debe implementarse exclusivamente como panel deslizante (`aside`) ubicado a la derecha (`fixed right-0 top-0 h-full w-80` a `w-84`, z-50) con animacion de transicion (`translate-x-full` a `translate-x-0`).
  * Fondo oscuro difuminado (`fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-40`) que bloquea el fondo y se cierra con clic exterior.
  * Jerarquia estricta de controles de filtro:
    1. Ciclo Comercial (`YYYYCC`) siempre en primera posicion.
    2. Gerencia de Ventas (GV) en segunda posicion.
    3. Filtros adicionales de segmento/canal.
  * Acciones obligatorias en el drawer: Boton "Aplicar y Cerrar" y boton "Restablecer a Valores Predeterminados".
  * Tarjeta informativa inferior con fecha y hora de sincronizacion del ETL.
