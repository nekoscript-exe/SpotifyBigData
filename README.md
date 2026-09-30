# SpotifyBigData

Proyecto universitario de la materia **Manejo Masivo de Datos / Big Data**. Su
objetivo es estudiar los fundamentos de Big Data y explicar las cinco V
(volumen, velocidad, variedad, veracidad y valor) mediante un dataset de
canciones de Spotify.

El programa localiza el único CSV de `data/`, lo carga sin modificarlo y
muestra un diagnóstico de su estructura. La segunda etapa analiza las V de
**Veracidad** y **Variedad**. La tercera estudia **Volumen**, rendimiento local
y escalabilidad mediante mediciones y proyecciones reproducibles. La cuarta
demuestra **Velocidad** mediante un flujo local de eventos sintéticos.

## Estructura

```text
SpotifyBigData/
├── data/                 # Dataset CSV original
├── outputs/
│   ├── graficas/         # Reservado para etapas posteriores
│   └── reportes/         # Reservado para etapas posteriores
├── src/
│   ├── __init__.py
│   ├── carga.py
│   ├── calidad.py
│   ├── diagnostico.py
│   ├── rendimiento.py
│   ├── variedad.py
│   ├── velocidad.py
│   └── volumen.py
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## Preparación del entorno

Se necesita Python 3. Desde la raíz del proyecto, crea un entorno virtual:

```bash
python -m venv .venv
```

Actívalo en Linux o macOS:

```bash
source .venv/bin/activate
```

O en Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Instala la dependencia:

```bash
python -m pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

El diagnóstico informa dimensiones, variables, tipos de datos, tamaños,
valores faltantes, duplicados, primeras filas y estadísticas descriptivas.
También presenta en la terminal un resumen de Veracidad y Variedad. Los
detalles se escriben en `outputs/reportes/`.

## Veracidad

La Veracidad estudia qué tan confiables y consistentes son los datos antes de
utilizarlos. El análisis implementado revisa:

- valores faltantes por columna y las filas afectadas;
- filas completamente duplicadas y sus grupos;
- `track_id` repetidos y las variaciones de género, álbum, artista, nombre y
  popularidad que existen dentro de cada ID;
- rangos esperados para popularidad y características acústicas normalizadas;
- duraciones, tempos y compases menores o iguales que cero;
- distribuciones de `time_signature`, `mode` y `key`;
- valores atípicos de `duration_ms`, `tempo` y `loudness` mediante el método
  del rango intercuartílico (IQR).

Una fila completamente duplicada y un `track_id` repetido son conceptos
distintos. Una canción puede aparecer en más de un género o contexto sin que
sus filas sean idénticas.

Los límites de IQR ayudan a localizar observaciones que merecen revisión, pero
no demuestran que sean errores: **valor atípico != dato incorrecto**. De igual
forma, un tempo o compás cero se reporta como potencialmente sospechoso, no
como corrupción confirmada.

Los reportes de esta sección son:

```text
outputs/reportes/calidad_columnas.csv
outputs/reportes/filas_con_faltantes.csv
outputs/reportes/duplicados_exactos.csv
outputs/reportes/track_ids_repetidos.csv
```

`duplicados_exactos.csv` incluye tanto la primera aparición como sus copias
para que cada grupo pueda inspeccionarse completo. La métrica de duplicados
excedentes, en cambio, no cuenta la primera aparición de cada grupo.

## Variedad

La Variedad se observa en la combinación de diferentes representaciones y
significados. El proyecto analiza dos perspectivas:

- **tipo técnico:** `object`, enteros, decimales, booleanos y cualquier otro
  dtype que pandas encuentre;
- **significado semántico:** identificadores, texto, categorías, booleanos y
  métricas numéricas.

El dtype técnico no equivale al significado semántico. Por ejemplo, `key` se
almacena como entero, pero conceptualmente representa una categoría musical.
También se calculan la cardinalidad y el porcentaje de unicidad de cada
columna, además de los dominios de variables como `explicit`, `mode` y
`time_signature`.

El detalle se guarda en:

```text
outputs/reportes/resumen_variedad.csv
```

## Volumen

El análisis de Volumen calcula directamente sobre el dataset actual:

- cantidad de registros y columnas;
- tamaño del CSV serializado en disco;
- memoria profunda utilizada por el DataFrame;
- bytes promedio por fila en disco y en memoria;
- factor de expansión entre el archivo y su representación en pandas.

El tamaño del archivo serializado en disco no equivale necesariamente a la
cantidad de RAM requerida para procesarlo. Los tipos internos de pandas, el
índice y especialmente las cadenas de texto pueden aumentar el consumo en
memoria.

### Benchmarks locales

La carga se mide sobre varias cantidades de filas y sobre el dataset completo.
Se realiza una lectura breve de calentamiento y luego tres repeticiones por
tamaño; el reporte conserva mediana, mínimo, máximo, throughput y memoria. Las
operaciones `isna().sum()`, `duplicated().sum()`, `nunique()` y `describe()`
también se miden tres veces de manera independiente.

Los benchmarks dependen del equipo donde se ejecuta el proyecto. Además, la
caché del sistema operativo puede acelerar lecturas posteriores, por lo que
estas cifras muestran el comportamiento aproximado en el equipo local y no
constituyen un benchmark científico universal del almacenamiento físico.

Los reportes medidos son:

```text
outputs/reportes/benchmark_carga.csv
outputs/reportes/benchmark_operaciones.csv
```

### Proyección de escalabilidad

Se proyectan escalas desde x1 hasta x1,000,000 manteniendo fija la estructura
y el número de columnas. Solo crece matemáticamente la cantidad de registros,
el almacenamiento, la memoria y una estimación lineal del tiempo basada en la
mediana de carga completa.

No se concatenan DataFrames ni se crean archivos ampliados. Esto evita usar
grandes cantidades de RAM o almacenamiento solo para una demostración.

```text
outputs/reportes/proyeccion_escalabilidad.csv
```

Las proyecciones representan estimaciones matemáticas y no mediciones de
infraestructura real de Spotify. La estimación temporal tampoco implica que
el rendimiento real vaya a crecer de manera perfectamente lineal.

## Velocidad

La V de Velocidad describe la rapidez con la que los datos llegan y deben ser
procesados. El CSV original contiene características y metadatos de canciones,
pero no eventos de reproducción, timestamps de usuarios ni un flujo en tiempo
real. Por ello, esta etapa utiliza una simulación local simplificada.

Cada evento tiene exactamente esta estructura:

```text
timestamp   datetime sintético, desde 2025-01-01 UTC
user_id     identificador de usuario sintético
track_id    identificador real extraído del CSV
evento      play, pause, skip, like o add_to_playlist
```

La generación utiliza la semilla fija `42` y las siguientes probabilidades,
elegidas únicamente para la demostración:

```text
play             45%
pause            15%
skip             25%
like             10%
add_to_playlist   5%
```

`generar_eventos()` es un generador de Python: produce un evento, lo entrega
al procesador y continúa con el siguiente. El programa no crea una lista con
todo el flujo. Solo conserva contadores de tipos y conjuntos pequeños de
usuarios y canciones observados.

El benchmark mide conjuntamente generación y procesamiento para 10,000,
50,000, 100,000, 250,000 y 500,000 eventos, con tres repeticiones por tamaño.
La escala de un millón se omite para mantener razonable la duración total de
la exposición. Los reportes agregados son:

```text
outputs/reportes/benchmark_velocidad.csv
outputs/reportes/resumen_eventos.csv
```

Conceptualmente, un proceso **batch** acumula datos y los procesa después. En
esta simulación tipo **streaming**, cada evento se procesa conforme el
generador lo produce. Esto no constituye un sistema distribuido real ni una
conexión en tiempo real con Spotify.

> Los eventos, usuarios, timestamps y probabilidades utilizados en esta
> sección son sintéticos y se generan exclusivamente con fines académicos. Los
> resultados no representan métricas de la infraestructura real de Spotify.

## Conservación de los datos

En estas etapas no se modifica ni limpia el dataset original. No se rellenan
faltantes, no se eliminan duplicados, no se corrigen valores sospechosos y no
se descartan outliers. Tampoco se generan físicamente datasets escalados. Todos
los resultados derivados se guardan fuera de `data/`. La simulación de
Velocidad tampoco modifica el CSV ni guarda eventos individuales.
