# Especificación del Widget y Estándar de Exportación a Imagen (PNG)

Este documento establece la anatomía exacta del **Widget** en el framework y la especificación del componente descargable en formato PNG.

---

## 1. Anatomía Estructural del Widget

Un **Widget** es una tarjeta independiente (**Card**) que encapsula una métrica o temática analítica completa. Su jerarquía interna se estructura de la siguiente forma:

```
+-----------------------------------------------------------------------------------+
|  [TITULO DEL WIDGET]  (i)           [ TAB 1: Diagrama ] [ TAB 2: Matriz ]   [PNG] |
|  Subtítulo / descripción corta                                                    |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [CONTENIDO DEL TAB ACTIVO]                                                       |
|  - Si Tab 1: Gráfico interactivo (ECharts)                                        |
|  - Si Tab 2: Tabla de datos / Matriz analítica                                    |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Componentes Clave del Header del Widget:
1. **Título del Widget:** Nombre oficial de la métrica o análisis analítico.
2. **Subtítulo:** Breve resumen explicativo del objetivo visualizado.
3. **Detonador de Información `(i)`:** Botón circular que abre el modal contextual con la definición, fórmula matemática, regla de negocio, fuente primaria de información (Databricks, SQL Server o reporte local), archivo SQL de extracción y consulta analítica SQL asociada desde `docs/metricas_diccionario.json`.
4. **Selector de Tabs Internos:** Botonera integrada para alternar entre diferentes perspectivas del mismo tema (por ejemplo, *Diagrama* vs *Matriz Histórica* o *Actividad General* vs *Actividad Frecuente*).
5. **Botón de Descarga PNG:** Acciona la captura y composición institucional en alta resolución.

---

## 2. Especificación Técnica de la Exportación a PNG

La función [`exportWidgetToPng`](file:///c:/Users/339302/Documents/Template-Data-App/frontend/src/components/exporter.js) genera un canvas off-screen con renderizado HiDPI (**pixelRatio: 2x**) para uso ejecutivo en presentaciones (PowerPoint, Word, reportes).

### Componentes Integrados en la Imagen Final:
1. **Encabezado Institucional:**
   * **Nombre de la Data App Origen:** En la esquina superior izquierda (ejemplo: `MONITOR CRECIMIENTO & RETENCIÓN`).
   * **Fecha de Generación:** En la esquina superior derecha en formato local (`es-MX`).
2. **Bloque de Título y Subtítulo:**
   * Título destacado del Widget en tipografía corporativa y tamaño proporcional (18pt escalado).
   * Subtítulo explicativo debajo del título.
   * Línea divisoria formal.
3. **Cuerpo Central (Gráfico o Visualización):**
   * El gráfico vectorial exportado directamente desde el motor de ECharts en fondo limpio sin toolbox ruidoso.
4. **Pie Institucional (Footer):**
   * **Contexto de Filtros Activos:** Registra los filtros vigentes al momento de la captura (ejemplo: `Ciclo: 202601 · GV: GV_NORTE`).
   * Borde exterior continuo que enmarca la tarjeta.

---

## 3. Ejemplo de Uso en Alpine.js

Para añadir un nuevo widget con soporte de tabs y descarga:

```html
<div x-data="{ tabWidget: 'tab_grafico' }" class="bg-white dark:bg-slate-850 rounded-2xl border p-5">
  <div class="flex justify-between items-center pb-3 border-b">
    <!-- Titulo + Info Modal -->
    <div class="flex items-center space-x-2">
      <h3 class="font-bold text-sm">Mi Métrica Analítica</h3>
      <button @click="abrirModalWidget('mi_metrica_key')">(i)</button>
    </div>

    <!-- Tabs + Boton Descarga -->
    <div class="flex items-center space-x-2">
      <div class="flex bg-slate-100 p-1 rounded-lg">
        <button @click="tabWidget = 'tab_grafico'; onTabChanged()">Gráfico</button>
        <button @click="tabWidget = 'tab_tabla'; onTabChanged()">Tabla</button>
      </div>
      <button @click="descargarWidget('chart-id', 'Mi Métrica Analítica', 'Subtítulo explicativo')">
        [PNG]
      </button>
    </div>
  </div>

  <!-- Contenido -->
  <div x-show="tabWidget === 'tab_grafico'">
    <div id="chart-id" class="h-80 w-full"></div>
  </div>
  <div x-show="tabWidget === 'tab_tabla'">
    <!-- Tabla de datos -->
  </div>
</div>
```
