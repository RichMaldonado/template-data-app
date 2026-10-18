# Guía de Estándar de Layout Frontend

Esta guía define la arquitectura visual e interactiva obligatoria para todas las data apps que utilicen el framework.

---

## 1. Principio Fundamental: Maximización del Espacio Visual

* **Sin Sidebars Izquierdos Permanentes:** Queda estrictamente prohibido utilizar sidebars fijos en el costado izquierdo que resten ancho continuo a las matrices y visualizaciones gráficas.
* **Header de 3 Filas y Alturas Delimitadas:** La cabecera se organiza en 3 capas horizontales con responsabilidades separadas.
* **Filtros Globales en Drawer Deslizante Derecho:** Los controles de filtrado se despliegan únicamente bajo demanda del usuario en un drawer lateral derecho.

---

## 2. Anatomía del Header (3 Filas)

El contenedor `<header>` debe ser un bloque flexible no colapsable (`shrink-0`) con fondo sólido (`bg-white dark:bg-slate-850`) y borde inferior de contraste (`border-b border-slate-200 dark:border-slate-800`).

```
+---------------------------------------------------------------------------------------------------------+
| FILA 1: [Logo] Nombre App · Subtítulo   [Loader]     |   [Badge ETL]   [Filtros Comerciales] [Actualizar]|  h-14 (56px)
+---------------------------------------------------------------------------------------------------------+
| FILA 2: FILTROS ACTIVOS:  [Chip Ciclo]  [Chip GV]  [Chip Extra]                      [Editar Filtros]   |  py-2 (~36-38px)
+---------------------------------------------------------------------------------------------------------+
| FILA 3: [Tab: Panel General]  [Tab: Detalle Operativo]  [Tab: Metas CRUD]                               |  py-1.5 (~36-38px)
+---------------------------------------------------------------------------------------------------------+
```

### Fila 1: Branding, Estado y Acciones Rápidas (Altura fija `h-14` / 56px)
* **Lado Izquierdo:**
  * Isotipo institucional o de la app (caja con esquinas redondeadas, fondo corporativo).
  * Título del dashboard (`font-bold text-sm`).
  * Subtítulo o perímetro analítico (`text-[10px] text-slate-400 uppercase tracking-wide`).
  * Indicador de carga pulsante (`x-show="cargando"` con `text-xs text-amber-500 animate-pulse`).
* **Lado Derecho:**
  * **Badge de Sincronización ETL:** Pill compacta con indicador verde pulsante y fecha/hora (`x-text="ultimaActualizacion"`).
  * **Botón de Filtros Comerciales:** Botón destacado con icono SVG de embudo/filtro (`@click="isSidebarOpen = true"`).
  * **Botón de Actualizar:** Botón neutro para refrescar datos (`@click="cargarDatos()"` con spinner animado).

### Fila 2: Barra de Filtros Activos (Altura `py-2` / ~36-38px)
* Separada por borde superior (`border-t border-slate-100 dark:border-slate-800/80`) con fondo tenue (`bg-slate-50/70 dark:bg-slate-900/30`).
* **Lado Izquierdo / Centro:**
  * Etiqueta `FILTROS ACTIVOS:` en mayúsculas (`text-[10px] font-semibold text-slate-400`).
  * Chips interactivos redondeados (`rounded-md text-xs`):
    * **Chip de Ciclo:** Muestra el ciclo `YYYYCC`. Si coincide con el ciclo activo, puede incluir una etiqueta adicional. Al hacer clic (`@click="isSidebarOpen = true"`), abre directamente el drawer.
    * **Chip de Gerencia:** Muestra la GV seleccionada o "Consolidado Nacional".
    * **Chips Adicionales:** Sector, grupo, situación, etc., si están activos.
* **Lado Derecho:**
  * Enlace o botón `Editar Filtros` (`@click="isSidebarOpen = true"`).
  * Botón opcional `Restablecer` (`@click="limpiarFiltros()"`).

### Fila 3: Navegación de Paneles / Tabs (Altura `py-1.5` a `py-2` / ~36-38px)
* Separada por borde superior (`border-t border-slate-100 dark:border-slate-800/80`) en un contenedor `flex items-center space-x-1.5 px-6`.
* Pestañas tipo pastilla interactiva para alternar entre paneles (`panelActivo`):
  * **Pestaña Activa:** Fondo claro (`bg-white dark:bg-slate-800`), tipografía en negrita (`font-bold text-brand-600 dark:text-brand-400`), borde sutil y sombra mínima (`shadow-2xs`).
  * **Pestaña Inactiva:** Tipografía neutra (`text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800`).

---

## 3. Estrategia de Filtros Globales en Sidebar Drawer

* **Contenedor Deslizante (`aside`):**
  * Posición fija a la derecha: `fixed right-0 top-0 h-full w-80 sm:w-84 bg-white dark:bg-slate-850 shadow-2xl z-50`.
  * Transición fluida con Alpine.js: `x-transition:enter` de `translate-x-full` a `translate-x-0`.
* **Backdrop Oscurecido:**
  * Capa semitransparente con desenfoque: `fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40`.
  * Evento `@click="isSidebarOpen = false"` para cerrar el panel al hacer clic en cualquier área externa.
* **Orden Jerárquico de Selectores:**
  1. **Ciclo Comercial (`YYYYCC`):** Selector principal, 18 ciclos comerciales al año.
  2. **Gerencia de Ventas (GV):** Consolidado Nacional o lista de gerencias.
  3. **Filtros de Segmento / Canal / Sector:** Según el dominio del proyecto.
* **Acciones en la Base del Drawer:**
  * Botón primario: **"Aplicar y Cerrar"** (`@click="isSidebarOpen = false; cargarDatos()"`).
  * Botón secundario: **"Restablecer a Valores Predeterminados"** (`@click="limpiarFiltros()"`).
* **Tarjeta de Metadatos:**
  * Tarjeta inferior informativa con el estado del ETL, base de datos DuckDB conectada y perímetro territorial.

---

## 4. Plantilla de Implementación HTML / Alpine.js

```html
<!-- ==================== HEADER EN 3 FILAS ==================== -->
<header class="bg-white dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 shrink-0">

  <!-- Fila 1: Branding y Acciones Globales (h-14) -->
  <div class="flex items-center justify-between px-6 h-14">
    <div class="flex items-center space-x-3">
      <div class="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-black text-xs shadow-xs">
        DA
      </div>
      <div>
        <div class="flex items-center space-x-2">
          <h1 class="font-bold text-sm tracking-tight text-slate-900 dark:text-white" x-text="appName"></h1>
          <span class="text-[10px] text-slate-400 font-medium tracking-wide uppercase">· Nombre Subtítulo</span>
        </div>
      </div>
      <span x-show="cargando" class="text-xs text-amber-500 font-medium animate-pulse ml-2">Consultando analítica...</span>
    </div>

    <div class="flex items-center space-x-3">
      <div x-show="ultimaActualizacion"
           class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 text-xs font-medium border border-emerald-200 dark:border-emerald-800/60 shadow-2xs">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        <span>Actualizado: <b class="font-semibold text-emerald-900 dark:text-emerald-100" x-text="ultimaActualizacion"></b></span>
      </div>

      <button @click="isSidebarOpen = true" 
              class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition flex items-center shadow-xs cursor-pointer">
        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/></svg>
        <span>Filtros Comerciales</span>
      </button>

      <button @click="cargarDatos()" 
              class="text-xs px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold transition flex items-center space-x-1.5 cursor-pointer">
        <svg class="w-3.5 h-3.5" :class="cargando ? 'animate-spin' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        <span>Actualizar</span>
      </button>
    </div>
  </div>

  <!-- Fila 2: Barra de Filtros Activos (py-2) -->
  <div class="flex flex-wrap items-center justify-between px-6 py-2 border-t border-slate-100 dark:border-slate-800 text-xs bg-slate-50/70 dark:bg-slate-900/30 gap-3">
    <div class="flex items-center space-x-2 shrink-0">
      <span class="text-slate-400 font-semibold uppercase tracking-wider text-[10px] mr-1">Filtros Activos:</span>
      
      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/50 font-medium cursor-pointer hover:bg-blue-100 transition"
            @click="isSidebarOpen = true" title="Clic para cambiar ciclo comercial">
        <span class="text-blue-400 font-normal">Ciclo:</span>
        <b x-text="filtros.ciclo || '--'"></b>
      </span>

      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium cursor-pointer hover:bg-slate-200 transition"
            @click="isSidebarOpen = true" title="Clic para cambiar Gerencia de Ventas">
        <span class="text-slate-400 font-normal">GV:</span>
        <b x-text="filtros.gv ? filtros.gv : 'Nacional (Todas)'"></b>
      </span>
    </div>

    <div class="flex items-center space-x-3">
      <button @click="limpiarFiltros()" class="text-[11px] text-slate-500 hover:underline font-semibold cursor-pointer">
        Restablecer
      </button>
      <button @click="isSidebarOpen = true" class="text-[11px] text-blue-600 hover:underline font-semibold cursor-pointer">
        Editar Filtros
      </button>
    </div>
  </div>

  <!-- Fila 3: Navegación de Paneles / Tabs (py-1.5) -->
  <div class="flex items-center space-x-1.5 px-6 py-1.5 border-t border-slate-100 dark:border-slate-800 text-xs bg-white dark:bg-slate-850">
    <nav class="flex items-center space-x-1.5">
      <button @click="panelActivo = 'panel_general'"
              :class="panelActivo === 'panel_general' ? 'bg-slate-100 dark:bg-slate-800 text-blue-600 dark:text-blue-400 font-bold shadow-2xs' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'"
              class="flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-all cursor-pointer">
        <span>Visión General</span>
      </button>
      <button @click="panelActivo = 'panel_detalle'"
              :class="panelActivo === 'panel_detalle' ? 'bg-slate-100 dark:bg-slate-800 text-blue-600 dark:text-blue-400 font-bold shadow-2xs' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'"
              class="flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-all cursor-pointer">
        <span>Detalle Operativo</span>
      </button>
    </nav>
  </div>

</header>

<!-- ==================== SIDEBAR DRAWER LATERAL DERECHO ==================== -->
<div x-show="isSidebarOpen" style="display: none;"
     x-transition:enter="transition ease-out duration-300"
     x-transition:enter-start="opacity-0"
     x-transition:enter-end="opacity-100"
     x-transition:leave="transition ease-in duration-200"
     x-transition:leave-start="opacity-100"
     x-transition:leave-end="opacity-0"
     class="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40" 
     @click="isSidebarOpen = false"></div>

<aside x-show="isSidebarOpen" style="display: none;"
       x-transition:enter="transition ease-out duration-300 transform"
       x-transition:enter-start="translate-x-full"
       x-transition:enter-end="translate-x-0"
       x-transition:leave="transition ease-in duration-200 transform"
       x-transition:leave-start="translate-x-0"
       x-transition:leave-end="translate-x-full"
       class="fixed right-0 top-0 h-full w-84 bg-white dark:bg-slate-850 shadow-2xl z-50 overflow-y-auto flex flex-col justify-between border-l border-slate-200 dark:border-slate-800">
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-xs">DA</div>
        <div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">Filtros Comerciales</h3>
          <span class="text-[10px] text-slate-400 font-medium uppercase">Configuración Global</span>
        </div>
      </div>
      <button @click="isSidebarOpen = false" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </div>

    <!-- Controles Jerárquicos -->
    <div class="space-y-4">
      <div>
        <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Ciclo Comercial (YYYYCC)</label>
        <select x-model.number="filtros.ciclo" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-xs font-medium">
          <template x-for="c in ciclosDisponibles" :key="c">
            <option :value="c" x-text="c"></option>
          </template>
        </select>
      </div>

      <div>
        <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Gerencia de Ventas (GV)</label>
        <select x-model="filtros.gv" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-xs font-medium">
          <option value="">Nacional (Todas las Gerencias)</option>
          <template x-for="g in gerenciasDisponibles" :key="g">
            <option :value="g" x-text="g"></option>
          </template>
        </select>
      </div>
    </div>

    <div class="space-y-2 pt-2">
      <button @click="isSidebarOpen = false; cargarDatos()" 
              class="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center justify-center space-x-1.5 cursor-pointer">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
        <span>Aplicar y Cerrar</span>
      </button>

      <button @click="limpiarFiltros()" 
              class="w-full py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg transition flex items-center justify-center cursor-pointer">
        Restablecer a Valores Predeterminados
      </button>
    </div>
  </div>
</aside>
```
