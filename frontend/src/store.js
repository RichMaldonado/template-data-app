import { fetchGeneralKpis, fetchTendencia, fetchMetas, saveMeta, deleteMeta } from './api.js';
import { getChartInstance, resizeAllCharts } from './components/charts.js';
import { exportWidgetToPng } from './components/exporter.js';

export function createDashboardStore() {
  return {
    appName: 'Monitor Crecimiento & Retención',

    // Filtros comerciales
    filtros: {
      ciclo: 202601,
      gv: '',
      sector: ''
    },
    
    // Control de Sidebar Drawer y opciones
    isSidebarOpen: false,
    ultimaActualizacion: '01/10/2026 06:00',
    ciclosDisponibles: [202601, 202602, 202603, 202604],
    ciclosAbiertos: [202603, 202604],
    gerenciasDisponibles: ['GV_NORTE', 'GV_SUR', 'GV_CENTRO', 'GV_OCCIDENTE'],

    cambiarCiclo(nuevoCiclo) {
      const c = Number(nuevoCiclo);
      if (c && !isNaN(c)) {
        this.filtros.ciclo = c;
        this.cargarDatos();
      }
    },

    limpiarFiltros() {
      this.filtros.ciclo = 202601;
      this.filtros.gv = '';
      this.filtros.sector = '';
      this.cargarDatos();
    },

    cambiarTab(panel) {
      this.panelActivo = panel;
      this.onTabChanged();
    },
    
    // Jerarquia de Navegacion de Paneles
    panelActivo: 'panel_general', // 'panel_general', 'panel_detalle', 'panel_metas_crud'
    
    // Estado del Modal Explicativo de Widgets
    modalExplicacion: {
      abierto: false,
      titulo: '',
      descripcion: '',
      fuente: '',
      formula: '',
      regla_negocio: ''
    },

    // Datos reactivos analiticos (OLAP)
    kpis: {
      total_consultoras: 0,
      venta_total: 0,
      ticket_promedio: 0
    },
    tendenciaData: [],
    cargando: false,

    // Datos reactivos CRUD (OLTP - SQLite)
    metasLista: [],
    formularioMeta: {
      ciclo: 202601,
      gerencia: 'GV_NORTE',
      meta_monto: 1500000.0,
      meta_consultoras: 650,
      observaciones: ''
    },
    guardandoMeta: false,

    // Diccionario de explicaciones de metricas
    diccionarioMetricas: {},

    async init() {
      try {
        const resp = await fetch('/docs/metricas_diccionario.json');
        if (resp.ok) {
          this.diccionarioMetricas = await resp.json();
        }
      } catch (e) {
        console.warn('Diccionario de metricas local no disponible:', e);
      }
      await this.cargarDatos();
      await this.cargarMetas();
    },

    async cargarDatos() {
      this.cargando = true;
      try {
        const [resKpis, resTendencia] = await Promise.all([
          fetchGeneralKpis(this.filtros),
          fetchTendencia(this.filtros)
        ]);
        this.kpis = resKpis;
        this.tendenciaData = resTendencia;
        
        this.$dispatch('data-updated', { tendencia: this.tendenciaData });
      } catch (err) {
        console.error('Error al cargar datos del dashboard:', err);
      } finally {
        this.cargando = false;
      }
    },

    // =========================================================================
    // METODOS CRUD (SQLite WAL)
    // =========================================================================
    async cargarMetas() {
      try {
        const res = await fetchMetas({ ciclo: this.filtros.ciclo, gv: this.filtros.gv });
        this.metasLista = res;
      } catch (err) {
        console.error('Error al consultar metas CRUD:', err);
      }
    },

    async guardarMeta() {
      this.guardandoMeta = true;
      try {
        await saveMeta({
          ciclo: parseInt(this.formularioMeta.ciclo),
          gerencia: this.formularioMeta.gerencia,
          meta_monto: parseFloat(this.formularioMeta.meta_monto),
          meta_consultoras: parseInt(this.formularioMeta.meta_consultoras),
          observaciones: this.formularioMeta.observaciones
        });
        await this.cargarMetas();
        // Limpiar observaciones
        this.formularioMeta.observaciones = '';
      } catch (err) {
        console.error('Error al guardar meta:', err);
        alert('Error al guardar la meta: ' + err.message);
      } finally {
        this.guardandoMeta = false;
      }
    },

    async eliminarMeta(id) {
      if (!confirm('Desea eliminar este registro de meta?')) return;
      try {
        await deleteMeta(id);
        await this.cargarMetas();
      } catch (err) {
        console.error('Error al eliminar meta:', err);
      }
    },

    // Detonador del Modal de Explicacion en el titulo de cada Widget
    abrirModalWidget(metricaKey) {
      const def = this.diccionarioMetricas[metricaKey] || {
        titulo: metricaKey,
        descripcion: 'Definición analítica no documentada aún.',
        fuente_origen: 'No documentada',
        archivo_sql_origen: 'N/A',
        tabla_destino: 'DuckDB: fact_ventas',
        consulta_analitica_sql: 'N/A',
        formula: 'N/A',
        regla_negocio: 'N/A'
      };
      this.modalExplicacion = {
        abierto: true,
        fuente: def.fuente || `${def.fuente_origen || ''} -> ${def.tabla_destino || ''}`,
        ...def
      };
    },

    cerrarModalWidget() {
      this.modalExplicacion.abierto = false;
    },

    // Descarga institucional de Widget en PNG
    descargarWidget(chartId, widgetTitle, widgetSubtitle = '') {
      const chart = getChartInstance(chartId);
      if (!chart) {
        console.warn(`No se encontro instancia de chart para ${chartId}`);
        return;
      }

      const filtersContext = [
        `Ciclo: ${this.filtros.ciclo}`,
        this.filtros.gv ? `GV: ${this.filtros.gv}` : 'GV: Todas'
      ].join('  ·  ');

      exportWidgetToPng(chart, {
        appName: this.appName,
        widgetTitle: widgetTitle,
        widgetSubtitle: widgetSubtitle,
        filtersContext: filtersContext
      });
    },

    onTabChanged() {
      setTimeout(() => resizeAllCharts(), 80);
    }
  };
}
