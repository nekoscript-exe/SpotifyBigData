"""Métricas actuales y proyecciones matemáticas de volumen."""

from pathlib import Path
from typing import Any, TypedDict

import pandas as pd

from src.diagnostico import (
    formatear_tamano,
    obtener_informacion_general,
)


MULTIPLICADORES = (1, 10, 100, 1_000, 10_000, 100_000, 1_000_000)


class VolumenActual(TypedDict):
    """Mediciones reales del volumen del dataset cargado."""

    registros: int
    columnas: int
    almacenamiento_bytes: int
    memoria_bytes: int
    bytes_por_fila_disco: float
    bytes_por_fila_memoria: float
    factor_expansion_memoria: float


def analizar_volumen_actual(
    dataframe: pd.DataFrame, ruta_csv: Path
) -> VolumenActual:
    """Calcula las métricas reales de volumen del dataset cargado."""
    informacion = obtener_informacion_general(dataframe, ruta_csv)
    filas = int(informacion["registros"])
    disco = int(informacion["tamano_archivo_bytes"])
    memoria = int(informacion["memoria_dataframe_bytes"])

    resultado: VolumenActual = {
        "registros": filas,
        "columnas": int(informacion["columnas"]),
        "almacenamiento_bytes": disco,
        "memoria_bytes": memoria,
        "bytes_por_fila_disco": disco / filas if filas else 0.0,
        "bytes_por_fila_memoria": memoria / filas if filas else 0.0,
        "factor_expansion_memoria": memoria / disco if disco else 0.0,
    }
    return resultado


def formatear_duracion(segundos: float) -> str:
    """Representa segundos estimados en una unidad temporal legible."""
    if segundos < 60:
        return f"{segundos:,.2f} s"
    if segundos < 3_600:
        return f"{segundos / 60:,.2f} min"
    if segundos < 86_400:
        return f"{segundos / 3_600:,.2f} h"
    if segundos < 31_536_000:
        return f"{segundos / 86_400:,.2f} días"
    return f"{segundos / 31_536_000:,.2f} años"


def crear_proyeccion_escalabilidad(
    volumen_actual: VolumenActual,
    tiempo_base_medido: float,
    multiplicadores: tuple[int, ...] = MULTIPLICADORES,
) -> pd.DataFrame:
    """Proyecta filas, disco, RAM y tiempo sin crear nuevos registros."""
    resultados: list[dict[str, Any]] = []
    for multiplicador in multiplicadores:
        registros = int(volumen_actual["registros"]) * multiplicador
        almacenamiento = int(volumen_actual["almacenamiento_bytes"]) * multiplicador
        memoria = int(volumen_actual["memoria_bytes"]) * multiplicador
        tiempo_estimado = tiempo_base_medido * multiplicador
        resultados.append(
            {
                "multiplicador": multiplicador,
                "escala": f"x{multiplicador:,}",
                "naturaleza": (
                    "medición base"
                    if multiplicador == 1
                    else "estimación matemática"
                ),
                "registros_estimados": registros,
                "columnas_constantes": int(volumen_actual["columnas"]),
                "almacenamiento_bytes": almacenamiento,
                "almacenamiento_legible": formatear_tamano(almacenamiento),
                "memoria_bytes": memoria,
                "memoria_legible": formatear_tamano(memoria),
                "tiempo_estimado_lineal_segundos": tiempo_estimado,
                "tiempo_estimado_lineal_legible": formatear_duracion(tiempo_estimado),
            }
        )
    return pd.DataFrame(resultados)


def guardar_proyeccion_escalabilidad(
    directorio: Path, proyeccion: pd.DataFrame
) -> Path:
    """Guarda la proyección matemática en un CSV."""
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / "proyeccion_escalabilidad.csv"
    proyeccion.to_csv(ruta, index=False)
    return ruta


def generar_conclusion_volumen(
    volumen_actual: VolumenActual, proyeccion: pd.DataFrame
) -> str:
    """Genera una conclusión derivada de la medición y la mayor proyección."""
    maxima = proyeccion.iloc[-1]
    return (
        f"El dataset actual, con {int(volumen_actual['registros']):,} registros, "
        "pudo procesarse localmente con pandas. Su representación en memoria "
        f"ocupa {float(volumen_actual['factor_expansion_memoria']):.2f} veces el "
        "archivo serializado en disco. Si la misma estructura creciera hasta "
        f"{int(maxima['registros_estimados']):,} registros, la proyección sería "
        f"de {maxima['almacenamiento_legible']} en disco y "
        f"{maxima['memoria_legible']} en RAM. Son estimaciones matemáticas: que "
        "un volumen resulte o no razonable depende del hardware, la arquitectura, "
        "la velocidad requerida y la complejidad del procesamiento."
    )
