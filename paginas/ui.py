"""Funciones de interfaz compartidas por todas las páginas."""
import os

import numpy as np
import pandas as pd
import streamlit as st

from cep import graficos, patrones, reporte
from cep.estadistica import alfa_de_z

CARPETA_EJEMPLOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_ejemplo")


def estado(clave, defecto=None):
    if clave not in st.session_state:
        st.session_state[clave] = defecto
    return st.session_state[clave]


def config():
    """Configuración global elegida en la barra lateral."""
    return st.session_state.get("config", {"z": 3.0, "k_tend": 7, "k_corr": 8, "k_estr": 15, "k_mezcla": 8})


def barra_lateral_config(cont=None):
    """Parámetros generales (límites y reglas de patrones). cont: contenedor donde se dibujan."""
    cont = cont or st.sidebar
    cont.markdown("**Límites de control**")
    modo = cont.radio("Límites de control definidos por", ["Z_α/2 (sigmas)", "α (riesgo tipo I)"],
                      horizontal=True, key="modo_lim")
    if modo.startswith("Z"):
        z = cont.number_input("Z_α/2", 0.5, 6.0, 3.0, 0.1, key="z_in",
                              help="3 sigmas es el criterio clásico de Shewhart (α = 0,0027).")
    else:
        alfa = cont.number_input("α", 0.0001, 0.5, 0.0027, 0.0001, format="%.4f", key="a_in")
        from scipy import stats
        z = float(stats.norm.ppf(1 - alfa / 2))
    cont.caption(f"Z_α/2 = {z:.4f} → α = {alfa_de_z(z):.5f} → ARL0 = {1 / alfa_de_z(z):.1f}")
    cont.markdown("**Reglas de patrones no aleatorios (sección 4.5)**")
    c1, c2 = cont.columns(2)
    k_tend = c1.number_input("Tendencia: puntos seguidos", 5, 15, 7, key="k_tend")
    k_corr = c2.number_input("Corrimiento: a un lado de la LC", 5, 15, 8, key="k_corr")
    k_estr = c1.number_input("Estratificación: cerca de la LC", 6, 30, 15, key="k_estr",
                             help="El módulo no fija un número; valor configurable.")
    k_mezcla = c2.number_input("Mezcla: alejados de la LC", 4, 20, 8, key="k_mezcla",
                               help="El módulo no fija un número; valor configurable.")
    st.session_state["config"] = {"z": z, "k_tend": k_tend, "k_corr": k_corr, "k_estr": k_estr, "k_mezcla": k_mezcla}


def analizar_patrones(carta, excluir=None):
    c = config()
    vals = np.asarray(carta["valores"], float).copy()
    ok = ~np.isnan(vals)
    # los rangos móviles empiezan con NaN: se analizan sólo los puntos válidos
    idx = np.where(ok)[0]
    df = patrones.analizar(vals[ok], carta["lc"][ok], carta["lcs"][ok], carta["lci"][ok],
                           k_tendencia=c["k_tend"], k_corrimiento=c["k_corr"],
                           k_estratificacion=c["k_estr"], k_mezcla=c["k_mezcla"])
    if len(df):
        df["_puntos"] = df["_puntos"].apply(lambda pts: [int(idx[p - 1]) + 1 for p in pts])
        df["Puntos"] = df["_puntos"].apply(lambda pts: ", ".join(map(str, pts)))
    return df


def mostrar_carta(carta, excluir=None, clave=""):
    """Dibuja una carta, analiza patrones y devuelve (figura, tabla de señales)."""
    sen = analizar_patrones(carta)
    fig = graficos.carta_control(carta, senales=patrones.puntos_con_senal(sen), excluidos=excluir)
    st.plotly_chart(fig, width="stretch", key=f"fig_{clave}_{carta['nombre']}")
    return fig, sen


def tabla_parametros(d):
    filas = []
    for k, v in d.items():
        if isinstance(v, (float, np.floating)):
            v = round(float(v), 6)
        filas.append({"Parámetro": k, "Valor": str(v)})
    return pd.DataFrame(filas)


def registrar(clave, modulo, titulo, tablas=None, figuras=None, conclusiones=None):
    """Guarda (o reemplaza) una sección del reporte."""
    rep = estado("reporte", {})
    rep[clave] = reporte.nueva_seccion(modulo, titulo, tablas, figuras, conclusiones)
    st.session_state["reporte"] = rep


def boton_registrar(clave, modulo, titulo, tablas=None, figuras=None, conclusiones=None):
    if st.button("Agregar / actualizar en el reporte", key=f"reg_{clave}"):
        registrar(clave, modulo, titulo, tablas, figuras, conclusiones)
        st.success("Sección guardada en el informe (paso 13).")


def descarga_df(df, nombre, clave):
    st.download_button("Descargar tabla (CSV)", df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=f"{nombre}.csv", mime="text/csv", key=f"dl_{clave}")


def bitacora(senales, clave):
    """Bitácora de causas especiales (el módulo recomienda llevar una bitácora de cambios).
    Permite registrar, para cada señal, la causa asignable identificada y la acción tomada."""
    if senales is None or len(senales) == 0:
        return pd.DataFrame()
    st.markdown("**Bitácora de causas especiales** — registre la causa asignable encontrada y la acción "
                "(sirve para justificar el cepillado y para el informe).")
    guardada = estado(f"bit_{clave}", {})
    filas = []
    for _, s in senales.iterrows():
        k = f"{s['Regla']}|{s['Puntos']}"
        filas.append({"Regla": s["Regla"], "Puntos": s["Puntos"],
                      "Causa asignable identificada": guardada.get(k, {}).get("causa", ""),
                      "Acción tomada": guardada.get(k, {}).get("accion", "")})
    df = pd.DataFrame(filas)
    edit = st.data_editor(df, key=f"ed_{clave}", width="stretch", hide_index=True,
                          disabled=["Regla", "Puntos"])
    nuevo = {}
    for _, r in edit.iterrows():
        nuevo[f"{r['Regla']}|{r['Puntos']}"] = {"causa": r["Causa asignable identificada"],
                                                "accion": r["Acción tomada"]}
    st.session_state[f"bit_{clave}"] = nuevo
    return edit


def requiere(clave, mensaje):
    """Devuelve False (y muestra el mensaje) si falta el dato previo que el paso necesita."""
    if st.session_state.get(clave) is None:
        st.info(mensaje)
        return False
    return True


# ---------------------------------------------------------------- Libro Excel cargado (un archivo, varias hojas)
HOJAS_FICHA = ("empresa", "etapas", "procesos", "características", "caracteristicas", "especificaciones", "instrucciones",
               "notas", "leer")


def guardar_libro(nombre, contenido):
    """Guarda en la sesión un libro Excel para que los demás pasos usen sus hojas sin volver a subirlo."""
    import io
    try:
        hojas = pd.ExcelFile(io.BytesIO(contenido)).sheet_names
    except Exception:  # noqa: BLE001
        return
    previo = st.session_state.get("libro") or {}
    st.session_state["libro"] = {"nombre": nombre, "bytes": contenido, "hojas": hojas}
    if previo.get("nombre") == nombre and len(previo.get("bytes", b"")) == len(contenido):
        return
    # Si el libro trae la ficha de la empresa o la hoja de especificaciones, se aprovechan (sin borrar lo ya escrito).
    bajas = [h.strip().lower() for h in hojas]
    if any(h in bajas for h in ("empresa", "especificaciones", "características", "caracteristicas")):
        from cep import empresa as _emp
        try:
            leido = _emp.desde_excel(contenido)
        except Exception:  # noqa: BLE001
            return
        perfil = st.session_state.get("perfil") or _emp.nuevo("Empresa nueva (en blanco)")
        for k, v in leido.items():
            if k == "variables":
                if v and not perfil.get("variables"):
                    perfil["variables"] = v
            elif v not in (None, "") and not str(perfil.get(k) or "").strip():
                perfil[k] = v
        st.session_state["perfil"] = perfil


def libro():
    return st.session_state.get("libro")


def hojas_de_datos(lb=None):
    """Hojas del libro que no son de la ficha de la empresa ni notas."""
    lb = lb or libro()
    if not lb:
        return []
    return [h for h in lb["hojas"] if h.strip().lower() not in HOJAS_FICHA]


def hoja_df(hoja, lb=None):
    import io
    lb = lb or libro()
    return pd.read_excel(io.BytesIO(lb["bytes"]), sheet_name=hoja)


def hoja_sugerida(hojas, patrones_txt=()):
    """Índice de la primera hoja cuyo nombre contiene alguno de los patrones; si no, la primera hoja de datos."""
    import re
    for p in patrones_txt:
        for i, h in enumerate(hojas):
            if re.search(p, h, flags=re.I):
                return i
    for i, h in enumerate(hojas):
        if h.strip().lower() not in HOJAS_FICHA:
            return i
    return 0


def columna_sugerida(cols, patrones_txt, evitar=(), defecto=0):
    import re
    for p in patrones_txt:
        for i, c in enumerate(cols):
            if c not in evitar and re.search(p, str(c), flags=re.I):
                return i
    return defecto
