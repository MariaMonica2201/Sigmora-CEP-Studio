"""
Módulo 5. Capacidad del proceso.

Fórmulas (Módulo Académico cap. 3, presentación "Análisis de capacidad de
procesos" y hoja "Fórmulas control", sección 1):
  T = LSE − LIE ;  VN = (LSE + LIE)/2 ;  %ancho de banda = (1/Cp)·100
  Cp  = (LSE − LIE)/(6σ) ;  Cpu = (LSE − X̄)/(3σ) ;  Cpl = (X̄ − LIE)/(3σ)
  Cpk = mín{Cpu, Cpl}
  Z_LSE = (LSE − X̄)/σ ,  %PNC_LSE = P(Z ≥ Z_LSE)
  Z_LIE = (LIE − X̄)/σ ,  %PNC_LIE = P(Z ≤ Z_LIE)
  σ = R̄/d2  ó  S̄/c4
  Intervalos de confianza (100(1−α) %):
    Cp·√(χ²_{1−α/2,n−1}/(n−1)) ≤ Cp ≤ Cp·√(χ²_{α/2,n−1}/(n−1))
    Cpk·[1 − Z_{α/2}·√(1/(9nCpk²) + 1/(2(n−1)))] ≤ Cpk ≤ Cpk·[1 + Z_{α/2}·√(...)]
  Ventana de operación: valores de X̄ para los que %PNC por cada límite ≤ objetivo.
"""
import math

import numpy as np
import pandas as pd
from scipy import stats

from . import validacion as val
from .estadistica import phi, z_de_prob


def indices(media, sigma, lse=None, lie=None):
    """Calcula índices de capacidad y fracción no conforme. Acepta especificación unilateral."""
    val.especificaciones(lie, lse)
    val.exigir(media is not None and np.isfinite(media), "La media del proceso no es un número válido.")
    val.sigma_positiva(sigma)
    r = {"X̄": media, "σ": sigma, "LSE": lse, "LIE": lie}
    if lse is not None and lie is not None:
        T = lse - lie
        vn = (lse + lie) / 2
        cp = T / (6 * sigma)
        r.update({"T = LSE − LIE": T, "VN = (LSE+LIE)/2": vn, "Cp": cp,
                  "% ancho de banda = 100/Cp": 100 / cp if cp > 0 else np.nan})
        xi = (media - vn) / sigma
        r["Desplazamiento (X̄−VN)/σ"] = xi
    if lse is not None:
        r["Cpu"] = (lse - media) / (3 * sigma)
        r["Z_LSE"] = (lse - media) / sigma
        r["%PNC por LSE"] = 1 - phi(r["Z_LSE"])
    if lie is not None:
        r["Cpl"] = (media - lie) / (3 * sigma)
        r["Z_LIE"] = (lie - media) / sigma
        r["%PNC por LIE"] = phi(r["Z_LIE"])
    cands = [r[k] for k in ("Cpu", "Cpl") if k in r]
    r["Cpk"] = min(cands) if cands else np.nan
    r["%PNC total"] = r.get("%PNC por LSE", 0.0) + r.get("%PNC por LIE", 0.0)
    r["PPM no conformes"] = 1e6 * r["%PNC total"]
    return r


def clase_cp(cp):
    """Clasificación del proceso según Cp (presentación de capacidad, tabla 'Valor del Cp')."""
    if cp is None or np.isnan(cp):
        return None, "—"
    if cp > 1.33:
        return 1, "Clase 1 (Cp > 1,33): más que adecuado."
    if cp >= 1:
        return 2, "Clase 2 (1 < Cp < 1,33): adecuado para el trabajo, pero requiere control estricto conforme el Cp se acerca a 1."
    if cp >= 0.67:
        return 3, "Clase 3 (0,67 < Cp < 1): no adecuado para el trabajo; es necesario un análisis del proceso."
    return 4, "Clase 4 (Cp < 0,67): no adecuado para el trabajo; requiere serias modificaciones."


def situacion(cp, cpk, tol=0.02):
    """Tipo de proceso según Cp y Cpk (módulo 3.3.2, 'En general' 1–4)."""
    centrado = abs(cp - cpk) <= tol * max(abs(cp), 1e-9)
    if cpk <= 0:
        extra = " La media del proceso está fuera de las especificaciones (Cpk ≤ 0)."
    else:
        extra = ""
    if cp >= 1 and centrado:
        return "1. Proceso capaz y centrado (Cp > 1, Cp ≈ Cpk). Decisión: mantenerlo en esos niveles." + extra
    if cp >= 1:
        if cpk >= 1:
            return ("Proceso capaz (Cp > 1, Cpk > 1) aunque ligeramente descentrado: conviene acercar la media al "
                    "valor nominal." + extra)
        return ("2. Proceso potencialmente capaz pero descentrado (Cp > 1, Cpk < 1). Decisión: centrar el proceso "
                "(llevar la media al valor nominal); suele ser más económico que reducir la variabilidad." + extra)
    if centrado:
        return ("3. Proceso incapaz y centrado (Cp < 1, Cp ≈ Cpk). Decisión: modificar el proceso para reducir la "
                "variabilidad (análisis de las 6M)." + extra)
    return ("4. Proceso incapaz y descentrado (Cp < 1, Cpk < Cp). Decisión: acciones inmediatas: centrar y reducir "
            "la variabilidad." + extra)


def intervalos_confianza(cp, cpk, n, alfa=0.05):
    """IC para Cp y Cpk (presentación de capacidad, 'Intervalos de confianza'). n = número total de datos."""
    val.exigir(n is not None and n >= 2, "Los intervalos de confianza necesitan al menos 2 datos.")
    val.exigir(0 < alfa < 1, "α debe estar entre 0 y 1.")
    out = {}
    if cp is not None and not np.isnan(cp):
        lo = cp * math.sqrt(stats.chi2.ppf(alfa / 2, n - 1) / (n - 1))
        hi = cp * math.sqrt(stats.chi2.ppf(1 - alfa / 2, n - 1) / (n - 1))
        out["Cp"] = (lo, hi)
    if cpk is not None and not np.isnan(cpk) and cpk != 0:
        z = stats.norm.ppf(1 - alfa / 2)
        k = z * math.sqrt(1 / (9 * n * cpk ** 2) + 1 / (2 * (n - 1)))
        out["Cpk"] = (cpk * (1 - k), cpk * (1 + k))
    return out


def ventana_operacion(sigma, pnc_obj, lse=None, lie=None):
    """Valores de X̄ entre los cuales el %PNC por cada límite es ≤ pnc_obj (ejemplos 1.d y 3 del cap. 3).

    Por el LIE: P(Z < (LIE − X̄)/σ) = objetivo ⇒ (LIE − X̄)/σ = −z ⇒ X̄ = LIE + z·σ.
    Por el LSE: P(Z > (LSE − X̄)/σ) = objetivo ⇒ X̄ = LSE − z·σ.
    """
    val.especificaciones(lie, lse)
    val.sigma_positiva(sigma)
    val.exigir(0 < pnc_obj < 0.5, "El %PNC objetivo debe estar entre 0 y 0,5 (por ejemplo 0,04 = 4 %).")
    z = z_de_prob(1 - pnc_obj)  # P(Z > z) = pnc_obj
    sup = lse - z * sigma if lse is not None else None
    inf = lie + z * sigma if lie is not None else None
    return {"Z (P(Z>z) = objetivo)": z, "X̄ máximo (por LSE)": sup, "X̄ mínimo (por LIE)": inf}


def escenario_centrado(sigma, lse, lie):
    """Índices si el proceso se centrara en el valor nominal (ejemplo 1.c del cap. 3)."""
    val.exigir(lse is not None and lie is not None, "El escenario centrado necesita LIE y LSE.")
    return indices((lse + lie) / 2, sigma, lse, lie)


def tabla_indices(r):
    """Convierte el diccionario de índices en tabla para mostrar/exportar."""
    orden = ["X̄", "σ", "LSE", "LIE", "VN = (LSE+LIE)/2", "T = LSE − LIE", "Cp", "% ancho de banda = 100/Cp",
             "Cpu", "Cpl", "Cpk", "Desplazamiento (X̄−VN)/σ", "Z_LSE", "Z_LIE",
             "%PNC por LSE", "%PNC por LIE", "%PNC total", "PPM no conformes"]
    filas = [{"Indicador": k, "Valor": r[k]} for k in orden if k in r and r[k] is not None]
    return pd.DataFrame(filas)


def interpretar(r):
    """Texto de interpretación automática (conclusión preliminar)."""
    txt = []
    if "Cp" in r:
        _, cl = clase_cp(r["Cp"])
        txt.append(f"Cp = {r['Cp']:.3f}. {cl}")
        txt.append(f"La variabilidad natural (6σ) consume el {r['% ancho de banda = 100/Cp']:.1f} % de la tolerancia.")
        txt.append(situacion(r["Cp"], r["Cpk"]))
    else:
        txt.append(f"Especificación unilateral: Cpk = {r['Cpk']:.3f} "
                   f"({'el proceso cumple holgadamente' if r['Cpk'] >= 1.33 else 'riesgo de incumplimiento' if r['Cpk'] < 1 else 'cumple, con control estricto'}).")
    if "Cpu" in r and "Cpl" in r:
        peor = "superior (LSE)" if r["Cpu"] < r["Cpl"] else "inferior (LIE)"
        txt.append(f"El mayor riesgo de incumplimiento está en el límite {peor}.")
    for lado in ("LSE", "LIE"):
        k = f"%PNC por {lado}"
        c = "Cpu" if lado == "LSE" else "Cpl"
        if k in r and c in r and r[c] > 1:
            txt.append(f"{c} > 1: la fracción no conforme por el {lado} es despreciable ({100 * r[k]:.4f} %).")
    txt.append(f"Fracción no conforme esperada: {100 * r['%PNC total']:.4f} % ({r['PPM no conformes']:.0f} PPM).")
    if r.get("Cpk", 0) >= 1.33:
        txt.append("Cpk ≥ 1,33: valor deseado según el módulo.")
    return txt
