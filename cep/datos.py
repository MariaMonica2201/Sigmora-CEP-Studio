"""
Módulo 1. Gestión de datos.

Carga desde Excel/CSV, identificación de variables, definición de subgrupos
racionales, limpieza y tablas resumen.
"""
import io

import numpy as np
import pandas as pd


# ------------------------------------------------------------------ carga ---
def leer_archivo(archivo, hoja=None, sep=None, decimal=","):
    """Lee un archivo CSV o Excel subido por el usuario y devuelve un DataFrame.

    archivo: objeto tipo archivo (st.file_uploader) o ruta.
    hoja:    nombre de hoja para Excel (None = primera hoja).
    sep:     separador CSV (None = detección automática).
    decimal: separador decimal del CSV ("," o ".").
    """
    nombre = getattr(archivo, "name", str(archivo)).lower()
    if nombre.endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(archivo, sheet_name=hoja if hoja is not None else 0)
    datos = archivo.getvalue() if hasattr(archivo, "getvalue") else open(archivo, "rb").read()
    texto = datos.decode("utf-8-sig", errors="replace")
    if sep is None:
        primera = texto.splitlines()[0] if texto else ""
        sep = ";" if primera.count(";") > primera.count(",") else ("\t" if "\t" in primera else ",")
    if sep == "," and decimal == ",":
        decimal = "."
    return pd.read_csv(io.StringIO(texto), sep=sep, decimal=decimal)


def hojas_excel(archivo):
    """Lista de hojas de un libro Excel."""
    return pd.ExcelFile(archivo).sheet_names


# --------------------------------------------------------------- limpieza ---
def a_numerico(serie: pd.Series) -> pd.Series:
    """Convierte a número aceptando números escritos como texto, con coma o punto decimal
    (también «1.234,5» o «1,234.5»); lo que no sea número queda NaN."""
    if pd.api.types.is_numeric_dtype(serie) and not pd.api.types.is_bool_dtype(serie):
        return pd.to_numeric(serie, errors="coerce")
    def uno(v):
        if v is None or (isinstance(v, float) and v != v) or v is pd.NA:
            return None
        v = str(v).strip().replace(" ", "").replace("\u00a0", "")
        if not v:
            return None
        if "," in v and "." in v:  # el último separador es el decimal
            v = v.replace(".", "").replace(",", ".") if v.rfind(",") > v.rfind(".") else v.replace(",", "")
        else:
            v = v.replace(",", ".")
        return v

    return pd.to_numeric(pd.Series([uno(v) for v in serie.tolist()], index=serie.index, dtype="object"),
                         errors="coerce")


def limpiar(df: pd.DataFrame, columnas, quitar_vacios=True, rango=None):
    """Limpia las columnas numéricas indicadas.

    Devuelve (df_limpio, informe) donde informe es una lista de textos con lo realizado.
    rango: (minimo, maximo) para descartar valores fuera de un rango físico posible
           (por ejemplo errores de digitación); None = no se aplica.
    """
    informe = []
    df = df.copy()
    for c in columnas:
        antes = df[c].notna().sum()
        df[c] = a_numerico(df[c])
        despues = df[c].notna().sum()
        if despues < antes:
            informe.append(f"Columna «{c}»: {antes - despues} valores no numéricos convertidos a vacío.")
        if rango is not None:
            lo, hi = rango
            fuera = ((df[c] < lo) | (df[c] > hi)).sum()
            if fuera:
                df.loc[(df[c] < lo) | (df[c] > hi), c] = np.nan
                informe.append(f"Columna «{c}»: {fuera} valores fuera del rango [{lo}, {hi}] eliminados.")
    if quitar_vacios:
        n0 = len(df)
        df = df.dropna(subset=list(columnas), how="all")
        if len(df) < n0:
            informe.append(f"Se eliminaron {n0 - len(df)} filas completamente vacías.")
    if not informe:
        informe.append("No se encontraron problemas en los datos seleccionados.")
    return df, informe


# ------------------------------------------------------ subgrupos racionales ---
def subgrupos_desde_filas(df: pd.DataFrame, columnas_obs):
    """Formato ANCHO: cada fila es un subgrupo y cada columna una observación."""
    mat = df[list(columnas_obs)].apply(a_numerico)
    grupos = [fila.dropna().to_numpy(dtype=float) for _, fila in mat.iterrows()]
    etiquetas = list(range(1, len(grupos) + 1))
    return _filtrar_vacios(grupos, etiquetas)


def subgrupos_desde_id(df: pd.DataFrame, col_valor, col_grupo):
    """Formato LARGO: una columna con la medición y otra con el identificador del subgrupo."""
    d = df[[col_grupo, col_valor]].copy()
    d[col_valor] = a_numerico(d[col_valor])
    d = d.dropna()
    grupos, etiquetas = [], []
    for g, sub in d.groupby(col_grupo, sort=False):
        grupos.append(sub[col_valor].to_numpy(dtype=float))
        etiquetas.append(g)
    return _filtrar_vacios(grupos, etiquetas)


def subgrupos_consecutivos(valores, n):
    """Una sola columna en orden de producción: se agrupan cada n datos consecutivos.
    Los datos sobrantes al final (menos de n) se descartan."""
    x = pd.Series(valores).dropna().to_numpy(dtype=float)
    k = len(x) // n
    grupos = [x[i * n:(i + 1) * n] for i in range(k)]
    return grupos, list(range(1, k + 1))


def _filtrar_vacios(grupos, etiquetas):
    pares = [(g, e) for g, e in zip(grupos, etiquetas) if len(g) > 0]
    return [p[0] for p in pares], [p[1] for p in pares]


def tabla_subgrupos(grupos, etiquetas):
    """Tabla resumen por subgrupo: n, media, rango, desviación estándar."""
    filas = []
    for e, g in zip(etiquetas, grupos):
        filas.append({
            "Subgrupo": e,
            "n": len(g),
            "Media (X̄)": float(np.mean(g)),
            "Rango (R)": float(np.max(g) - np.min(g)),
            "Desv. est. (S)": float(np.std(g, ddof=1)) if len(g) > 1 else np.nan,
            "Mínimo": float(np.min(g)),
            "Máximo": float(np.max(g)),
        })
    return pd.DataFrame(filas)


def resumen_descriptivo(x):
    """Estadística descriptiva (módulo, sección 2 y presentación de capacidad)."""
    x = pd.Series(x).dropna().astype(float)
    moda = x.mode()
    return pd.DataFrame({
        "Estadístico": ["Número de datos (N)", "Media", "Mediana", "Moda", "Desviación estándar muestral (S)",
                        "Varianza", "Mínimo", "Máximo", "Rango (R = Xmáx − Xmín)", "Coef. de variación (%)"],
        "Valor": [len(x), x.mean(), x.median(), (moda.iloc[0] if len(moda) else np.nan), x.std(ddof=1),
                  x.var(ddof=1), x.min(), x.max(), x.max() - x.min(),
                  100 * x.std(ddof=1) / x.mean() if x.mean() != 0 else np.nan],
    })


def tamano_constante(grupos):
    """Devuelve el n más frecuente y si todos los subgrupos lo comparten."""
    ns = [len(g) for g in grupos]
    if not ns:
        return 0, True
    n_mod = max(set(ns), key=ns.count)
    return n_mod, all(v == n_mod for v in ns)
