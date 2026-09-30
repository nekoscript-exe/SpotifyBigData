# Guía de exposición — SpotifyBigData

Propuesta para una presentación de **7 a 10 minutos**. La intención es orientar
la explicación, no memorizar un discurso palabra por palabra.

## Recorrido sugerido

### 1. Problema: qué es Big Data — 40 segundos

- **Qué explicar:** Big Data no se define solo por una cantidad fija de filas;
  combina escala, rapidez, diversidad, confiabilidad y utilidad.
- **Qué mostrar:** la tabla de las cinco V del README.
- **Transición:** “Para aterrizar estos conceptos usamos un caso cotidiano: un
  catálogo musical relacionado con Spotify”.

### 2. Caso Spotify — 35 segundos

- **Qué explicar:** una plataforma musical combina catálogos, metadatos,
  características acústicas y potenciales flujos de interacción.
- **Aclaración clave:** el proyecto no reproduce la infraestructura real de
  Spotify ni se conecta a su API.
- **Transición:** “Nuestro punto de partida es una muestra finita en CSV”.

### 3. Dataset — 45 segundos

- **Qué explicar:** 114,000 filas, 20 columnas, 18.53 MB en disco y 48.79 MB
  como DataFrame.
- **Qué mostrar:** sección `[1] INFORMACIÓN GENERAL` de la terminal.
- **Idea clave:** archivo en disco y memoria de procesamiento no son lo mismo.
- **Transición:** “Primero observamos qué ocurre cuando esa base crece”.

### 4. Volumen — 55 segundos

- **Qué explicar:** se midieron disco, RAM y carga local; después se hicieron
  proyecciones sin crear físicamente datasets gigantes.
- **Qué mostrar:** `01_proyeccion_volumen.png`.
- **Aclaración clave:** x1 parte de una medición; x10 en adelante son
  estimaciones matemáticas.
- **Transición:** “La escala no solo ocupa espacio: también importa la rapidez
  con que llegan y se procesan los datos”.

### 5. Velocidad — 55 segundos

- **Qué explicar:** como el CSV no contiene eventos, se usa un generador con
  usuarios y timestamps sintéticos, pero `track_id` reales.
- **Qué mostrar:** `03_velocidad_eventos.png` y la sección `[11]` de terminal.
- **Idea clave:** los eventos se procesan uno a uno, sin guardar el flujo
  completo en una lista.
- **Transición:** “Además de llegar rápido, los datos musicales tienen formatos
  y significados distintos”.

### 6. Variedad — 40 segundos

- **Qué explicar:** existen objetos de texto, enteros, decimales y booleanos;
  semánticamente hay identificadores, categorías, metadatos y métricas.
- **Qué mostrar:** sección `[9] VARIEDAD DE LOS DATOS`.
- **Ejemplo útil:** `key` es entero en pandas, pero categoría musical por
  significado.
- **Transición:** “Tener datos variados no garantiza que sean confiables”.

### 7. Veracidad — 60 segundos

- **Qué explicar:** 3 faltantes, 450 duplicados exactos excedentes, IDs
  repetidos y valores que requieren investigación.
- **Qué mostrar:** `04_calidad_datos.png`.
- **Ideas clave:** ID repetido no equivale a fila duplicada; outlier no equivale
  a error; el proyecto analiza sin limpiar el CSV.
- **Transición:** “Después de entender sus límites, podemos convertir los
  registros en información útil”.

### 8. Valor — 70 segundos

- **Qué explicar:** se creó una vista de 89,741 tracks únicos; `popularity` se
  resume con la mediana y los géneros mantienen una relación muchos-a-muchos.
- **Qué mostrar:** `05_generos_popularidad.png` y
  `07_correlaciones_popularidad.png`.
- **Hallazgos útiles:** comparación por géneros, contenido explicit,
  correlaciones y perfil del cuartil superior.
- **Aclaración clave:** correlación no implica causalidad y los resultados solo
  describen este dataset.
- **Transición:** “Las visualizaciones permiten comunicar estas diferencias sin
  convertir la terminal en una tabla interminable”.

### 9. Visualizaciones — 40 segundos

- **Qué explicar:** se generan ocho PNG no interactivos a partir de DataFrames
  ya calculados; no se duplican los análisis.
- **Qué mostrar:** una vista rápida de las figuras 01, 03, 04, 05 y 07.
- **Idea clave:** cada gráfica identifica si usa medición, simulación,
  proyección o análisis descriptivo.
- **Transición:** “Con esto cubrimos las cinco V manteniendo claras las
  limitaciones de la evidencia”.

### 10. Conclusión — 35 segundos

- **Qué explicar:** el proyecto transforma un CSV en diagnóstico, evidencia
  sobre las cinco V, hallazgos, reportes y material presentable.
- **Cierre sugerido:** destacar que el valor académico está en aplicar y
  diferenciar correctamente los conceptos, no en afirmar que 114,000 filas son
  por sí solas Big Data.

## Demo técnica

Desde la raíz del repositorio:

```bash
source .venv/bin/activate
python main.py
```

Durante la ejecución, señalar brevemente:

1. dimensiones y diferencia entre disco y RAM;
2. faltantes, duplicados y repetición de `track_id`;
3. benchmark y proyección de Volumen;
4. aviso de que los eventos de Velocidad son sintéticos;
5. resumen de Valor basado en tracks únicos;
6. confirmación de los ocho PNG generados.

La ejecución ronda 11 segundos en el equipo de desarrollo. Conviene tener
abiertas con anticipación estas figuras:

```text
outputs/graficas/01_proyeccion_volumen.png
outputs/graficas/03_velocidad_eventos.png
outputs/graficas/04_calidad_datos.png
outputs/graficas/05_generos_popularidad.png
outputs/graficas/07_correlaciones_popularidad.png
```

Como respaldo técnico, tener disponibles:

```text
outputs/reportes/resumen_visualizaciones.csv
outputs/reportes/track_ids_repetidos.csv
outputs/reportes/analisis_generos.csv
outputs/reportes/correlaciones_popularidad.csv
```

No es necesario recorrer cada línea de terminal ni abrir los 19 reportes. La
demo debe conectar una evidencia concreta con cada V.

## Preguntas que podrían hacernos

### ¿Por qué este dataset puede usarse para explicar Big Data si solo pesa unos 18.5 MB?

Porque permite estudiar las cinco V, medir el costo local y razonar sobre
escalabilidad. Es una demostración académica de conceptos, no una afirmación de
que el archivo tenga escala industrial.

### ¿114,000 filas ya son Big Data?

No necesariamente. Big Data depende del contexto, la velocidad, la variedad y
las capacidades de la tecnología disponible, no de un umbral universal de
filas.

### ¿Por qué hicieron una simulación para Velocidad?

El CSV contiene tracks y atributos, pero no eventos ni timestamps de usuarios.
Inventar que eran datos reales habría sido incorrecto; por eso se creó un flujo
sintético reproducible y claramente etiquetado.

### ¿Las proyecciones x1,000 son mediciones reales?

No. Solo x1 parte del dataset medido. Las escalas superiores multiplican las
métricas base bajo el supuesto simplificado de conservar la misma estructura y
el mismo costo por fila.

### ¿Por qué un `track_id` puede aparecer varias veces?

Principalmente porque una canción puede estar asociada a varios géneros. Por
eso se distingue un ID repetido de una fila completamente duplicada.

### ¿Por qué `popularity` tiene valores decimales en algunos reportes?

Algunos IDs repetidos contienen valores distintos. La vista analítica usa la
mediana por `track_id`; con dos valores centrales, la mediana puede terminar en
`.5`.

### ¿Una correlación significa causalidad?

No. Pearson describe una asociación lineal dentro de esta muestra. No prueba
que un atributo musical cause un cambio en popularidad.

### ¿Por qué pandas dejaría de ser suficiente a una escala mucho mayor?

pandas procesa principalmente en la memoria de una sola máquina. Si los datos
superan esa memoria o exigen procesamiento distribuido y continuo, se requieren
otras estrategias de almacenamiento y cómputo.

### ¿Qué diferencia hay entre un outlier y un dato incorrecto?

Un outlier es un valor estadísticamente alejado del resto. Puede ser legítimo;
solo el contexto o una regla de negocio permite determinar si es incorrecto.

### ¿Qué aporta realmente el análisis de Valor?

Convierte registros en información interpretable: rankings internos,
comparaciones por género, diferencias entre grupos, asociaciones y perfiles.
Puede orientar nuevas preguntas o decisiones, sin convertir los resultados en
predicciones ni afirmaciones causales.
