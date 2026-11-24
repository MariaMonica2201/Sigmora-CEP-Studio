"""
Módulo 2. Gráficos de control por variables (Fase I y Fase II).

Fórmulas (Módulo Académico 4.7 y hoja "Fórmulas control"):
  Carta X̄ :  LCS = X̿ + Z_{α/2}·σ/√n ,  LC = X̿ ,  LCI = X̿ − Z_{α/2}·σ/√n
             (con Z_{α/2}=3 equivale a X̿ ± A2·R̄ o X̿ ± A3·S̄)
  Carta R :  LCS = D4·R̄ , LC = R̄ , LCI = D3·R̄ ;  σ = R̄/d2
  Carta S :  LCS = B4·S̄ , LC = S̄ , LCI = B3·S̄ ;  σ = S̄/c4
  Carta I-MR (pedida en el enunciado): es la carta X̄-R aplicada con n = 1 para
  los individuos y rangos móviles de 2 observaciones consecutivas, por lo que
  σ = MR̄/d2(n=2) y LCS_MR = D4(n=2)·MR̄, LCI_MR = D3(n=2)·MR̄ = 0.

Fase I: se estiman los límites con los datos históricos; los subgrupos con causa
especial identificada se excluyen ("cepillado") y los límites se recalculan.
Fase II: los límites de Fase I (X̿ y σ) se usan para monitorear datos nuevos,
con el tamaño de muestra de monitoreo (que puede ser distinto al de Fase I).
"""
import numpy as np

from . import validacion as val
from .constantes import factor


def _carta(nombre, valores, lc, lcs, lci, etiquetas, unidad=""):
    m = len(valores)
    return {
        "nombre": nombre,
        "valores": np.asarray(valores, dtype=float),
        "lc": np.full(m, float(lc)) if np.isscalar(lc) else np.asarray(lc, float),
        "lcs": np.full(m, float(lcs)) if np.isscalar(lcs) else np.asarray(lcs, float),
        "lci": np.full(m, float(lci)) if np.isscalar(lci) else np.asarray(lci, float),
        "etiquetas": list(etiquetas),
        "unidad": unidad,
    }


def _incluidos(m, excluir):
    excluir = set(excluir or [])
    return np.array([(i + 1) not in excluir for i in range(m)])


# ------------------------------------------------------------- X̄ - R --------
def fase1_xr(grupos, etiquetas, z=3.0, excluir=None):
    """Carta X̄-R en Fase I. Requiere subgrupos de igual tamaño n (2..25)."""
    n = val.subgrupos(grupos)
    xb = np.array([np.mean(g) for g in grupos])
    r = np.array([np.max(g) - np.min(g) for g in grupos])
    inc = _incluidos(len(grupos), excluir)
    val.subgrupos_usados(inc)
    xbb, rbar = xb[inc].mean(), r[inc].mean()
    d2, d3_, d4 = factor("d2", n), factor("D3", n), factor("D4", n)
    sigma = val.sigma_positiva(rbar / d2, "R̄ y σ = R̄/d2")
    a = z * sigma / np.sqrt(n)
    cartas = [
        _carta("Carta X̄", xb, xbb, xbb + a, xbb - a, etiquetas),
        _carta("Carta R", r, rbar, d4 * rbar, d3_ * rbar, etiquetas),
    ]
    params = {
        "Tipo": "X̄-R", "n": n, "Z_α/2": z, "Subgrupos usados (k)": int(inc.sum()),
        "X̿": xbb, "R̄": rbar, "d2": d2, "D3": d3_, "D4": d4, "A2": factor("A2", n),
        "σ = R̄/d2": sigma,
        "LCS X̄": xbb + a, "LCI X̄": xbb - a, "LCS R": d4 * rbar, "LCI R": d3_ * rbar,
    }
    return {"cartas": cartas, "params": params, "media": xbb, "sigma": sigma, "n": n, "tipo": "X̄-R"}


# ------------------------------------------------------------- X̄ - S --------
def fase1_xs(grupos, etiquetas, z=3.0, excluir=None):
    """Carta X̄-S en Fase I. Requiere subgrupos de igual tamaño n (2..25)."""
    n = val.subgrupos(grupos)
    xb = np.array([np.mean(g) for g in grupos])
    s = np.array([np.std(g, ddof=1) for g in grupos])
    inc = _incluidos(len(grupos), excluir)
    val.subgrupos_usados(inc)
    xbb, sbar = xb[inc].mean(), s[inc].mean()
    c4, b3, b4 = factor("c4", n), factor("B3", n), factor("B4", n)
    sigma = val.sigma_positiva(sbar / c4, "S̄ y σ = S̄/c4")
    a = z * sigma / np.sqrt(n)
    cartas = [
        _carta("Carta X̄", xb, xbb, xbb + a, xbb - a, etiquetas),
        _carta("Carta S", s, sbar, b4 * sbar, b3 * sbar, etiquetas),
    ]
    params = {
        "Tipo": "X̄-S", "n": n, "Z_α/2": z, "Subgrupos usados (k)": int(inc.sum()),
        "X̿": xbb, "S̄": sbar, "c4": c4, "B3": b3, "B4": b4, "A3": factor("A3", n),
        "σ = S̄/c4": sigma,
        "LCS X̄": xbb + a, "LCI X̄": xbb - a, "LCS S": b4 * sbar, "LCI S": b3 * sbar,
    }
    return {"cartas": cartas, "params": params, "media": xbb, "sigma": sigma, "n": n, "tipo": "X̄-S"}


# ------------------------------------------------------------- I - MR -------
def fase1_imr(valores, etiquetas=None, z=3.0, excluir=None):
    """Carta de individuos y rangos móviles (n = 1, rango móvil de 2)."""
    x = val.individuales(valores)
    m = len(x)
    etiquetas = etiquetas if etiquetas is not None else list(range(1, m + 1))
    mr = np.r_[np.nan, np.abs(np.diff(x))]
    inc = _incluidos(m, excluir)
    val.subgrupos_usados(inc, que="datos")
    # un rango móvil se usa si ambos puntos que lo forman están incluidos
    inc_mr = inc & np.r_[False, inc[:-1]]
    val.exigir(inc_mr.sum() >= 1, "No queda ningún par de datos consecutivos incluidos para calcular el rango móvil.")
    xbar, mrbar = x[inc].mean(), np.nanmean(mr[inc_mr])
    d2, d3_, d4 = factor("d2", 2), factor("D3", 2), factor("D4", 2)
    sigma = val.sigma_positiva(mrbar / d2, "MR̄ y σ = MR̄/d2")
    cartas = [
        _carta("Carta I (individuos)", x, xbar, xbar + z * sigma, xbar - z * sigma, etiquetas),
        _carta("Carta MR (rango móvil)", mr, mrbar, d4 * mrbar, d3_ * mrbar, etiquetas),
    ]
    params = {
        "Tipo": "I-MR", "n": 1, "Z_α/2": z, "Observaciones usadas": int(inc.sum()),
        "X̄": xbar, "MR̄": mrbar, "d2 (n=2)": d2, "D4 (n=2)": d4, "σ = MR̄/d2": sigma,
        "LCS I": xbar + z * sigma, "LCI I": xbar - z * sigma, "LCS MR": d4 * mrbar, "LCI MR": d3_ * mrbar,
    }
    return {"cartas": cartas, "params": params, "media": xbar, "sigma": sigma, "n": 1, "tipo": "I-MR"}


# ------------------------------------------------------- cepillado auto ------
def cepillado_automatico(funcion, datos, etiquetas, z, max_iter=20):
    """Repite Fase I quitando los puntos fuera de límites de CUALQUIERA de las dos
    cartas hasta que todos los puntos restantes estén dentro (sección 4.7.1.2)."""
    excluir = set()
    historial = []
    for _ in range(max_iter):
        try:
            res = funcion(datos, etiquetas, z=z, excluir=excluir)
        except val.DatosInvalidos:
            break  # ya no quedan datos suficientes: se detiene con lo excluido hasta aquí
        nuevos = set()
        for c in res["cartas"]:
            for i, v in enumerate(c["valores"]):
                if (i + 1) in excluir or np.isnan(v):
                    continue
                if v > c["lcs"][i] + 1e-12 or v < c["lci"][i] - 1e-12:
                    nuevos.add(i + 1)
        if not nuevos or len(datos) - len(excluir | nuevos) < 2:
            break
        historial.append(sorted(nuevos))
        excluir |= nuevos
    return excluir, historial


# --------------------------------------------------------------- FASE II ----
def fase2(tipo, datos, etiquetas, media, sigma, z=3.0):
    """Monitoreo con parámetros de Fase I.

    tipo:  "X̄-R", "X̄-S" o "I-MR"
    datos: lista de subgrupos (X̄-R / X̄-S) o arreglo de individuos (I-MR)
    media, sigma: X̿' y σ' estimados en Fase I (o conocidos/estándar)
    El tamaño n de monitoreo se toma de los datos nuevos.
    """
    val.exigir(media is not None and np.isfinite(media), "Falta la media de Fase I: termine el paso 6.")
    val.sigma_positiva(sigma, "σ de Fase I")
    if tipo == "I-MR":
        x = val.individuales(datos, minimo=1, que="el monitoreo")
        mr = np.r_[np.nan, np.abs(np.diff(x))]
        mrbar = factor("d2", 2) * sigma
        cartas = [
            _carta("Carta I (Fase II)", x, media, media + z * sigma, media - z * sigma, etiquetas),
            _carta("Carta MR (Fase II)", mr, mrbar, factor("D4", 2) * mrbar, 0.0, etiquetas),
        ]
        return {"cartas": cartas, "n": 1}
    n = val.subgrupos(datos, k_min=1)
    xb = np.array([np.mean(g) for g in datos])
    a = z * sigma / np.sqrt(n)
    c1 = _carta("Carta X̄ (Fase II)", xb, media, media + a, media - a, etiquetas)
    if tipo == "X̄-R":
        r = np.array([np.max(g) - np.min(g) for g in datos])
        rbar = factor("d2", n) * sigma  # R̄ = d2·σ  (despeje de σ = R̄/d2)
        c2 = _carta("Carta R (Fase II)", r, rbar, factor("D4", n) * rbar, factor("D3", n) * rbar, etiquetas)
    else:
        s = np.array([np.std(g, ddof=1) for g in datos])
        sbar = factor("c4", n) * sigma  # S̄ = c4·σ
        c2 = _carta("Carta S (Fase II)", s, sbar, factor("B4", n) * sbar, factor("B3", n) * sbar, etiquetas)
    return {"cartas": [c1, c2], "n": n}
