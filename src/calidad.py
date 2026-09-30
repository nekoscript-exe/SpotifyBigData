"""Análisis de veracidad y calidad sin modificar el dataset original."""

from collections import Counter
from pathlib import Path
from typing import Any, TypedDict

import pandas as pd

from src.diagnostico import contar_filas_duplicadas, obtener_valores_faltantes


COLUMNAS_NORMALIZADAS = (
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
)
COLUMNAS_CONTEXTO_TRACK = ("track_genre", "album_name", "artists", "track_name")
COLUMNAS_OUTLIERS = ("duration_ms", "tempo", "loudness")


class ResumenFaltantes(TypedDict):
    """Totales de completitud del dataset."""

    valores_faltantes: int
    filas_con_faltantes: int


class ResumenDuplicados(TypedDict):
    """Métricas de filas completamente duplicadas."""

    filas_duplicadas: int
    porcentaje_duplicadas: float
    grupos_duplicados: int
    filas_en_grupos_duplicados: int


class ResumenTrackIds(TypedDict):
    """Métricas de repetición y variación de track_id."""

    track_ids_unicos: int
    track_ids_faltantes: int
    track_ids_repetidos: int
    porcentaje_ids_repetidos: float
    frecuencia_maxima: int
    filas_con_track_id_repetido: int
    ids_con_generos_distintos: int
    ids_con_albumes_distintos: int
    ids_con_artistas_distintos: int
    ids_con_nombres_distintos: int
    ids_con_popularidad_distinta: int
    ids_con_filas_distintas: int


def _validar_columnas(dataframe: pd.DataFrame, columnas: tuple[str, ...]) -> None:
    """Comprueba que existan las columnas necesarias para un análisis."""
    faltantes = [columna for columna in columnas if columna not in dataframe.columns]
    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias para el análisis de calidad: "
            + ", ".join(faltantes)
        )


def _mascara_filas_con_faltantes(dataframe: pd.DataFrame):
    """Obtiene una máscara booleana inequívoca para las filas incompletas."""
    return dataframe.isna().to_numpy().any(axis=1)


def crear_reporte_calidad_columnas(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Resume completitud, tipo y cardinalidad de cada columna."""
    faltantes = obtener_valores_faltantes(dataframe)
    total_filas = len(dataframe)
    valores_unicos = dataframe.nunique(dropna=True)
    porcentaje_unicidad = (
        valores_unicos.div(total_filas).mul(100)
        if total_filas
        else valores_unicos.astype(float)
    )

    return pd.DataFrame(
        {
            "columna": dataframe.columns,
            "tipo": dataframe.dtypes.astype(str).to_numpy(),
            "valores_totales": total_filas,
            "valores_no_nulos": dataframe.notna().sum().to_numpy(),
            "valores_faltantes": faltantes["faltantes"].to_numpy(),
            "porcentaje_faltantes": faltantes["porcentaje"].to_numpy(),
            "valores_unicos": valores_unicos.to_numpy(),
            "porcentaje_unicidad": porcentaje_unicidad.to_numpy(),
        }
    )


def resumir_valores_faltantes(dataframe: pd.DataFrame) -> ResumenFaltantes:
    """Calcula totales de celdas faltantes y filas afectadas."""
    faltantes = obtener_valores_faltantes(dataframe)
    return {
        "valores_faltantes": int(faltantes["faltantes"].sum()),
        "filas_con_faltantes": int(_mascara_filas_con_faltantes(dataframe).sum()),
    }


def obtener_filas_con_faltantes(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Devuelve las filas afectadas, conservando su índice original."""
    mascara = _mascara_filas_con_faltantes(dataframe)
    filas = dataframe.loc[mascara].copy()
    filas.insert(0, "indice_original", filas.index)
    return filas.reset_index(drop=True)


def analizar_duplicados_exactos(
    dataframe: pd.DataFrame,
) -> tuple[ResumenDuplicados, pd.DataFrame]:
    """Resume duplicados exactos y devuelve todas las filas involucradas."""
    cantidad_duplicados = contar_filas_duplicadas(dataframe)
    mascara = dataframe.duplicated(keep=False)
    filas = dataframe.loc[mascara].copy()

    if filas.empty:
        reporte = pd.DataFrame(
            columns=["grupo_duplicado", "apariciones_grupo", "indice_original"]
            + dataframe.columns.tolist()
        )
        cantidad_grupos = 0
    else:
        grupos = filas.groupby(
            dataframe.columns.tolist(), dropna=False, sort=False
        ).ngroup()
        apariciones = grupos.map(grupos.value_counts())
        filas.insert(0, "indice_original", filas.index)
        filas.insert(0, "apariciones_grupo", apariciones.to_numpy())
        filas.insert(
            0,
            "grupo_duplicado",
            [f"DUP-{grupo + 1:04d}" for grupo in grupos],
        )
        reporte = filas.reset_index(drop=True)
        cantidad_grupos = int(grupos.nunique())

    resumen: ResumenDuplicados = {
        "filas_duplicadas": cantidad_duplicados,
        "porcentaje_duplicadas": (
            cantidad_duplicados / len(dataframe) * 100 if len(dataframe) else 0.0
        ),
        "grupos_duplicados": cantidad_grupos,
        "filas_en_grupos_duplicados": int(mascara.sum()),
    }
    return resumen, reporte


def analizar_track_ids_repetidos(
    dataframe: pd.DataFrame,
) -> tuple[ResumenTrackIds, pd.DataFrame]:
    """Analiza IDs repetidos sin confundirlos con duplicados exactos."""
    columnas_necesarias = ("track_id",) + COLUMNAS_CONTEXTO_TRACK + ("popularity",)
    _validar_columnas(dataframe, columnas_necesarias)

    frecuencias = Counter(dataframe["track_id"].dropna().tolist())
    frecuencias_repetidas = {
        track_id: frecuencia
        for track_id, frecuencia in frecuencias.items()
        if frecuencia > 1
    }
    filas_repetidas = dataframe[
        dataframe["track_id"].isin(list(frecuencias_repetidas))
    ]

    if filas_repetidas.empty:
        reporte = pd.DataFrame(
            columns=[
                "track_id",
                "apariciones",
                "filas_distintas_completas",
                "generos_unicos",
                "albumes_unicos",
                "artistas_unicos",
                "nombres_unicos",
                "popularidades_unicas",
                "generos_observados",
            ]
        )
    else:
        grupos = filas_repetidas.groupby("track_id", sort=False, dropna=False)
        apariciones = grupos.size()
        if not isinstance(apariciones, pd.Series):
            raise TypeError("Se esperaba una Serie con las apariciones por track_id.")
        reporte = apariciones.to_frame(name="apariciones")
        reporte["filas_distintas_completas"] = (
            filas_repetidas.drop_duplicates().groupby("track_id", dropna=False).size()
        )

        nombres_conteos = {
            "track_genre": "generos_unicos",
            "album_name": "albumes_unicos",
            "artists": "artistas_unicos",
            "track_name": "nombres_unicos",
            "popularity": "popularidades_unicas",
        }
        for columna, nombre_salida in nombres_conteos.items():
            reporte[nombre_salida] = grupos[columna].nunique(dropna=False)

        reporte["artista"] = grupos["artists"].first()
        reporte["album"] = grupos["album_name"].first()
        reporte["cancion"] = grupos["track_name"].first()
        reporte["generos_observados"] = grupos["track_genre"].agg(
            lambda serie: " | ".join(sorted({str(valor) for valor in serie.dropna()}))
        )
        reporte = (
            reporte.reset_index()
            .sort_values(["apariciones", "track_id"], ascending=[False, True])
            .reset_index(drop=True)
        )

    ids_unicos = int(dataframe["track_id"].nunique(dropna=True))
    cantidad_ids_repetidos = len(reporte)
    resumen: ResumenTrackIds = {
        "track_ids_unicos": ids_unicos,
        "track_ids_faltantes": int(dataframe["track_id"].isna().sum()),
        "track_ids_repetidos": cantidad_ids_repetidos,
        "porcentaje_ids_repetidos": (
            cantidad_ids_repetidos / ids_unicos * 100 if ids_unicos else 0.0
        ),
        "frecuencia_maxima": max(frecuencias_repetidas.values(), default=0),
        "filas_con_track_id_repetido": sum(frecuencias_repetidas.values()),
        "ids_con_generos_distintos": int(reporte["generos_unicos"].gt(1).sum()),
        "ids_con_albumes_distintos": int(reporte["albumes_unicos"].gt(1).sum()),
        "ids_con_artistas_distintos": int(reporte["artistas_unicos"].gt(1).sum()),
        "ids_con_nombres_distintos": int(reporte["nombres_unicos"].gt(1).sum()),
        "ids_con_popularidad_distinta": int(
            reporte["popularidades_unicas"].gt(1).sum()
        ),
        "ids_con_filas_distintas": int(
            reporte["filas_distintas_completas"].gt(1).sum()
        ),
    }
    return resumen, reporte


def analizar_consistencia_variables(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aplica reglas razonables y reporta incumplimientos sin corregirlos."""
    columnas = (
        "popularity",
        *COLUMNAS_NORMALIZADAS,
        "duration_ms",
        "tempo",
        "time_signature",
        "mode",
        "key",
    )
    _validar_columnas(dataframe, columnas)
    resultados: list[dict[str, Any]] = []

    def agregar_resultado(
        columna: str,
        criterio: str,
        mascara: pd.Series,
        ceros: int | None = None,
        negativos: int | None = None,
    ) -> None:
        serie = dataframe[columna]
        cantidad = int(mascara.sum())
        resultados.append(
            {
                "columna": columna,
                "criterio_revisado": criterio,
                "valores_sospechosos": cantidad,
                "porcentaje": cantidad / len(dataframe) * 100 if len(dataframe) else 0.0,
                "ceros": ceros,
                "negativos": negativos,
                "minimo_observado": serie.min(),
                "maximo_observado": serie.max(),
            }
        )

    popularidad = dataframe["popularity"]
    agregar_resultado(
        "popularity",
        "fuera de [0, 100]",
        popularidad.notna() & ~popularidad.between(0, 100),
    )

    for columna in COLUMNAS_NORMALIZADAS:
        serie = dataframe[columna]
        agregar_resultado(
            columna,
            "fuera de [0, 1]",
            serie.notna() & ~serie.between(0, 1),
        )

    for columna in ("duration_ms", "tempo", "time_signature"):
        serie = dataframe[columna]
        agregar_resultado(
            columna,
            "menor o igual que 0",
            serie.notna() & serie.le(0),
            ceros=int(serie.eq(0).sum()),
            negativos=int(serie.lt(0).sum()),
        )

    return pd.DataFrame(resultados)


def obtener_distribuciones_consistencia(
    dataframe: pd.DataFrame,
) -> dict[str, pd.Series]:
    """Obtiene frecuencias para compás, modo y tonalidad musical."""
    columnas = ("time_signature", "mode", "key")
    _validar_columnas(dataframe, columnas)
    return {
        columna: dataframe[columna].value_counts(dropna=False).sort_index()
        for columna in columnas
    }


def analizar_outliers_iqr(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Describe valores atípicos por IQR; no los clasifica como errores."""
    _validar_columnas(dataframe, COLUMNAS_OUTLIERS)
    resultados = []

    for columna in COLUMNAS_OUTLIERS:
        serie = dataframe[columna].dropna()
        q1 = float(serie.quantile(0.25))
        mediana = float(serie.median())
        q3 = float(serie.quantile(0.75))
        iqr = q3 - q1
        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr
        inferiores = int(serie.lt(limite_inferior).sum())
        superiores = int(serie.gt(limite_superior).sum())
        total = inferiores + superiores
        resultados.append(
            {
                "columna": columna,
                "q1": q1,
                "mediana": mediana,
                "q3": q3,
                "iqr": iqr,
                "limite_inferior": limite_inferior,
                "limite_superior": limite_superior,
                "outliers_inferiores": inferiores,
                "outliers_superiores": superiores,
                "total_outliers": total,
                "porcentaje_outliers": total / len(serie) * 100 if len(serie) else 0.0,
            }
        )

    return pd.DataFrame(resultados)


def guardar_reportes_calidad(
    directorio: Path,
    calidad_columnas: pd.DataFrame,
    filas_con_faltantes: pd.DataFrame,
    duplicados_exactos: pd.DataFrame,
    track_ids_repetidos: pd.DataFrame,
) -> dict[str, Path]:
    """Guarda los reportes detallados de calidad en archivos CSV."""
    directorio.mkdir(parents=True, exist_ok=True)
    reportes = {
        "calidad_columnas": directorio / "calidad_columnas.csv",
        "filas_con_faltantes": directorio / "filas_con_faltantes.csv",
        "duplicados_exactos": directorio / "duplicados_exactos.csv",
        "track_ids_repetidos": directorio / "track_ids_repetidos.csv",
    }
    calidad_columnas.to_csv(reportes["calidad_columnas"], index=False)
    filas_con_faltantes.to_csv(reportes["filas_con_faltantes"], index=False)
    duplicados_exactos.to_csv(reportes["duplicados_exactos"], index=False)
    track_ids_repetidos.to_csv(reportes["track_ids_repetidos"], index=False)
    return reportes


def generar_conclusion_veracidad(
    dataframe: pd.DataFrame,
    resumen_faltantes: ResumenFaltantes,
    resumen_duplicados: ResumenDuplicados,
    consistencia: pd.DataFrame,
) -> str:
    """Redacta una conclusión cuantitativa a partir de los resultados."""
    total_celdas = dataframe.size
    faltantes = resumen_faltantes["valores_faltantes"]
    completitud = (1 - faltantes / total_celdas) * 100 if total_celdas else 0.0
    sospechosos = int(consistencia["valores_sospechosos"].sum())
    return (
        f"La completitud observada es de {completitud:.6f}%. Se detectaron "
        f"{faltantes:,} valores faltantes, "
        f"{int(resumen_duplicados['filas_duplicadas']):,} filas duplicadas "
        f"excedentes y {sospechosos:,} valores que incumplen las reglas "
        "revisadas. Deben investigarse antes de un análisis definitivo, sin "
        "asumir que un valor sospechoso o atípico sea necesariamente incorrecto."
    )
