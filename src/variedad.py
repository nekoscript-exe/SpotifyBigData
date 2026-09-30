"""Análisis de variedad técnica, semántica y cardinalidad."""

from pathlib import Path
from typing import Any, TypedDict

import pandas as pd
from pandas.api.types import is_bool_dtype, is_float_dtype, is_integer_dtype


CATEGORIAS_SEMANTICAS = {
    "track_id": "Identificador",
    "artists": "Texto",
    "album_name": "Texto",
    "track_name": "Texto",
    "track_genre": "Categórica",
    "key": "Categórica",
    "mode": "Categórica",
    "time_signature": "Categórica",
    "explicit": "Booleana",
    "popularity": "Numérica / métrica",
    "duration_ms": "Numérica / métrica",
    "danceability": "Numérica / métrica",
    "energy": "Numérica / métrica",
    "loudness": "Numérica / métrica",
    "speechiness": "Numérica / métrica",
    "acousticness": "Numérica / métrica",
    "instrumentalness": "Numérica / métrica",
    "liveness": "Numérica / métrica",
    "valence": "Numérica / métrica",
    "tempo": "Numérica / métrica",
}


class InformacionEspecial(TypedDict):
    """Cardinalidades y distribuciones destacadas del dataset."""

    generos: int
    artistas: int
    albumes: int
    canciones: int
    track_ids: int
    explicit: pd.Series
    mode: pd.Series
    time_signature: pd.Series


def _clasificar_dtype(dtype: Any) -> str:
    """Agrupa un dtype de pandas en una categoría técnica legible."""
    if is_bool_dtype(dtype):
        return "bool"
    if is_integer_dtype(dtype):
        return "int"
    if is_float_dtype(dtype):
        return "float"
    if dtype == object or isinstance(dtype, pd.StringDtype):
        return "object"
    return str(dtype)


def resumir_tipos_tecnicos(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Cuenta columnas por familia técnica de dtype."""
    tipos = pd.Series(
        [_clasificar_dtype(dtype) for dtype in dataframe.dtypes],
        name="tipo_tecnico",
    )
    conteos = tipos.value_counts(sort=False)
    conteos.index.name = "tipo_tecnico"
    resumen = conteos.to_frame(name="cantidad_columnas").reset_index()
    resumen["columnas"] = resumen["tipo_tecnico"].map(
        lambda tipo: " | ".join(
            columna
            for columna in dataframe.columns
            if _clasificar_dtype(dataframe[columna].dtype) == tipo
        )
    )
    return resumen


def crear_resumen_variedad(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Combina dtype, significado semántico y cardinalidad por columna."""
    total_filas = len(dataframe)
    valores_unicos = dataframe.nunique(dropna=True)
    porcentaje = (
        valores_unicos.div(total_filas).mul(100)
        if total_filas
        else valores_unicos.astype(float)
    )
    return pd.DataFrame(
        {
            "columna": dataframe.columns,
            "dtype": dataframe.dtypes.astype(str).to_numpy(),
            "tipo_tecnico": [
                _clasificar_dtype(dtype) for dtype in dataframe.dtypes
            ],
            "categoria_semantica": [
                CATEGORIAS_SEMANTICAS.get(columna, "Sin clasificar")
                for columna in dataframe.columns
            ],
            "valores_unicos": valores_unicos.to_numpy(),
            "porcentaje_unicidad": porcentaje.to_numpy(),
        }
    )


def obtener_informacion_especial(dataframe: pd.DataFrame) -> InformacionEspecial:
    """Obtiene cardinalidades y dominios especialmente útiles para Spotify."""
    columnas = (
        "track_genre",
        "artists",
        "album_name",
        "track_name",
        "track_id",
        "explicit",
        "mode",
        "time_signature",
    )
    faltantes = [columna for columna in columnas if columna not in dataframe.columns]
    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias para el análisis de variedad: "
            + ", ".join(faltantes)
        )

    return {
        "generos": int(dataframe["track_genre"].nunique(dropna=True)),
        "artistas": int(dataframe["artists"].nunique(dropna=True)),
        "albumes": int(dataframe["album_name"].nunique(dropna=True)),
        "canciones": int(dataframe["track_name"].nunique(dropna=True)),
        "track_ids": int(dataframe["track_id"].nunique(dropna=True)),
        "explicit": dataframe["explicit"].value_counts(dropna=False).sort_index(),
        "mode": dataframe["mode"].value_counts(dropna=False).sort_index(),
        "time_signature": dataframe["time_signature"]
        .value_counts(dropna=False)
        .sort_index(),
    }


def guardar_reporte_variedad(directorio: Path, resumen: pd.DataFrame) -> Path:
    """Guarda el resumen de variedad y devuelve la ruta generada."""
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / "resumen_variedad.csv"
    resumen.to_csv(ruta, index=False)
    return ruta


def generar_conclusion_variedad(
    tipos_tecnicos: pd.DataFrame, resumen_variedad: pd.DataFrame
) -> str:
    """Redacta una conclusión basada en los tipos realmente encontrados."""
    tipos = ", ".join(tipos_tecnicos["tipo_tecnico"].astype(str))
    categorias = ", ".join(resumen_variedad["categoria_semantica"].drop_duplicates())
    return (
        f"El dataset contiene {len(tipos_tecnicos)} familias técnicas ({tipos}) y "
        f"{resumen_variedad['categoria_semantica'].nunique()} categorías semánticas "
        f"({categorias}). Esto combina metadatos y métricas musicales; el dtype "
        "técnico no determina por sí solo el significado de una variable."
    )
