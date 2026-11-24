"""
Módulo 3. Gráficos de control por atributos: p, np, c y u.

Fórmulas (Módulo Académico 4.8 y hoja "Fórmulas control", sección 6):
  p  : LC = p̄ , LCS/LCI = p̄ ± Z_{α/2}·√(p̄(1−p̄)/n)         (n fijo o variable)
  np : LC = np̄ , LCS/LCI = np̄ ± Z_{α/2}·√(np̄(1−p̄))         (n fijo)
       p̄ = ΣD_i / (k·n)
  c  : LC = c̄ , LCS/LCI = c̄ ± Z_{α/2}·√c̄                   (n fijo)
  u  : LC = Ū , LCS/LCI = Ū ± Z_{α/2}·√(Ū/n)                 (n variable)
       Ū = ΣC_i / Σn_i
  Si el LCI resulta negativo toma el valor cero.

Carta p con n variable (4.8.1.2): Método 1 límites variables, Método 2 tamaño
de muestra promedio (válido si los n no difieren más de ±25 % del promedio),
Método 3 carta estandarizada Z_i = (p_i − p̄)/√(p̄(1−p̄)/n_i) con límites ±Z_{α/2}.
"""
import numpy as np
import pandas as pd

from . import validacion as val


def _carta(nombre, valores, lc, lcs, lci, etiquetas):
    m = len(valores)
    f = lambda v: np.full(m, float(v)) if np.isscalar(v) else np.asarray(v, float)
    return {"nombre": nombre, "valores": np.asarray(valores, float), "lc": f(lc),
            "lcs": f(lcs), "lci": np.maximum(f(lci), 0.0) if nombre != "Carta p estandarizada" else f(lci),
            "etiquetas": list(etiquetas)}


def _inc(m, excluir):
    excluir = set(excluir or [])
    return np.array([(i + 1) not in excluir for i in range(m)])


def _aviso_extremo(info, valor, nombre, tasa=False):
    """Con p̄ = 0, p̄ = 1 o c̄ = 0 la desviación de la carta es cero y los límites colapsan en la LC."""
    if valor <= 0 or (not tasa and valor >= 1):
        info["Advertencia"] = (f"{nombre} = {valor:g}: la desviación de la carta es cero y los límites coinciden con la "
                               "línea central. La carta no puede distinguir causas comunes de especiales; reúna más "
                               "subgrupos o revise la definición de defectuoso/defecto.")


# ------------------------------------------------------------------ p ------
def carta_p(defectuosos, n, etiquetas, z=3.0, excluir=None, metodo="variables", p_estandar=None):
    """Carta p. `n` puede ser un número o un arreglo (n variable).

    metodo: "variables" (Método 1, límites individuales), "promedio" (Método 2, n̄),
            "estandarizada" (Método 3).
    p_estandar: si se da, se usa como p̄ (Fase II / valor estándar).
    """
    val.conteos(defectuosos, n, "defectuosos")
    d = np.asarray(defectuosos, float)
    m = len(d)
    nn = np.full(m, float(n)) if np.isscalar(n) else np.asarray(n, float)
    p = d / nn
    inc = _inc(m, excluir)
    if p_estandar is None:
        val.subgrupos_usados(inc)
    else:
        val.proporcion(p_estandar, "p̄ estándar")
    pbar = float(p_estandar) if p_estandar is not None else d[inc].sum() / nn[inc].sum()
    info = {"p̄": pbar, "Z_α/2": z, "Subgrupos usados (k)": int(inc.sum()) if p_estandar is None else m}
    _aviso_extremo(info, pbar, "p̄")
    if metodo == "estandarizada":
        val.exigir(0 < pbar < 1, f"Con p̄ = {pbar:g} la desviación √(p̄(1−p̄)/n) es cero y la carta estandarizada "
                                 "no se puede calcular (división entre cero). Use el Método 1 o 2.")
    variable = not np.allclose(nn, nn[0])
    if metodo == "estandarizada":
        zi = (p - pbar) / np.sqrt(pbar * (1 - pbar) / nn)
        carta = _carta("Carta p estandarizada", zi, 0.0, z, -z, etiquetas)
        info.update({"LC": 0.0, "LCS": z, "LCI": -z})
    elif metodo == "promedio" or not variable:
        nbar = nn[inc].mean() if p_estandar is None else nn.mean()
        if not variable:
            nbar = nn[0]
        sd = np.sqrt(pbar * (1 - pbar) / nbar)
        carta = _carta("Carta p", p, pbar, pbar + z * sd, pbar - z * sd, etiquetas)
        info.update({"n usado": nbar, "σ_p": sd, "LCS": pbar + z * sd, "LCI": max(pbar - z * sd, 0.0)})
        if variable:
            dif = np.max(np.abs(nn - nbar) / nbar)
            info["Máx. diferencia de n respecto a n̄"] = f"{100 * dif:.1f} %"
            info["Advertencia"] = ("Los tamaños difieren más de ±25 % del promedio: el Método 2 no es adecuado (4.8.1.2)."
                                   if dif > 0.25 else "Diferencias dentro de ±25 %: Método 2 aceptable.")
    else:
        sd = np.sqrt(pbar * (1 - pbar) / nn)
        carta = _carta("Carta p (límites variables)", p, pbar, pbar + z * sd, pbar - z * sd, etiquetas)
        info.update({"LCS (rango)": f"{(pbar + z * sd).min():.5f} – {(pbar + z * sd).max():.5f}",
                     "LCI (rango)": f"{np.maximum(pbar - z * sd, 0).min():.5f} – {np.maximum(pbar - z * sd, 0).max():.5f}"})
    tabla = pd.DataFrame({"Subgrupo": etiquetas, "n": nn, "Defectuosos (D)": d, "p_i = D/n": p,
                          "LCS": carta["lcs"], "LCI": carta["lci"]})
    return {"cartas": [carta], "params": info, "tabla": tabla, "pbar": pbar, "tipo": "p", "n": nn}


# ----------------------------------------------------------------- np ------
def carta_np(defectuosos, n, etiquetas, z=3.0, excluir=None, p_estandar=None):
    val.exigir(np.isscalar(n), "La carta np exige un tamaño de muestra constante; con n variable use la carta p.")
    val.tamano(n, "n")
    val.conteos(defectuosos, n, "defectuosos")
    d = np.asarray(defectuosos, float)
    m = len(d)
    inc = _inc(m, excluir)
    if p_estandar is None:
        val.subgrupos_usados(inc)
    else:
        val.proporcion(p_estandar, "p̄ estándar")
    pbar = float(p_estandar) if p_estandar is not None else d[inc].sum() / (inc.sum() * n)
    c = n * pbar
    sd = np.sqrt(n * pbar * (1 - pbar))
    carta = _carta("Carta np", d, c, c + z * sd, c - z * sd, etiquetas)
    info = {"n": n, "p̄ = ΣD/(k·n)": pbar, "LC = np̄": c, "σ_np": sd, "LCS": c + z * sd,
            "LCI": max(c - z * sd, 0.0), "Z_α/2": z, "Subgrupos usados (k)": int(inc.sum())}
    _aviso_extremo(info, pbar, "p̄")
    tabla = pd.DataFrame({"Subgrupo": etiquetas, "Defectuosos (D)": d})
    return {"cartas": [carta], "params": info, "tabla": tabla, "pbar": pbar, "tipo": "np", "n": n}


# ------------------------------------------------------------------ c ------
def carta_c(defectos, etiquetas, z=3.0, excluir=None, c_estandar=None):
    val.conteos(defectos, None, "defectos")
    x = np.asarray(defectos, float)
    inc = _inc(len(x), excluir)
    if c_estandar is None:
        val.subgrupos_usados(inc)
    else:
        val.exigir(c_estandar >= 0, "El c̄ estándar no puede ser negativo.")
    cbar = float(c_estandar) if c_estandar is not None else x[inc].mean()
    sd = np.sqrt(cbar)
    carta = _carta("Carta c", x, cbar, cbar + z * sd, cbar - z * sd, etiquetas)
    info = {"c̄ = ΣC/k": cbar, "LCS": cbar + z * sd, "LCI": max(cbar - z * sd, 0.0), "Z_α/2": z,
            "Subgrupos usados (k)": int(inc.sum())}
    _aviso_extremo(info, cbar, "c̄", tasa=True)
    tabla = pd.DataFrame({"Subgrupo": etiquetas, "Defectos (C)": x})
    return {"cartas": [carta], "params": info, "tabla": tabla, "cbar": cbar, "tipo": "c"}


# ------------------------------------------------------------------ u ------
def carta_u(defectos, n, etiquetas, z=3.0, excluir=None, u_estandar=None):
    val.conteos(defectos, n, "defectos")
    x = np.asarray(defectos, float)
    m = len(x)
    nn = np.full(m, float(n)) if np.isscalar(n) else np.asarray(n, float)
    u = x / nn
    inc = _inc(m, excluir)
    if u_estandar is None:
        val.subgrupos_usados(inc)
    else:
        val.exigir(u_estandar >= 0, "El Ū estándar no puede ser negativo.")
    ubar = float(u_estandar) if u_estandar is not None else x[inc].sum() / nn[inc].sum()
    sd = np.sqrt(ubar / nn)
    carta = _carta("Carta u", u, ubar, ubar + z * sd, ubar - z * sd, etiquetas)
    info = {"Ū = ΣC/Σn": ubar, "Z_α/2": z, "Subgrupos usados (k)": int(inc.sum())}
    _aviso_extremo(info, ubar, "Ū", tasa=True)
    if np.allclose(nn, nn[0]):
        info.update({"n": nn[0], "LCS": ubar + z * sd[0], "LCI": max(ubar - z * sd[0], 0.0)})
    else:
        info.update({"LCS (rango)": f"{(ubar + z * sd).min():.5f} – {(ubar + z * sd).max():.5f}"})
    tabla = pd.DataFrame({"Subgrupo": etiquetas, "Unidades (n)": nn, "Defectos (C)": x, "u_i = C/n": u,
                          "LCS": carta["lcs"], "LCI": carta["lci"]})
    return {"cartas": [carta], "params": info, "tabla": tabla, "ubar": ubar, "tipo": "u", "n": nn}


# ------------------------------------------------------ selección -----------
def recomendar(que_cuenta: str, n_constante: bool):
    """Selección justificada de la carta según el módulo (4.8).

    que_cuenta: "defectuosos" (unidades no conformes, distribución binomial) o
                "defectos" (no conformidades por unidad, distribución de Poisson).
    """
    if que_cuenta == "defectuosos":
        if n_constante:
            return ("np (o p)", "Se cuentan unidades defectuosas (conforme / no conforme → Binomial) con n fijo: "
                    "la carta np grafica directamente la cantidad de defectuosos y es la más cómoda; la carta p "
                    "es equivalente en proporción.")
        return ("p", "Se cuentan unidades defectuosas (Binomial) y el tamaño de muestra varía: la carta p admite n "
                "variable (límites variables, n promedio o carta estandarizada). La carta np exige n fijo.")
    if n_constante:
        return ("c", "Se cuentan defectos / no conformidades (una unidad puede tener varios → Poisson) en unidades de "
                "inspección de tamaño constante: carta c.")
    return ("u", "Se cuentan defectos (Poisson) pero el tamaño de la unidad de inspección varía (m² de tela, lotes "
            "de distinto tamaño, etc.): carta u (defectos por unidad).")


def pareto(categorias, frecuencias):
    """Tabla de Pareto (módulo 2.7.2): ordenada, con % y % acumulado."""
    df = pd.DataFrame({"Categoría": categorias, "Frecuencia": frecuencias})
    df = df.groupby("Categoría", as_index=False)["Frecuencia"].sum().sort_values("Frecuencia", ascending=False)
    tot = df["Frecuencia"].sum()
    df["%"] = 100 * df["Frecuencia"] / tot
    df["% acumulado"] = df["%"].cumsum()
    df["Total acumulado"] = df["Frecuencia"].cumsum()
    return df.reset_index(drop=True)
