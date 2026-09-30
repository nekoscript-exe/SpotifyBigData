"""Localización y carga del dataset CSV del proyecto."""

from pathlib import Path

import pandas as pd


RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
DIRECTORIO_DATOS = RAIZ_PROYECTO / "data"


def localizar_csv(directorio_datos: Path = DIRECTORIO_DATOS) -> Path:
    """Devuelve el único CSV presente en el directorio de datos.

    Raises:
        FileNotFoundError: Si el directorio no existe o no contiene archivos CSV.
        RuntimeError: Si se encuentran varios CSV y no es posible elegir uno.
    """
    if not directorio_datos.is_dir():
        raise FileNotFoundError(
            f"No existe el directorio de datos esperado: {directorio_datos}"
        )

    archivos_csv = sorted(
        archivo
        for archivo in directorio_datos.iterdir()
        if archivo.is_file() and archivo.suffix.lower() == ".csv"
    )

    if not archivos_csv:
        raise FileNotFoundError(
            f"No se encontró ningún archivo CSV en: {directorio_datos}"
        )

    if len(archivos_csv) > 1:
        nombres = "\n  - ".join(archivo.name for archivo in archivos_csv)
        raise RuntimeError(
            "Se encontró más de un archivo CSV. No se seleccionará uno "
            f"arbitrariamente:\n  - {nombres}"
        )

    return archivos_csv[0]


def cargar_dataset(directorio_datos: Path = DIRECTORIO_DATOS) -> tuple[Path, pd.DataFrame]:
    """Localiza el CSV del proyecto y lo carga sin modificar sus datos."""
    ruta_csv = localizar_csv(directorio_datos)

    try:
        dataframe = pd.read_csv(ruta_csv)
    except pd.errors.EmptyDataError as error:
        raise ValueError(f"El archivo CSV está vacío: {ruta_csv.name}") from error
    except pd.errors.ParserError as error:
        raise ValueError(
            f"No fue posible interpretar la estructura del CSV {ruta_csv.name}: {error}"
        ) from error
    except UnicodeDecodeError as error:
        raise ValueError(
            f"No fue posible decodificar {ruta_csv.name} como texto: {error}"
        ) from error

    return ruta_csv, dataframe
