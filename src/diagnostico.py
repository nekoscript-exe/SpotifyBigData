"""Funciones de diagnóstico que no alteran el dataset."""

from pathlib import Path
from typing import Any

import pandas as pd


def formatear_tamano(cantidad_bytes: int) -> str:
    """Convierte una cantidad de bytes a una unidad legible."""
    unidades = ("B", "KB", "MB", "GB", "TB", "PB")
    tamano = float(cantidad_bytes)

    for unidad in unidades[:-1]:
        if abs(tamano) < 1024:
            return f"{tamano:,.2f} {unidad}"
        tamano /= 1024

    return f"{tamano:,.2f} PB"


def obtener_informacion_general(
    dataframe: pd.DataFrame, ruta_csv: Path
) -> dict[str, Any]:
    """Obtiene dimensiones y tamaños del CSV y del DataFrame."""
    registros, columnas = dataframe.shape
    memoria_bytes = int(dataframe.memory_usage(index=True, deep=True).sum())

    return {
        "dataset": ruta_csv.name,
        "registros": registros,
        "columnas": columnas,
        "dimensiones": dataframe.shape,
        "tamano_archivo_bytes": ruta_csv.stat().st_size,
        "memoria_dataframe_bytes": memoria_bytes,
    }


def obtener_nombres_variables(dataframe: pd.DataFrame) -> list[str]:
    """Devuelve los nombres de las columnas respetando su orden original."""
    return dataframe.columns.tolist()


def obtener_tipos_datos(dataframe: pd.DataFrame) -> pd.Series:
    """Devuelve el tipo de dato inferido para cada columna."""
    return dataframe.dtypes.astype(str).rename("tipo")


def obtener_valores_faltantes(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calcula cantidad y porcentaje de valores faltantes por columna."""
    cantidad = dataframe.isna().sum()
    porcentaje = cantidad.div(len(dataframe)).mul(100) if len(dataframe) else cantidad

    return pd.DataFrame(
        {
            "faltantes": cantidad.astype(int),
            "porcentaje": porcentaje.astype(float),
        }
    )


def contar_filas_duplicadas(dataframe: pd.DataFrame) -> int:
    """Cuenta filas completamente duplicadas sin eliminarlas."""
    return int(dataframe.duplicated().sum())


def obtener_primeros_registros(
    dataframe: pd.DataFrame, cantidad: int = 5
) -> pd.DataFrame:
    """Devuelve una vista de los primeros registros."""
    return dataframe.head(cantidad)


def obtener_estadisticas_descriptivas(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calcula estadísticas básicas para las columnas numéricas."""
    columnas_numericas = dataframe.select_dtypes(include="number")
    if columnas_numericas.empty:
        return pd.DataFrame()
    return columnas_numericas.describe().transpose()
