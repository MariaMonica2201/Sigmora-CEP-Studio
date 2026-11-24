"""Módulo 1. Gestión de datos."""
import os

import numpy as np
import pandas as pd
import streamlit as st

from cep import atributos, datos, empresa, graficos, supuestos, validacion
from paginas import estilo, ui

EJEMPLOS = {
    "Diámetro de agujeros (variables, 20 subgrupos × 5) — módulo 2.6": ("diametro_agujeros_XR.csv", "var_ancho"),
    "Espesor de disco de plástico (variables, 120 individuales) — presentación de capacidad": ("espesor_disco_IMR.csv", "var_col"),
    "Latas defectuosas, n = 40 (carta p/np, Fase I) — módulo 4.8.1": ("latas_p_fase1.csv", "attr"),
    "Módems defectuosos, n variable (carta p) — módulo 4.8.1.2": ("modems_p_n_variable.csv", "attr"),
    "Duraznos golpeados, n = 300 (carta np) — módulo 4.8.2": ("duraznos_np.csv", "attr"),
    "Disconformidades en circuitos (carta c) — módulo 4.8.3": ("circuitos_c.csv", "attr"),
    "Defectos en computadoras, n = 5 (carta u) — módulo 4.8.4": ("computadoras_u.csv", "attr"),
    "Defectos en tela, n variable (carta u) — módulo 4.8.4.1": ("textil_u_n_variable.csv", "attr"),
}


def render():
    estilo.encabezado("folder-open", "Gestión de datos", "Carga desde Excel o CSV, variables, subgrupos racionales, limpieza y tablas resumen.", "Paso 3")
    t1, t2, t3 = st.tabs(["1. Cargar datos", "2. Variables y subgrupos", "3. Tablas resumen"])

    with t1:
        lb = ui.libro()
        origenes = ["Subir archivo (Excel o CSV)", "Usar datos de ejemplo del módulo"]
        if lb:
            origenes.insert(0, f"Libro ya cargado: {lb['nombre']}")
        origen = st.radio("Origen de los datos", origenes, horizontal=True)
        df = None
        if origen.startswith("Libro"):
            st.caption("Cada hoja del libro se puede analizar por separado; elija aquí la que va a usar. Las cartas "
                       "p/c y el Pareto (paso 10) toman sus hojas de este mismo libro.")
            hojas = lb["hojas"]
            hoja = st.selectbox("Hoja", hojas, index=ui.hoja_sugerida(hojas), key="hoja_libro")
            df = ui.hoja_df(hoja)
            st.session_state["df_nombre"] = f"{lb['nombre']} · hoja «{hoja}»"
            st.session_state["df_hoja"] = hoja
        elif origen.startswith("Subir"):
            arch = st.file_uploader("Archivo de datos", type=["csv", "xlsx", "xls", "txt"])
            if arch is not None:
                hoja = None
                c1, c2 = st.columns(2)
                if arch.name.lower().endswith((".xlsx", ".xls")):
                    ui.guardar_libro(arch.name, arch.getvalue())
                    hojas = datos.hojas_excel(arch)
                    hoja = st.selectbox("Hoja", hojas, index=ui.hoja_sugerida(hojas))
                    arch.seek(0)
                else:
                    sep = c1.selectbox("Separador (CSV)", ["Automático", ";", ",", "Tabulación"])
                    dec = c2.selectbox("Separador decimal (CSV)", [",", "."])
                sep = None if hoja is not None or sep == "Automático" else ("\t" if sep == "Tabulación" else sep)
                dec = "," if hoja is not None else dec
                try:
                    df = datos.leer_archivo(arch, hoja=hoja, sep=sep, decimal=dec)
                    st.session_state["df_nombre"] = arch.name + (f" · hoja «{hoja}»" if hoja else "")
                    st.session_state["df_hoja"] = hoja or ""
                except Exception as e:  # noqa: BLE001
                    st.error(f"No se pudo leer el archivo: {e}")
        else:
            nombre = st.selectbox("Conjunto de datos de ejemplo", list(EJEMPLOS))
            df = pd.read_csv(os.path.join(ui.CARPETA_EJEMPLOS, EJEMPLOS[nombre][0]))
            st.session_state["df_nombre"] = EJEMPLOS[nombre][0]
            st.session_state["df_hoja"] = ""
        if df is not None:
            st.session_state["df"] = df
        df = st.session_state.get("df")
        if df is not None:
            st.success(f"Datos cargados: {st.session_state.get('df_nombre', '')} — {df.shape[0]} filas × {df.shape[1]} columnas.")
            st.dataframe(df, width="stretch", height=280)
            with st.expander("Formatos de entrada aceptados"):
                st.markdown("""
- **Variables, formato ancho:** cada fila es un subgrupo y cada columna una observación (X1, X2, …, Xn).
- **Variables, formato largo:** una columna con la medición y otra con el número/código de subgrupo.
- **Variables, una columna:** mediciones en orden de producción; se agrupan cada *n* datos consecutivos o se usan como individuales (carta I-MR).
- **Atributos:** una columna con el conteo (defectuosos o defectos) y, opcionalmente, otra con el tamaño de muestra *n* de cada subgrupo.
- CSV con `;` o `,` y coma o punto decimal; Excel `.xlsx`.
""")

    with t2:
        df = st.session_state.get("df")
        if df is None:
            st.info("Primero cargue datos en la pestaña 1.")
            return
        import re
        es_attr = bool(re.search(r"carta p|recus|defect|rechaz|atribut|no conform",
                                 str(st.session_state.get("df_hoja") or ""), flags=re.I))
        es_attr = es_attr or any(es_col(PAT_CONTEO, c) for c in df.columns)
        tipo = st.radio("Tipo de característica de calidad",
                        ["Variable (se mide: peso, longitud, diámetro…)", "Atributo (se cuenta: defectuosos o defectos)"],
                        index=1 if es_attr else 0, horizontal=True, key=f"tipo_dato_{es_attr}")
        if tipo.startswith("Variable"):
            _variables(df)
        else:
            _atributos(df)

    with t3:
        _resumen()


def _horas_entre_subgrupos(df):
    """Si el archivo trae una columna de hora (una fila por subgrupo), estima las horas entre subgrupos con la mediana
    de las diferencias positivas entre filas consecutivas. Devuelve None si no se puede."""
    import re
    col = next((c for c in df.columns if re.match(r"^\s*hora", str(c), flags=re.I)), None)
    if col is None:
        return None
    horas = []
    for v in df[col]:
        try:
            if hasattr(v, "hour"):
                horas.append(v.hour + v.minute / 60)
            else:
                hh, mm = (str(v).strip().replace(".", ":").split(":") + ["0"])[:2]
                horas.append(int(hh) + int(mm[:2]) / 60)
        except (ValueError, TypeError):
            horas.append(np.nan)
    dif = np.diff(np.asarray(horas, float))
    dif = dif[np.isfinite(dif) & (dif > 0)]
    if len(dif) == 0:
        return None
    t = float(np.median(dif))
    return round(t * 4) / 4 if t >= 0.25 else None


def _raiz_columna(c):
    """Nombre base de una columna de observación: 'Peso R1 (kg)' -> 'Peso', 'X3' -> 'X'."""
    import re
    base = re.sub(r"\s*\([^)]*\)\s*$", "", str(c)).strip()
    base = re.sub(r"[\s_\-]*(R|X|Obs|M)?\s*\d+$", "", base, flags=re.I).strip()
    return base or "Observaciones"


def _variables(df):
    cols = list(df.columns)
    num = [c for c in cols if datos.a_numerico(df[c]).notna().mean() > 0.5]
    formato = st.radio("Formato de los datos", ["Ancho (fila = subgrupo)", "Largo (columna de subgrupo)",
                                                "Una columna en orden de producción"])
    perfil = st.session_state.get("perfil")
    sugeridas = [f"{v['Característica']} ({v.get('Unidad') or ''})".replace(" ()", "")
                 for v in (perfil or {}).get("variables", []) if v.get("Tipo") == "Variable"]
    if sugeridas:
        elegida = st.selectbox("Característica de la hoja «Especificaciones»", ["(escribir otra)"] + sugeridas)
        if elegida != "(escribir otra)":
            st.session_state["nombre_var"] = elegida
    grupos_cols = {}
    if formato.startswith("Ancho"):
        for c in num:
            if c.lower() in ("subgrupo", "muestra", "orden", "id"):
                continue
            grupos_cols.setdefault(_raiz_columna(c), []).append(c)
        if len(grupos_cols) > 1:
            st.info("El archivo trae varias características medidas en el mismo registro. "
                    "Elija una: cada carta se hace con una sola característica.")
            carac = st.selectbox("Característica a analizar", list(grupos_cols), key="carac_ancho")
            if st.session_state.get("_carac_ancho_prev") != carac:
                st.session_state["_carac_ancho_prev"] = carac
                coinc = [s for s in sugeridas if s.lower().startswith(carac.lower())]
                st.session_state["nombre_var"] = coinc[0] if coinc else carac
    nombre_var = st.text_input("Nombre de la variable de calidad (y unidad)", st.session_state.get("nombre_var", "Medición"))
    with st.expander("Limpieza de datos"):
        usar_rango = st.checkbox("Descartar valores fuera de un rango físicamente posible (errores de digitación)")
        lo = hi = None
        if usar_rango:
            c1, c2 = st.columns(2)
            lo = c1.number_input("Mínimo posible", value=0.0, format="%.6f")
            hi = c2.number_input("Máximo posible", value=1e6, format="%.6f")
    rango = (lo, hi) if usar_rango else None
    grupos = etiquetas = None
    individuales = None
    if formato.startswith("Ancho"):
        if len(grupos_cols) > 1:
            defecto = grupos_cols[st.session_state["carac_ancho"]]
        else:
            defecto = [c for c in num if c.lower() not in ("subgrupo", "muestra", "orden", "id")]
        obs = st.multiselect("Columnas de observaciones", num, default=defecto,
                             key=f"obs_{'|'.join(defecto)}")
        col_id = st.selectbox("Columna de identificación del subgrupo (opcional)", ["(ninguna)"] + cols)
        if obs:
            dfl, informe = datos.limpiar(df, obs, rango=rango)
            grupos, etiquetas = datos.subgrupos_desde_filas(dfl, obs)
            if col_id != "(ninguna)":
                etiquetas = list(dfl.loc[dfl[obs].notna().any(axis=1), col_id])
    elif formato.startswith("Largo"):
        c1, c2 = st.columns(2)
        cv = c1.selectbox("Columna de la medición", num)
        cg = c2.selectbox("Columna del subgrupo", cols)
        dfl, informe = datos.limpiar(df, [cv], rango=rango)
        grupos, etiquetas = datos.subgrupos_desde_id(dfl, cv, cg)
    else:
        cv = st.selectbox("Columna de la medición", num, index=len(num) - 1 if num else 0)
        dfl, informe = datos.limpiar(df, [cv], rango=rango)
        individuales = dfl[cv].dropna().to_numpy(dtype=float)
        n = st.number_input("Tamaño de subgrupo racional n (1 = individuales, carta I-MR)", 1, 25, 1)
        if n > 1:
            grupos, etiquetas = datos.subgrupos_consecutivos(individuales, int(n))
            sobran = len(individuales) - len(grupos) * n
            if sobran:
                informe.append(f"Se descartan los últimos {sobran} datos que no completan un subgrupo.")
        else:
            grupos = [np.array([v]) for v in individuales]
            etiquetas = list(range(1, len(individuales) + 1))
    st.markdown("**Subgrupo racional:** debe formarse con unidades producidas en condiciones lo más homogéneas "
                "posible (misma máquina, operador, materia prima y momento), para que la variación *dentro* del "
                "subgrupo refleje sólo causas comunes y la variación *entre* subgrupos revele las causas especiales.")
    if grupos:
        for t in informe:
            st.caption("" + t)
        n_mod, constante = datos.tamano_constante(grupos)
        todos = np.concatenate(grupos)
        if len(todos) > 1 and np.ptp(todos) == 0:
            st.error("Todos los datos son iguales (variabilidad nula): no se pueden calcular límites de control, "
                     "normalidad ni capacidad. Revise la columna elegida o la resolución del instrumento.")
            return
        if n_mod > 1 and sum(len(g) == n_mod for g in grupos) < 2:
            st.warning(f"Sólo hay {sum(len(g) == n_mod for g in grupos)} subgrupo completo de n = {n_mod}: las cartas "
                       "X̄-R y X̄-S necesitan al menos 2.")
        if not constante:
            st.warning(f"Los subgrupos no tienen todos el mismo tamaño (el más frecuente es n = {n_mod}). Las cartas "
                       f"X̄-R y X̄-S usarán sólo los subgrupos completos de tamaño {n_mod}.")
        if individuales is None:
            individuales = np.concatenate(grupos)
        if st.button("Usar estos datos para el análisis", type="primary"):
            st.session_state["var"] = {"grupos": grupos, "etiquetas": etiquetas, "individuales": individuales,
                                       "nombre": nombre_var, "n": n_mod, "constante": constante,
                                       "t_datos": _horas_entre_subgrupos(df)}
            st.session_state["nombre_var"] = nombre_var
            st.session_state["fase1_var"] = None
            if (st.session_state.get("attr") or {}).get("desde_variables"):
                st.session_state["attr"] = None  # la conversión a atributos era de los datos anteriores
            st.success(f"{len(grupos)} subgrupos (n = {n_mod}) y {len(individuales)} datos listos. "
                       "Continúe con el paso 4 (Especificaciones) y luego Supuestos (5), Estabilidad · Fase I (6) y Capacidad (7); en el paso 10 puede convertirlos en atributos con el LIE/LSE.")


PAT_CONTEO = (r"recus|defectuos|defecto|rechaz|no ?conform|fuera de (calibr|especif|toler|rango)|malos|malas|"
              r"descart|conteo|fallas|danad")
PAT_N = (r"cortad|inspecc|revisad|evaluad|muestread|examinad|unidades|tamano|^n$|^n ?\(|total|producid")
PAT_ID = (r"subgrupo|muestra|lote|^dia|fecha|semana|^hora|^turno|^n[°ºo.]? ?(de )?(subgrupo|muestra)?$|^id$|codigo")


def norm_col(c):
    """Nombre de columna normalizado para reconocerlo: minúsculas, sin tildes y con espacios simples."""
    import unicodedata
    t = unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode()
    return " ".join(t.lower().split())


def es_col(patron, c):
    import re
    return bool(re.search(patron, norm_col(c)))


def es_id(c):
    """Columna de identificación (subgrupo, fecha, hora…): nunca es un conteo ni un tamaño de muestra."""
    return es_col(PAT_ID, c) and not es_col(PAT_CONTEO, c) and not es_col(PAT_N, c)


def columnas_enteras(df, incluir_id=False):
    """Columnas numéricas cuyos valores son enteros no negativos (sirven como conteos o como n). Las columnas de
    identificación (subgrupo, fecha, hora…) se dejan fuera."""
    salida = []
    for c in df.columns:
        x = datos.a_numerico(df[c])
        if x.notna().mean() <= 0.5:
            continue
        v = x.dropna().to_numpy(float)
        if len(v) and np.all(v >= 0) and np.allclose(v, np.round(v), atol=1e-6):
            salida.append(c)
    return salida if incluir_id else [c for c in salida if not es_id(c)]


def unidad_tiempo_attr(df):
    """«horas» si la hoja trae una columna de hora con varias muestras por día; si no, «días» (una muestra diaria)."""
    col = next((c for c in df.columns if norm_col(c).startswith("hora")), None)
    return "horas" if col is not None and df[col].nunique() > 1 else "días"


def sugerir_columnas_attr(df, num=None):
    """(conteo, n) sugeridos: primero por nombre; si no, el conteo es la columna de valores más pequeños y n la de
    valores más grandes que nunca es menor que el conteo."""
    num = columnas_enteras(df) if num is None else num
    cc = next((c for c in num if es_col(PAT_CONTEO, c)), None)
    cn = next((c for c in num if c != cc and es_col(PAT_N, c)), None)
    medias = {c: float(datos.a_numerico(df[c]).mean()) for c in num}
    if cc is None and num:
        cand = [c for c in num if c != cn] or num
        cc = min(cand, key=lambda c: medias[c])
    if cn is None and cc is not None:
        xc = datos.a_numerico(df[cc])
        cand = [c for c in num if c != cc and (datos.a_numerico(df[c]) >= xc).all() and medias[c] > medias[cc]]
        cn = max(cand, key=lambda c: medias[c]) if cand else None
    return cc, cn


def atributos_automaticos(df):
    """Arma los datos por atributos de una hoja sin intervención: conteo = columna de defectuosos/defectos
    (por nombre), n = columna de unidades inspeccionadas. Devuelve None si la hoja no tiene esas columnas."""
    import re
    ent = columnas_enteras(df)
    cc = next((c for c in ent if es_col(PAT_CONTEO, c)), None)
    if cc is None:
        return None
    cn = next((c for c in ent if c != cc and es_col(PAT_N, c)), None)
    cid = next((c for c in df.columns if c != cc and es_id(c)), None)
    use = [cc] + ([cn] if cn else [])
    dfl = df.dropna(subset=use)
    conteo = datos.a_numerico(dfl[cc]).to_numpy(float)
    if cn is None:
        return None
    n = datos.a_numerico(dfl[cn]).to_numpy(float)
    que = "defectos" if re.search(r"defecto(?!s? ?uos)|no ?conformidad", norm_col(cc)) and not re.search(
        r"defectuos", norm_col(cc)) else "defectuosos"
    if que == "defectuosos" and np.any(conteo > n):
        return None
    return {"conteo": conteo, "n": n, "etiquetas": list(dfl[cid]) if cid else list(range(1, len(conteo) + 1)),
            "que": que, "constante": bool(np.allclose(n, n[0])), "nombre": cc, "conteo_reconocido": True,
            "t_unidad": unidad_tiempo_attr(df)}


def attr_dudoso(a):
    """Datos por atributos que no parecen conteos: decimales o una columna que no se llama como un conteo."""
    if not a or a.get("desde_variables"):
        return False
    c = np.asarray(a["conteo"], float)
    return (not np.allclose(c, np.round(c))) or (not a.get("conteo_reconocido", False))


def _atributos(df, en_paso8=False):
    import re
    cols = list(df.columns)
    num = columnas_enteras(df)
    raras = [c for c in cols if c not in num and (es_col(PAT_CONTEO, c) or es_col(PAT_N, c))]
    for c in raras:
        x = datos.a_numerico(df[c])
        malos = [str(v) for v, xv in zip(df[c], x) if pd.notna(v) and (pd.isna(xv) or xv < 0 or xv != round(xv))][:3]
        st.warning(f"La columna «{c}» parece de conteo o de tamaño de muestra, pero no se puede usar: tiene valores "
                   f"que no son enteros no negativos ({', '.join(malos) or 'celdas vacías'}). Corríjalos en el Excel.")
    if not num:
        st.warning("Esta hoja no tiene columnas de conteo: los defectuosos o defectos se cuentan con números "
                   "enteros (0, 1, 2…). Las columnas con decimales son mediciones: analícelas como **Variable**.")
        return
    sug_c, sug_n = sugerir_columnas_attr(df, num)
    if not any(es_col(PAT_CONTEO, c) for c in num):
        st.info(f"Ninguna columna se llama como un conteo (defectuosos, no conformes, rechazados…): se propone "
                f"«{sug_c}» por tener los valores más pequeños. Revíselo; sólo se muestran columnas con números enteros "
                "y no se ofrecen las de identificación (subgrupo, fecha, hora).")
    que = st.radio("¿Qué se cuenta en cada muestra?",
                   ["Unidades defectuosas / no conformes (cada unidad es buena o mala)",
                    "Defectos / no conformidades (una unidad puede tener varios)"])
    que = "defectuosos" if que.startswith("Unidades") else "defectos"
    c1, c2 = st.columns(2)
    cc = c1.selectbox("Columna del conteo", num, index=num.index(sug_c) if sug_c in num else 0)
    opciones_n = ["(tamaño constante)"] + [c for c in num if c != cc]
    cn = c2.selectbox("Columna del tamaño de muestra n (o unidades de inspección)", opciones_n,
                      index=opciones_n.index(sug_n) if sug_n in opciones_n else 0,
                      help="Sólo columnas con números enteros.")
    n_const = None
    if cn == "(tamaño constante)":
        n_const = st.number_input("Tamaño de muestra n (para carta c use 1 = una unidad de inspección)", 1.0,
                                  1e7, 1.0 if que == "defectos" else 50.0)
    op_id = ["(ninguna)"] + cols
    col_id = st.selectbox("Columna de identificación (opcional)", op_id,
                          index=next((i for i, c in enumerate(op_id) if i and c != cc and es_id(c)), 0))
    use = [cc] + ([cn] if cn != "(tamaño constante)" else [])
    dfl, informe = datos.limpiar(df, use)
    dfl = dfl.dropna(subset=use)
    conteo = dfl[cc].to_numpy(dtype=float)
    n = dfl[cn].to_numpy(dtype=float) if cn != "(tamaño constante)" else np.full(len(conteo), n_const)
    etiquetas = list(dfl[col_id]) if col_id != "(ninguna)" else list(range(1, len(conteo) + 1))
    for t in informe:
        st.caption("" + t)
    try:
        validacion.conteos(conteo, n, que)
    except validacion.DatosInvalidos as e:
        st.error(str(e))
        return
    st.dataframe(pd.DataFrame({"Subgrupo": etiquetas, "n": n, "Conteo": conteo}), width="stretch", height=220)
    if st.button("Usar estos datos para el análisis", type="primary"):
        st.session_state["attr"] = {"conteo": conteo, "n": n, "etiquetas": etiquetas, "que": que,
                                    "constante": bool(np.allclose(n, n[0])), "nombre": cc,
                                    "conteo_reconocido": es_col(PAT_CONTEO, cc), "t_unidad": unidad_tiempo_attr(df)}
        st.session_state["fase1_attr"] = None
        if en_paso8:
            st.rerun()
        st.success(f"{len(conteo)} subgrupos listos. Continúe con el paso 10 (Cartas p/c).")


def _resumen():
    var = st.session_state.get("var")
    attr = st.session_state.get("attr")
    if var is None and attr is None:
        st.info("Defina las variables en la pestaña 2.")
        return
    if var is not None:
        st.subheader(f"Variable: {var['nombre']}")
        x = var["individuales"]
        desc = datos.resumen_descriptivo(x)
        c1, c2 = st.columns([1, 2])
        c1.dataframe(desc, hide_index=True, width="stretch")
        fig_h = graficos.histograma_capacidad(x, float(np.mean(x)), float(np.std(x, ddof=1)),
                                              nbins=supuestos.numero_clases(len(x)), titulo="Histograma de los datos")
        c2.plotly_chart(fig_h, width="stretch")
        tf, info = supuestos.tabla_frecuencias(x)
        st.markdown(f"**Tabla de frecuencias** (k = 1 + 3,3·log N = {info['k']} clases, amplitud h = {info['h']:.5g}). "
                    f"Media agrupada = {info['media agrupada']:.5g}; desviación agrupada = {info['desv. agrupada']:.5g}. "
                    f"Forma: {supuestos.forma_histograma(x)}")
        st.dataframe(tf, hide_index=True, width="stretch")
        ts = datos.tabla_subgrupos(var["grupos"], var["etiquetas"])
        if var["n"] > 1:
            st.markdown("**Tabla resumen por subgrupo**")
            st.dataframe(ts, hide_index=True, width="stretch", height=260)
        fig_s = graficos.serie_tiempo(x, f"{var['nombre']} en orden de producción")
        st.plotly_chart(fig_s, width="stretch")
        ui.boton_registrar("m1_var", "Datos", f"Caracterización de datos: {var['nombre']}",
                           tablas=[("Estadística descriptiva", desc), ("Tabla de frecuencias", tf),
                                   ("Resumen por subgrupo", ts)],
                           figuras=[("Histograma de los datos", fig_h), ("Datos en orden de producción", fig_s)],
                           conclusiones=[f"Se analizaron {len(x)} datos en {len(var['grupos'])} subgrupos de tamaño "
                                         f"n = {var['n']}.", f"Forma del histograma: {supuestos.forma_histograma(x)}"])
    if attr is not None:
        st.subheader(f"Atributo: {attr['nombre']} ({attr['que']})")
        tasa = attr["conteo"] / attr["n"]
        tab = pd.DataFrame({"Estadístico": ["Subgrupos (k)", "Total inspeccionado (Σn)", f"Total {attr['que']}",
                                            "Proporción / tasa global", "Mínimo por subgrupo", "Máximo por subgrupo"],
                            "Valor": [len(tasa), attr["n"].sum(), attr["conteo"].sum(),
                                      attr["conteo"].sum() / attr["n"].sum(), tasa.min(), tasa.max()]})
        st.dataframe(tab, hide_index=True)
        ui.boton_registrar("m1_attr", "Datos", f"Caracterización de datos por atributos: {attr['nombre']}",
                           tablas=[("Resumen de atributos", tab)])
