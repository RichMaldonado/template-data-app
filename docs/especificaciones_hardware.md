# Especificaciones de Hardware y Entorno del Servidor de Data Apps

## 1. Ficha Tecnica del Hardware

| Componente | Especificacion | Detalle Tecnico |
| :--- | :--- | :--- |
| **Equipo** | Dell OptiPlex 3050 | Formato de escritorio comercial |
| **Placa Base** | Dell 08NPPY | Chipset Intel B250 |
| **Procesador (CPU)** | Intel Core i5-6500 @ 3.20 GHz | 4 nucleos fisicos / 4 hilos (sin Hyper-Threading), Skylake (14 nm), Frecuencia turbo 3.60 GHz |
| **Memoria RAM** | 16 GB DDR4 | 2 x 8 GB SK Hynix (HMA81GU6AFR8N-UH) @ 2400 MHz en Dual Channel (Maximo soportado por el equipo: 32 GB) |
| **Almacenamiento** | SSD SATA III 960 GB | Kingston SA400S37960G (~500 MB/s lectura secuencial, sin memoria DRAM dedicada) |
| **Particiones de Disco** | C: (~960 GB brutos) | ~350 GB ocupados / ~533 GB libres |
| **Red** | Realtek PCIe GbE Family Controller | 1 Gbps Ethernet cableada full duplex |
| **Sistema Operativo** | Microsoft Windows 11 Pro | Version 10.0.26100 (64 bits) |

---

## 2. Contexto de Operacion Actual

El equipo opera como un nodo centralizado de ejecucion para multiples data apps, APIs y procesos automatizados de datos sin ser un servidor dedicado de centro de datos:

* **Gestor de procesos:** PM2 con persistencia automatica mediante `pm2-windows-startup` y rotacion con `pm2-logrotate`.
* **Procesos registrados:** 32 servicios configurados (aplicaciones R Shiny, backends FastAPI / Node.js, pipelines ETL y sincronizadores).
* **Servicios activos concurrentes:** 11 procesos en estado `online` (incluyendo `monitor-cubos-shiny`, `monitor-retail`, APIs de venta y telemetria).
* **Consumo base de memoria:** ~11.5 GB ocupados, ~4.4 GB libres bajo operacion normal (72% de ocupacion media).
* **Carga interactiva:** Coexistencia de servicios de produccion con sesiones interactivas locales y entornos de desarrollo (IDE Antigravity, terminales, procesos de compilacion).

---

## 3. Diagnostico Operativo y Riesgos

### 3.1 Capacidad de Computo (CPU)
* La limitacion a 4 hilos sin multihilo simultaneo (SMT/Hyper-Threading) reduce la concurrencia real.
* Tareas ETL pesadas o consultas no indexadas compiten directamente contra los workers que atienden peticiones HTTP de las aplicaciones web, elevando la latencia en las respuestas de los dashboards.

### 3.2 Margen de Memoria RAM
* Las aplicaciones Shiny basadas en `Rscript` retienen en memoria estructuras completas de datos de sesion (~300 a ~450 MB por app activa).
* Con un remanente libre de aproximadamente 4.4 GB, cualquier proceso ETL que intente cargar conjuntos de datos extensos en memoria no optimizada corre alto riesgo de invocar el compresor de memoria de Windows, paginacion a disco o errores fatales por OOM (Out Of Memory).

### 3.3 Cuello de Botella de Entrada / Salida (I/O)
* El disco Kingston A400 opera sobre interfaz SATA III y carece de memoria cache DRAM propia.
* Operaciones intensivas de escritura y lectura simultanea (multiples ETLs escribiendo archivos parquet o bases SQLite) saturan rapidamente la cola de I/O, penalizando los tiempos de acceso concurrentes.

### 3.4 Confiabilidad de Entorno
* No cuenta con tolerancia a fallas a nivel de hardware: fuente de poder sencilla, memoria RAM sin correccion de errores (Non-ECC), ni administracion fuera de banda (iDRAC).
* El sistema operativo cliente (Windows 11) puede programar reinicios por actualizaciones si no se encuentra gestionada la politica de mantenimiento del sistema.

---

## 4. Directrices de Diseno y Optimizacion Obligatorias

Dado el perfil de recursos del equipo, cualquier desarrollo o data app desplegada debe adherirse a los siguientes estandares:

1. **Eficiencia en Procesamiento de Datos:**
   * Utilizar **Polars** con evaluaciones perezosas (`lazy`) y ejecucion en modo streaming (`sink_parquet`, `collect(streaming=True)`) en lugar de Pandas para mantener el uso de memoria minimo.
2. **Acceso a Bases de Datos Locales:**
   * Toda conexion a SQLite debe operar obligatoriamente en **Modo WAL** (`PRAGMA journal_mode = WAL;`) y con parametros de `timeout` definidos para evitar bloqueos por concurrencia en disco SATA.
3. **Liberacion Proactiva de Recursos:**
   * En endpoints FastAPI o scripts Shiny, invocar liberacion explicita de memoria tras transformaciones pesadas y evitar variables globales no acotadas.
4. **Programacion de Tareas (ETLs):**
   * Escalonar la ejecucion de procesos pesados de transformacion de datos fuera de las ventanas horarias pico de consulta de los usuarios finales.
