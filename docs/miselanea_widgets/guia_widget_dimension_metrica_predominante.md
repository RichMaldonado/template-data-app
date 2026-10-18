# Guia de Diseno e Implementacion: Widget "Dimension Predominante y Mix de Distribucion"

Documento de referencia tecnica para la reutilizacion del patron de diseno analitico que conjuga una **variable categorica (dimension)** con una **variable continua (metrica)** en tarjetas de KPI dentro de Data Apps.

---

## 1. Fundamento Conceptual y Objetivo

El patron "Predominante & Mix" tiene como objetivo sintetizar en un unico componente compacto de UI:
1. **Liderazgo / Concentracion:** La entidad categorica dominante segun una metrica cuantitativa acumulada.
2. **Intensidad Relativa:** El peso porcentual que representa el lider sobre el total consolidado.
3. **Distribucion Integral (Mix):** La participacion de cada una de las categorias complementarias, permitiendo evaluar diversificacion versus dependencia en una sola mirada.

### Formula General

Dada una dimension discreta $D = \{d_1, d_2, \dots, d_k\}$ y una metrica aditiva continua $M$:

* **Metrica Total:**
  $$M_{Total} = \sum_{i=1}^k M(d_i)$$

* **Categoria Predominante ($d^*$):**
  $$d^* = \arg\max_{d_i \in D} M(d_i)$$

* **Participacion Porcentual de la Categoria ($P_i$):**
  $$P(d_i) = \begin{cases} \left( \frac{M(d_i)}{M_{Total}} \right) \times 100 & \text{si } M_{Total} > 0 \\ 0 & \text{si } M_{Total} = 0 \end{cases}$$

---

## 2. Casos de Uso y Matriz de Conjugacion

| Dimension Categorica ($D$) | Metrica Continua ($M$) | KPI Predominante | Mix Analizado | Caso de Aplicacion |
| :--- | :--- | :--- | :--- | :--- |
| **Canal de Captacion** | Inicios + Reinicios (I+R) | Canal Predominante | Mix de Canales (Autocadastro, Lider, Impulsa, CN) | Monitoreo comercial de atraccion |
| **Marca Comercial** | Facturacion / Venta Neta | Marca Lider | Mix de Facturacion por Marca | Analisis de portafolio y dependencia |
| **Categoria de Producto** | Unidades Vendidas | Categoria Principal | Distribucion de Unidades (Perfumaria, Maquillaje, etc.) | Gestion de cadena de suministro e inventario |
| **Segmento / Nivel** | Facturacion o Cartera | Nivel Dominante | Aportacion por Nivel de Consultora | Evaluacion de estructura comercial |
| **Metodo de Pago** | Monto Cobrado | Metodo Predominante | Mix de Cobranza (Tarjeta, Efectivo, Credito) | Gestion financiera y riesgo crediticio |

---

## 3. Criterios de Diseno y Restricciones de Cardinalidad

Para mantener la eficacia cognitiva y estetica del widget:

1. **Cardinalidad Ideal ($k$):** Entre 3 y 5 categorias.
2. **Cardinalidad Maxima Recomendada:** 6 categorias. Si la dimension contiene mas de 6 valores, se debe aplicar agrupacion en la capa de datos: mantener el Top 4 o Top 5 por volumen y colapsar el resto bajo la categoria sintetica `'Otros'`.
3. **Naturaleza de la Metrica:** La metrica $M$ debe ser aditiva (cantidades, importes monetarios, conteos). No debe utilizarse directamente con metricas no aditivas (promedios, ratios, porcentajes) sin haber calculado antes los numeradores y denominadores base.

---

## 4. Arquitectura de Datos y Backend (Polars + DuckDB)

### 4.1. Consulta SQL Base en DuckDB

```sql
SELECT 
    categoria_dimension AS categoria,
    COALESCE(SUM(metrica_continua), 0) AS total_metrica
FROM tabla_analitica
WHERE periodo = :periodo_filtro
  AND fecha_evento <= CURRENT_DATE
GROUP BY categoria_dimension;
```

### 4.2. Procesamiento y Generacion de Respuesta con Polars

Implementacion de alto rendimiento y bajo consumo de memoria:

```python
import polars as pl
from typing import Dict, Any, List

def calcular_kpi_predominante(
    df_raw: pl.DataFrame, 
    col_dimension: str, 
    col_metrica: str,
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Procesa una dimension y metrica continua retornando el lider y el mix de participacion.
    Optimizado en memoria con Polars.
    """
    if df_raw.is_empty():
        return {
            "lider": "N/A",
            "lider_metrica": 0,
            "lider_pct": 0.0,
            "total_metrica": 0,
            "categorias": []
        }

    # Asegurar agregacion por dimension y orden descendente
    df_agrupado = (
        df_raw
        .group_by(col_dimension)
        .agg(pl.col(col_metrica).sum().alias("metrica"))
        .sort("metrica", descending=True)
    )

    total_general = df_agrupado["metrica"].sum()

    # Si hay mas categorias que top_n, agrupar el excedente en 'Otros'
    if df_agrupado.height > top_n:
        df_top = df_agrupado.head(top_n)
        metrica_otros = df_agrupado.tail(df_agrupado.height - top_n)["metrica"].sum()
        
        df_otros = pl.DataFrame({
            col_dimension: ["Otros"],
            "metrica": [metrica_otros]
        })
        df_final = pl.concat([df_top, df_otros])
    else:
        df_final = df_agrupado

    if total_general == 0:
        return {
            "lider": "N/A",
            "lider_metrica": 0,
            "lider_pct": 0.0,
            "total_metrica": 0,
            "categorias": []
        }

    # Extraccion del lider (primer registro)
    fila_lider = df_final.row(0, named=True)
    lider_nombre = fila_lider[col_dimension]
    lider_metrica = float(fila_lider["metrica"])
    lider_pct = round((lider_metrica / total_general) * 100, 1)

    # Construccion del mix de categorias
    categorias_lista: List[Dict[str, Any]] = []
    for row in df_final.iter_rows(named=True):
        val_metrica = float(row["metrica"])
        pct = round((val_metrica / total_general) * 100, 1)
        categorias_lista.append({
            "categoria": row[col_dimension],
            "metrica": val_metrica,
            "pct": pct
        })

    return {
        "lider": lider_nombre,
        "lider_metrica": lider_metrica,
        "lider_pct": lider_pct,
        "total_metrica": float(total_general),
        "categorias": categorias_lista
    }
```

### 4.3. Estructura del Contrato JSON de Salida

```json
{
  "lider": "Natura",
  "lider_metrica": 1450200.50,
  "lider_pct": 68.4,
  "total_metrica": 2120000.00,
  "categorias": [
    { "categoria": "Natura", "metrica": 1450200.50, "pct": 68.4 },
    { "categoria": "Avon", "metrica": 540300.00, "pct": 25.5 },
    { "categoria": "The Body Shop", "metrica": 129499.50, "pct": 6.1 }
  ]
}
```

---

## 5. Implementacion en Frontend

### 5.1. Estructura HTML Semantica (TailwindCSS + Alpine.js)

```html
<div class="bg-white dark:bg-slate-850 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm relative flex flex-col justify-between">
  <div>
    <!-- Encabezado de Tarjeta -->
    <div class="flex items-center justify-between">
      <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Marca Predominante</span>
      <button @click="abrirModalInfo('marca_predominante')" 
              class="w-5 h-5 rounded-full border border-slate-300 dark:border-slate-600 flex items-center justify-center text-xs text-slate-400 hover:text-brand-600 transition"
              title="Ver definicion y formula">
        i
      </button>
    </div>

    <!-- Valor Principal (Lider y Concentracion) -->
    <div class="mt-2 flex items-baseline justify-between">
      <div class="flex items-baseline space-x-2">
        <span class="text-xl font-black text-slate-900 dark:text-white" x-text="kpiMarca.lider"></span>
        <span class="text-xs font-bold text-brand-600" x-text="kpiMarca.lider_pct + '%'"></span>
      </div>
      <span class="text-[11px] text-slate-500 font-medium" 
            x-text="'$' + Number(kpiMarca.lider_metrica).toLocaleString('es-MX', {minimumFractionDigits: 0, maximumFractionDigits: 0})"></span>
    </div>

    <!-- Barra de Segmentos Proporcionales -->
    <div class="w-full h-1.5 rounded-full overflow-hidden flex bg-slate-100 dark:bg-slate-700 mt-2.5">
      <template x-for="item in (kpiMarca.categorias || [])" :key="item.categoria">
        <div :style="'width: ' + item.pct + '%; background-color: getCategoriaColor(item.categoria)'" 
             :title="item.categoria + ': ' + item.pct + '% ($' + Number(item.metrica).toLocaleString() + ')'" 
             class="h-full transition-all"></div>
      </template>
    </div>
  </div>

  <!-- Grilla de Desglose del Mix (2 Columnas) -->
  <div class="grid grid-cols-2 gap-x-2 gap-y-1 mt-2.5 pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px]">
    <template x-for="item in (kpiMarca.categorias || [])" :key="item.categoria">
      <div class="flex items-center justify-between pr-1" 
           :title="item.categoria + ': $' + Number(item.metrica).toLocaleString()">
        <div class="flex items-center space-x-1.5 truncate">
          <span class="w-2 h-2 rounded-full flex-shrink-0" :style="'background-color: getCategoriaColor(item.categoria)'"></span>
          <span class="text-slate-600 dark:text-slate-300 truncate font-medium" x-text="item.categoria"></span>
        </div>
        <span class="font-bold text-slate-800 dark:text-slate-200 ml-1" x-text="item.pct + '%'"></span>
      </div>
    </template>
  </div>
</div>
```

### 5.2. Mapeo Cromatico Dinamico en JavaScript

```javascript
function getCategoriaColor(categoria) {
  const paleta = {
    // Ejemplo Marcas
    "Natura": "#ea580c",        // Naranja
    "Avon": "#db2777",          // Rosa/Magenta
    "The Body Shop": "#059669", // Verde
    "Otros": "#64748b",         // Gris pizarra
    
    // Ejemplo Canales
    "Autocadastro": "#2563eb",  // Azul
    "Líder": "#16a34a",         // Verde
    "Impulsa": "#f59e0b",       // Ambar
    "CN": "#8b5cf6"             // Purpura
  };
  return paleta[categoria] || "#94a3b8";
}
```

---

## 6. Validaciones y Reglas de Calidad Analitica

1. **Suma de Porcentajes:** La suma de participaciones debe totalizar $100.0\% \pm 0.1\%$ debido al redondeo a un decimal.
2. **Control de Division por Cero:** Si $M_{Total} = 0$, el lider se reporta como `"N/A"` y los porcentajes en `0.0%`, evitando excepciones en tiempo de ejecucion.
3. **Formato Numerico Contextual:**
   * Metricas monetarias: Incluir prefijo de moneda (`$`), separador de miles y sin decimales en tarjeta para no saturar espacio.
   * Metricas de conteo: Formato entero con separador de miles.
   * Porcentajes: Exactamente un decimal (`X.X%`).
4. **Respeto a Filtros Activos:** El calculo debe responder a los filtros globales de la aplicacion (ciclo comercial `YYYYCC`, periodo, region, corte temporal diario).
