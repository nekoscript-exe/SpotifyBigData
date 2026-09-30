"""Benchmarks locales y acotados sobre el dataset real."""

from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Callable

import pandas as pd

from src.diagnostico import (
    contar_filas_duplicadas,
    formatear_tamano,
    obtener_estadisticas_descriptivas,
    obtener_valores_faltantes,
)


REPETICIONES_PREDETERMINADAS = 3


def seleccionar_tamanos_benchmark(total_filas: int) -> list[int]:
    """Selecciona tamaños razonables y siempre incluye el dataset completo."""
    if total_filas <= 0:
        return [0]

    candidatos = [10_000, 25_000, 50_000, 75_000]
    tamanos = [cantidad for cantidad in candidatos if cantidad < total_filas]

    if not tamanos:
        tamanos = [
            max(1, round(total_filas * proporcion))
            for proporcion in (0.25, 0.50, 0.75)
        ]

    return sorted(set(tamanos + [total_filas]))


def ejecutar_benchmark_carga(
    ruta_csv: Path,
    total_filas: int,
    repeticiones: int = REPETICIONES_PREDETERMINADAS,
) -> pd.DataFrame:
    """Mide lecturas parciales y completa del CSV con una mediana robusta."""
    if repeticiones < 1:
        raise ValueError("El benchmark de carga requiere al menos una repetición.")

    tamanos = seleccionar_tamanos_benchmark(total_filas)

    # Esta lectura breve calienta el parser y permite que el sistema operativo
    # pueda poblar su caché antes de las mediciones registradas.
    pd.read_csv(ruta_csv, nrows=min(1_000, total_filas) if total_filas else 0)

    resultados = []
    for filas_solicitadas in tamanos:
        tiempos = []
        memorias = []
        filas_observadas = []

        for _ in range(repeticiones):
            inicio = perf_counter()
            if filas_solicitadas == total_filas:
                muestra = pd.read_csv(ruta_csv)
            else:
                muestra = pd.read_csv(ruta_csv, nrows=filas_solicitadas)
            tiempos.append(perf_counter() - inicio)
            filas_observadas.append(len(muestra))
            memorias.append(int(muestra.memory_usage(index=True, deep=True).sum()))

        tiempo_mediano = float(median(tiempos))
        filas_cargadas = int(median(filas_observadas))
        memoria_bytes = int(median(memorias))
        resultados.append(
            {
                "filas_solicitadas": filas_solicitadas,
                "filas_cargadas": filas_cargadas,
                "alcance": (
                    "dataset completo"
                    if filas_solicitadas == total_filas
                    else "lectura parcial"
                ),
                "repeticiones": repeticiones,
                "tiempo_mediano_segundos": tiempo_mediano,
                "tiempo_minimo_segundos": min(tiempos),
                "tiempo_maximo_segundos": max(tiempos),
                "filas_por_segundo": (
                    filas_cargadas / tiempo_mediano if tiempo_mediano else 0.0
                ),
                "memoria_bytes": memoria_bytes,
                "memoria_legible": formatear_tamano(memoria_bytes),
            }
        )

    return pd.DataFrame(resultados)


def ejecutar_benchmark_operaciones(
    dataframe: pd.DataFrame,
    repeticiones: int = REPETICIONES_PREDETERMINADAS,
) -> pd.DataFrame:
    """Mide operaciones reales del proyecto de manera independiente."""
    if repeticiones < 1:
        raise ValueError("El benchmark de operaciones requiere al menos una repetición.")

    operaciones: dict[str, Callable[[], object]] = {
        "isna().sum()": lambda: obtener_valores_faltantes(dataframe),
        "duplicated().sum()": lambda: contar_filas_duplicadas(dataframe),
        "nunique()": lambda: dataframe.nunique(dropna=True),
        "describe()": lambda: obtener_estadisticas_descriptivas(dataframe),
    }
    resultados = []

    for nombre, operacion in operaciones.items():
        tiempos = []
        for _ in range(repeticiones):
            inicio = perf_counter()
            operacion()
            tiempos.append(perf_counter() - inicio)

        resultados.append(
            {
                "operacion": nombre,
                "repeticiones": repeticiones,
                "tiempo_mediano_segundos": float(median(tiempos)),
                "tiempo_minimo_segundos": min(tiempos),
                "tiempo_maximo_segundos": max(tiempos),
            }
        )

    return pd.DataFrame(resultados)


def guardar_reportes_rendimiento(
    directorio: Path,
    benchmark_carga: pd.DataFrame,
    benchmark_operaciones: pd.DataFrame,
) -> dict[str, Path]:
    """Guarda las mediciones locales en reportes CSV separados."""
    directorio.mkdir(parents=True, exist_ok=True)
    rutas = {
        "benchmark_carga": directorio / "benchmark_carga.csv",
        "benchmark_operaciones": directorio / "benchmark_operaciones.csv",
    }
    benchmark_carga.to_csv(rutas["benchmark_carga"], index=False)
    benchmark_operaciones.to_csv(rutas["benchmark_operaciones"], index=False)
    return rutas
