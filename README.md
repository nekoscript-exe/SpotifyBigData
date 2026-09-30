# SpotifyBigData

## Descripción

SpotifyBigData es un proyecto universitario de **Manejo Masivo de Datos / Big
Data**. Utiliza un dataset público relacionado con Spotify como caso de estudio
para explicar las cinco V de Big Data mediante análisis reproducibles con
Python y pandas.

El proyecto diagnostica el CSV, evalúa su calidad y variedad, mide su volumen,
ejecuta benchmarks locales, simula un flujo de eventos, obtiene hallazgos
descriptivos y genera reportes y visualizaciones estáticas.

No reproduce la arquitectura interna de Spotify ni se conecta a su API. Es una
demostración académica sobre una muestra finita.

## Objetivo académico

El objetivo es mostrar el recorrido completo desde datos crudos hasta evidencia
útil:

```text
CSV original
    ↓
diagnóstico y controles de calidad
    ↓
mediciones, simulaciones y proyecciones diferenciadas
    ↓
análisis descriptivos
    ↓
reportes y visualizaciones para comunicar resultados
```

La prioridad es distinguir correctamente qué se midió, qué se simuló, qué se
proyectó y qué solo puede interpretarse de forma descriptiva.

## Caso de estudio: Spotify

Una plataforma musical es un caso intuitivo para estudiar las cinco V: combina
catálogos extensos, metadatos textuales, categorías, características acústicas
y flujos de interacción. El CSV utilizado contiene información sobre tracks,
pero no contiene tráfico real de usuarios, reproducciones en vivo ni la
infraestructura de Spotify.

Por esa razón, el proyecto utiliza el dataset para Veracidad, Variedad, Volumen
y Valor, mientras que Velocidad se representa mediante eventos sintéticos con
`track_id` que sí existen en el CSV.

## Dataset

Archivo analizado:

```text
data/spotify-tracks-dataset-detailed.csv
```

| Característica                | Valor observado |
| ------------------------------ | --------------: |
| Filas                          |         114,000 |
| Columnas                       |              20 |
| Tamaño del CSV en disco       |        18.53 MB |
| Memoria profunda del DataFrame |        48.79 MB |

El tamaño serializado en disco no equivale a la memoria necesaria durante el
procesamiento. pandas debe representar índices, objetos y cadenas en memoria,
por lo que el DataFrame ocupa más que el archivo CSV.

El análisis nunca sobrescribe, limpia ni modifica el dataset original. Su
SHA-256 esperado es:

```text
db8cd3670209db33285dbfa7ad08dc05446219e9c430e7750abfd17e99297c42
```

## Las 5 V de Big Data

| V                   | Cómo se demuestra en el proyecto                                                                   | Evidencia principal                                                    |
| ------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Volumen**   | Tamaño en disco y RAM, benchmark de carga y escalas proyectadas                                    | `benchmark_carga.csv`, `proyeccion_escalabilidad.csv`, gráfica 01 |
| **Velocidad** | Generación incremental y procesamiento de eventos sintéticos sin acumular todo el flujo           | `benchmark_velocidad.csv`, `resumen_eventos.csv`, gráfica 03      |
| **Variedad**  | Tipos técnicos y semánticos: texto, categorías, booleanos, métricas e identificadores           | `resumen_variedad.csv`                                               |
| **Veracidad** | Faltantes, duplicados exactos, IDs repetidos, reglas de consistencia y outliers informativos        | reportes de calidad, gráfica 04                                       |
| **Valor**     | Tracks únicos, créditos, géneros, contenido explicit, correlaciones y perfil de popularidad alta | reportes de Valor, gráficas 05–08                                    |

### Volumen

Se miden las filas, columnas, bytes en disco y memoria del DataFrame. La carga
del CSV y varias operaciones comunes se repiten tres veces y se resume su
mediana. Las escalas x10 a x1,000,000 son cálculos matemáticos: no se crean
datasets gigantes ni se presentan esas cifras como mediciones reales.

### Velocidad

El CSV no contiene eventos reales ni timestamps de usuarios. La simulación
produce un evento a la vez mediante un generador de Python y lo procesa de
forma incremental. Cada evento contiene:

```text
timestamp   instante sintético desde una fecha fija
user_id     usuario sintético
track_id    identificador real tomado del dataset
evento      play, pause, skip, like o add_to_playlist
```

Se usa la semilla fija `42`. Las probabilidades —45% `play`, 25% `skip`, 15%
`pause`, 10% `like` y 5% `add_to_playlist`— son decisiones de la simulación,
no estadísticas de Spotify. El benchmark mide generación y procesamiento para
10,000, 50,000, 100,000, 250,000 y 500,000 eventos.

### Variedad

Se distinguen los dtypes técnicos de su significado semántico. Por ejemplo,
`key` se almacena como entero, pero conceptualmente es una categoría musical.
También se calcula la cardinalidad de cada columna para reconocer variables
identificadoras, textuales, categóricas, binarias y métricas.

### Veracidad

Se estudian valores faltantes, duplicados exactos, `track_id` repetidos, rangos
esperados y valores potencialmente sospechosos. Una fila duplicada no equivale
a un ID repetido: la misma canción puede estar asociada a distintos géneros.

Los outliers de duración, tempo y sonoridad se detectan con IQR únicamente para
investigarlos. **Valor atípico no significa dato incorrecto.** En esta etapa no
se eliminan, rellenan ni corrigen registros.

### Valor

Para no contar cada fila como una canción independiente se construye en memoria
una vista con una fila por `track_id`. Los metadatos y atributos estables se
conservan; cuando `popularity` varía entre apariciones se utiliza su mediana.
Los géneros mantienen una relación muchos-a-muchos mediante asociaciones únicas
`track_id + track_genre`.

El análisis compara canciones, créditos artísticos, géneros, grupos explicit y
no explicit, correlaciones de Pearson y el cuartil superior de popularidad. Los
resultados corresponden solo a este dataset. **Correlación no implica
causalidad.**

## Estructura del proyecto

```text
SpotifyBigData/
├── data/
│   └── spotify-tracks-dataset-detailed.csv
├── outputs/
│   ├── graficas/          # Ocho PNG para la exposición
│   └── reportes/          # Reportes CSV de todas las etapas
├── src/
│   ├── __init__.py
│   ├── carga.py           # Localización y carga portable del CSV
│   ├── diagnostico.py     # Diagnóstico inicial
│   ├── calidad.py         # Veracidad
│   ├── variedad.py        # Variedad
│   ├── volumen.py         # Volumen y proyecciones
│   ├── rendimiento.py     # Benchmarks locales
│   ├── velocidad.py       # Flujo sintético incremental
│   ├── valor.py           # Análisis descriptivos
│   └── visualizacion.py   # Figuras estáticas
├── GUIA_EXPOSICION.md
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Requisitos

- Git.
- Python 3.10 o posterior.
- Espacio suficiente para el dataset, los reportes y las imágenes.

Las únicas dependencias directas son pandas y matplotlib.

## Instalación

### Linux o macOS

```bash
git clone https://github.com/nekoscript-exe/SpotifyBigData.git
cd SpotifyBigData
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
git clone https://github.com/nekoscript-exe/SpotifyBigData.git
cd SpotifyBigData
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Ejecución

Con el entorno virtual activado, la ejecución oficial es:

```bash
python3 main.py
```

El programa:

1. carga el CSV sin modificarlo;
2. presenta el diagnóstico y las cinco V en la terminal;
3. ejecuta benchmarks locales y la simulación sintética;
4. actualiza los CSV de `outputs/reportes/`;
5. genera ocho PNG en `outputs/graficas/`.

La ejecución completa tarda aproximadamente 11 segundos en el equipo usado
durante el desarrollo. Los tiempos cambiarán entre equipos y ejecuciones.

## Resultados principales

Esta selección resume resultados estables del dataset, no cifras externas de
la plataforma Spotify:

| Resultado                        |    Valor | Naturaleza             |
| -------------------------------- | -------: | ---------------------- |
| Registros                        |  114,000 | Conteo real del CSV    |
| Columnas                         |       20 | Conteo real del CSV    |
| Tamaño en disco                 | 18.53 MB | Medición real         |
| Memoria del DataFrame            | 48.79 MB | Medición local        |
| `track_id` únicos             |   89,741 | Análisis descriptivo  |
| Valores faltantes                |        3 | Análisis de Veracidad |
| Duplicados exactos excedentes    |      450 | Análisis de Veracidad |
| Géneros                         |      114 | Análisis descriptivo  |
| Créditos artísticos distintos  |   31,437 | Análisis descriptivo  |
| Álbumes distintos               |   46,589 | Análisis descriptivo  |
| Tracks únicos marcados explicit |    8.58% | Análisis descriptivo  |

Los benchmarks no se fijan aquí como resultados universales porque dependen
del equipo, la carga del sistema y la caché del sistema operativo.

## Visualizaciones

Las figuras son PNG de 1920×1120 a 160 dpi y se generan con el backend no
interactivo `Agg`.

| Archivo                              | Tema                                | Naturaleza                            |
| ------------------------------------ | ----------------------------------- | ------------------------------------- |
| `01_proyeccion_volumen.png`        | Disco y RAM por escala              | x1 real; x10+ estimación matemática |
| `02_benchmark_carga.png`           | Registros frente al tiempo de carga | Medición real local                  |
| `03_velocidad_eventos.png`         | Eventos frente al tiempo            | Simulación sintética local          |
| `04_calidad_datos.png`             | Indicadores de calidad              | Análisis descriptivo de datos reales |
| `05_generos_popularidad.png`       | Top 10 de géneros                  | Análisis descriptivo                 |
| `06_explicit_popularidad.png`      | Explicit frente a no explicit       | Análisis descriptivo                 |
| `07_correlaciones_popularidad.png` | Correlaciones con popularidad       | Análisis descriptivo, no causal      |
| `08_perfil_alta_popularidad.png`   | Cuartil superior frente al resto    | Análisis descriptivo                 |

El catálogo completo se encuentra en
`outputs/reportes/resumen_visualizaciones.csv`.

## Naturaleza de la evidencia

| Tipo                              | Qué significa aquí                                               | Ejemplos                                                  |
| --------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------- |
| **Medición real**          | Operación ejecutada sobre el archivo o equipo local               | Tamaño del CSV, RAM del DataFrame, benchmark de carga    |
| **Simulación sintética**  | Eventos creados con reglas reproducibles para representar un flujo | Benchmark de Velocidad                                    |
| **Proyección matemática** | Multiplicación de la medición base bajo supuestos constantes     | Escalas x10 a x1,000,000                                  |
| **Análisis descriptivo**   | Resumen y comparación de los registros del dataset                | Géneros, popularidad, explicit, correlaciones y perfiles |

Una medición local no describe todos los equipos; una simulación no es tráfico
real; una proyección no es una prueba física; y una asociación descriptiva no
demuestra causalidad.

## Reproducibilidad

- Las rutas se construyen desde la ubicación del proyecto mediante
  `pathlib.Path`; no dependen del directorio personal del autor.
- La simulación utiliza semilla y timestamp inicial fijos.
- El CSV puede verificarse con el SHA-256 documentado anteriormente.
- Los reportes y gráficas se regeneran con `python main.py`.
- Los resultados analíticos son deterministas para el mismo CSV.
- Los tiempos de benchmark pueden variar legítimamente por hardware, procesos
  concurrentes y caché.

## Limitaciones

- 114,000 filas no convierten automáticamente al dataset en Big Data. El
  proyecto demuestra conceptos y problemas de escala en un entorno académico.
- El CSV es una muestra finita y no representa necesariamente el catálogo ni
  el comportamiento actual de toda la plataforma Spotify.
- No hay usuarios ni eventos reales; la etapa de Velocidad es sintética.
- No hay timestamps históricos que permitan interpretar cambios de
  `popularity` como evolución temporal.
- Las proyecciones suponen estructura y costo por fila constantes; sistemas
  reales pueden escalar de forma no lineal.
- Los benchmarks son locales y no comparan la infraestructura del proyecto con
  la de Spotify.
- Las correlaciones y diferencias entre grupos son descriptivas y no permiten
  afirmar causas ni preferencias de usuarios.
- No se realiza limpieza definitiva, modelado predictivo ni recomendación.

## Tecnologías utilizadas

- **Python:** orquestación, simulación y biblioteca estándar.
- **pandas:** carga, agregaciones, calidad, cardinalidad y reportes CSV.
- **matplotlib:** ocho visualizaciones estáticas.
- **Git:** control de versiones y flujo de trabajo por ramas.
- **Pyright/Pylance:** validación estática del código.

Para preparar la defensa del proyecto, consulta
[`GUIA_EXPOSICION.md`](GUIA_EXPOSICION.md).
