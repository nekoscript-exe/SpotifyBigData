"""Simulación académica de eventos sintéticos para estudiar Velocidad.

Los eventos no proceden de Spotify ni representan su infraestructura real.
Los únicos datos tomados del dataset son los identificadores de canciones.
"""

from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter
from typing import Literal, TypedDict

import pandas as pd


TipoEvento = Literal["play", "pause", "skip", "like", "add_to_playlist"]

SEMILLA = 42
CANTIDAD_USUARIOS = 10_000
CANTIDAD_EVENTOS_RESUMEN = 100_000
TAMANOS_BENCHMARK = (10_000, 50_000, 100_000, 250_000, 500_000)
REPETICIONES = 3
TIMESTAMP_INICIAL = datetime(2025, 1, 1, tzinfo=timezone.utc)
INTERVALO_MILISEGUNDOS = 250

TIPOS_EVENTO: tuple[TipoEvento, ...] = (
    "play",
    "pause",
    "skip",
    "like",
    "add_to_playlist",
)
PROBABILIDADES_EVENTO: tuple[float, ...] = (0.45, 0.15, 0.25, 0.10, 0.05)
UMBRALES_EVENTO: tuple[tuple[float, TipoEvento], ...] = (
    (0.45, "play"),
    (0.60, "pause"),
    (0.85, "skip"),
    (0.95, "like"),
    (1.00, "add_to_playlist"),
)


class EventoSintetico(TypedDict):
    """Estructura de una interacción ficticia generada localmente."""

    timestamp: datetime
    user_id: str
    track_id: str
    evento: TipoEvento


class ResumenFlujo(TypedDict):
    """Métricas agregadas calculadas sin conservar eventos individuales."""

    eventos_totales: int
    conteos_por_tipo: dict[TipoEvento, int]
    porcentajes_por_tipo: dict[TipoEvento, float]
    usuarios_distintos: int
    tracks_distintos: int
    evento_mas_frecuente: TipoEvento | None


class MedicionVelocidad(TypedDict):
    """Resultado nativo de un tamaño del benchmark."""

    eventos: int
    repeticiones: int
    tiempo_mediano_segundos: float
    tiempo_minimo_segundos: float
    tiempo_maximo_segundos: float
    eventos_por_segundo: float
    microsegundos_por_evento: float
    naturaleza: str


def obtener_track_ids_reales(dataframe: pd.DataFrame) -> tuple[str, ...]:
    """Extrae IDs reales, no nulos y sin repeticiones del dataset."""
    if "track_id" not in dataframe.columns:
        raise ValueError("El dataset no contiene la columna requerida: track_id")

    ids_unicos: dict[str, None] = {}
    for valor in dataframe["track_id"].tolist():
        if isinstance(valor, str) and valor:
            ids_unicos.setdefault(valor, None)

    if not ids_unicos:
        raise ValueError("No hay track_id válidos para generar la simulación.")
    return tuple(ids_unicos)


def _seleccionar_tipo_evento(aleatorio: Random) -> TipoEvento:
    """Selecciona un tipo usando las probabilidades sintéticas documentadas."""
    valor = aleatorio.random()
    for limite, tipo_evento in UMBRALES_EVENTO:
        if valor < limite:
            return tipo_evento
    return "add_to_playlist"


def generar_eventos(
    track_ids: Sequence[str],
    cantidad_eventos: int,
    *,
    semilla: int = SEMILLA,
    cantidad_usuarios: int = CANTIDAD_USUARIOS,
) -> Iterator[EventoSintetico]:
    """Produce eventos sintéticos uno a uno, sin almacenarlos en una lista."""
    if cantidad_eventos < 0:
        raise ValueError("La cantidad de eventos no puede ser negativa.")
    if cantidad_usuarios < 1:
        raise ValueError("Debe existir al menos un usuario sintético.")
    if not track_ids:
        raise ValueError("Se requiere al menos un track_id real.")

    aleatorio = Random(semilla)
    for indice in range(cantidad_eventos):
        yield EventoSintetico(
            timestamp=TIMESTAMP_INICIAL
            + timedelta(milliseconds=indice * INTERVALO_MILISEGUNDOS),
            user_id=f"user_{aleatorio.randrange(1, cantidad_usuarios + 1):06d}",
            track_id=aleatorio.choice(track_ids),
            evento=_seleccionar_tipo_evento(aleatorio),
        )


def procesar_eventos(eventos: Iterable[EventoSintetico]) -> ResumenFlujo:
    """Procesa progresivamente un flujo y conserva solo métricas agregadas."""
    conteos: Counter[TipoEvento] = Counter()
    usuarios: set[str] = set()
    tracks: set[str] = set()
    total = 0

    for evento in eventos:
        total += 1
        conteos[evento["evento"]] += 1
        usuarios.add(evento["user_id"])
        tracks.add(evento["track_id"])

    conteos_completos: dict[TipoEvento, int] = {
        tipo: conteos[tipo] for tipo in TIPOS_EVENTO
    }
    porcentajes: dict[TipoEvento, float] = {
        tipo: cantidad / total * 100 if total else 0.0
        for tipo, cantidad in conteos_completos.items()
    }
    mas_frecuente = conteos.most_common(1)[0][0] if conteos else None
    resultado: ResumenFlujo = {
        "eventos_totales": total,
        "conteos_por_tipo": conteos_completos,
        "porcentajes_por_tipo": porcentajes,
        "usuarios_distintos": len(usuarios),
        "tracks_distintos": len(tracks),
        "evento_mas_frecuente": mas_frecuente,
    }
    return resultado


def ejecutar_simulacion(
    track_ids: Sequence[str],
    cantidad_eventos: int,
    *,
    semilla: int = SEMILLA,
    cantidad_usuarios: int = CANTIDAD_USUARIOS,
) -> ResumenFlujo:
    """Conecta el generador sintético con el procesador progresivo."""
    flujo = generar_eventos(
        track_ids,
        cantidad_eventos,
        semilla=semilla,
        cantidad_usuarios=cantidad_usuarios,
    )
    return procesar_eventos(flujo)


def ejecutar_benchmark_velocidad(
    track_ids: Sequence[str],
    *,
    tamanos: tuple[int, ...] = TAMANOS_BENCHMARK,
    repeticiones: int = REPETICIONES,
    semilla: int = SEMILLA,
    cantidad_usuarios: int = CANTIDAD_USUARIOS,
) -> tuple[pd.DataFrame, dict[int, MedicionVelocidad], ResumenFlujo]:
    """Mide generación más procesamiento y devuelve el resumen representativo."""
    if repeticiones < 1:
        raise ValueError("El benchmark requiere al menos una repetición.")
    if CANTIDAD_EVENTOS_RESUMEN not in tamanos:
        raise ValueError(
            f"El benchmark debe incluir {CANTIDAD_EVENTOS_RESUMEN:,} eventos."
        )

    mediciones: dict[int, MedicionVelocidad] = {}
    filas_reporte: list[MedicionVelocidad] = []
    resumen_representativo: ResumenFlujo | None = None

    for cantidad_eventos in tamanos:
        tiempos: list[float] = []
        for repeticion in range(repeticiones):
            inicio = perf_counter()
            resumen = ejecutar_simulacion(
                track_ids,
                cantidad_eventos,
                semilla=semilla,
                cantidad_usuarios=cantidad_usuarios,
            )
            tiempos.append(perf_counter() - inicio)
            if resumen["eventos_totales"] != cantidad_eventos:
                raise RuntimeError("La simulación no procesó todos los eventos.")
            if (
                cantidad_eventos == CANTIDAD_EVENTOS_RESUMEN
                and repeticion == 0
            ):
                resumen_representativo = resumen

        tiempo_mediano = float(median(tiempos))
        medicion: MedicionVelocidad = {
            "eventos": cantidad_eventos,
            "repeticiones": repeticiones,
            "tiempo_mediano_segundos": tiempo_mediano,
            "tiempo_minimo_segundos": min(tiempos),
            "tiempo_maximo_segundos": max(tiempos),
            "eventos_por_segundo": (
                cantidad_eventos / tiempo_mediano if tiempo_mediano else 0.0
            ),
            "microsegundos_por_evento": (
                tiempo_mediano / cantidad_eventos * 1_000_000
                if cantidad_eventos
                else 0.0
            ),
            "naturaleza": "simulación sintética local",
        }
        mediciones[cantidad_eventos] = medicion
        filas_reporte.append(medicion)

    if resumen_representativo is None:
        raise RuntimeError("No se obtuvo el resumen representativo esperado.")
    return pd.DataFrame(filas_reporte), mediciones, resumen_representativo


def crear_resumen_eventos(resumen: ResumenFlujo) -> pd.DataFrame:
    """Crea el reporte pequeño de distribución de eventos sintéticos."""
    return pd.DataFrame(
        [
            {
                "tipo_evento": tipo,
                "cantidad": resumen["conteos_por_tipo"][tipo],
                "porcentaje": resumen["porcentajes_por_tipo"][tipo],
                "naturaleza": "evento sintético académico",
            }
            for tipo in TIPOS_EVENTO
        ]
    )


def guardar_reportes_velocidad(
    directorio: Path,
    benchmark: pd.DataFrame,
    resumen_eventos: pd.DataFrame,
) -> dict[str, Path]:
    """Guarda únicamente métricas agregadas, nunca los eventos individuales."""
    directorio.mkdir(parents=True, exist_ok=True)
    rutas = {
        "benchmark_velocidad": directorio / "benchmark_velocidad.csv",
        "resumen_eventos": directorio / "resumen_eventos.csv",
    }
    benchmark.to_csv(rutas["benchmark_velocidad"], index=False)
    resumen_eventos.to_csv(rutas["resumen_eventos"], index=False)
    return rutas


def generar_conclusion_velocidad(medicion: MedicionVelocidad) -> str:
    """Genera una conclusión basada exclusivamente en el benchmark local."""
    return (
        f"La simulación local procesó {medicion['eventos_por_segundo']:,.0f} "
        "eventos sintéticos por segundo para esta prueba. Esto ilustra que, "
        "cuando los datos llegan continuamente, también importa la rapidez para "
        "recibirlos y procesarlos. El resultado pertenece exclusivamente a esta "
        "simulación académica y no representa el rendimiento de Spotify."
    )
