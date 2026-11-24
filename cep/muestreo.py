"""
Módulo 7. Muestreo de aceptación por atributos.

Fórmulas (Módulo Académico cap. 5, presentación "Muestreo para la inspección
por atributos" y hoja "Fórmulas control", sección 7):
  Plan simple (n, c):  Pa = P(x ≤ c)
     Hipergeométrica: Σ C(k,x)·C(N−k,n−x)/C(N,n)  (k = p'·N defectuosos en el lote; k debe ser
                      entero: si p'·N no lo es se usa round(p'·N) y la app lo avisa, ver defectuosos_en_lote)
     Binomial:        Σ C(n,x)·p'^x·(1−p')^(n−x)
     Poisson:         Σ e^{−λ}λ^x/x!,  λ = n·p'
  Riesgos: 1 − α = Pa(NAC) (riesgo del productor α) ;  β = Pa(LTPD) (riesgo del consumidor)
  AOQ = Pa·p'·(N − n)/N  ≈ Pa·p' ;  AOQL = máximo de la curva AOQ
  IQL (nivel de calidad indiferente): p' con Pa = 0,5
  Plan doble (n1, c1, n2, c2): se acepta si d1 ≤ c1; se rechaza si d1 > c2; si
     c1 < d1 ≤ c2 se toma la 2ª muestra y se acepta si d1 + d2 ≤ c2.
     ASN = n1·P1 + (n1 + n2)(1 − P1), P1 = P(decidir con la 1ª muestra)
     Pa = P(d1 ≤ c1) + Σ_{d1=c1+1}^{c2} P(d1)·P(d2 ≤ c2 − d1 | d1)
     Con lote finito (hipergeométrica) la 2ª muestra sale de lo que QUEDA del lote:
       P(d2 ≤ c2 − d1 | d1) = H(c2 − d1; N − n1, D − d1, n2),  D = p'·N defectuosos.
     Con Binomial o Poisson (lote grande o flujo de lotes) la fracción no cambia y la
     2ª muestra usa la misma p'.
  Diseño — Método matemático (ecuaciones 5.5–5.12):
     λ1 = [(|Zα| + |Zβ|·√(LTPD/NAC)) / (LTPD/NAC − 1)]² ;  λ2 = λ1·LTPD/NAC
     c1 = λ1 + |Zα|·√λ1 ;  c2 = λ2 − |Zβ|·√λ2 ;  c = (c1 + c2)/2
     n1 = λ1/NAC ; n2 = λ2/LTPD ; n = (n1 + n2)/2
  MIL-STD-105E: letra código (Tabla de tamaño de muestra) y tabla maestra de
     inspección normal, muestreo simple (presentación de muestreo, diapositivas 16–17).
"""
import math

import numpy as np
import pandas as pd

from . import validacion as val
from .estadistica import (binom_cdf, binom_pmf, hiper_cdf, hiper_pmf, poisson_cdf, poisson_pmf, z_de_prob)

DISTRIBUCIONES = ("Binomial", "Hipergeométrica", "Poisson")


# ------------------------------------------------ defectuosos en el lote ----
def defectuosos_en_lote(p, N):
    """Número de defectuosos D de un lote finito a partir de la fracción p'.

    En un lote real D es un número entero. Si p'·N no es entero (p. ej. 80 · 0,03 = 2,4) se usa el
    entero más cercano, D = round(p'·N), y la fracción con la que realmente se calcula es D/N.
    Devuelve (D, exacto, p_efectiva).
    """
    bruto = p * N
    D = int(round(bruto))
    exacto = abs(bruto - D) < 1e-9
    return D, exacto, D / N


def aviso_redondeo(p, N, nombre="p'"):
    """Texto para la interfaz cuando p'·N no es entero (None si es exacto)."""
    D, exacto, pe = defectuosos_en_lote(p, N)
    if exacto:
        return None
    c = lambda v, f="g": format(v, f).replace(".", ",")  # noqa: E731 (coma decimal)
    return (f"{nombre} · N = {c(p)} · {N} = {c(p * N, '.4g')} no es un número entero de defectuosos. La distribución "
            f"hipergeométrica necesita un número entero: se calcula con D = {D} defectuosos, es decir "
            f"{nombre} efectiva = {D}/{N} = {c(pe, '.5g')}. Para evitar la aproximación, escriba D directamente.")


def fracciones_exactas(ps, N):
    """Para curvas OC hipergeométricas: deja sólo fracciones D/N con D entero (sin aproximar)."""
    return np.unique([defectuosos_en_lote(p, N)[2] for p in ps])


def _cdf(x, n, p, dist, N=None):
    if x < 0:
        return 0.0
    if dist == "Hipergeométrica":
        K = defectuosos_en_lote(p, N)[0]
        return hiper_cdf(x, N, K, n)
    if dist == "Poisson":
        return poisson_cdf(x, n * p)
    return binom_cdf(x, n, p)


def _pmf(x, n, p, dist, N=None):
    if dist == "Hipergeométrica":
        K = defectuosos_en_lote(p, N)[0]
        return hiper_pmf(x, N, K, n)
    if dist == "Poisson":
        return poisson_pmf(x, n * p)
    return binom_pmf(x, n, p)


def _validar_plan(n, c, p, dist, N, nombre_n="n", nombre_c="c"):
    val.tamano(n, nombre_n)
    val.exigir(c is not None and float(c) >= 0 and float(c) == int(c),
               f"El número de aceptación {nombre_c} debe ser un entero mayor o igual que 0.")
    val.proporcion(p)
    val.exigir(dist in DISTRIBUCIONES, f"Distribución no reconocida: {dist}.")
    if dist == "Hipergeométrica":
        val.tamano(N, "del lote N", minimo=2)
        val.muestra_en_lote(n, N, nombre_n)


# ---------------------------------------------------------------- simple ----
def pa_simple(n, c, p, dist="Binomial", N=None):
    _validar_plan(n, c, p, dist, N)
    return _cdf(c, n, p, dist, N)


def curva_oc_simple(n, c, ps, dist="Binomial", N=None):
    if dist == "Hipergeométrica":
        ps = fracciones_exactas(ps, N)  # en un lote finito sólo existen fracciones D/N
    filas = []
    for p in ps:
        pa = pa_simple(n, c, p, dist, N)
        aoq = pa * p * ((N - n) / N if N else 1.0)
        filas.append({"p'": p, "Pa": pa, "AOQ": aoq})
    return pd.DataFrame(filas)


def riesgos(n, c, nac, ltpd, dist="Binomial", N=None):
    pa_nac = pa_simple(n, c, nac, dist, N)
    pa_ltpd = pa_simple(n, c, ltpd, dist, N)
    return {"Pa(NAC) = 1 − α": pa_nac, "α (riesgo del productor)": 1 - pa_nac,
            "β = Pa(LTPD) (riesgo del consumidor)": pa_ltpd}


def aoql(n, c, dist="Binomial", N=None, pmax=None):
    pmax = pmax or min(1.0, max(0.05, 3 * (c + 1) / n))
    ps = np.linspace(1e-6, pmax, 800)
    df = curva_oc_simple(n, c, ps, dist, N)
    i = int(df["AOQ"].idxmax())
    return float(df.loc[i, "AOQ"]), float(df.loc[i, "p'"])


def iql(n, c, dist="Binomial", N=None):
    """p' con Pa = 0,5 (bisección)."""
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if pa_simple(n, c, mid, dist, N) > 0.5:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def prob_aceptar_m_lotes(pa, m):
    """Probabilidad de aceptar los m lotes (Binomial con x = m): Pa^m (ejemplo MIL-STD del módulo)."""
    return pa ** m


# ----------------------------------------------------------------- doble ----
def pa_doble(n1, c1, n2, c2, p, dist="Binomial", N=None):
    """Probabilidad de aceptación y ASN del plan doble (árbol de decisión del módulo 5.7.1).

    Regla: se acepta si d1 ≤ c1; se rechaza si d1 > c2; si c1 < d1 ≤ c2 se toma la 2ª muestra
    y se acepta si d1 + d2 ≤ c2.
    Hipergeométrica (lote finito): la 2ª muestra se extrae del lote restante, N − n1 unidades
    con D − d1 defectuosos, porque las n1 unidades de la 1ª muestra ya salieron del lote.
    """
    _validar_plan(n1, c1, p, dist, N, "n1", "c1")
    _validar_plan(n2, c2, p, dist, N, "n2", "c2")
    val.exigir(c2 >= c1, "c2 debe ser mayor o igual que c1.")
    if dist == "Hipergeométrica":
        val.exigir(n1 + n2 <= N, f"n1 + n2 = {n1 + n2} no puede ser mayor que el lote N = {N}.")
        D = defectuosos_en_lote(p, N)[0]
    pa1 = _cdf(c1, n1, p, dist, N)  # acepta en la 1ª
    rech1 = 1 - _cdf(c2, n1, p, dist, N)  # rechaza en la 1ª (d1 > c2)
    pa2 = 0.0
    for d1 in range(c1 + 1, c2 + 1):
        p_d1 = _pmf(d1, n1, p, dist, N)
        if p_d1 == 0:
            continue
        if dist == "Hipergeométrica":
            p_seg = hiper_cdf(c2 - d1, N - n1, D - d1, n2)  # lote restante
        else:
            p_seg = _cdf(c2 - d1, n2, p, dist, N)
        pa2 += p_d1 * p_seg
    p1 = pa1 + rech1
    asn = n1 * p1 + (n1 + n2) * (1 - p1)
    extra = {}
    if dist == "Hipergeométrica":
        extra = {"D (defectuosos en el lote)": D, "p' efectiva = D/N": D / N}
    return {**extra, "Pa": pa1 + pa2, "Pa en 1ª muestra": pa1, "Pa en 2ª muestra": pa2,
            "Rechazo en 1ª muestra": rech1, "P1 (decidir con 1ª)": p1, "ASN": asn}


def curva_oc_doble(n1, c1, n2, c2, ps, dist="Binomial", N=None):
    if dist == "Hipergeométrica":
        ps = fracciones_exactas(ps, N)
    filas = []
    for p in ps:
        r = pa_doble(n1, c1, n2, c2, p, dist, N)
        filas.append({"p'": p, "Pa": r["Pa"], "Pa 1ª muestra": r["Pa en 1ª muestra"], "ASN": r["ASN"],
                      "AOQ": r["Pa"] * p})
    return pd.DataFrame(filas)


# -------------------------------------------------------- método matemático --
def disenar_plan(nac, ltpd, alfa, beta):
    """Método matemático de diseño (ec. 5.5 – 5.12). Zα y Zβ son valores de cola (P(Z > Zα) = α)."""
    val.exigir(0 < nac < ltpd < 1, "Debe cumplirse 0 < NAC < LTPD < 1.")
    val.exigir(0 < alfa < 0.5 and 0 < beta < 0.5, "α y β deben estar entre 0 y 0,5.")
    za, zb = z_de_prob(1 - alfa), z_de_prob(1 - beta)
    r = ltpd / nac
    lam1 = ((abs(za) + abs(zb) * math.sqrt(r)) / (r - 1)) ** 2
    lam2 = lam1 * r
    c1 = lam1 + abs(za) * math.sqrt(lam1)
    c2 = lam2 - abs(zb) * math.sqrt(lam2)
    c = (c1 + c2) / 2
    n1, n2 = lam1 / nac, lam2 / ltpd
    n = (n1 + n2) / 2
    pasos = pd.DataFrame({"Ecuación": ["Zα", "Zβ", "LTPD/NAC", "λ1 (5.5)", "λ2 (5.6)", "c1 (5.7)", "c2 (5.8)",
                                       "c (5.9)", "n1 (5.10)", "n2 (5.11)", "n (5.12)"],
                          "Valor": [za, zb, r, lam1, lam2, c1, c2, c, n1, n2, n]})
    n_fin, c_fin = int(math.ceil(n)), int(round(c))
    return {"pasos": pasos, "n": n, "c": c, "n_plan": n_fin, "c_plan": c_fin}


# ------------------------------------------------------------ MIL-STD-105E --
TAMANOS_LOTE = [(2, 8), (9, 15), (16, 25), (26, 50), (51, 90), (91, 150), (151, 280), (281, 500),
                (501, 1200), (1201, 3200), (3201, 10000), (10001, 35000), (35001, 150000),
                (150001, 500000), (500001, math.inf)]
LETRAS_NIVEL = {
    "I":   "AABCCDEFGHJKLMN",
    "II":  "ABCDEFGHJKLMNPQ",
    "III": "BCDEFGHJKLMNPQR",
}
LETRAS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R"]
TAMANO_MUESTRA = dict(zip(LETRAS, [2, 3, 5, 8, 13, 20, 32, 50, 80, 125, 200, 315, 500, 800, 1250, 2000]))
NAC_COLUMNAS = [0.010, 0.015, 0.025, 0.040, 0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.0, 1.5, 2.5, 4.0, 6.5,
                10, 15, 25, 40, 65, 100, 150, 250, 400, 650, 1000]
_PLANES = {0: (0, 1), 3: (1, 2), 4: (2, 3), 5: (3, 4), 6: (5, 6), 7: (7, 8), 8: (10, 11), 9: (14, 15),
           10: (21, 22), 11: (30, 31), 12: (44, 45)}


def letra_codigo(N, nivel="II"):
    for i, (lo, hi) in enumerate(TAMANOS_LOTE):
        if lo <= N <= hi:
            return LETRAS_NIVEL[nivel][i]
    raise val.DatosInvalidos("Tamaño de lote no válido: el lote debe tener al menos 2 unidades.")


def _celda(fila, col):
    """Contenido de la tabla maestra (inspección normal): (Ac, Re), '↑' o '↓'.
    La tabla tiene estructura diagonal; esta función la reproduce celda a celda."""
    k = fila + col - 14
    maximo = 12 if fila <= 4 else 10
    if k < 0:
        return "↓"
    if k == 1:
        return "↓" if fila == 0 else "↑"
    if k == 2:
        return "↑" if fila == len(LETRAS) - 1 else "↓"
    if k > maximo:
        return "↑"
    return _PLANES[k]


def plan_mil_std(N, nac, nivel="II"):
    """Plan de muestreo simple, inspección normal, MIL-STD-105E. Sigue las flechas de la tabla."""
    letra = letra_codigo(N, nivel)
    col = min(range(len(NAC_COLUMNAS)), key=lambda j: abs(NAC_COLUMNAS[j] - nac))
    fila = LETRAS.index(letra)
    pasos = [f"Lote N = {N:,} y nivel {nivel} → letra código {letra} (n = {TAMANO_MUESTRA[letra]})."]
    while True:
        c = _celda(fila, col)
        if isinstance(c, tuple):
            break
        nueva = fila + (1 if c == "↓" else -1)
        pasos.append(f"En la fila {LETRAS[fila]} con NAC {NAC_COLUMNAS[col]} hay una flecha {c}: "
                     f"se usa el primer plan {'abajo' if c == '↓' else 'arriba'} → fila {LETRAS[nueva]}.")
        fila = nueva
    letra_final = LETRAS[fila]
    n = TAMANO_MUESTRA[letra_final]
    if n >= N:
        pasos.append("El tamaño de muestra es mayor o igual al lote: se hace inspección 100 %.")
    pasos.append(f"Plan: letra {letra_final}, n = {n}, Ac = {c[0]}, Re = {c[1]}.")
    return {"letra inicial": letra, "letra": letra_final, "n": n, "Ac": c[0], "Re": c[1],
            "NAC tabla": NAC_COLUMNAS[col], "pasos": pasos}


def tabla_mil_std():
    """Reconstrucción de la tabla maestra de inspección normal para mostrarla en la app."""
    filas = []
    for i, L in enumerate(LETRAS):
        fila = {"Letra": L, "n": TAMANO_MUESTRA[L]}
        for j, a in enumerate(NAC_COLUMNAS):
            c = _celda(i, j)
            fila[str(a)] = f"{c[0]} {c[1]}" if isinstance(c, tuple) else c
        filas.append(fila)
    return pd.DataFrame(filas)
