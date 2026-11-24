"""
Módulo 4 (parte). Análisis de patrones no aleatorios en cartas de control.

Basado en el Módulo Académico, sección 4.5 "Análisis de patrones de
comportamiento en las cartas de control":
  4.5.1 Punto(s) fuera de control
  4.5.2 Tendencias: 7 o más puntos ascendentes o descendentes
  4.5.3 Corrimiento en la media: 8 puntos consecutivos a un lado de la línea central
  4.5.4 Estratificación: sucesión de puntos pegados a la línea central
  4.5.5 Patrones cíclicos (inspección visual)
  4.5.6 Mezcla de lotes: puntos cerca o fuera de los límites, muy pocos cerca de la LC

Para 4.5.4 y 4.5.6 el módulo no fija un número de puntos, por eso aquí son
parámetros configurables por el usuario (valores por defecto indicados).
"""
import numpy as np
import pandas as pd

REGLAS = {
    "fuera": "Punto fuera de los límites de control (4.5.1)",
    "tendencia": "Tendencia: {k} o más puntos consecutivos ascendentes o descendentes (4.5.2)",
    "corrimiento": "Corrimiento de la media: {k} puntos consecutivos a un mismo lado de la LC (4.5.3)",
    "estratificacion": "Estratificación: {k} puntos consecutivos muy cerca de la LC (4.5.4, criterio configurable)",
    "mezcla": "Mezcla: {k} puntos consecutivos alejados de la LC, ninguno cerca de ella (4.5.6, criterio configurable)",
}

CAUSAS_TIPICAS = {
    "fuera": "Causa especial puntual: mal ajuste de máquina, error del operador, materia prima defectuosa, error de medición.",
    "tendencia": "Desgaste o deterioro gradual de herramienta/componente, fatiga del operador, cambios de temperatura (estacionales).",
    "corrimiento": "Cambio repentino del promedio: nuevo lote de materia prima, cambio de operador, ajuste de herramienta, nuevo método.",
    "estratificacion": "Límites de control mal calculados o mezcla de fuentes dentro del subgrupo (subgrupos no racionales).",
    "mezcla": "Sobrecontrol del operador o productos de varias fuentes (máquinas, turnos) con distinta media.",
}


def analizar(valores, lc, lcs, lci, k_tendencia=7, k_corrimiento=8,
             k_estratificacion=15, k_mezcla=8, zona_sigma=1 / 3):
    """Aplica las reglas de patrones a una serie graficada en una carta.

    valores, lcs, lci: arreglos (los límites pueden variar punto a punto, p. ej. carta p con n variable).
    zona_sigma: fracción de la distancia LC–límite considerada "cerca de la LC"
                (por defecto 1/3, es decir 1 sigma cuando los límites están a 3 sigmas).
    Devuelve un DataFrame con una fila por señal: Regla, Puntos (índices 1..k), Descripción.
    """
    x = np.asarray(valores, dtype=float)
    m = len(x)
    lcs = np.broadcast_to(np.asarray(lcs, dtype=float), (m,))
    lci = np.broadcast_to(np.asarray(lci, dtype=float), (m,))
    lc = np.broadcast_to(np.asarray(lc, dtype=float), (m,))
    senales = []

    # 4.5.1 fuera de límites
    for i in range(m):
        if x[i] > lcs[i] or x[i] < lci[i]:
            lado = "por encima del LCS" if x[i] > lcs[i] else "por debajo del LCI"
            senales.append(("fuera", [i + 1], f"Punto {i + 1} {lado}."))

    # 4.5.2 tendencias (k puntos consecutivos estrictamente crecientes o decrecientes)
    for signo, nombre in ((1, "ascendente"), (-1, "descendente")):
        inicio = 0
        for i in range(1, m + 1):
            sigue = i < m and signo * (x[i] - x[i - 1]) > 0
            if not sigue:
                largo = i - inicio
                if largo >= k_tendencia:
                    pts = list(range(inicio + 1, i + 1))
                    senales.append(("tendencia", pts, f"Tendencia {nombre} de {largo} puntos ({pts[0]} a {pts[-1]})."))
                inicio = i

    # 4.5.3 corrimiento (k puntos seguidos del mismo lado)
    lado = np.sign(x - lc)
    inicio = 0
    for i in range(1, m + 1):
        if i == m or lado[i] != lado[inicio] or lado[i] == 0:
            largo = i - inicio
            if lado[inicio] != 0 and largo >= k_corrimiento:
                pts = list(range(inicio + 1, i + 1))
                donde = "por encima" if lado[inicio] > 0 else "por debajo"
                senales.append(("corrimiento", pts, f"{largo} puntos seguidos {donde} de la LC ({pts[0]} a {pts[-1]})."))
            inicio = i

    # 4.5.4 estratificación y 4.5.6 mezcla
    dist = np.where(x >= lc, (x - lc) / np.where(lcs - lc == 0, np.nan, lcs - lc),
                    (lc - x) / np.where(lc - lci == 0, np.nan, lc - lci))
    cerca = dist <= zona_sigma
    lejos = dist > zona_sigma
    for mascara, regla, k, txt in ((cerca, "estratificacion", k_estratificacion, "muy cerca de la LC"),
                                   (lejos, "mezcla", k_mezcla, "alejados de la LC")):
        inicio = None
        for i in range(m + 1):
            ok = i < m and bool(mascara[i])
            if ok and inicio is None:
                inicio = i
            if not ok and inicio is not None:
                largo = i - inicio
                cambia_lado = regla != "mezcla" or len(set(lado[inicio:i])) > 1
                if largo >= k and cambia_lado:
                    pts = list(range(inicio + 1, i + 1))
                    senales.append((regla, pts, f"{largo} puntos consecutivos {txt} ({pts[0]} a {pts[-1]})."))
                inicio = None

    filas = []
    params = {"tendencia": k_tendencia, "corrimiento": k_corrimiento,
              "estratificacion": k_estratificacion, "mezcla": k_mezcla}
    for regla, pts, desc in senales:
        filas.append({
            "Regla": REGLAS[regla].format(k=params.get(regla, "")),
            "Puntos": ", ".join(map(str, pts)),
            "Descripción": desc,
            "Posibles causas (módulo)": CAUSAS_TIPICAS[regla],
            "_regla": regla,
            "_puntos": pts,
        })
    return pd.DataFrame(filas, columns=["Regla", "Puntos", "Descripción", "Posibles causas (módulo)", "_regla", "_puntos"])


def puntos_con_senal(df_senales):
    """Conjunto de índices (1..k) involucrados en alguna señal."""
    s = set()
    for pts in df_senales.get("_puntos", []):
        s.update(pts)
    return s


def puntos_fuera(df_senales):
    s = set()
    for regla, pts in zip(df_senales.get("_regla", []), df_senales.get("_puntos", [])):
        if regla == "fuera":
            s.update(pts)
    return s
