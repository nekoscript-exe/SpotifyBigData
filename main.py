"""Punto de entrada para el diagnóstico de SpotifyBigData."""

from collections.abc import Hashable
from numbers import Real
from time import perf_counter

import pandas as pd

from src.calidad import (
    COLUMNAS_NORMALIZADAS,
    ResumenDuplicados,
    ResumenFaltantes,
    ResumenTrackIds,
    analizar_consistencia_variables,
    analizar_duplicados_exactos,
    analizar_outliers_iqr,
    analizar_track_ids_repetidos,
    crear_reporte_calidad_columnas,
    generar_conclusion_veracidad,
    guardar_reportes_calidad,
    obtener_distribuciones_consistencia,
    obtener_filas_con_faltantes,
    resumir_valores_faltantes,
)
from src.carga import RAIZ_PROYECTO, cargar_dataset
from src.diagnostico import (
    contar_filas_duplicadas,
    formatear_tamano,
    obtener_estadisticas_descriptivas,
    obtener_informacion_general,
    obtener_nombres_variables,
    obtener_primeros_registros,
    obtener_tipos_datos,
    obtener_valores_faltantes,
)
from src.variedad import (
    InformacionEspecial,
    crear_resumen_variedad,
    generar_conclusion_variedad,
    guardar_reporte_variedad,
    obtener_informacion_especial,
    resumir_tipos_tecnicos,
)
from src.rendimiento import (
    ejecutar_benchmark_carga,
    ejecutar_benchmark_operaciones,
    guardar_reportes_rendimiento,
)
from src.volumen import (
    VolumenActual,
    analizar_volumen_actual,
    crear_proyeccion_escalabilidad,
    generar_conclusion_volumen,
    guardar_proyeccion_escalabilidad,
)
from src.velocidad import (
    CANTIDAD_EVENTOS_RESUMEN,
    CANTIDAD_USUARIOS,
    PROBABILIDADES_EVENTO,
    TIPOS_EVENTO,
    MedicionVelocidad,
    ResumenFlujo,
    crear_resumen_eventos,
    ejecutar_benchmark_velocidad,
    generar_conclusion_velocidad,
    guardar_reportes_velocidad,
    obtener_track_ids_reales,
)


ANCHO = 72


def imprimir_titulo(texto: str) -> None:
    """Imprime un encabezado de sección uniforme."""
    print(f"\n{texto}")
    print("-" * ANCHO)


def convertir_numero(valor: object, contexto: str) -> float:
    """Valida y convierte un escalar numérico nativo o de NumPy."""
    if not isinstance(valor, Real):
        raise ValueError(f"Se esperaba un número en {contexto}; se recibió {valor!r}.")
    return float(valor)


def convertir_entero(valor: object, contexto: str) -> int:
    """Valida que un escalar numérico represente un entero."""
    numero = convertir_numero(valor, contexto)
    if not numero.is_integer():
        raise ValueError(f"Se esperaba un entero en {contexto}; se recibió {numero}.")
    return int(numero)


def obtener_numero_celda(
    dataframe: pd.DataFrame, fila: Hashable, columna: str
) -> float:
    """Extrae explícitamente una única celda numérica mediante DataFrame.at."""
    return convertir_numero(dataframe.at[fila, columna], f"{fila!r}/{columna}")


def obtener_entero_celda(
    dataframe: pd.DataFrame, fila: Hashable, columna: str
) -> int:
    """Extrae una única celda y comprueba que represente un entero."""
    return convertir_entero(dataframe.at[fila, columna], f"{fila!r}/{columna}")


def formatear_frecuencias(frecuencias: pd.Series) -> str:
    """Convierte una distribución corta en texto para la terminal."""
    return ", ".join(
        f"{valor}: {convertir_entero(cantidad, f'frecuencia de {valor!r}'):,}"
        for valor, cantidad in frecuencias.items()
    )


def imprimir_veracidad(
    dataframe: pd.DataFrame,
    resumen_faltantes: ResumenFaltantes,
    resumen_duplicados: ResumenDuplicados,
    resumen_track_ids: ResumenTrackIds,
    track_ids_repetidos: pd.DataFrame,
    consistencia: pd.DataFrame,
    distribuciones: dict[str, pd.Series],
    outliers: pd.DataFrame,
) -> None:
    """Presenta un resumen del análisis de veracidad."""
    imprimir_titulo("[8] VERACIDAD DE LOS DATOS")
    print(f"Valores faltantes:              {resumen_faltantes['valores_faltantes']:,}")
    print(f"Filas con algún faltante:       {resumen_faltantes['filas_con_faltantes']:,}")
    print(
        "Duplicados exactos excedentes:  "
        f"{resumen_duplicados['filas_duplicadas']:,} "
        f"({resumen_duplicados['porcentaje_duplicadas']:.4f}%)"
    )
    print(
        "Grupos de duplicados exactos:  "
        f"{resumen_duplicados['grupos_duplicados']:,} "
        f"({resumen_duplicados['filas_en_grupos_duplicados']:,} filas implicadas)"
    )
    print(f"track_id únicos:                {resumen_track_ids['track_ids_unicos']:,}")
    print(f"track_id repetidos:             {resumen_track_ids['track_ids_repetidos']:,}")
    print(f"Frecuencia máxima de un ID:     {resumen_track_ids['frecuencia_maxima']:,}")
    print(
        "IDs repetidos con varios géneros: "
        f"{resumen_track_ids['ids_con_generos_distintos']:,}"
    )
    print(
        "IDs repetidos con distinto álbum/artista/nombre: "
        f"{resumen_track_ids['ids_con_albumes_distintos']:,}/"
        f"{resumen_track_ids['ids_con_artistas_distintos']:,}/"
        f"{resumen_track_ids['ids_con_nombres_distintos']:,}"
    )
    print(
        "IDs repetidos con distinta popularidad: "
        f"{resumen_track_ids['ids_con_popularidad_distinta']:,}"
    )

    print("\nEjemplos de track_id con mayor frecuencia:")
    if track_ids_repetidos.empty:
        print("No se encontraron track_id repetidos.")
    else:
        print(
            track_ids_repetidos[
                ["track_id", "apariciones", "generos_unicos", "popularidades_unicas"]
            ]
            .head(5)
            .to_string(index=False)
        )

    consistencia_indice = consistencia.set_index("columna")
    normalizadas_fuera = sum(
        obtener_entero_celda(
            consistencia_indice, columna, "valores_sospechosos"
        )
        for columna in COLUMNAS_NORMALIZADAS
    )
    print("\nValores potencialmente sospechosos:")
    print(
        "popularity fuera de [0, 100]:  "
        f"{obtener_entero_celda(consistencia_indice, 'popularity', 'valores_sospechosos'):,}"
    )
    print(f"Variables normalizadas fuera de [0, 1]: {normalizadas_fuera:,}")
    for columna in ("duration_ms", "tempo", "time_signature"):
        print(
            f"{columna} <= 0: "
            f"{obtener_entero_celda(consistencia_indice, columna, 'valores_sospechosos'):,} "
            f"(ceros: {obtener_entero_celda(consistencia_indice, columna, 'ceros'):,}; "
            f"negativos: {obtener_entero_celda(consistencia_indice, columna, 'negativos'):,})"
        )

    print("\nDistribuciones de consistencia:")
    print(f"time_signature -> {formatear_frecuencias(distribuciones['time_signature'])}")
    print(f"mode -> {formatear_frecuencias(distribuciones['mode'])}")
    print(
        f"key -> rango {dataframe['key'].min()} a {dataframe['key'].max()}; "
        f"{formatear_frecuencias(distribuciones['key'])}"
    )

    print("\nOutliers informativos por método IQR:")
    columnas_outliers = [
        "columna",
        "q1",
        "mediana",
        "q3",
        "iqr",
        "limite_inferior",
        "limite_superior",
        "total_outliers",
    ]
    print(
        outliers[columnas_outliers].to_string(index=False, float_format="%.3f")
    )
    print("\nValor atípico != dato incorrecto.")
    print("\nConclusión — VERACIDAD")
    print(
        generar_conclusion_veracidad(
            dataframe, resumen_faltantes, resumen_duplicados, consistencia
        )
    )


def imprimir_variedad(
    tipos_tecnicos: pd.DataFrame,
    resumen_variedad: pd.DataFrame,
    informacion_especial: InformacionEspecial,
) -> None:
    """Presenta un resumen del análisis de variedad."""
    imprimir_titulo("[9] VARIEDAD DE LOS DATOS")
    conteos = {
        str(tipo): convertir_entero(cantidad, f"cantidad de columnas {tipo!r}")
        for tipo, cantidad in tipos_tecnicos[
            ["tipo_tecnico", "cantidad_columnas"]
        ].itertuples(index=False, name=None)
    }
    print(f"Texto/object: {conteos.get('object', 0):,}")
    print(f"Enteros:      {conteos.get('int', 0):,}")
    print(f"Decimales:    {conteos.get('float', 0):,}")
    print(f"Booleanos:    {conteos.get('bool', 0):,}")

    print("\nClasificación semántica:")
    for categoria, grupo in resumen_variedad.groupby("categoria_semantica", sort=False):
        print(f"{categoria}: {', '.join(grupo['columna'])}")

    print("\nCardinalidades relevantes:")
    print(f"Géneros:             {informacion_especial['generos']:,}")
    print(f"Artistas:            {informacion_especial['artistas']:,}")
    print(f"Álbumes:             {informacion_especial['albumes']:,}")
    print(f"Nombres de canción:  {informacion_especial['canciones']:,}")
    print(f"track_id diferentes: {informacion_especial['track_ids']:,}")
    print(f"explicit -> {formatear_frecuencias(informacion_especial['explicit'])}")
    print(f"mode -> {formatear_frecuencias(informacion_especial['mode'])}")
    print(
        "time_signature -> "
        f"{formatear_frecuencias(informacion_especial['time_signature'])}"
    )

    print("\nConclusión — VARIEDAD")
    print(generar_conclusion_variedad(tipos_tecnicos, resumen_variedad))


def imprimir_volumen(
    volumen_actual: VolumenActual,
    benchmark_carga: pd.DataFrame,
    benchmark_operaciones: pd.DataFrame,
    proyeccion: pd.DataFrame,
) -> None:
    """Presenta mediciones reales y proyecciones de volumen por separado."""
    imprimir_titulo("[10] VOLUMEN, RENDIMIENTO Y ESCALABILIDAD")
    print("MEDICIÓN REAL DEL DATASET ACTUAL")
    print(f"Registros:                    {volumen_actual['registros']:,}")
    print(f"Columnas:                     {volumen_actual['columnas']:,}")
    print(
        "Tamaño serializado en disco:  "
        f"{formatear_tamano(volumen_actual['almacenamiento_bytes'])}"
    )
    print(
        "Memoria profunda DataFrame:   "
        f"{formatear_tamano(volumen_actual['memoria_bytes'])}"
    )
    print(
        "Bytes promedio/fila en disco: "
        f"{volumen_actual['bytes_por_fila_disco']:,.2f} B"
    )
    print(
        "Bytes promedio/fila en RAM:   "
        f"{volumen_actual['bytes_por_fila_memoria']:,.2f} B"
    )
    print(
        "Factor disco -> memoria:      "
        f"{volumen_actual['factor_expansion_memoria']:.4f}x"
    )
    print(
        "El tamaño del archivo serializado en disco no representa necesariamente "
        "la RAM necesaria durante el procesamiento."
    )

    print("\nBENCHMARK LOCAL DE CARGA — MEDICIÓN EXPERIMENTAL")
    columnas_carga = [
        "filas_cargadas",
        "tiempo_mediano_segundos",
        "filas_por_segundo",
        "memoria_legible",
    ]
    for filas, tiempo, throughput, memoria in benchmark_carga[
        columnas_carga
    ].itertuples(index=False, name=None):
        print(
            f"{filas:>9,} filas | mediana {tiempo:.6f} s "
            f"| {throughput:,.0f} filas/s | {memoria}"
        )
    print(
        "Una lectura breve de calentamiento precede a 3 mediciones por tamaño. "
        "La caché del sistema operativo puede influir; no es un benchmark "
        "universal del disco."
    )

    print("\nBENCHMARK LOCAL DE OPERACIONES — MEDICIÓN EXPERIMENTAL")
    columnas_operaciones = [
        "operacion",
        "tiempo_mediano_segundos",
        "tiempo_minimo_segundos",
        "tiempo_maximo_segundos",
    ]
    for operacion, mediana, minimo, maximo in benchmark_operaciones[
        columnas_operaciones
    ].itertuples(index=False, name=None):
        print(
            f"{operacion:<20} | mediana {mediana:.6f} s "
            f"| mín. {minimo:.6f} s | máx. {maximo:.6f} s"
        )

    print("\nPROYECCIÓN MATEMÁTICA — NO SE CREARON DATASETS AMPLIADOS")
    columnas = [
        "escala",
        "registros_estimados",
        "almacenamiento_legible",
        "memoria_legible",
        "tiempo_estimado_lineal_legible",
    ]
    proyeccion_mostrable = pd.DataFrame(
        {
            "Escala": proyeccion["escala"],
            "Registros": proyeccion["registros_estimados"],
            "Disco estimado": proyeccion["almacenamiento_legible"],
            "RAM estimada": proyeccion["memoria_legible"],
            "Tiempo lineal estimado": proyeccion[
                "tiempo_estimado_lineal_legible"
            ],
        }
    )
    print(proyeccion_mostrable.to_string(index=False))
    print(
        "Las columnas permanecen constantes. El tiempo es una extrapolación "
        "lineal basada en la mediana medida para el dataset completo; el "
        "comportamiento real no tiene por qué ser perfectamente lineal."
    )

    print("\nConclusión — VOLUMEN")
    print(generar_conclusion_volumen(volumen_actual, proyeccion))


def imprimir_velocidad(
    benchmark: pd.DataFrame,
    medicion_representativa: MedicionVelocidad,
    resumen: ResumenFlujo,
) -> None:
    """Presenta el benchmark y la distribución sintética sin eventos individuales."""
    imprimir_titulo("[11] VELOCIDAD — SIMULACIÓN DE EVENTOS")
    print("AVISO: todos los eventos, usuarios y timestamps son sintéticos.")
    print("No proceden de Spotify ni representan su infraestructura real.")

    print("\nBENCHMARK LOCAL — GENERACIÓN + PROCESAMIENTO PROGRESIVO")
    columnas = [
        "eventos",
        "tiempo_mediano_segundos",
        "tiempo_minimo_segundos",
        "tiempo_maximo_segundos",
        "eventos_por_segundo",
        "microsegundos_por_evento",
    ]
    for valores in benchmark[columnas].itertuples(index=False, name=None):
        eventos = convertir_entero(valores[0], "eventos del benchmark")
        mediana = convertir_numero(valores[1], "mediana del benchmark")
        minimo = convertir_numero(valores[2], "mínimo del benchmark")
        maximo = convertir_numero(valores[3], "máximo del benchmark")
        throughput = convertir_numero(valores[4], "throughput del benchmark")
        microsegundos = convertir_numero(valores[5], "microsegundos por evento")
        print(
            f"{eventos:>9,} eventos | mediana {mediana:.6f} s "
            f"| mín. {minimo:.6f} s | máx. {maximo:.6f} s "
            f"| {throughput:,.0f} eventos/s | {microsegundos:.3f} µs/evento"
        )

    print(f"\nSIMULACIÓN REPRESENTATIVA: {CANTIDAD_EVENTOS_RESUMEN:,} EVENTOS")
    print(
        "Tiempo mediano:             "
        f"{medicion_representativa['tiempo_mediano_segundos']:.6f} s"
    )
    print(
        "Eventos por segundo:        "
        f"{medicion_representativa['eventos_por_segundo']:,.0f}"
    )
    print(
        "Promedio por evento:        "
        f"{medicion_representativa['microsegundos_por_evento']:.3f} µs"
    )
    print(f"Usuarios sintéticos posibles: {CANTIDAD_USUARIOS:,}")
    print(f"Usuarios observados:          {resumen['usuarios_distintos']:,}")
    print(f"Tracks reales utilizados:     {resumen['tracks_distintos']:,}")
    print(f"Evento más frecuente:         {resumen['evento_mas_frecuente']}")

    print("\nTipos y probabilidades definidas para la simulación:")
    for tipo, probabilidad in zip(TIPOS_EVENTO, PROBABILIDADES_EVENTO):
        cantidad = resumen["conteos_por_tipo"][tipo]
        porcentaje = resumen["porcentajes_por_tipo"][tipo]
        print(
            f"{tipo:<16} probabilidad {probabilidad:>6.1%} | "
            f"observados {cantidad:>6,} ({porcentaje:.3f}%)"
        )

    print("\nInterpretación:")
    print(
        "Batch acumula datos antes de procesarlos; esta simulación tipo streaming "
        "procesa cada evento conforme el generador lo produce, sin conservar el "
        "flujo completo. No es un sistema distribuido real de streaming."
    )
    print("\nConclusión — VELOCIDAD")
    print(generar_conclusion_velocidad(medicion_representativa))


def ejecutar_diagnostico() -> None:
    """Carga el CSV y presenta su diagnóstico en la terminal."""
    inicio_programa = perf_counter()
    ruta_csv, dataframe = cargar_dataset()
    informacion = obtener_informacion_general(dataframe, ruta_csv)
    # Se conserva la medición profunda inmediatamente después de la carga.
    # Algunas operaciones de hashing sobre texto pueden materializar cachés
    # internas de Python y cambiar levemente una medición posterior de deep=True.
    volumen_actual = analizar_volumen_actual(dataframe, ruta_csv)

    print("=" * ANCHO)
    print("SPOTIFY BIG DATA".center(ANCHO))
    print("=" * ANCHO)
    print(f"\nDataset: {informacion['dataset']}")

    imprimir_titulo("[1] INFORMACIÓN GENERAL")
    print(f"Registros:          {informacion['registros']:,}")
    print(f"Columnas:           {informacion['columnas']:,}")
    print(f"Dimensiones:        {informacion['dimensiones']}")
    print(
        "Tamaño archivo:     "
        f"{formatear_tamano(informacion['tamano_archivo_bytes'])} "
        f"({informacion['tamano_archivo_bytes']:,} bytes)"
    )
    print(
        "Memoria DataFrame:  "
        f"{formatear_tamano(informacion['memoria_dataframe_bytes'])} "
        f"({informacion['memoria_dataframe_bytes']:,} bytes)"
    )

    imprimir_titulo("[2] VARIABLES DISPONIBLES")
    for numero, variable in enumerate(obtener_nombres_variables(dataframe), start=1):
        print(f"{numero:>2}. {variable}")

    imprimir_titulo("[3] TIPOS DE DATOS")
    print(obtener_tipos_datos(dataframe).to_string())

    imprimir_titulo("[4] VALORES FALTANTES")
    faltantes = obtener_valores_faltantes(dataframe)
    faltantes_mostrables = faltantes.copy()
    faltantes_mostrables["porcentaje"] = faltantes_mostrables["porcentaje"].map(
        lambda valor: f"{valor:.4f}%"
    )
    print(faltantes_mostrables.to_string())
    print(f"\nTotal de valores faltantes: {faltantes['faltantes'].sum():,}")

    imprimir_titulo("[5] DUPLICADOS")
    print(f"Filas completamente duplicadas: {contar_filas_duplicadas(dataframe):,}")

    imprimir_titulo("[6] PRIMEROS CINCO REGISTROS")
    print(obtener_primeros_registros(dataframe).to_string(index=False))

    imprimir_titulo("[7] ESTADÍSTICAS DESCRIPTIVAS (VARIABLES NUMÉRICAS)")
    estadisticas = obtener_estadisticas_descriptivas(dataframe)
    if estadisticas.empty:
        print("No hay variables numéricas para describir.")
    else:
        print(estadisticas.to_string(float_format="%.3f"))

    directorio_reportes = RAIZ_PROYECTO / "outputs" / "reportes"
    calidad_columnas = crear_reporte_calidad_columnas(dataframe)
    resumen_faltantes = resumir_valores_faltantes(dataframe)
    filas_con_faltantes = obtener_filas_con_faltantes(dataframe)
    resumen_duplicados, duplicados_exactos = analizar_duplicados_exactos(dataframe)
    resumen_track_ids, track_ids_repetidos = analizar_track_ids_repetidos(dataframe)
    consistencia = analizar_consistencia_variables(dataframe)
    distribuciones = obtener_distribuciones_consistencia(dataframe)
    outliers = analizar_outliers_iqr(dataframe)
    guardar_reportes_calidad(
        directorio_reportes,
        calidad_columnas,
        filas_con_faltantes,
        duplicados_exactos,
        track_ids_repetidos,
    )

    imprimir_veracidad(
        dataframe,
        resumen_faltantes,
        resumen_duplicados,
        resumen_track_ids,
        track_ids_repetidos,
        consistencia,
        distribuciones,
        outliers,
    )

    tipos_tecnicos = resumir_tipos_tecnicos(dataframe)
    resumen_variedad = crear_resumen_variedad(dataframe)
    informacion_especial = obtener_informacion_especial(dataframe)
    guardar_reporte_variedad(directorio_reportes, resumen_variedad)
    imprimir_variedad(tipos_tecnicos, resumen_variedad, informacion_especial)

    benchmark_carga = ejecutar_benchmark_carga(
        ruta_csv, volumen_actual["registros"]
    )
    benchmark_operaciones = ejecutar_benchmark_operaciones(dataframe)
    posicion_dataset_completo = convertir_entero(
        benchmark_carga["filas_cargadas"].to_numpy().argmax(),
        "posición del benchmark de carga completa",
    )
    tiempo_carga_completa = convertir_numero(
        benchmark_carga["tiempo_mediano_segundos"].to_numpy()[
            posicion_dataset_completo
        ],
        "tiempo del benchmark de carga completa",
    )
    proyeccion = crear_proyeccion_escalabilidad(
        volumen_actual,
        tiempo_carga_completa,
    )
    guardar_reportes_rendimiento(
        directorio_reportes, benchmark_carga, benchmark_operaciones
    )
    guardar_proyeccion_escalabilidad(directorio_reportes, proyeccion)
    imprimir_volumen(
        volumen_actual, benchmark_carga, benchmark_operaciones, proyeccion
    )

    track_ids_reales = obtener_track_ids_reales(dataframe)
    benchmark_velocidad, mediciones_velocidad, resumen_flujo = (
        ejecutar_benchmark_velocidad(track_ids_reales)
    )
    resumen_eventos = crear_resumen_eventos(resumen_flujo)
    guardar_reportes_velocidad(
        directorio_reportes, benchmark_velocidad, resumen_eventos
    )
    imprimir_velocidad(
        benchmark_velocidad,
        mediciones_velocidad[CANTIDAD_EVENTOS_RESUMEN],
        resumen_flujo,
    )

    print("\nReportes guardados en: outputs/reportes/")
    print(f"Duración aproximada de esta ejecución: {perf_counter() - inicio_programa:.3f} s")

    print("\n" + "=" * ANCHO)


def main() -> None:
    """Ejecuta el programa y presenta errores de entrada de forma clara."""
    try:
        ejecutar_diagnostico()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()
