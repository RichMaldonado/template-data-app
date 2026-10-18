# Guía de Replicación: Widget de Curvas y Matriz de Avance Día 0 Multimétrica

Esta guía técnica detalla la arquitectura, el modelado de datos y la implementación en frontend/backend para replicar el widget analítico **Curvas y Matriz de Avance** sobre cualquier métrica comercial (Inicios, Reinicios, Facturación, Pedidos Totales, Recuperos) en data apps y cuadros de mando.

---

## 1. Fundamento Conceptual y Problema Operativo

### 1.1 El Efecto Cascada del Calendario Comercial
En el modelo comercial de venta directa (México, mercado 484), cada Gerencia de Ventas (GV) abre y cierra su ciclo comercial (`YYYYCC`) en fechas de calendario distintas. Las gerencias se agrupan en 4 bloques de escalonamiento:

* **Bloque 1:** Cierre operativo en Día 20 país.
* **Bloque 2:** Cierre operativo en Día 25 a 27 país.
* **Bloque 3:** Cierre operativo en Día 32 a 34 país.
* **Bloque 4:** Cierre operativo en Día 40 a 41 país.

Existe una brecha de hasta **20 días naturales** entre el cierre del Bloque 1 y el Bloque 4. Comparar el desempeño acumulado sobre el calendario civil (`YYYY-MM-DD`) introduce sesgos:
1. Una gerencia del Bloque 4 parece rezagada en volumen simplemente porque su fecha de apertura fue posterior.
2. Una gerencia del Bloque 1 presenta un aplanamiento artificial prematuro mientras el resto del país continúa facturando.

### 1.2 La Solución: Normalización Temporal a Día 0
La estrategia **Día 0** reindexa el eje de avance temporal tomando la fecha de corte oficial de cada GV (`cycle_date_end`) como origen relativo ($D_0$):

$$\text{dia\_gerencia\_ventas} = \text{fecha\_evento} - \text{cycle\_date\_end}_{\text{GV}}$$

* **Ciclo Regular ($-21 \le D \le 0$):** Periodo operativo estándar de captación y facturación (duración local de 20 a 21 días).
* **Capta Oficial ($+1 \le D \le +7$):** Ventana comercial complementaria autorizada para procesar pedidos rezagados y derrame operativo asignados a dicho ciclo.
* **Ajustes Post-Capta ($D > +7$):** Regularizaciones administrativas, liberación de pedidos retenidos por crédito y cobranza previa al cierre definitivo.

---

## 2. Integración con la Detección de Ciclos Activos

Para que el widget opere con rigor en ciclos cerrados (históricos) y en ciclos abiertos (en curso), debe incorporar las cuatro reglas de sincronización temporal documentadas en la arquitectura de Databricks:

```
[========================== CICLO PAÍS (Día 1 a 41) ==========================]
  [Block 1: GV 01-02 (20d)]
      [Block 2: GV 03-06 (20-21d)]
            [Block 3: GV 07-10 (20-21d)]
                  [Block 4: GV 11-13 (20-21d)]
                                            [Ventana de Gracia País (+7d)]
```

### Regla 1: Anclaje de la Fecha de Referencia (`fecha_ref`)
No utilizar exclusivamente la fecha del sistema (`CURRENT_DATE`) para evitar marcar días futuros con valor cero debido a rezagos o desfases en los pipelines nocturnos de ETL:

$$\text{fecha\_ref} = \min(\text{CURRENT\_DATE}, \max(\text{fecha\_transaccional\_cargada}))$$

### Regla 2: Determinación de Ciclos Abiertos País (Macro)
Un ciclo comercial nacional está abierto si la fecha de referencia se ubica entre la apertura de la primera gerencia y el corte de la última más la ventana de gracia de ajustes:

$$\text{Ciclo Abierto País} \iff \text{fecha\_ref} \ge \min(\text{cycle\_date\_start}) \quad \text{AND} \quad \text{fecha\_ref} \le \max(\text{cycle\_date\_end}) + 7\text{ días}$$

### Regla 3: Determinación de Estado Asíncrono por GV (Micro)
En un ciclo activo nacional, las GVs no cierran al mismo tiempo:

$$\text{GV Cerrada Localmente} \iff \text{fecha\_ref} > \text{cycle\_date\_end}_{\text{GV}} + 7\text{ días}$$

* **Efecto de diseño:** La matriz debe marcar con estilo atenuado las filas de gerencias que ya completaron su ventana de gracia, permitiendo identificar cuáles siguen aportando volumen transaccional activo.

### Regla 4: Coexistencia Multiciclo (Traslape Nacional)
Debido a que cada 21 días arranca un ciclo nuevo mientras el previo dura 41 días país, en cualquier fecha del año coexisten **dos ciclos activos en paralelo**. El selector de ciclos debe identificar y destacar ambos ciclos abiertos.

---

## 3. Catálogo de Métricas Aplicables

El patrón de visualización se adapta a diferentes variables operativas definiendo su numerador (evento transaccional deduplicado) y su denominador (base de normalización):

| Métrica | Numerador (Evento Transaccional) | Denominador (Universo / Base) | Interpretación de la Tasa |
| :--- | :--- | :--- | :--- |
| **Recuperos** | Primer pedido facturado de consultoras con estatus $INA_{3+}$ (`rn = 1`). | Padrón de $INA_{4\text{--}6}$ del ciclo previo + recuperadas efectivas. | Tasa de reactivación sobre el universo inactivo recuperable. |
| **Inicios** | Primer pedido facturado de consultoras nuevas (`begin_ind = 1`). | Meta comercial de Inicios de la GV o Base de prospectos captados. | Cumplimiento porcentual de captación de nuevo talento. |
| **Reinicios** | Primer pedido facturado de consultoras en inactividad temprana (`restart_ind = 1`). | Base de consultoras $INA_{1\text{--}3}$ registradas al cierre del ciclo previo. | Tasa de rescate temprano antes de caer en abandono estructural. |
| **Facturación** | Monto acumulado de venta neta facturada (\$ MXN). | Meta financiera comercial presupuestada para la GV en el ciclo. | Porcentaje de avance y cumplimiento de cuota de venta. |
| **Pedidos Totales** | Conteo acumulado de órdenes facturadas (`ID_EXPEDICAO_PEDIDO`). | Padrón total de consultoras activas disponibles en la gerencia. | Nivel de actividad y frecuencia de compra de la red. |

---

## 4. Arquitectura del Widget y Controles de Barra

El widget se estructura en una cabecera con cuatro dimensiones de control independientes:

```
+----------------------------------------------------------------------------------------------------+
| Titulo del Widget: Curvas y Matriz de Avance ([Métrica])                                           |
+----------------------------------------------------------------------------------------------------+
| Alineación: [ Día 0 (Cierre) | Calendario | Día Global ]   Gerencias: [ Multiselect (Top 5 / Nac) ]|
| Vista:      [ Curvas Acumuladas | Matriz Detallada ]        Métrica:   [ Tasa % | Volumen | % Cierre ] |
+----------------------------------------------------------------------------------------------------+
| [ Subvista 1: Gráfico ECharts Multilínea ]   o   [ Subvista 2: Tabla Matriz con Mapa de Calor ]    |
+----------------------------------------------------------------------------------------------------+
```

### 4.1 Modos de Alineación Temporal
* **Día 0 (Cierre):** Eje X centrado en $D_0$. Las columnas van desde $-21$ hasta $0$, seguidas por `Capta` ($D+1$ a $D+7$) y `Ajustes` ($> D+7$). Permite comparar la velocidad de cierre entre gerencias.
* **Calendario:** Eje X expresado en fechas naturales (`YYYY-MM-DD`). Muestra los días calendario reales de mayor actividad.
* **Día Global:** Eje X continuo del ciclo nacional (días 1 a 41). Muestra el aporte de cada GV a la curva macro del país.

### 4.2 Métricas del Eje Y / Valores de Celda
1. **Tasa % sobre Universo:** Normaliza el volumen dividiendo entre el universo o meta de la GV. Permite comparar gerencias grandes y pequeñas.
2. **Volumen Absoluto:** Conteos enteros o montos acumulados sin normalizar.
3. **% sobre Cierre Propio:** Mide el avance porcentual respecto al total final alcanzado por la propia GV ($100 \times \frac{\text{Acumulado}_d}{\text{Total Cierre}}$). Todas las curvas concluyen en 100%, exponiendo perfiles comerciales tempranos vs tardíos.

---

## 5. Pipeline de Datos y Modelado SQL en Databricks / DuckDB

### 5.1 Generación de la Matriz Densa en Databricks (Capa Gold)
Para evitar discontinuidades en las curvas, se realiza un `CROSS JOIN` entre las gerencias y la secuencia completa de días relativos ($-21$ a $+7$):

```sql
WITH tbl_calendario AS (
    SELECT
        operational_cycle AS ciclo,
        CAST(structure_code2 AS INT) AS cd_gv,
        structure_name_level2 AS nombre_gv,
        MIN(cycle_date_start) AS inicio_ciclo,
        MAX(cycle_date_end) AS cierre_ciclo,
        MIN(MIN(cycle_date_start)) OVER (PARTITION BY operational_cycle) AS inicio_pais,
        DATE_ADD(MAX(cycle_date_end), 7) AS limite_capta
    FROM product.elo_modelo_combinado.cmm_structure_operational_cycle
    WHERE country = 484
      AND structure_level2_name = 'GV'
      AND operational_cycle = :ciclo
    GROUP BY operational_cycle, structure_code2, structure_name_level2
),
transacciones_metrica AS (
    SELECT
        p.order_cycle AS ciclo,
        p.sales_management_code AS cd_gv,
        CAST(p.DT_CAPTACAO - INTERVAL 6 HOUR AS DATE) AS fecha_pedido,
        -- Numerador de la métrica (ejemplo: Inicios o Venta)
        COUNT(DISTINCT CASE WHEN p.begin_ind = 1 THEN p.person_code END) AS valor_evento
    FROM platform.dw_o01dw_sisdmi_replica.t_prj_2go_f_pedido p
    WHERE p.country_code = 484
      AND p.order_cycle = :ciclo
      AND p.status_id NOT IN (10, 11) -- Excluir cancelados / anulados
    GROUP BY p.order_cycle, p.sales_management_code, CAST(p.DT_CAPTACAO - INTERVAL 6 HOUR AS DATE)
),
secuencia_dias AS (
    SELECT explode(sequence(-21, 7)) AS dia_gerencia_ventas
),
matriz_base AS (
    SELECT
        c.ciclo,
        c.cd_gv,
        c.nombre_gv,
        c.inicio_ciclo,
        c.cierre_ciclo,
        c.inicio_pais,
        s.dia_gerencia_ventas,
        DATE_ADD(c.cierre_ciclo, s.dia_gerencia_ventas) AS fecha_calendario,
        DATEDIFF(DATE_ADD(c.cierre_ciclo, s.dia_gerencia_ventas), c.inicio_pais) + 1 AS dia_global
    FROM tbl_calendario c
    CROSS JOIN secuencia_dias s
)
SELECT
    m.ciclo,
    m.cd_gv,
    m.nombre_gv,
    m.dia_gerencia_ventas,
    m.dia_global,
    m.fecha_calendario,
    COALESCE(t.valor_evento, 0) AS valor_diario,
    u.universo_base
FROM matriz_base m
LEFT JOIN transacciones_metrica t
    ON m.ciclo = t.ciclo
   AND m.cd_gv = t.cd_gv
   AND m.fecha_calendario = t.fecha_pedido
LEFT JOIN universo_base_gv u
    ON m.ciclo = u.ciclo
   AND m.cd_gv = u.cd_gv
ORDER BY m.cd_gv, m.dia_gerencia_ventas;
```

### 5.2 Estructura de la Tabla Analítica en DuckDB / SQLite Local
Almacenar los datos precalculados en la base local de la aplicación garantizando modo WAL:

```sql
CREATE TABLE IF NOT EXISTS avance_diario_metrica (
    ciclo BIGINT,
    cd_gv BIGINT,
    nombre_gv VARCHAR,
    dia_gerencia_ventas BIGINT,
    dia_global BIGINT,
    fecha_calendario DATE,
    valor_diario BIGINT,
    universo_base BIGINT,
    PRIMARY KEY (ciclo, cd_gv, dia_gerencia_ventas)
);
```

---

## 6. Servicio Backend (FastAPI / Polars)

El backend debe procesar los conteos diarios, segmentar las fases operativas y retornar un payload JSON uniforme para el frontend:

```python
import polars as pl
from typing import Optional
from fastapi import APIRouter

router = APIRouter()

def procesar_matriz_avance(conn, ciclo: int, metrica: str) -> dict:
    query = f"""
        SELECT 
            cd_gv, nombre_gv, dia_gerencia_ventas, dia_global,
            CAST(fecha_calendario AS VARCHAR) AS fecha_calendario,
            valor_diario, universo_base
        FROM avance_diario_metrica
        WHERE ciclo = {ciclo}
        ORDER BY cd_gv, dia_gerencia_ventas
    """
    # Carga eficiente en Polars
    df = pl.read_database(query, conn)
    if df.is_empty():
        return {"gv_rows": [], "nacional": None}

    # Segmentación en fases operativas
    # dia_gv <= 0: ciclo regular | 1 <= dia_gv <= 7: 'capta' | dia_gv > 7: 'ajustes'
    filas_gv = []
    for (cd_gv, nombre_gv), sub_df in df.group_by(["cd_gv", "nombre_gv"]):
        counts_cierre = {}
        counts_global = {}
        counts_fecha = {}
        
        for row in sub_df.iter_rows(named=True):
            d_gv = row["dia_gerencia_ventas"]
            v = row["valor_diario"]
            
            # Clasificación de fases
            clave_cierre = str(d_gv) if d_gv <= 0 else ("capta" if d_gv <= 7 else "ajustes")
            counts_cierre[clave_cierre] = counts_cierre.get(clave_cierre, 0) + v
            
            if row["dia_global"]:
                counts_global[str(row["dia_global"])] = counts_global.get(str(row["dia_global"]), 0) + v
            if row["fecha_calendario"]:
                counts_fecha[row["fecha_calendario"]] = counts_fecha.get(row["fecha_calendario"], 0) + v

        univ = sub_df["universo_base"][0]
        tot = sum(counts_cierre.values())
        
        filas_gv.append({
            "cd_gv": cd_gv,
            "nombre_gv": nombre_gv,
            "universo": univ,
            "total_acumulado": tot,
            "tasa_final": round((tot / univ * 100), 2) if univ > 0 else 0.0,
            "counts_by_dia_cierre": counts_cierre,
            "counts_by_dia_global": counts_global,
            "counts_by_fecha": counts_fecha,
        })

    # Fila Nacional Agregada
    nacional_universo = sum(f["universo"] for f in filas_gv)
    nacional_total = sum(f["total_acumulado"] for f in filas_gv)
    
    nacional_data = {
        "cd_gv": 0,
        "nombre_gv": "Total Nacional",
        "universo": nacional_universo,
        "total_acumulado": nacional_total,
        "tasa_final": round((nacional_total / nacional_universo * 100), 2) if nacional_universo > 0 else 0.0,
        # Agregaciones de diccionarios de conteo
        "counts_by_dia_cierre": aggregate_dict_keys([f["counts_by_dia_cierre"] for f in filas_gv]),
        "counts_by_dia_global": aggregate_dict_keys([f["counts_by_dia_global"] for f in filas_gv]),
    }

    cols_cierre = [str(d) for d in range(-21, 1)] + ["capta", "ajustes"]
    cols_global = [str(d) for d in range(1, 42)]

    return {
        "ciclo": ciclo,
        "cols_dias_cierre": cols_cierre,
        "cols_dias_global": cols_global,
        "gv_rows": filas_gv,
        "nacional": nacional_data,
    }
```

---

## 7. Implementación en Frontend (ECharts y Matriz HTML)

### 7.1 Gráfico de Curvas Acumuladas (`renderCurvasAvance`)
Configuración de Apache ECharts con soporte de métricas y líneas guía operativas:

```javascript
export function renderCurvasAvance(domElement, payload) {
    const chart = echarts.init(domElement);
    const { data, opts } = payload;
    const alineacion = opts.alineacion || 'dia0'; // 'dia0' | 'fecha' | 'global'
    const metrica = opts.metrica || 'tasa';       // 'tasa' | 'abs' | 'pct'

    const xLabels = (alineacion === 'dia0') 
        ? data.cols_dias_cierre 
        : (alineacion === 'global' ? data.cols_dias_global : data.fechas_cal);

    const series = [];

    // Curva destacada de Total Nacional
    if (data.nacional && opts.seleccion.has('Nacional')) {
        let acumNac = 0;
        const valsNac = data.cols_dias_cierre.map(col => {
            acumNac += (data.nacional.counts_by_dia_cierre[col] || 0);
            if (metrica === 'tasa') return ((acumNac / data.nacional.universo) * 100).toFixed(2);
            if (metrica === 'pct') return ((acumNac / data.nacional.total_acumulado) * 100).toFixed(1);
            return acumNac;
        });

        series.push({
            name: 'Total Nacional',
            type: 'line',
            smooth: true,
            lineStyle: { width: 3.5, color: '#06b6d4' },
            itemStyle: { color: '#06b6d4' },
            z: 10,
            data: valsNac
        });
    }

    // Series por Gerencia de Ventas
    data.gv_rows.filter(f => opts.seleccion.has(f.nombre_gv)).forEach(fila => {
        let acum = 0;
        const vals = data.cols_dias_cierre.map(col => {
            acum += (fila.counts_by_dia_cierre[col] || 0);
            if (metrica === 'tasa') return fila.universo ? ((acum / fila.universo) * 100).toFixed(2) : 0;
            if (metrica === 'pct') return fila.total_acumulado ? ((acum / fila.total_acumulado) * 100).toFixed(1) : 0;
            return acum;
        });

        series.push({
            name: fila.nombre_gv,
            type: 'line',
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 2.0 },
            data: vals
        });
    });

    // Marcas de corte operativo en Dia 0
    if (series.length > 0 && alineacion === 'dia0') {
        const idxCierre = data.cols_dias_cierre.indexOf('0');
        const idxCapta = data.cols_dias_cierre.indexOf('capta');

        series[0].markLine = {
            silent: true,
            symbol: 'none',
            data: [
                { xAxis: idxCierre, lineStyle: { color: '#ef4444', type: 'dashed' }, label: { formatter: 'Cierre (D0)' } },
                { xAxis: idxCapta, lineStyle: { color: '#eab308', type: 'dashed' }, label: { formatter: 'Capta Oficial' } }
            ]
        };
    }

    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { bottom: 0, type: 'scroll' },
        xAxis: { type: 'category', boundaryGap: false, data: xLabels },
        yAxis: { type: 'value', axisLabel: { formatter: metrica === 'abs' ? '{value}' : '{value}%' } },
        series
    }, true);

    return chart;
}
```

### 7.2 Matriz Térmica Tabular (`renderMatrizAvance`)
Lógica para renderizar la tabla con mapa de calor condicional y delimitación de fases operativas:

```javascript
export function renderMatrizAvance(tablaElement, data, alineacion = 'dia0') {
    const columnasDias = (alineacion === 'dia0') ? data.cols_dias_cierre : data.fechas_cal;
    let maxVisible = Math.max(...data.gv_rows.flatMap(f => Object.values(f.counts_by_dia_cierre)));

    let html = '<thead><tr><th>Gerencia</th><th>Universo</th>';
    columnasDias.forEach(col => {
        let cls = (col === '0') ? 'th-cierre' : (col === 'capta' ? 'th-capta' : (col === 'ajustes' ? 'th-ajustes' : ''));
        html += `<th class="${cls}">${col}</th>`;
    });
    html += '<th>Total</th><th>Tasa</th></tr></thead><tbody>';

    data.gv_rows.forEach(fila => {
        html += `<tr><td>${fila.nombre_gv}</td><td>${fila.universo.toLocaleString()}</td>`;
        columnasDias.forEach(col => {
            const v = fila.counts_by_dia_cierre[col] || 0;
            if (v === 0) {
                html += '<td class="cell-zero">0</td>';
            } else {
                // Cálculo de opacidad dinámica verde
                const alpha = Math.min(0.90, Math.max(0.18, v / (maxVisible * 0.75 || 1)));
                html += `<td style="background: rgba(16, 185, 129, ${alpha.toFixed(2)});" class="cell-val">${v}</td>`;
            }
        });
        html += `<td>${fila.total_acumulado.toLocaleString()}</td><td>${fila.tasa_final}%</td></tr>`;
    });

    html += '</tbody>';
    tablaElement.innerHTML = html;
}
```

---

## 8. Estilos CSS Recomendados

Clases para estructurar bordes de corte operativo y contrastes en modo oscuro:

```css
/* Cabeceras de fases operativas */
.th-cierre { color: #ef4444; border-bottom: 2px solid #ef4444; }
.th-capta { color: #eab308; border-bottom: 2px solid #eab308; }
.th-ajustes { color: #a855f7; border-bottom: 2px solid #a855f7; }

/* Celdas de datos */
.cell-zero { color: rgba(148, 163, 184, 0.4); text-align: right; }
.cell-val { font-variant-numeric: tabular-nums; text-align: right; font-weight: 500; }
.react-row-nacional { background: rgba(6, 182, 212, 0.08); font-weight: 600; }

/* Celdas fuera de ventana operativa de la GV */
.react-cell-fuera { background: rgba(15, 23, 42, 0.4); opacity: 0.3; }
```

---

## 9. Checklist de Calidad para Nuevas Implementaciones

1. **Notación de Ciclos:** Utilizar estrictamente el formato `YYYYCC` en parámetros de API, base de datos y UI.
2. **Deduplicación de Eventos:** Si la métrica mide personas (ej. consultoras con inicio o reactivación), aplicar `ROW_NUMBER() = 1` particionado por consultora y ciclo para no contar pedidos repetidos.
3. **Exclusión de Pedidos Anulados:** Filtrar en origen `status_id NOT IN (10, 11)` o equivalente antes de agregar volúmenes.
4. **Modo WAL y Tiempos de Espera:** Configurar SQLite o DuckDB con `journal_mode = WAL` y `busy_timeout` adecuado para soportar lecturas simultáneas desde el dashboard.
5. **Eficiencia de Memoria:** Emplear Polars para procesar DataFrames y agregaciones en backend; evitar conversiones a estructuras pesadas de Python.
6. **Manejo de Ciclos Abiertos:** Evaluar `fecha_ref = min(CURRENT_DATE, max(fecha_datos))` para no truncar datos prematuramente por desfases en el ETL nocturno.
