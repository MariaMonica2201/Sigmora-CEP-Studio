"""
Módulo 4. Validación de supuestos.

Normalidad: prueba de bondad de ajuste Ji-cuadrada (Módulo Académico 2.6):
  1. H0: los datos se ajustan a una distribución normal; H1: no se ajustan.
  2. Número de clases k = 1 + 3,3·log10(N) y amplitud h = R/k (presentación de
     capacidad, "Pasos para la construcción de un histograma").
  3. Frecuencia observada O_i de cada clase.
  4. Probabilidad de cada clase con la normal N(X̄, S): p_i = P(Z ≤ z_sup) − P(Z ≤ z_inf).
  5. Frecuencia esperada E_i = N·p_i. Condición: E_i ≥ 5; si no, se unen clases vecinas.
  6. χ²_obs = Σ (O_i − E_i)²/E_i con ν = k − r − 1 grados de libertad (r = 2 parámetros
     estimados: media y desviación). Se acepta H0 si χ²_obs ≤ χ²_{α, ν}.

Condiciones de aplicación que el programa verifica antes de concluir:
  - toda clase agrupada tiene E_i ≥ 5 (paso 5);
  - ν = k_agrupadas − r − 1 ≥ 1, es decir, al menos r + 2 clases tras unirlas;
  - por lo anterior, N ≥ 5·(r + 2) datos (20 con r = 2); con menos datos no se pueden
    formar las clases necesarias y la prueba no se aplica;
  - datos con variabilidad (S > 0) e independientes (pestaña Independencia).
Interpretación: "no rechazar H0" significa que los datos no contradicen la normalidad
con el nivel α elegido; NO demuestra que la distribución sea normal. Con pocos datos
la prueba sólo detecta alejamientos grandes.

Independencia y estabilidad preliminar: diagrama de dispersión entre cada dato y
el siguiente (2.7.4 "Diagrama de dispersión") y análisis de patrones no aleatorios
(4.5, rachas a un lado de la LC y tendencias) en el orden de producción.
"""
import math

import numpy as np
import pandas as pd

from . import validacion as val
from .estadistica import chi2_critico, chi2_cola_derecha, phi

E_MINIMA = 5


def numero_clases(N):
    """k = 1 + 3,3·log10(N), redondeado al entero más cercano (en el ejemplo del módulo 7,6 → 8)."""
    return max(3, int(round(1 + 3.3 * math.log10(max(N, 1)))))


def datos_minimos_chi2(r=2):
    """Datos mínimos para que la prueba sea aplicable: r + 2 clases con E ≥ 5 cada una."""
    return E_MINIMA * (r + 2)


def tabla_frecuencias(x, k=None):
    """Tabla de frecuencias / histograma (módulo 2.7.1.1). Los datos en un límite van a la clase superior."""
    x = np.asarray(x, float)
    N = len(x)
    k = k or numero_clases(N)
    xmin, xmax = x.min(), x.max()
    h = (xmax - xmin) / k if xmax > xmin else 1.0
    bordes = xmin + h * np.arange(k + 1)
    idx = np.clip(np.floor((x - xmin) / h + 1e-9).astype(int), 0, k - 1)
    frec = np.bincount(idx, minlength=k)
    marcas = (bordes[:-1] + bordes[1:]) / 2
    df = pd.DataFrame({"Clase": range(1, k + 1), "Lím. inferior": bordes[:-1], "Lím. superior": bordes[1:],
                       "Marca de clase (x_i)": marcas, "Frecuencia (f_i)": frec,
                       "f_i·x_i": frec * marcas, "f_i·x_i²": frec * marcas ** 2})
    df["Frec. relativa"] = df["Frecuencia (f_i)"] / N
    df["Frec. acumulada"] = df["Frecuencia (f_i)"].cumsum()
    media_agr = df["f_i·x_i"].sum() / N
    s_agr = math.sqrt(max((df["f_i·x_i²"].sum() - df["f_i·x_i"].sum() ** 2 / N) / N, 0))
    return df, {"k": k, "h": h, "media agrupada": media_agr, "desv. agrupada": s_agr}


def chi2_normalidad(x, alfa=0.05, k=None, r=2):
    """Prueba Ji-cuadrada de normalidad según el procedimiento del módulo (2.6).

    Devuelve, además del estadístico, la tabla «condiciones» con cada condición de aplicación
    y si se cumple, y «estado»: "no se rechaza", "se rechaza" o "no aplicable".
    """
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    N = len(x)
    val.exigir(r in (0, 1, 2), "r (parámetros estimados) debe ser 0, 1 o 2.")
    val.exigir(0 < alfa < 1, "α debe estar entre 0 y 1.")
    val.exigir(N >= 2, f"Hay {N} dato(s): la prueba de normalidad necesita datos con variabilidad.")
    media, s = x.mean(), x.std(ddof=1)
    val.sigma_positiva(s, "S de los datos")
    k = int(k or numero_clases(N))
    val.exigir(3 <= k <= N, f"El número de clases debe estar entre 3 y N = {N} (se pidió k = {k}).")
    tf, info = tabla_frecuencias(x, k)
    inf = tf["Lím. inferior"].to_numpy()
    sup = tf["Lím. superior"].to_numpy()
    obs = tf["Frecuencia (f_i)"].to_numpy().astype(float)
    # probabilidades; las clases extremas se extienden a ±∞ para que Σp = 1
    cdf_sup = np.array([phi((v - media) / s) for v in sup])
    cdf_sup[-1] = 1.0
    cdf_inf = np.r_[0.0, cdf_sup[:-1]]
    prob = cdf_sup - cdf_inf
    esp = N * prob
    detalle = pd.DataFrame({"Clase": tf["Clase"], "Lím. inferior": inf, "Lím. superior": sup,
                            "Z sup": (sup - media) / s, "Probabilidad": prob,
                            "Observada (O)": obs, "Esperada (E = N·p)": esp})
    # unir clases con E < 5 (desde los extremos hacia el centro, como en el ejemplo del módulo)
    grupos = [[i] for i in range(len(obs))]
    def e(g):
        return esp[g].sum()
    while len(grupos) > 1 and e(grupos[0]) < E_MINIMA:
        grupos[1] = grupos[0] + grupos[1]
        grupos.pop(0)
    while len(grupos) > 1 and e(grupos[-1]) < E_MINIMA:
        grupos[-2] = grupos[-2] + grupos[-1]
        grupos.pop()
    i = 1
    while i < len(grupos) - 1:
        if e(grupos[i]) < E_MINIMA:
            grupos[i + 1] = grupos[i] + grupos[i + 1]
            grupos.pop(i)
        else:
            i += 1
    filas = []
    for j, g in enumerate(grupos, 1):
        O, E = obs[g].sum(), esp[g].sum()
        filas.append({"Clase agrupada": j, "Desde": inf[g[0]], "Hasta": sup[g[-1]],
                      "Clases originales": ", ".join(str(t + 1) for t in g),
                      "Observada (O)": O, "Esperada (E)": E, "(O−E)²/E": (O - E) ** 2 / E})
    agr = pd.DataFrame(filas)
    chi_obs = float(agr["(O−E)²/E"].sum())
    k_agr = len(agr)
    gl = k_agr - r - 1
    n_min = datos_minimos_chi2(r)
    e_min = float(agr["Esperada (E)"].min())
    condiciones = pd.DataFrame([
        {"Condición": f"Datos suficientes: N ≥ 5·(r + 2) = {n_min}", "¿Cumple?": "Sí" if N >= n_min else "No",
         "Detalle": f"N = {N}"},
        {"Condición": "Toda clase agrupada con frecuencia esperada E ≥ 5",
         "¿Cumple?": "Sí" if e_min >= E_MINIMA else "No", "Detalle": f"E mínima = {e_min:.2f} en {k_agr} clases"},
        {"Condición": "Grados de libertad ν = k − r − 1 ≥ 1", "¿Cumple?": "Sí" if gl >= 1 else "No",
         "Detalle": f"ν = {k_agr} − {r} − 1 = {gl}"},
        {"Condición": "Variabilidad en los datos (S > 0)", "¿Cumple?": "Sí", "Detalle": f"S = {s:.4g}"},
        {"Condición": "Observaciones independientes", "¿Cumple?": "Revisar",
         "Detalle": "Se verifica en la pestaña Independencia (dispersión y rachas)."},
    ])
    base = {"detalle": detalle, "agrupada": agr, "chi2_obs": chi_obs, "gl": gl, "media": media, "s": s,
            "info": info, "condiciones": condiciones, "N": N, "k_agrupadas": k_agr}
    problemas = [c for c in condiciones.itertuples() if c[2] == "No"]
    if problemas:
        motivo = "; ".join(f"{c[1].split(':')[0]} ({c[3]})" for c in problemas)
        return {**base, "chi2_tabla": np.nan, "valor_p": np.nan, "normal": None, "estado": "no aplicable",
                "advertencias": [],
                "conclusion": (f"La prueba Ji-cuadrada no es aplicable con estos datos: {motivo}. Se necesitan al "
                               f"menos {n_min} datos para formar {r + 2} clases con E ≥ 5. Mientras tanto, juzgue la "
                               "forma con el histograma y no dé por supuesta la normalidad.")}
    crit = chi2_critico(alfa, gl)
    vp = chi2_cola_derecha(chi_obs, gl)
    normal = chi_obs <= crit
    advertencias = []
    if N < 50 or gl <= 2:
        advertencias.append(f"Con N = {N} datos y ν = {gl} la prueba sólo detecta alejamientos grandes de la "
                            "normal (poca potencia).")
    concl = (f"χ²_obs = {chi_obs:.4f} {'≤' if normal else '>'} χ²({alfa}, {gl}) = {crit:.4f} (valor p = {vp:.4f}). "
             + ("No se rechaza H0: con estos datos no hay evidencia para descartar la distribución normal, por lo que "
                "es razonable usarla para las cartas y la capacidad. Esto no demuestra que los datos sean normales: "
                "sólo indica que la diferencia observada puede deberse al azar del muestreo." if normal else
                "Se rechaza H0: los datos NO se ajustan a una distribución normal; las fracciones no conformes "
                "calculadas con la normal deben tomarse con precaución (revise estratificación, mezcla de fuentes o "
                "datos atípicos)."))
    return {**base, "chi2_tabla": crit, "valor_p": vp, "normal": normal,
            "estado": "no se rechaza" if normal else "se rechaza", "advertencias": advertencias, "conclusion": concl}


def pares_consecutivos(x):
    """Pares (x_t, x_{t+1}) para el diagrama de dispersión de independencia."""
    x = np.asarray(x, float)
    return x[:-1], x[1:]


def forma_histograma(x):
    """Descripción cualitativa de la forma (simétrica / sesgada), según 2.4.3 del módulo.
    Compara media y mediana respecto a la desviación estándar."""
    x = np.asarray(x, float)
    media, med, s = x.mean(), np.median(x), x.std(ddof=1)
    d = (media - med) / s if s > 0 else 0
    if abs(d) < 0.1:
        return "Aproximadamente simétrica (media ≈ mediana)."
    return ("Asimétrica, sesgada a la derecha (media > mediana)." if d > 0
            else "Asimétrica, sesgada a la izquierda (media < mediana).")
