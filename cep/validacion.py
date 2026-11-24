"""
Validación de entradas antes de calcular.

Cada función revisa que los datos tengan sentido para el cálculo que sigue y, si no
lo tienen, detiene el cálculo con un mensaje claro (excepción DatosInvalidos).
La interfaz muestra ese mensaje en lugar de un error técnico o de un resultado
indefinido (división por cero, NaN, límites que colapsan).

Casos controlados:
  - tamaños de muestra o de lote iguales a cero, negativos o vacíos;
  - defectuosos mayores que el tamaño de muestra, conteos negativos;
  - subgrupos vacíos, de tamaño distinto o fuera de la tabla de constantes (2 a 25);
  - desviación estándar (σ, R̄ o S̄) igual a cero;
  - límites de especificación invertidos (LIE ≥ LSE);
  - datos insuficientes para la prueba o la carta pedida.
"""
import math

import numpy as np

from .constantes import N_MAX, N_MIN


class DatosInvalidos(ValueError):
    """Los datos no permiten hacer el cálculo pedido. El texto explica por qué y qué hacer."""


def exigir(condicion, mensaje):
    if not condicion:
        raise DatosInvalidos(mensaje)


def _finito(v):
    try:
        return v is not None and math.isfinite(float(v))
    except (TypeError, ValueError):
        return False


# ------------------------------------------------------------ tamaños -------
def tamano(n, nombre="n", minimo=1, entero=True):
    """Tamaño de muestra o de lote: número finito ≥ mínimo (entero, salvo en fórmulas continuas)."""
    exigir(_finito(n), f"El tamaño {nombre} está vacío o no es un número.")
    exigir(float(n) >= minimo, f"El tamaño {nombre} debe ser al menos {minimo} (se recibió {float(n):g}).")
    if entero:
        exigir(float(n) == int(n), f"El tamaño {nombre} debe ser un número entero (se recibió {float(n):g}).")
        return int(n)
    return float(n)


def proporcion(p, nombre="p'"):
    exigir(_finito(p) and 0 <= float(p) <= 1, f"La fracción {nombre} debe estar entre 0 y 1 (se recibió {p}).")
    return float(p)


def muestra_en_lote(n, N, nombre="n"):
    exigir(n <= N, f"La muestra {nombre} = {n} no puede ser mayor que el lote N = {N}.")


# ------------------------------------------------------------ atributos -----
def conteos(conteo, n=None, tipo="defectuosos"):
    """Conteos por subgrupo (defectuosos o defectos) y, si aplica, tamaños de muestra."""
    c = np.asarray(conteo, float)
    exigir(c.size > 0, "No hay subgrupos con conteos.")
    exigir(np.all(np.isfinite(c)), "Hay conteos vacíos o que no son números.")
    exigir(np.all(c >= 0), "Hay conteos negativos: un número de defectuosos o defectos no puede ser menor que 0.")
    if n is not None:
        nn = np.full(c.size, float(n)) if np.isscalar(n) else np.asarray(n, float)
        exigir(nn.size == c.size, "Hay distinto número de tamaños de muestra que de conteos.")
        exigir(np.all(np.isfinite(nn)), "Hay tamaños de muestra vacíos o que no son números.")
        malos = [i + 1 for i, v in enumerate(nn) if v <= 0]
        exigir(not malos, "Hay subgrupos con tamaño de muestra n = 0 o negativo (subgrupos "
                          f"{_lista(malos)}). Cada subgrupo debe tener al menos una unidad inspeccionada.")
        if tipo == "defectuosos":
            exceso = [i + 1 for i in range(c.size) if c[i] > nn[i]]
            exigir(not exceso, "Hay subgrupos con más defectuosos que unidades inspeccionadas (subgrupos "
                               f"{_lista(exceso)}). Revise que la columna de conteo y la de tamaño no estén cruzadas.")


def subgrupos_usados(incluidos, minimo=2, que="subgrupos"):
    k = int(np.sum(incluidos))
    exigir(k >= minimo, f"Quedan {k} {que} para calcular los límites y se necesitan al menos {minimo}. "
                        "Reduzca los puntos excluidos o cargue más datos.")
    return k


# ------------------------------------------------------------ variables -----
def subgrupos(grupos, n_min=N_MIN, n_max=N_MAX, k_min=2):
    """Subgrupos para cartas X̄-R / X̄-S: no vacíos, numéricos, del mismo tamaño y n en la tabla."""
    exigir(grupos is not None and len(grupos) > 0, "No hay subgrupos: cargue datos en el paso 3.")
    tam = [len(g) for g in grupos]
    vacios = [i + 1 for i, t in enumerate(tam) if t == 0]
    exigir(not vacios, f"Hay subgrupos vacíos (subgrupos {_lista(vacios)}).")
    for i, g in enumerate(grupos):
        exigir(np.all(np.isfinite(np.asarray(g, float))), f"El subgrupo {i + 1} tiene valores vacíos o no numéricos.")
    exigir(len(set(tam)) == 1, f"Los subgrupos tienen tamaños distintos ({_lista(sorted(set(tam)))}). Las cartas "
                               "X̄-R y X̄-S necesitan el mismo n en todos los subgrupos.")
    n = tam[0]
    exigir(n_min <= n <= n_max, f"El tamaño de subgrupo n = {n} está fuera de la tabla de constantes ({n_min} a "
                                f"{n_max}). Con n = 1 use la carta I-MR.")
    exigir(len(grupos) >= k_min, f"Hay {len(grupos)} subgrupo(s) y se necesitan al menos {k_min} para estimar límites.")
    return n


def individuales(x, minimo=2, que="la carta I-MR"):
    x = np.asarray(x, float)
    exigir(x.size >= minimo, f"Hay {x.size} dato(s) y {que} necesita al menos {minimo}.")
    exigir(np.all(np.isfinite(x)), "Hay datos vacíos o no numéricos.")
    return x


def sigma_positiva(sigma, origen="σ"):
    """Desviación estándar positiva: con σ = 0 los límites colapsan y los índices se dividen entre cero."""
    exigir(_finito(sigma), f"La desviación estándar ({origen}) no se pudo calcular.")
    exigir(float(sigma) > 0, f"La variabilidad es nula ({origen} = 0): todos los datos usados son iguales. Así no se "
                             "pueden calcular límites de control ni índices de capacidad. Revise la resolución del "
                             "instrumento de medición o si los datos se copiaron repetidos.")
    return float(sigma)


# ------------------------------------------------------- especificaciones ---
def especificaciones(lie=None, lse=None, exigir_una=True):
    if exigir_una:
        exigir(lie is not None or lse is not None, "Indique al menos un límite de especificación (LIE o LSE).")
    for nombre, v in (("LIE", lie), ("LSE", lse)):
        exigir(v is None or _finito(v), f"El {nombre} no es un número válido.")
    if lie is not None and lse is not None:
        exigir(lie < lse, f"Los límites de especificación están invertidos o son iguales (LIE = {lie:g}, "
                          f"LSE = {lse:g}). El LIE debe ser menor que el LSE.")


def _lista(v, maximo=8):
    v = list(v)
    txt = ", ".join(str(x) for x in v[:maximo])
    return txt + (f" y {len(v) - maximo} más" if len(v) > maximo else "")
