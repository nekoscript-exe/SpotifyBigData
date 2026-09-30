"""Visualizaciones académicas de los resultados ya calculados.

Este módulo no vuelve a ejecutar los análisis ni modifica el dataset. Recibe
sus resultados agregados y genera archivos PNG mediante un backend no
interactivo de matplotlib.
"""

from numbers import Real
from pathlib import Path
from typing import TypedDict

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter
import pandas as pd

from src.calidad import ResumenDuplicados, ResumenFaltantes


TAMANO_FIGURA = (12, 7)
DPI = 160
COLOR_PRINCIPAL = "#1DB954"
COLOR_SECUNDARIO = "#1F77B4"
COLOR_CONTRASTE = "#E76F51"
COLOR_NEUTRO = "#64748B"
ATRIBUTOS_NORMALIZADOS = (
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "liveness",
    "speechiness",
)
ETIQUETAS_ATRIBUTOS = {
    "danceability": "Bailabilidad",
    "energy": "Energía",
    "loudness": "Sonoridad",
    "speechiness": "Contenido hablado",
    "acousticness": "Acústica",
    "instrumentalness": "Instrumentalidad",
    "liveness": "Presencia en vivo",
    "valence": "Valencia",
    "tempo": "Tempo",
    "duration_ms": "Duración",
}


class EspecificacionVisualizacion(TypedDict):
    """Metadatos de una visualización generada."""

    archivo: str
    titulo: str
    tema: str
    v_relacionada: str
    origen_datos: str
    naturaleza: str


ESPECIFICACIONES: tuple[EspecificacionVisualizacion, ...] = (
    {
        "archivo": "01_proyeccion_volumen.png",
        "titulo": "Crecimiento proyectado del volumen",
        "tema": "Disco y RAM por escala",
        "v_relacionada": "Volumen",
        "origen_datos": "proyeccion_escalabilidad",
        "naturaleza": "medición real (x1) y estimación matemática (x10+)",
    },
    {
        "archivo": "02_benchmark_carga.png",
        "titulo": "Tiempo de carga según cantidad de registros",
        "tema": "Costo local de lectura",
        "v_relacionada": "Volumen",
        "origen_datos": "benchmark_carga",
        "naturaleza": "medición real local",
    },
    {
        "archivo": "03_velocidad_eventos.png",
        "titulo": "Tiempo de procesamiento del flujo sintético",
        "tema": "Eventos y tiempo mediano",
        "v_relacionada": "Velocidad",
        "origen_datos": "benchmark_velocidad",
        "naturaleza": "simulación sintética local",
    },
    {
        "archivo": "04_calidad_datos.png",
        "titulo": "Indicadores de calidad del dataset",
        "tema": "Faltantes, duplicados y valores sospechosos",
        "v_relacionada": "Veracidad",
        "origen_datos": "resúmenes y consistencia de calidad",
        "naturaleza": "análisis descriptivo de datos reales",
    },
    {
        "archivo": "05_generos_popularidad.png",
        "titulo": "Géneros con mayor mediana de popularidad",
        "tema": "Top 10 de géneros",
        "v_relacionada": "Valor / Variedad",
        "origen_datos": "analisis_generos",
        "naturaleza": "análisis descriptivo",
    },
    {
        "archivo": "06_explicit_popularidad.png",
        "titulo": "Popularidad mediana: Explicit vs No explicit",
        "tema": "Comparación de grupos",
        "v_relacionada": "Valor",
        "origen_datos": "comparacion_explicit",
        "naturaleza": "análisis descriptivo",
    },
    {
        "archivo": "07_correlaciones_popularidad.png",
        "titulo": "Correlación entre popularidad y atributos musicales",
        "tema": "Correlaciones de Pearson",
        "v_relacionada": "Valor",
        "origen_datos": "correlaciones_popularidad",
        "naturaleza": "análisis descriptivo",
    },
    {
        "archivo": "08_perfil_alta_popularidad.png",
        "titulo": "Perfil musical: alta popularidad vs resto",
        "tema": "Medianas de atributos normalizados",
        "v_relacionada": "Valor",
        "origen_datos": "perfil_alta_popularidad",
        "naturaleza": "análisis descriptivo",
    },
)


def _numero(valor: object, contexto: str) -> float:
    """Convierte un escalar numérico validado a float."""
    if not isinstance(valor, Real):
        raise ValueError(f"Se esperaba un número en {contexto}; se recibió {valor!r}.")
    return float(valor)


def _numeros(dataframe: pd.DataFrame, columna: str) -> list[float]:
    """Extrae una columna numérica como valores nativos."""
    return [
        _numero(valor, f"{columna}[{posicion}]")
        for posicion, valor in enumerate(dataframe[columna].tolist())
    ]


def _textos(dataframe: pd.DataFrame, columna: str) -> list[str]:
    """Extrae una columna textual y rechaza valores de otro tipo."""
    valores: list[str] = []
    for posicion, valor in enumerate(dataframe[columna].tolist()):
        if not isinstance(valor, str):
            raise ValueError(
                f"Se esperaba texto en {columna}[{posicion}]; se recibió {valor!r}."
            )
        valores.append(valor)
    return valores


def _crear_figura(*, logaritmica: bool = False) -> tuple[Figure, Axes]:
    """Crea explícitamente una figura con un solo eje."""
    figura = Figure(figsize=TAMANO_FIGURA)
    ax = figura.add_subplot(
        1,
        1,
        1,
        xscale="log" if logaritmica else "linear",
        yscale="log" if logaritmica else "linear",
    )
    return figura, ax


def _preparar_ejes(ax: Axes) -> None:
    """Aplica un estilo sobrio y consistente a un eje de matplotlib."""
    ax.grid(axis="y", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=10)


def _guardar(figura: Figure, ruta: Path, margen_inferior: float = 0.10) -> Path:
    """Ajusta, guarda y cierra una figura para no acumular memoria."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    figura.tight_layout(rect=(0, margen_inferior, 1, 1))
    figura.savefig(ruta, dpi=DPI, format="png", facecolor="white")
    plt.close(figura)
    return ruta


def graficar_proyeccion_volumen(
    proyeccion: pd.DataFrame, directorio: Path
) -> Path:
    """Compara disco y RAM proyectados mediante escalas logarítmicas."""
    multiplicadores = _numeros(proyeccion, "multiplicador")
    disco_gb = [valor / 1024**3 for valor in _numeros(proyeccion, "almacenamiento_bytes")]
    memoria_gb = [valor / 1024**3 for valor in _numeros(proyeccion, "memoria_bytes")]
    etiquetas = _textos(proyeccion, "escala")

    figura, ax = _crear_figura(logaritmica=True)
    ax.plot(multiplicadores, disco_gb, marker="o", linewidth=2.4,
            color=COLOR_SECUNDARIO, label="Disco estimado")
    ax.plot(multiplicadores, memoria_gb, marker="o", linewidth=2.4,
            color=COLOR_PRINCIPAL, label="RAM estimada")
    ax.xaxis.set_ticks(multiplicadores, labels=etiquetas)
    ax.set_xlabel("Multiplicador de registros")
    ax.set_ylabel("Capacidad estimada (GB, escala logarítmica)")
    ax.set_title("Crecimiento proyectado del volumen", fontsize=16, pad=14)
    ax.legend(fontsize=10)
    ax.grid(which="both", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    figura.text(
        0.5,
        0.025,
        "x1 parte del dataset medido; x10 en adelante son proyecciones matemáticas. "
        "Proyección basada en el tamaño real del dataset actual.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    return _guardar(figura, directorio / ESPECIFICACIONES[0]["archivo"], 0.12)


def graficar_benchmark_carga(
    benchmark: pd.DataFrame, directorio: Path
) -> Path:
    """Representa tiempo mediano de carga frente a registros leídos."""
    filas = _numeros(benchmark, "filas_cargadas")
    tiempos = _numeros(benchmark, "tiempo_mediano_segundos")

    figura, ax = _crear_figura()
    ax.plot(filas, tiempos, marker="o", markersize=7, linewidth=2.4,
            color=COLOR_SECUNDARIO)
    ax.fill_between(filas, tiempos, alpha=0.12, color=COLOR_SECUNDARIO)
    ax.set_title("Tiempo de carga según cantidad de registros", fontsize=16, pad=14)
    ax.set_xlabel("Registros cargados")
    ax.set_ylabel("Tiempo mediano (segundos)")
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    _preparar_ejes(ax)
    figura.text(
        0.5,
        0.025,
        "Benchmark local con tres repeticiones; depende del equipo y de la caché del sistema.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    return _guardar(figura, directorio / ESPECIFICACIONES[1]["archivo"])


def graficar_velocidad_eventos(
    benchmark: pd.DataFrame, directorio: Path
) -> Path:
    """Muestra el costo temporal del flujo sintético según su tamaño."""
    eventos = _numeros(benchmark, "eventos")
    tiempos = _numeros(benchmark, "tiempo_mediano_segundos")

    figura, ax = _crear_figura()
    ax.plot(eventos, tiempos, marker="o", markersize=7, linewidth=2.4,
            color=COLOR_CONTRASTE)
    ax.fill_between(eventos, tiempos, alpha=0.12, color=COLOR_CONTRASTE)
    ax.set_title("Tiempo de procesamiento del flujo sintético", fontsize=16, pad=14)
    ax.set_xlabel("Cantidad de eventos sintéticos")
    ax.set_ylabel("Tiempo mediano (segundos)")
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    _preparar_ejes(ax)
    figura.text(
        0.5,
        0.025,
        "Simulación sintética local: los eventos no proceden de Spotify y el resultado no "
        "representa su infraestructura real.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    return _guardar(figura, directorio / ESPECIFICACIONES[2]["archivo"])


def graficar_calidad_datos(
    resumen_faltantes: ResumenFaltantes,
    resumen_duplicados: ResumenDuplicados,
    consistencia: pd.DataFrame,
    directorio: Path,
) -> Path:
    """Resume incidencias de calidad sin tratar sospechas como errores."""
    ceros: dict[str, float] = {}
    columnas = consistencia.loc[:, ["columna", "ceros"]]
    for columna, cantidad in columnas.itertuples(index=False, name=None):
        if isinstance(columna, str) and columna in {
            "duration_ms", "tempo", "time_signature"
        }:
            ceros[columna] = _numero(cantidad, f"ceros de {columna}")

    etiquetas = [
        "Valores faltantes",
        "Duplicados exactos\nexcedentes",
        "duration_ms = 0",
        "tempo = 0",
        "time_signature = 0",
    ]
    valores = [
        float(resumen_faltantes["valores_faltantes"]),
        float(resumen_duplicados["filas_duplicadas"]),
        ceros["duration_ms"],
        ceros["tempo"],
        ceros["time_signature"],
    ]
    colores = [COLOR_SECUNDARIO, COLOR_SECUNDARIO, COLOR_CONTRASTE,
               COLOR_CONTRASTE, COLOR_CONTRASTE]

    figura, ax = _crear_figura()
    barras = ax.bar(etiquetas, valores, color=colores, width=0.68)
    ax.bar_label(barras, labels=[f"{valor:,.0f}" for valor in valores], padding=4)
    ax.set_title("Indicadores de calidad del dataset", fontsize=16, pad=14)
    ax.set_xlabel("Indicador")
    ax.set_ylabel("Cantidad de incidencias")
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    _preparar_ejes(ax)
    figura.text(
        0.5,
        0.025,
        "Azul: faltantes o duplicados detectados. Naranja: valores potencialmente "
        "sospechosos; no se clasifican automáticamente como errores.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    return _guardar(figura, directorio / ESPECIFICACIONES[3]["archivo"], 0.12)


def graficar_generos_popularidad(
    generos: pd.DataFrame, directorio: Path
) -> Path:
    """Muestra un top legible de géneros por mediana de popularidad."""
    top = generos.sort_values(
        ["popularidad_mediana", "tracks_unicos", "track_genre"],
        ascending=[False, False, True],
    ).head(10)
    top = top.iloc[::-1]
    etiquetas = _textos(top, "track_genre")
    popularidades = _numeros(top, "popularidad_mediana")
    cantidades = _numeros(top, "tracks_unicos")

    figura, ax = _crear_figura()
    barras = ax.barh(etiquetas, popularidades, color=COLOR_PRINCIPAL)
    ax.bar_label(
        barras,
        labels=[f"{valor:g}  ({cantidad:,.0f} tracks)"
                for valor, cantidad in zip(popularidades, cantidades)],
        padding=5,
        fontsize=9,
    )
    ax.set_xlim(0, max(popularidades) * 1.25)
    ax.set_title(
        "Géneros con mayor mediana de popularidad en el dataset",
        fontsize=16,
        pad=14,
    )
    ax.set_xlabel("Mediana de popularity")
    ax.set_ylabel("Género")
    _preparar_ejes(ax)
    figura.text(
        0.5,
        0.025,
        "Asociaciones únicas track_id + track_genre; resultados descriptivos del dataset.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    return _guardar(figura, directorio / ESPECIFICACIONES[4]["archivo"])


def graficar_explicit_popularidad(
    comparacion: pd.DataFrame, directorio: Path
) -> Path:
    """Compara popularidad mediana sin combinar escalas incompatibles."""
    ordenada = comparacion.sort_values("explicit")
    medianas = _numeros(ordenada, "popularidad_mediana")
    porcentajes = _numeros(ordenada, "porcentaje")
    grupos = ["No explicit", "Explicit"]
    etiquetas = [
        f"{grupo}\n({porcentaje:.1f}% de tracks)"
        for grupo, porcentaje in zip(grupos, porcentajes)
    ]

    figura, ax = _crear_figura()
    barras = ax.bar(etiquetas, medianas,
                    color=[COLOR_SECUNDARIO, COLOR_CONTRASTE], width=0.55)
    ax.bar_label(barras, labels=[f"{valor:g}" for valor in medianas], padding=5,
                 fontsize=11)
    ax.set_ylim(0, max(medianas) * 1.25)
    ax.set_title("Popularidad mediana: Explicit vs No explicit", fontsize=16, pad=14)
    ax.set_xlabel("Grupo")
    ax.set_ylabel("Mediana de popularity")
    _preparar_ejes(ax)
    figura.text(
        0.5,
        0.025,
        "Comparación descriptiva dentro del dataset; no implica causalidad.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    return _guardar(figura, directorio / ESPECIFICACIONES[5]["archivo"])


def graficar_correlaciones_popularidad(
    correlaciones: pd.DataFrame, directorio: Path
) -> Path:
    """Representa correlaciones positivas y negativas alrededor de cero."""
    etiquetas_originales = _textos(correlaciones, "atributo")
    etiquetas = [ETIQUETAS_ATRIBUTOS.get(valor, valor) for valor in etiquetas_originales]
    valores = _numeros(correlaciones, "correlacion_pearson")
    colores = [COLOR_SECUNDARIO if valor >= 0 else COLOR_CONTRASTE for valor in valores]
    limite = max(abs(valor) for valor in valores) * 1.35

    figura, ax = _crear_figura()
    barras = ax.barh(etiquetas, valores, color=colores)
    ax.invert_yaxis()
    ax.axvline(0, color="#111827", linewidth=1)
    ax.set_xlim(-limite, limite)
    ax.bar_label(
        barras,
        labels=[f"{valor:+.3f}" for valor in valores],
        padding=4,
        fontsize=9,
    )
    ax.set_title(
        "Correlación entre popularidad y atributos musicales",
        fontsize=16,
        pad=14,
    )
    ax.set_xlabel("Coeficiente de Pearson")
    ax.set_ylabel("Atributo")
    ax.grid(axis="x", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    figura.text(
        0.5,
        0.025,
        "Ordenadas por magnitud absoluta. Correlación no implica causalidad.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    return _guardar(figura, directorio / ESPECIFICACIONES[6]["archivo"])


def graficar_perfil_alta_popularidad(
    perfil: pd.DataFrame, directorio: Path
) -> Path:
    """Compara solo atributos normalizados para mantener una escala común."""
    filtrado = perfil.loc[perfil["atributo"].isin(ATRIBUTOS_NORMALIZADOS)].copy()
    orden = {atributo: posicion for posicion, atributo in enumerate(ATRIBUTOS_NORMALIZADOS)}
    filtrado["orden"] = filtrado["atributo"].map(orden)
    filtrado = filtrado.sort_values("orden")
    atributos = _textos(filtrado, "atributo")
    etiquetas = [ETIQUETAS_ATRIBUTOS.get(valor, valor) for valor in atributos]
    altas = _numeros(filtrado, "mediana_alta_popularidad")
    resto = _numeros(filtrado, "mediana_resto")
    posiciones = list(range(len(etiquetas)))
    posiciones_altas = [posicion + 0.19 for posicion in posiciones]
    posiciones_resto = [posicion - 0.19 for posicion in posiciones]

    figura, ax = _crear_figura()
    barras_resto = ax.barh(
        posiciones_resto,
        resto,
        height=0.36,
        color=COLOR_NEUTRO,
        label="Resto",
    )
    barras_altas = ax.barh(
        posiciones_altas,
        altas,
        height=0.36,
        color=COLOR_PRINCIPAL,
        label="Alta popularidad",
    )
    ax.bar_label(
        barras_resto,
        labels=[f"{valor:.4f}" for valor in resto],
        padding=3,
        fontsize=8,
    )
    ax.bar_label(
        barras_altas,
        labels=[f"{valor:.4f}" for valor in altas],
        padding=3,
        fontsize=8,
    )
    ax.yaxis.set_ticks(posiciones, labels=etiquetas)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_title("Perfil musical: alta popularidad vs resto", fontsize=16, pad=14)
    ax.set_xlabel("Mediana del atributo normalizado (0–1)")
    ax.set_ylabel("Atributo")
    ax.legend(fontsize=10)
    ax.grid(axis="x", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    figura.text(
        0.5,
        0.025,
        "Comparación descriptiva basada en el cuartil superior de popularity; "
        "tempo y duración se excluyen por usar otras escalas.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    return _guardar(figura, directorio / ESPECIFICACIONES[7]["archivo"], 0.12)


def crear_resumen_visualizaciones() -> pd.DataFrame:
    """Crea el catálogo que documenta origen y naturaleza de cada figura."""
    return pd.DataFrame(ESPECIFICACIONES)


def generar_visualizaciones(
    directorio_graficas: Path,
    directorio_reportes: Path,
    proyeccion: pd.DataFrame,
    benchmark_carga: pd.DataFrame,
    benchmark_velocidad: pd.DataFrame,
    resumen_faltantes: ResumenFaltantes,
    resumen_duplicados: ResumenDuplicados,
    consistencia: pd.DataFrame,
    analisis_generos: pd.DataFrame,
    comparacion_explicit: pd.DataFrame,
    correlaciones_popularidad: pd.DataFrame,
    perfil_alta_popularidad: pd.DataFrame,
) -> tuple[list[Path], pd.DataFrame]:
    """Genera las ocho figuras y guarda su catálogo descriptivo."""
    directorio_graficas.mkdir(parents=True, exist_ok=True)
    rutas = [
        graficar_proyeccion_volumen(proyeccion, directorio_graficas),
        graficar_benchmark_carga(benchmark_carga, directorio_graficas),
        graficar_velocidad_eventos(benchmark_velocidad, directorio_graficas),
        graficar_calidad_datos(
            resumen_faltantes,
            resumen_duplicados,
            consistencia,
            directorio_graficas,
        ),
        graficar_generos_popularidad(analisis_generos, directorio_graficas),
        graficar_explicit_popularidad(comparacion_explicit, directorio_graficas),
        graficar_correlaciones_popularidad(
            correlaciones_popularidad, directorio_graficas
        ),
        graficar_perfil_alta_popularidad(
            perfil_alta_popularidad, directorio_graficas
        ),
    ]
    resumen = crear_resumen_visualizaciones()
    directorio_reportes.mkdir(parents=True, exist_ok=True)
    resumen.to_csv(directorio_reportes / "resumen_visualizaciones.csv", index=False)
    return rutas, resumen
