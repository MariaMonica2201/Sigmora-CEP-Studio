"""
Módulo 6. Diseño de gráficos de control: ARL0, ARL1, ATS.

Fórmulas (hoja "Fórmulas control" secciones 2–5 y Módulo Académico 4.6, 4.7.1.3,
4.7.1.4, 4.8.1.1, 4.8.2):
  ARL0 = 1/α        ATS0 = ARL0·t
  ARL1 = 1/(1−β)    ATS1 = ARL1·t
  Potencia carta X̄:  d = |X̄' − X̄''|/σ ;  1 − β = P(Z ≥ |Z_{α/2}| − d·√n)
  Tamaño de muestra:   n = [(|Z_{α/2}| + Z_{1−β})/d]²
  Prob. detectar en las k primeras muestras: 1 − β^k
  Prob. detectar en la muestra k: β^{k−1}(1 − β);  no detectar hasta la k: β^k
  Valor esperado de PNC: VEPNC = TP·%PNC_corr·(1−β)·[t1 + t2·β + … + tk·β^{k−1}], t_i = i·t
  Valor promedio de PNC: VPPNC = TP·ATS·%PNC_corr
  Carga muestral: Cm = n/t ;  t = n/Cm_nueva
  Cartas por atributos (curva OC de la carta):
    β = P(D ≤ ⌊n·LCS⌋ | p) − P(D ≤ ⌊n·LCI⌋ | p)   (Binomial; Poisson para c y u)
  Esquema DS-c (Campuzano, Carrión y Mosquera, 2019, EJIE 13(6)):
    Pa = 1 − [P(x1 < WL) + Σ_{i=⌈WL⌉}^{⌊UCL1⌋} P(x1 = i)·P(x2 < UCL2 − i)]
    ASN = m1 + m2·P(WL < x1 < UCL1)
"""
import math

import numpy as np
import pandas as pd

from . import validacion as val
from .estadistica import (alfa_de_z, binom_cdf, phi, poisson_cdf, poisson_pmf, z_alfa_medios, z_de_prob)


# ============================================================ carta X̄ ======
def potencia_xbar(d, n, z):
    """1 − β para un corrimiento de d desviaciones estándar (fórmula del módulo, 4.7.1.3).

    d = |X̄' − X̄''|/σ se expresa en desviaciones del proceso; la carta X̄ grafica medias de n datos,
    cuya desviación es σ/√n, por eso el corrimiento en la escala de la carta es d·√n.
    """
    val.tamano(n, "n", entero=False)
    val.exigir(z is not None and abs(z) > 0, "Z_α/2 debe ser mayor que cero.")
    return phi(abs(d) * math.sqrt(n) - abs(z))


def media_por_pnc(sigma, pnc, limite, lado):
    """X̄'' con la que el proceso produce un %PNC dado por un límite (capítulo 3, %PNC con la normal):
    por el LSE  P(Z > (LSE − X̄)/σ) = pnc ⇒ X̄ = LSE − z·σ ;  por el LIE  X̄ = LIE + z·σ ;  P(Z > z) = pnc."""
    val.sigma_positiva(sigma)
    val.exigir(0 < pnc < 0.5, "El %PNC debe estar entre 0 y 0,5 (por ejemplo 0,01 = 1 %).")
    z = z_de_prob(1 - pnc)
    return limite - z * sigma if lado == "LSE" else limite + z * sigma


def media_por_cpk(sigma, cpk, limite, lado):
    """X̄'' con la que el Cpk baja a un valor dado (Cpu = (LSE − X̄)/3σ, Cpl = (X̄ − LIE)/3σ):
    por el LSE X̄ = LSE − 3σ·Cpk ; por el LIE X̄ = LIE + 3σ·Cpk."""
    val.sigma_positiva(sigma)
    return limite - 3 * sigma * cpk if lado == "LSE" else limite + 3 * sigma * cpk


def desempeno_xbar(d, n, z, t=1.0):
    """ARL0, ARL1, ATS0, ATS1 de una carta X̄ con límites a ±Z_{α/2}, muestra n, intervalo t."""
    alfa = alfa_de_z(z)
    pot = potencia_xbar(d, n, z)
    beta = 1 - pot
    return {"α": alfa, "ARL0": 1 / alfa, "ATS0": t / alfa, "1−β (potencia)": pot, "β": beta,
            "ARL1": 1 / pot if pot > 0 else math.inf, "ATS1": t / pot if pot > 0 else math.inf,
            "Carga muestral Cm = n/t": n / t}


def n_para_potencia(d, z, potencia):
    """n = [(|Z_{α/2}| + Z_{1−β})/d]², con Z_{1−β} tal que P(Z ≤ Z_{1−β}) = 1 − β."""
    val.exigir(d is not None and abs(d) > 0, "El corrimiento d debe ser distinto de cero.")
    val.exigir(0 < potencia < 1, "La potencia 1 − β debe estar entre 0 y 1.")
    z1b = z_de_prob(potencia)
    n = ((abs(z) + z1b) / abs(d)) ** 2
    return n, z1b


def beta_para_detectar(prob, k):
    """β que garantiza detectar con probabilidad `prob` en alguna de las k primeras muestras: 1 − β^k = prob."""
    return (1 - prob) ** (1 / k)


def prob_deteccion(beta, kmax=10):
    filas = []
    for k in range(1, kmax + 1):
        filas.append({"Muestra k": k, "P(detectar exactamente en k) = β^(k−1)(1−β)": beta ** (k - 1) * (1 - beta),
                      "P(detectar en las k primeras) = 1−β^k": 1 - beta ** k,
                      "P(no detectar hasta k) = β^k": beta ** k})
    return pd.DataFrame(filas)


def vepnc(TP, pnc_corr, beta, t, k):
    """Valor esperado de productos no conformes hasta la muestra k (4.7.1.4)."""
    suma = sum((i * t) * beta ** (i - 1) for i in range(1, k + 1))
    return TP * pnc_corr * (1 - beta) * suma


def vppnc(TP, ats, pnc_corr):
    """Valor promedio de productos no conformes hasta la detección: TP·ATS·%PNC."""
    return TP * ats * pnc_corr


def tabla_diseno_xbar(ds, ns, z, t):
    """Tabla de ARL1/ATS1 para varias combinaciones de corrimiento d y tamaño n."""
    filas = []
    for n in ns:
        for d in ds:
            r = desempeno_xbar(d, n, z, t)
            filas.append({"n": n, "d (σ)": d, "1−β": r["1−β (potencia)"], "ARL1": r["ARL1"], "ATS1": r["ATS1"],
                          "ARL0": r["ARL0"], "ATS0": r["ATS0"], "Cm = n/t": n / t})
    return pd.DataFrame(filas)


# ======================================================= cartas por atributos ==
def beta_atributos(tipo, n, lcs, lci, valores):
    """Curva OC de una carta por atributos.

    tipo: "p", "np", "c" o "u"
    n:    tamaño de muestra (para c usar 1)
    lcs, lci: límites de la carta en sus propias unidades (p: proporción; np: conteo; c: conteo; u: por unidad)
    valores: lista de p (p/np) o de c, u (media de defectos) para los que se calcula β
    """
    filas = []
    for v in valores:
        if tipo in ("p", "np"):
            sup = math.floor(n * lcs) if tipo == "p" else math.floor(lcs)
            inf = math.floor(n * lci) if tipo == "p" else math.floor(lci)
            ps = binom_cdf(sup, n, v)
            pi = binom_cdf(inf, n, v) if (n * lci if tipo == "p" else lci) >= 0 else 0.0
            if (tipo == "p" and lci <= 0) or (tipo == "np" and lci <= 0):
                pi = 0.0
        else:
            lam = v if tipo == "c" else n * v
            sup = math.floor(lcs if tipo == "c" else n * lcs)
            inf = math.floor(lci if tipo == "c" else n * lci)
            ps = poisson_cdf(sup, lam)
            pi = poisson_cdf(inf, lam) if lci > 0 else 0.0
        b = ps - pi
        filas.append({"Parámetro": v, "P(D ≤ sup)": ps, "P(D ≤ inf)": pi, "β": b, "1−β": 1 - b,
                      "ARL = 1/(1−β)": 1 / (1 - b) if b < 1 else math.inf})
    return pd.DataFrame(filas)


def n_carta_p(p, metodo, **kw):
    """Tamaño de muestra para la carta p (4.8.1.1).
    Método 1: P(D ≥ 1) ≥ γ con Poisson → n = −ln(1−γ)/p.
    Método 2 (Duncan): n = (L/δ)²·p(1−p) con δ = p_nueva − p.
    Método 3: LCI > 0 → n > (1−p)·L²/p.
    Método 4: n = [(Z_{α/2}·√(p(1−p)) + Z_{1−β}·√(p1(1−p1)))/(p1 − p)]².
    """
    val.exigir(0 < p < 1, "La fracción p debe estar entre 0 y 1 (sin incluirlos).")
    if metodo in (2, 4):
        val.exigir(0 < kw["p1"] < 1 and kw["p1"] != p, "La nueva fracción p1 debe estar entre 0 y 1 y ser distinta de p.")
    if metodo == 1:
        g = kw["gamma"]
        lam = -math.log(1 - g)
        return lam / p, f"λ = np ≥ {lam:.3f} (Poisson) → n ≥ {lam / p:.1f}"
    if metodo == 2:
        L, p1 = kw["L"], kw["p1"]
        dlt = p1 - p
        n = (L / dlt) ** 2 * p * (1 - p)
        return n, f"δ = {dlt:.4f}; n = (L/δ)²·p(1−p) = {n:.1f}"
    if metodo == 3:
        L = kw["L"]
        n = (1 - p) * L ** 2 / p
        return n, f"n > (1−p)·L²/p = {n:.1f} para que LCI > 0"
    if metodo == 4:
        z, pot, p1 = kw["z"], kw["potencia"], kw["p1"]
        z1b = z_de_prob(pot)
        n = ((abs(z) * math.sqrt(p * (1 - p)) + z1b * math.sqrt(p1 * (1 - p1))) / (p1 - p)) ** 2
        return n, f"Z_(1−β) = {z1b:.4f}; n = {n:.1f}"
    raise ValueError("Método no válido")


def potencia_carta_p(p, p1, n, z=3.0):
    """1 − β = P(Z > (p̄ + Z_{α/2}·√(p̄(1−p̄)/n) − p1)/√(p1(1−p1)/n)) (4.8.1.1)."""
    val.tamano(n, "n", entero=False)
    val.exigir(0 < p < 1 and 0 < p1 < 1, "p y p1 deben estar entre 0 y 1 (sin incluirlos).")
    lcs = p + z * math.sqrt(p * (1 - p) / n)
    return 1 - phi((lcs - p1) / math.sqrt(p1 * (1 - p1) / n))


# ============================================================ DS-c =========
def ds_c(m1, m2, wl, ucl1, ucl2, lam):
    """Probabilidad de alarma, ARL y ASN del esquema de muestreo doble DS-c (Campuzano et al., 2019)."""
    l1, l2 = lam * m1, lam * m2
    # P(x1 < WL)
    p_ok1 = poisson_cdf(math.ceil(wl) - 1, l1)
    suma = 0.0
    for i in range(math.ceil(wl), math.floor(ucl1) + 1):
        suma += poisson_pmf(i, l1) * poisson_cdf(math.ceil(ucl2 - i) - 1, l2)
    pa = 1 - (p_ok1 + suma)
    p_seg = poisson_cdf(math.floor(ucl1), l1) - p_ok1  # P(WL < x1 < UCL1)
    asn = m1 + m2 * p_seg
    return {"Pa (prob. de alarma)": pa, "ARL": 1 / pa if pa > 0 else math.inf, "ASN": asn,
            "P(ir a 2ª etapa)": p_seg}


def fp_c(m, ucl, lam):
    """Carta c clásica (FP-c) de una cara con muestra m: alarma si x > UCL."""
    pa = 1 - poisson_cdf(math.floor(ucl), lam * m)
    return {"Pa (prob. de alarma)": pa, "ARL": 1 / pa if pa > 0 else math.inf, "ASN": m}
