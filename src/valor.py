"""Análisis descriptivo que transforma el dataset en hallazgos útiles.

Los resultados corresponden únicamente al dataset analizado. No representan
necesariamente el comportamiento actual de Spotify y no implican causalidad.
"""

from math import ceil
from numbers import Real
from pathlib import Path
from typing import Sequence, TypedDict

import pandas as pd


TOP_RESULTADOS = 15
MINIMO_TRACKS_CREDITO = 5
ATRIBUTOS_CORRELACION = (
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
)
ATRIBUTOS_PERFIL = (
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "liveness",
    "speechiness",
    "tempo",
    "duration_ms",
)
ATRIBUTOS_NORMALIZADOS_PERFIL = (
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "liveness",
    "speechiness",
)


class ConsistenciaVistaTracks(TypedDict):
    """Resultado de comprobar la consistencia antes de deduplicar tracks."""

    tracks_unicos: int
    ids_con_popularidad_variable: int
    columnas_estables_verificadas: int


class ResumenValor(TypedDict):
    """Selección de métricas nativas para terminal, hallazgos y conclusión."""

    tracks_unicos: int
    popularidad_media: float
    popularidad_mediana: float
    top_cancion: str
    top_cancion_artistas: str
    top_cancion_popularidad: float
    credito_mas_tracks: str
    credito_mas_tracks_cantidad: int
    credito_mayor_popularidad: str
    credito_mayor_popularidad_mediana: float
    credito_mayor_popularidad_tracks: int
    umbral_tracks_credito: int
    genero_mas_tracks: str
    genero_mas_tracks_cantidad: int
    genero_mayor_popularidad: str
    genero_mayor_popularidad_mediana: float
    genero_mayor_popularidad_tracks: int
    explicit_cantidad: int
    explicit_porcentaje: float
    explicit_popularidad_mediana: float
    no_explicit_cantidad: int
    no_explicit_porcentaje: float
    no_explicit_popularidad_mediana: float
    correlacion_atributo: str
    correlacion_valor: float
    umbral_alta_popularidad: float
    tracks_alta_popularidad: int
    tracks_resto: int
    perfil_atributo_destacado: str
    perfil_mediana_alta: float
    perfil_mediana_resto: float


def _numero(valor: object, contexto: str) -> float:
    """Valida escalares numéricos producidos por pandas o NumPy."""
    if not isinstance(valor, Real):
        raise ValueError(f"Se esperaba un número en {contexto}; se recibió {valor!r}.")
    return float(valor)


def _entero(valor: object, contexto: str) -> int:
    """Valida que un escalar numérico represente un entero."""
    numero = _numero(valor, contexto)
    if not numero.is_integer():
        raise ValueError(f"Se esperaba un entero en {contexto}; se recibió {numero}.")
    return int(numero)


def _texto(valor: object, contexto: str) -> str:
    """Valida un escalar textual extraído de un resultado analítico."""
    if not isinstance(valor, str):
        raise ValueError(f"Se esperaba texto en {contexto}; se recibió {valor!r}.")
    return valor


def _asegurar_dataframe(valor: object, contexto: str) -> pd.DataFrame:
    """Acota resultados amplios de las sobrecargas de pandas."""
    if not isinstance(valor, pd.DataFrame):
        raise TypeError(f"Se esperaba un DataFrame en {contexto}.")
    return valor


def _asegurar_serie(valor: object, contexto: str) -> pd.Series:
    """Acota resultados que necesariamente deben ser una Serie."""
    if not isinstance(valor, pd.Series):
        raise TypeError(f"Se esperaba una Serie en {contexto}.")
    return valor


def _seleccionar_columnas(
    dataframe: pd.DataFrame, columnas: Sequence[str]
) -> pd.DataFrame:
    """Selecciona varias columnas y valida el resultado esperado."""
    resultado = dataframe.loc[:, list(columnas)]
    return _asegurar_dataframe(resultado, "selección de columnas")


def construir_vista_tracks_unicos(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, ConsistenciaVistaTracks]:
    """Construye una fila por track_id tras comprobar columnas supuestamente fijas.

    Los metadatos y atributos constantes se conservan. La popularidad se agrega
    mediante mediana y el género se excluye porque es una relación muchos-a-muchos.
    """
    if "track_id" not in dataframe.columns:
        raise ValueError("El dataset no contiene la columna requerida: track_id")

    datos_validos = dataframe.dropna(subset=["track_id"])
    columnas_estables = [
        columna
        for columna in dataframe.columns
        if columna not in {"track_id", "popularity", "track_genre"}
    ]
    grupos = datos_validos.groupby("track_id", sort=False, dropna=False)
    variaciones: dict[str, int] = {}
    for columna in columnas_estables:
        cantidades = grupos[columna].nunique(dropna=False)
        variaciones[columna] = _entero(
            cantidades.gt(1).to_numpy().sum(),
            f"variaciones de {columna}",
        )

    inconsistentes = [
        columna for columna, cantidad in variaciones.items() if cantidad > 0
    ]
    if inconsistentes:
        raise ValueError(
            "No se puede construir la vista sin definir una estrategia para: "
            + ", ".join(inconsistentes)
        )

    popularidades_distintas = grupos["popularity"].nunique(dropna=False)
    ids_popularidad_variable = _entero(
        popularidades_distintas.gt(1).to_numpy().sum(),
        "track_id con popularidad variable",
    )
    popularidad_mediana_serie = _asegurar_serie(
        grupos["popularity"].median(), "mediana de popularity por track_id"
    )
    popularidad_mediana = popularidad_mediana_serie.to_frame(
        name="popularity"
    ).reset_index()

    columnas_vista = [
        columna for columna in dataframe.columns if columna != "track_genre"
    ]
    vista = _seleccionar_columnas(datos_validos, columnas_vista).drop_duplicates(
        subset="track_id", keep="first"
    )
    vista = vista.drop(columns=["popularity"]).merge(
        popularidad_mediana,
        on="track_id",
        how="left",
        validate="one_to_one",
    )
    orden = [columna for columna in columnas_vista if columna != "popularity"]
    orden.insert(4, "popularity")
    vista = (
        _seleccionar_columnas(vista, orden)
        .sort_values("track_id")
        .reset_index(drop=True)
    )

    consistencia: ConsistenciaVistaTracks = {
        "tracks_unicos": len(vista),
        "ids_con_popularidad_variable": ids_popularidad_variable,
        "columnas_estables_verificadas": len(columnas_estables),
    }
    return vista, consistencia


def crear_resumen_general(vista: pd.DataFrame) -> pd.DataFrame:
    """Crea un panorama compacto de los tracks únicos."""
    metricas = [
        ("tracks_unicos", len(vista), "tracks", "Canciones diferentes por track_id"),
        (
            "creditos_artisticos_unicos",
            vista["artists"].nunique(dropna=True),
            "créditos",
            "Valores textuales distintos de artists, sin dividir colaboraciones",
        ),
        (
            "albumes_unicos",
            vista["album_name"].nunique(dropna=True),
            "álbumes",
            "Álbumes distintos entre los tracks únicos",
        ),
        (
            "popularidad_media",
            vista["popularity"].mean(),
            "puntos",
            "Media de popularity agregada por track_id",
        ),
        (
            "popularidad_mediana",
            vista["popularity"].median(),
            "puntos",
            "Mediana de popularity agregada por track_id",
        ),
        (
            "duracion_media",
            vista["duration_ms"].mean(),
            "ms",
            "Duración media de los tracks únicos",
        ),
        ("tempo_medio", vista["tempo"].mean(), "BPM", "Tempo medio"),
        (
            "porcentaje_explicit",
            vista["explicit"].mean() * 100,
            "%",
            "Porcentaje de tracks marcados como explicit",
        ),
    ]
    for columna in (
        "danceability",
        "energy",
        "valence",
        "acousticness",
        "instrumentalness",
        "liveness",
    ):
        metricas.append(
            (
                f"promedio_{columna}",
                vista[columna].mean(),
                "índice 0-1",
                f"Promedio descriptivo de {columna}",
            )
        )
    return pd.DataFrame(metricas, columns=["metrica", "valor", "unidad", "descripcion"])


def crear_top_canciones(vista: pd.DataFrame) -> pd.DataFrame:
    """Selecciona las canciones con mayor popularity dentro del dataset."""
    columnas = ["track_id", "track_name", "artists", "album_name", "popularity"]
    return (
        _seleccionar_columnas(vista, columnas)
        .sort_values(["popularity", "track_id"], ascending=[False, True])
        .head(TOP_RESULTADOS)
        .reset_index(drop=True)
    )


def crear_top_artistas(vista: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Analiza créditos artísticos textuales sin intentar dividir sus nombres."""
    agregados_resultado = (
        vista.dropna(subset=["artists"])
        .groupby("artists", as_index=False)
        .agg(
            tracks_unicos=("track_id", "nunique"),
            popularidad_media=("popularity", "mean"),
            popularidad_mediana=("popularity", "median"),
        )
    )
    agregados = _asegurar_dataframe(agregados_resultado, "agregación por artists")
    percentil_90 = ceil(
        _numero(agregados["tracks_unicos"].quantile(0.90), "percentil 90 de tracks")
    )
    umbral = max(MINIMO_TRACKS_CREDITO, percentil_90)

    por_cantidad = (
        agregados.sort_values(
            ["tracks_unicos", "popularidad_mediana", "artists"],
            ascending=[False, False, True],
        )
        .head(TOP_RESULTADOS)
        .copy()
    )
    por_cantidad.insert(0, "criterio", "mayor_numero_tracks")

    elegibles = _asegurar_dataframe(
        agregados.loc[agregados["tracks_unicos"].ge(umbral)],
        "créditos elegibles por cantidad de tracks",
    )
    por_popularidad = (
        elegibles
        .sort_values(
            ["popularidad_mediana", "tracks_unicos", "artists"],
            ascending=[False, False, True],
        )
        .head(TOP_RESULTADOS)
        .copy()
    )
    por_popularidad.insert(
        0,
        "criterio",
        f"mayor_popularidad_mediana_min_{umbral}_tracks",
    )
    reporte = pd.concat([por_cantidad, por_popularidad], ignore_index=True)
    reporte["ranking"] = list(range(1, len(por_cantidad) + 1)) + list(
        range(1, len(por_popularidad) + 1)
    )
    reporte["unidad_analisis"] = "crédito artístico textual"
    orden_columnas = [
        "criterio",
        "ranking",
        "unidad_analisis",
        "artists",
        "tracks_unicos",
        "popularidad_media",
        "popularidad_mediana",
    ]
    return _seleccionar_columnas(reporte, orden_columnas), umbral


def crear_analisis_generos(
    dataframe: pd.DataFrame, vista: pd.DataFrame
) -> pd.DataFrame:
    """Agrega asociaciones únicas track_id + género, no filas originales."""
    relaciones = _seleccionar_columnas(
        dataframe, ("track_id", "track_genre")
    ).dropna().drop_duplicates()
    columnas_metricas = [
        "track_id",
        "popularity",
        "danceability",
        "energy",
        "valence",
        "acousticness",
        "tempo",
    ]
    relaciones = relaciones.merge(
        _seleccionar_columnas(vista, columnas_metricas),
        on="track_id",
        how="left",
        validate="many_to_one",
    )
    reporte_agregado = _asegurar_dataframe(
        relaciones.groupby("track_genre", as_index=False).agg(
            tracks_unicos=("track_id", "nunique"),
            popularidad_media=("popularity", "mean"),
            popularidad_mediana=("popularity", "median"),
            danceability_media=("danceability", "mean"),
            energy_media=("energy", "mean"),
            valence_media=("valence", "mean"),
            acousticness_media=("acousticness", "mean"),
            tempo_medio=("tempo", "mean"),
        ),
        "agregación por género",
    )
    reporte = (
        reporte_agregado
        .sort_values(["tracks_unicos", "track_genre"], ascending=[False, True])
        .reset_index(drop=True)
    )
    orden_tracks = reporte["track_genre"].tolist()
    orden_popularidad = reporte.sort_values(
        ["popularidad_mediana", "tracks_unicos", "track_genre"],
        ascending=[False, False, True],
    )["track_genre"].tolist()
    ranking_tracks = pd.DataFrame(
        {
            "track_genre": orden_tracks,
            "ranking_tracks": range(1, len(orden_tracks) + 1),
        }
    )
    ranking_popularidad = pd.DataFrame(
        {
            "track_genre": orden_popularidad,
            "ranking_popularidad_mediana": range(1, len(orden_popularidad) + 1),
        }
    )
    return reporte.merge(ranking_tracks, on="track_genre", validate="one_to_one").merge(
        ranking_popularidad, on="track_genre", validate="one_to_one"
    )


def crear_comparacion_explicit(vista: pd.DataFrame) -> pd.DataFrame:
    """Compara descriptivamente tracks explícitos y no explícitos."""
    reporte_agregado = _asegurar_dataframe(
        vista.groupby("explicit", as_index=False).agg(
            cantidad=("track_id", "size"),
            popularidad_media=("popularity", "mean"),
            popularidad_mediana=("popularity", "median"),
            duracion_media_ms=("duration_ms", "mean"),
            danceability_media=("danceability", "mean"),
            energy_media=("energy", "mean"),
            valence_media=("valence", "mean"),
        ),
        "comparación explicit",
    )
    reporte = (
        reporte_agregado
        .sort_values("explicit")
        .reset_index(drop=True)
    )
    reporte["porcentaje"] = reporte["cantidad"].div(len(vista)).mul(100)
    reporte["grupo"] = [
        "explicit" if bool(valor) else "no_explicit"
        for valor in reporte["explicit"].tolist()
    ]
    orden = [
        "explicit",
        "grupo",
        "cantidad",
        "porcentaje",
        "popularidad_media",
        "popularidad_mediana",
        "duracion_media_ms",
        "danceability_media",
        "energy_media",
        "valence_media",
    ]
    return _seleccionar_columnas(reporte, orden)


def crear_correlaciones_popularidad(vista: pd.DataFrame) -> pd.DataFrame:
    """Calcula asociaciones lineales de Pearson; correlación no implica causalidad."""
    matriz = _seleccionar_columnas(
        vista, ("popularity", *ATRIBUTOS_CORRELACION)
    ).corr(method="pearson")
    filas = []
    for atributo in ATRIBUTOS_CORRELACION:
        correlacion = _numero(
            matriz.at[atributo, "popularity"],
            f"correlación de popularity con {atributo}",
        )
        filas.append(
            {
                "atributo": atributo,
                "correlacion_pearson": correlacion,
                "correlacion_absoluta": abs(correlacion),
                "interpretacion": "asociación descriptiva; no implica causalidad",
            }
        )
    return (
        pd.DataFrame(filas)
        .sort_values(["correlacion_absoluta", "atributo"], ascending=[False, True])
        .reset_index(drop=True)
    )


def crear_perfil_alta_popularidad(vista: pd.DataFrame) -> pd.DataFrame:
    """Compara medianas del cuartil superior de popularity contra el resto."""
    umbral = _numero(
        vista["popularity"].quantile(0.75), "cuartil superior de popularity"
    )
    mascara_alta = vista["popularity"].ge(umbral)
    cantidad_alta = _entero(mascara_alta.to_numpy().sum(), "tracks de popularidad alta")
    cantidad_resto = len(vista) - cantidad_alta
    filas = []
    for atributo in ATRIBUTOS_PERFIL:
        mediana_alta = _numero(
            vista.loc[mascara_alta, atributo].median(),
            f"mediana alta de {atributo}",
        )
        mediana_resto = _numero(
            vista.loc[~mascara_alta, atributo].median(),
            f"mediana del resto de {atributo}",
        )
        filas.append(
            {
                "atributo": atributo,
                "estadistico": "mediana",
                "mediana_alta_popularidad": mediana_alta,
                "mediana_resto": mediana_resto,
                "diferencia_alta_menos_resto": mediana_alta - mediana_resto,
                "umbral_popularidad_q3": umbral,
                "tracks_alta_popularidad": cantidad_alta,
                "tracks_resto": cantidad_resto,
            }
        )
    return pd.DataFrame(filas)


def crear_resumen_valor(
    vista: pd.DataFrame,
    top_canciones: pd.DataFrame,
    top_artistas: pd.DataFrame,
    umbral_artistas: int,
    generos: pd.DataFrame,
    explicit: pd.DataFrame,
    correlaciones: pd.DataFrame,
    perfil: pd.DataFrame,
) -> ResumenValor:
    """Extrae escalares validados para la presentación y los hallazgos."""
    cancion = top_canciones.iloc[0]
    artista_tracks = top_artistas[
        top_artistas["criterio"] == "mayor_numero_tracks"
    ].iloc[0]
    criterio_pop = f"mayor_popularidad_mediana_min_{umbral_artistas}_tracks"
    artista_pop = top_artistas[top_artistas["criterio"] == criterio_pop].iloc[0]
    genero_tracks = generos.sort_values(
        ["tracks_unicos", "track_genre"], ascending=[False, True]
    ).iloc[0]
    genero_pop = generos.sort_values(
        ["popularidad_mediana", "tracks_unicos", "track_genre"],
        ascending=[False, False, True],
    ).iloc[0]
    explicit_indice = explicit.set_index("explicit")
    correlacion = correlaciones.iloc[0]
    perfil_normalizado = _asegurar_dataframe(
        perfil.loc[perfil["atributo"].isin(ATRIBUTOS_NORMALIZADOS_PERFIL)],
        "perfil normalizado",
    ).copy()
    perfil_normalizado["diferencia_absoluta"] = [
        abs(_numero(valor, "diferencia del perfil"))
        for valor in perfil_normalizado["diferencia_alta_menos_resto"].tolist()
    ]
    perfil_destacado = perfil_normalizado.sort_values(
        ["diferencia_absoluta", "atributo"], ascending=[False, True]
    ).iloc[0]

    return {
        "tracks_unicos": len(vista),
        "popularidad_media": _numero(vista["popularity"].mean(), "popularidad media"),
        "popularidad_mediana": _numero(
            vista["popularity"].median(), "popularidad mediana"
        ),
        "top_cancion": _texto(cancion["track_name"], "nombre de canción top"),
        "top_cancion_artistas": _texto(cancion["artists"], "artistas de canción top"),
        "top_cancion_popularidad": _numero(
            cancion["popularity"], "popularidad de canción top"
        ),
        "credito_mas_tracks": _texto(artista_tracks["artists"], "crédito con más tracks"),
        "credito_mas_tracks_cantidad": _entero(
            artista_tracks["tracks_unicos"], "tracks del crédito principal"
        ),
        "credito_mayor_popularidad": _texto(
            artista_pop["artists"], "crédito con mayor popularidad"
        ),
        "credito_mayor_popularidad_mediana": _numero(
            artista_pop["popularidad_mediana"], "popularidad mediana del crédito"
        ),
        "credito_mayor_popularidad_tracks": _entero(
            artista_pop["tracks_unicos"], "tracks del crédito por popularidad"
        ),
        "umbral_tracks_credito": umbral_artistas,
        "genero_mas_tracks": _texto(genero_tracks["track_genre"], "género con más tracks"),
        "genero_mas_tracks_cantidad": _entero(
            genero_tracks["tracks_unicos"], "tracks del género principal"
        ),
        "genero_mayor_popularidad": _texto(
            genero_pop["track_genre"], "género con mayor popularidad"
        ),
        "genero_mayor_popularidad_mediana": _numero(
            genero_pop["popularidad_mediana"], "mediana del género"
        ),
        "genero_mayor_popularidad_tracks": _entero(
            genero_pop["tracks_unicos"], "tracks del género por popularidad"
        ),
        "explicit_cantidad": _entero(explicit_indice.at[True, "cantidad"], "tracks explicit"),
        "explicit_porcentaje": _numero(
            explicit_indice.at[True, "porcentaje"], "porcentaje explicit"
        ),
        "explicit_popularidad_mediana": _numero(
            explicit_indice.at[True, "popularidad_mediana"], "mediana explicit"
        ),
        "no_explicit_cantidad": _entero(
            explicit_indice.at[False, "cantidad"], "tracks no explicit"
        ),
        "no_explicit_porcentaje": _numero(
            explicit_indice.at[False, "porcentaje"], "porcentaje no explicit"
        ),
        "no_explicit_popularidad_mediana": _numero(
            explicit_indice.at[False, "popularidad_mediana"], "mediana no explicit"
        ),
        "correlacion_atributo": _texto(
            correlacion["atributo"], "atributo con mayor correlación"
        ),
        "correlacion_valor": _numero(
            correlacion["correlacion_pearson"], "correlación principal"
        ),
        "umbral_alta_popularidad": _numero(
            perfil_destacado["umbral_popularidad_q3"], "umbral de popularidad"
        ),
        "tracks_alta_popularidad": _entero(
            perfil_destacado["tracks_alta_popularidad"], "tracks de popularidad alta"
        ),
        "tracks_resto": _entero(perfil_destacado["tracks_resto"], "tracks restantes"),
        "perfil_atributo_destacado": _texto(
            perfil_destacado["atributo"], "atributo destacado del perfil"
        ),
        "perfil_mediana_alta": _numero(
            perfil_destacado["mediana_alta_popularidad"], "mediana alta destacada"
        ),
        "perfil_mediana_resto": _numero(
            perfil_destacado["mediana_resto"], "mediana resto destacada"
        ),
    }


def generar_hallazgos_valor(resumen: ResumenValor) -> pd.DataFrame:
    """Genera hallazgos cortos basados exclusivamente en métricas calculadas."""
    comparacion_explicit = (
        "explicit"
        if resumen["explicit_popularidad_mediana"]
        > resumen["no_explicit_popularidad_mediana"]
        else "no_explicit"
    )
    hallazgos = [
        {
            "categoria": "géneros",
            "hallazgo": (
                f"{resumen['genero_mayor_popularidad']} presenta la mayor mediana "
                "de popularity dentro de los géneros del dataset."
            ),
            "metrica": "popularidad_mediana",
            "valor": resumen["genero_mayor_popularidad_mediana"],
        },
        {
            "categoria": "géneros",
            "hallazgo": (
                f"{resumen['genero_mas_tracks']} es uno de los géneros con mayor "
                "cantidad de asociaciones únicas track-género."
            ),
            "metrica": "tracks_unicos",
            "valor": resumen["genero_mas_tracks_cantidad"],
        },
        {
            "categoria": "correlaciones",
            "hallazgo": (
                f"{resumen['correlacion_atributo']} tiene la mayor correlación "
                "absoluta observada con popularity; correlación no implica causalidad."
            ),
            "metrica": "correlacion_pearson",
            "valor": resumen["correlacion_valor"],
        },
        {
            "categoria": "explicit",
            "hallazgo": (
                f"Los tracks explicit representan {resumen['explicit_porcentaje']:.2f}% "
                f"de la vista única; el grupo {comparacion_explicit} presenta la "
                "mayor mediana descriptiva de popularity."
            ),
            "metrica": "porcentaje_explicit",
            "valor": resumen["explicit_porcentaje"],
        },
        {
            "categoria": "perfil_alta_popularidad",
            "hallazgo": (
                f"En {resumen['perfil_atributo_destacado']}, el grupo del cuartil "
                f"superior presenta mediana {resumen['perfil_mediana_alta']:.6f} "
                f"frente a {resumen['perfil_mediana_resto']:.6f} en el resto."
            ),
            "metrica": resumen["perfil_atributo_destacado"],
            "valor": resumen["perfil_mediana_alta"] - resumen["perfil_mediana_resto"],
        },
    ]
    return pd.DataFrame(hallazgos)


def generar_conclusion_valor(resumen: ResumenValor) -> str:
    """Explica la V de Valor con resultados descriptivos reales."""
    return (
        f"Al consolidar {resumen['tracks_unicos']:,} tracks únicos fue posible "
        f"identificar que {resumen['genero_mayor_popularidad']} tiene la mayor "
        f"mediana de popularity por género y que {resumen['correlacion_atributo']} "
        "presenta la asociación lineal más fuerte con popularity dentro de los "
        "atributos revisados. Así, los registros se transforman en información "
        "útil para comparar canciones, créditos, géneros y grupos. Los resultados "
        "son descriptivos, corresponden solo a este dataset y no demuestran causalidad."
    )


def guardar_reportes_valor(
    directorio: Path,
    resumen_general: pd.DataFrame,
    top_canciones: pd.DataFrame,
    top_artistas: pd.DataFrame,
    generos: pd.DataFrame,
    comparacion_explicit: pd.DataFrame,
    correlaciones: pd.DataFrame,
    perfil_alta_popularidad: pd.DataFrame,
    hallazgos: pd.DataFrame,
) -> dict[str, Path]:
    """Guarda los ocho reportes descriptivos de Valor."""
    directorio.mkdir(parents=True, exist_ok=True)
    tablas = {
        "resumen_valor.csv": resumen_general,
        "top_canciones_populares.csv": top_canciones,
        "top_artistas.csv": top_artistas,
        "analisis_generos.csv": generos,
        "comparacion_explicit.csv": comparacion_explicit,
        "correlaciones_popularidad.csv": correlaciones,
        "perfil_alta_popularidad.csv": perfil_alta_popularidad,
        "hallazgos_valor.csv": hallazgos,
    }
    rutas: dict[str, Path] = {}
    for nombre, tabla in tablas.items():
        ruta = directorio / nombre
        tabla.to_csv(ruta, index=False)
        rutas[nombre] = ruta
    return rutas
