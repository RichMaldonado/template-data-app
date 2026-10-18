# Guía Técnica: Determinación de Ciclos Activos y Arquitectura Temporal Multiciclo

Esta guía documenta la naturaleza de los ciclos comerciales en México (escala nacional vs. gerencia), las tablas fuente en Databricks y la estrategia algorítmica para determinar ciclos activos (abiertos) y cerrados en aplicaciones analíticas y data apps.

---

## 1. Tablas Fuente en Databricks

La arquitectura de datos se alimenta de dos componentes principales en Databricks: la dimensión del calendario operativo escalonado y los hechos transaccionales de pedidos.

### 1.1 Dimensión de Calendario: `product.elo_modelo_combinado.cmm_structure_operational_cycle`
Es la tabla dimensional analítica precalculada (capa Gold / Modelo Combinado ELO) que desnormaliza la jerarquía comercial por ciclo.

* **Filtros requeridos para México:**
  * `country = 484` (Identificador de México).
  * `structure_level2_name = 'GV'` (Nivel Gerencia de Ventas).
  * `operational_cycle >= YYYYCC` (Ciclos comerciales en formato estándar de 6 dígitos).
* **Columnas operativas clave:**
  * `operational_cycle`: Ciclo comercial (`YYYYCC`, ej. `202613`).
  * `structure_code2`: Código de la Gerencia de Ventas (ej. `164`, `170`).
  * `structure_name_level2`: Nombre oficial de la GV (ej. `GV 01 CATRINA`, `GV 05 APAPACHO`).
  * `cycle_date_start`: Fecha oficial de apertura de la GV para el ciclo.
  * `cycle_date_end`: Fecha oficial de cierre de la GV para el ciclo (Día 0 local).
  * `block`: Bloque de escalonamiento de cierre (`Block 1` a `Block 4`).
  * `block_sub`: Día de la semana asignado al corte (`Tuesday`, `Wednesday`, `Thursday`, `Friday`).

### 1.2 Hechos Transaccionales: `platform.dw_o01dw_sisdmi_replica.t_prj_2go_f_pedido`
Fuente de hechos para captación y facturación de pedidos de consultoras.

* **Columnas clave:**
  * `DT_CAPTACAO`: Fecha de captura del pedido.
  * `NM_DIA_CICLO`: Día relativo del ciclo en la escala local de la GV (días 1 a 26).
  * `ID_EXPEDICAO_PEDIDO`: Identificador de pedido con estatus facturado.
  * Indicadores de canal: `begin_ind = 1` (Inicios), `restart_ind = 1` (Reinicios).

---

## 2. Naturaleza del Ciclo Comercial: Nacional vs. Gerencia de Ventas (GV)

El concepto temporal del ciclo opera en dos niveles jerárquicos con dinámicas distintas:

```
[========================== CICLO PAÍS (Día 1 a 41) ==========================]
  [Block 1: GV 01-02 (20d)]
      [Block 2: GV 03-06 (20-21d)]
            [Block 3: GV 07-10 (20-21d)]
                  [Block 4: GV 11-13 (20-21d)]
                                            [Ventana de Gracia País (+7d)]
```

### 2.1 El Ciclo País (Macro)
* **Definición:** Es la envolvente temporal total entre la apertura de la primera gerencia del país y el cierre de la última gerencia.
* **Fórmula de límites nacionales:**
  $$\text{Fecha Inicio País} = \min_{\text{GVs}}(\text{cycle\_date\_start})$$
  $$\text{Fecha Fin País} = \max_{\text{GVs}}(\text{cycle\_date\_end})$$
* **Duración:** Entre **40 y 41 días calendario** (`dia_global` 1 a 41).
* **Comportamiento:** No todas las consultoras del país inician o cierran al mismo tiempo. El ciclo nacional es la acumulación progresiva de curvas locales desfasadas.

### 2.2 El Ciclo por Gerencia de Ventas (Micro / Local)
* **Definición:** Ventana efectiva de operación de cada una de las 13 GVs de México.
* **Duración Local:** Únicamente **20 a 21 días** (3 semanas exactas).
* **Escalonamiento por Bloques:** Las 13 gerencias se distribuyen en 4 bloques de cierre:

| Bloque | GVs Asociadas | Apertura Relativa | Cierre Relativo País | Duración Local |
| :--- | :--- | :---: | :---: | :---: |
| **Block 1** | GV 01 CATRINA, GV 02 ALEBRIJE | Día 1 País | Día 20 País | 20 días |
| **Block 2** | GV 03 FOLCLOR, GV 04 MÍSTICA, GV 05 APAPACHO, GV 06 TELAR | Día 4 a 6 País | Día 25 a 27 País | 20 a 21 días |
| **Block 3** | GV 07 ESENCIA, GV 08 RAÍCES, GV 08 CARNAVAL, GV 09 ARTESANÍA, GV 10 FERIA | Día 11 a 13 País | Día 32 a 34 País | 20 a 21 días |
| **Block 4** | GV 11 OCARINA, GV 12 ARTE, GV 13 ANCESTRAL | Día 18 a 20 País | Día 40 a 41 País | 20 a 21 días |

### 2.3 Desfase y Concepto de Día 0
Existe una brecha de **20 días calendario** entre el cierre de Block 1 y Block 4. Para comparar equitativamente la fuerza comercial de una GV contra otra:
* **Día 0:** Fecha oficial de corte de la GV (`cycle_date_end`).
* **Días Negativos (-21 a 0):** Carrera comercial de captación activa.
* **Capta (+1 a +7):** Facturación tardía y pedidos rezagados.
* **Ajustes (> +7):** Regularizaciones administrativas y cobranza antes de cierre definitivo.

### 2.4 Traslape entre Ciclos Consecutivos
Debido a que cada 21 días abre un ciclo nuevo mientras el ciclo previo dura 41 días a nivel país:
* **En cualquier fecha dada, coexisten al menos 2 ciclos activos.**
* Por ejemplo: El ciclo `202613` se encuentra en el día 40 (cierre de Block 4 y ajustes), mientras que el ciclo `202614` se encuentra en el día 19 (aceleración de Block 1 y 2).

---

## 3. Estrategia Algorítmica para Determinar Ciclos Activos

Para implementar esta lógica en cualquier data app de forma consistente y sin errores de sincronización, se deben aplicar tres reglas secuenciales:

### Regla 1: Anclaje de la Fecha de Referencia (`fecha_ref`)
No se debe confiar exclusivamente en el reloj del servidor (`CURRENT_DATE`), ya que los pipelines ETL pueden ejecutarse de noche o con desfase de fines de semana.

* **Fórmula:**
  $$\text{fecha\_ref} = \min(\text{CURRENT\_DATE}, \max(\text{fecha\_transaccional\_cargada}))$$
* Si no existen registros transaccionales, se utiliza `CURRENT_DATE`.

### Regla 2: Determinación de Ciclos Abiertos a Nivel País (Macro)
Un ciclo comercial nacional se considera **Abierto** si la fecha de referencia se ubica entre la apertura del primer bloque y la fecha de corte del último bloque más la ventana de gracia de ajustes:

$$\text{Ciclo Abierto País} \iff \text{fecha\_ref} \ge \text{fecha\_inicio\_pais} \quad \text{AND} \quad \text{fecha\_ref} \le \text{fecha\_fin\_pais} + 7\text{ días}$$

* **Ventana de gracia (+7 días):** Margen operativo donde aún se procesan ajustes de pedidos y facturación final del ciclo.
* **Ciclo Cerrado País:** Aquel donde $\text{fecha\_ref} > \text{fecha\_fin\_pais} + 7\text{ días}$. Sus datos se consideran definitivos y congelados.

### Regla 3: Determinación de Estado por Gerencia de Ventas (Micro)
En vistas filtradas por GV, el estado depende de las fechas locales de esa GV:

$$\text{GV Abierta en Ciclo} \iff \text{fecha\_ref} \le \text{cycle\_date\_end}_{\text{GV}} + 7\text{ días}$$

* **Efecto de negocio:** Una GV de Block 1 puede estar formalmente **cerrada**, mientras que el ciclo a nivel país y las GVs de Block 4 siguen **abiertas**.

---

## 4. Consultas SQL de Extracción Recomendadas

### 4.1 Extracción de Calendario País (`dim_calendario_ciclos`)
```sql
SELECT
    operational_cycle AS ciclo,
    MIN(cycle_date_start) AS fecha_inicio,
    MAX(cycle_date_end) AS fecha_fin,
    DATEDIFF(MAX(cycle_date_end), MIN(cycle_date_start)) + 1 AS duracion_dias
FROM
    product.elo_modelo_combinado.cmm_structure_operational_cycle
WHERE
    country = 484
    AND structure_level2_name = 'GV'
    AND operational_cycle >= 202501
GROUP BY
    operational_cycle
ORDER BY
    operational_cycle ASC;
```

### 4.2 Extracción de Bloques por Ciclo (`dim_bloques_ciclos`)
```sql
SELECT
    operational_cycle AS ciclo,
    block,
    MIN(cycle_date_start) AS fecha_inicio_bloque,
    MAX(cycle_date_end) AS fecha_fin_bloque,
    COUNT(DISTINCT structure_code2) AS total_gvs
FROM
    product.elo_modelo_combinado.cmm_structure_operational_cycle
WHERE
    country = 484
    AND structure_level2_name = 'GV'
    AND operational_cycle >= 202501
    AND block IS NOT NULL
GROUP BY
    operational_cycle,
    block
ORDER BY
    operational_cycle ASC,
    fecha_fin_bloque ASC;
```

---

## 5. Implementación en Backend (Python / DuckDB / Polars)

Patrón de implementación para el servicio analítico:

```python
from datetime import date
import duckdb
import polars as pl

def obtener_estado_ciclos(conn: duckdb.DuckDBPyConnection) -> dict:
    # 1. Obtener fecha maxima de datos disponibles
    max_fecha_row = conn.execute("""
        SELECT MAX(fecha_calendario) 
        FROM fact_curva_canal_gv
    """).fetchone()
    
    fecha_hoy = date.today()
    fecha_datos = max_fecha_row[0] if max_fecha_row and max_fecha_row[0] else fecha_hoy
    fecha_ref = min(fecha_hoy, fecha_datos)

    # 2. Consultar ciclos abiertos a nivel pais (con ventana de gracia de 7 dias)
    ciclos_abiertos_df = conn.execute("""
        SELECT ciclo
        FROM dim_calendario_ciclos
        WHERE ? BETWEEN fecha_inicio AND fecha_fin + INTERVAL 7 DAY
        ORDER BY ciclo ASC
    """, [fecha_ref]).fetchall()
    
    ciclos_abiertos = [int(r[0]) for r in ciclos_abiertos_df]

    # 3. Fallback en caso de bases desfasadas
    if not ciclos_abiertos:
        ciclos_disponibles = conn.execute("""
            SELECT DISTINCT ciclo 
            FROM fact_curva_pais 
            ORDER BY ciclo DESC LIMIT 2
        """).fetchall()
        ciclos_abiertos = sorted([int(r[0]) for r in ciclos_disponibles])

    # 4. Obtener los 3 ciclos cerrados inmediatamente anteriores para benchmark
    todos_ciclos = [r[0] for r in conn.execute("""
        SELECT DISTINCT ciclo 
        FROM fact_curva_pais 
        ORDER BY ciclo DESC
    """).fetchall()]
    
    ciclos_cerrados = [c for c in todos_ciclos if c not in set(ciclos_abiertos)][:3]

    return {
        "fecha_referencia": str(fecha_ref),
        "ciclos_abiertos_pais": ciclos_abiertos,
        "ciclos_referencia_benchmark": ciclos_cerrados
    }
```

---

## 6. Tratamiento Analítico y Visual en la Data App

| Componente | Ciclo Abierto | Ciclo Cerrado |
| :--- | :--- | :--- |
| **Curva de Avance** | Línea dinámica activa hasta el día actual observado. | Curva completa continua del día 1 al cierre final. |
| **Etiqueta Final (Pin)** | Despliega Pin enriquecido con velocidad: `[Ritmo: X% \| Brecha]`. | Despliega únicamente volumen o % acumulado final. |
| **Tooltip Interactivo** | Incluye tarjeta con: `% Histórico del día`, `Meta esperada al día`, `Desvío` y `Ritmo con estatus`. | Despliega únicamente la serie y volumen acumulado del día. |
| **Matriz Diaria** | Inserta badge `Abierto` en encabezado y sub-renglón con `Meta esperada` y `% ritmo` en celdas. | Celda estándar con volumen o % de meta alcanzado. |
| **Benchmark de Velocidad** | Se le calcula la meta esperada diaria basada en el promedio de los 3 ciclos cerrados previos. | No se le proyecta velocidad; sirve como base histórica para los ciclos abiertos. |
