"""Módulo 3. Gráficos de control por atributos (p, np, c, u)."""
import math
import os
import re

import numpy as np
import pandas as pd
import streamlit as st

from cep import atributos, datos, diseno, graficos
from cep.estadistica import phi
from paginas import estilo, ui


def _calcular(tipo, conteo, n, et, z, excluir, metodo, estandar=None):
    if tipo == "p":
        return atributos.carta_p(conteo, n, et, z, excluir, metodo, p_estandar=estandar)
    if tipo == "np":
        return atributos.carta_np(conteo, float(n[0]), et, z, excluir, p_estandar=estandar)
    if tipo == "c":
        return atributos.carta_c(conteo, et, z, excluir, c_estandar=estandar)
    return atributos.carta_u(conteo, n, et, z, excluir, u_estandar=estandar)


F2_ATTR = r"atribut.*fase ?(ii|2)|fase ?(ii|2).*(atribut|no ?conform|recus|defect)"


def render():
    estilo.encabezado("hash", "Cartas por atributos", "Los pasos 2 a 6 para atributos: estabilidad (Fase I), capacidad, "
                      "Fase II con muestras nuevas, potencia y carga muestral de la misma característica.", "Paso 10")
    from paginas import m1_datos
    var, attr = st.session_state.get("var"), st.session_state.get("attr")
    lb = ui.libro()
    if lb and ui.hojas_de_datos(lb) and (attr is None or m1_datos.attr_dudoso(attr)):
        # Toma sola la hoja de conteos del libro (p. ej. «Recusados (carta p)») en vez de mediciones con decimales.
        hojas = [h for h in ui.hojas_de_datos(lb) if re.search(r"carta p|recus|defect|rechaz|atribut", h, flags=re.I)
                 and not re.search(r"fase ?(ii|2)", h, flags=re.I)]
        for h in hojas:
            auto = m1_datos.atributos_automaticos(ui.hoja_df(h, lb))
            if auto:
                auto["hoja"] = h
                previo = attr
                st.session_state["attr"], st.session_state["fase1_attr"] = auto, None
                attr = auto
                st.info(f"Se tomó automáticamente la hoja **«{h}»** del libro: conteo = «{auto['nombre']}», "
                        f"{len(auto['conteo'])} muestras." + (" Los datos anteriores no eran conteos (tenían decimales "
                                                              "o no eran defectuosos/defectos)." if previo else ""))
                break
    if lb and ui.hojas_de_datos(lb):
        with st.expander(f"Muestras iniciales desde una hoja del libro ({lb['nombre']})",
                         expanded=attr is None or bool(attr.get("desde_variables"))):
            _desde_libro(lb)
        attr = st.session_state.get("attr")
    if var is not None:
        convertido = bool(attr and attr.get("desde_variables"))
        with st.expander("Calcular atributos a partir de los datos por variables cargados",
                         expanded=attr is None or convertido):
            _desde_variables(var)
        attr = st.session_state.get("attr")
    tabs = st.tabs(["2 · Estabilidad (Fase I)", "3 · Capacidad", "4 · Monitoreo Fase II", "5 · Potencia",
                    "6 · Carga muestral (ATS1)", "Pareto de causas (opcional)"])
    with tabs[5]:
        _pareto()
    if attr is None:
        with tabs[0]:
            st.info("Cargue datos por atributos (arriba, desde el libro, o en el paso 3), o convierta sus datos por "
                    "variables con el LIE/LSE.")
        return
    with tabs[0]:
        eleccion = _cartas()
    f1 = st.session_state.get("fase1_attr")
    for t in tabs[1:5]:
        if not f1 or not eleccion:
            with t:
                st.info("Complete primero la pestaña 2 (Fase I).")
    if not f1 or not eleccion:
        return
    a, tipo, z, metodo = eleccion
    with tabs[1]:
        _capacidad_attr(a, f1)
    with tabs[2]:
        _fase2(a, f1["tipo"], z, metodo)
    with tabs[3]:
        ctx = _potencia_attr(a, f1, z)
    with tabs[4]:
        _carga_attr(ctx)


def _desde_libro(lb):
    """Toma los conteos de una hoja del libro ya cargado (paso 2 o paso 3), sin volver a subir el archivo."""
    from paginas import m1_datos
    hojas = ui.hojas_de_datos(lb)
    hoja = st.selectbox("Hoja con los conteos", hojas,
                        index=ui.hoja_sugerida(hojas, [r"atribut", r"no ?conform", r"carta p", r"defect", r"rechaz", r"recus"]),
                        key="m3_hoja")
    df = ui.hoja_df(hoja, lb)
    st.dataframe(df, hide_index=True, width="stretch", height=min(240, 38 + 35 * len(df)))
    m1_datos._atributos(df, en_paso8=True)
    a = st.session_state.get("attr")
    if a and not a.get("desde_variables"):
        st.caption(f"En uso: «{a['nombre']}», {len(a['conteo'])} subgrupos.")


def _desde_variables(var):
    """Cada unidad medida fuera de [LIE, LSE] es una unidad defectuosa (no conforme): por subgrupo se cuentan las
    defectuosas d_i sobre n_i unidades inspeccionadas, y con eso se construyen las cartas p y np."""
    from cep import empresa
    st.markdown("Cada unidad cuya medición cae **fuera de las especificaciones** se cuenta como **defectuosa "
                "(no conforme)**. Por subgrupo queda: unidades inspeccionadas **n** y defectuosas **d**, que es "
                "justo lo que usan las cartas **p** (p = d/n) y **np**.")
    pv = empresa.buscar_variable(st.session_state.get("perfil"), var.get("nombre"))
    lie0, _, lse0 = empresa.especificaciones(pv)
    c1, c2, c3, c4 = st.columns(4)
    usa_lie = c1.checkbox("Tiene LIE", lie0 is not None or lse0 is None, key="va_usa_lie")
    lie = c2.number_input("LIE", value=lie0, format="%.6f", key="va_lie", placeholder="Escriba el LIE") if usa_lie else None
    usa_lse = c3.checkbox("Tiene LSE", lse0 is not None or lie0 is None, key="va_usa_lse")
    lse = c4.number_input("LSE", value=lse0, format="%.6f", key="va_lse", placeholder="Escriba el LSE") if usa_lse else None
    if lie is None and lse is None:
        st.info(f"**Se necesitan especificaciones (LIE y/o LSE)** de «{var['nombre']}» para saber qué unidad es "
                "defectuosa; sin ellas no se pueden armar las cartas p y np desde las mediciones. Pídalas a la empresa "
                "o al cliente. Las cartas X̄-R, X̄-S e I-MR (paso 6) sí funcionan sin especificaciones.")
        return
    if lie is not None and lse is not None and lie >= lse:
        st.error("El LIE debe ser menor que el LSE.")
        return
    grupos = [np.asarray(g, float) for g in var["grupos"]]
    fuera = [((g < lie) if lie is not None else np.zeros(len(g), bool)) | ((g > lse) if lse is not None else np.zeros(len(g), bool))
             for g in grupos]
    n = np.array([len(g) for g in grupos], float)
    d = np.array([int(f.sum()) for f in fuera], float)
    tabla = pd.DataFrame({"Subgrupo": var["etiquetas"], "n (inspeccionadas)": n.astype(int),
                          "d (defectuosas)": d.astype(int), "p = d/n": np.round(d / n, 4)})
    st.dataframe(tabla, hide_index=True, width="stretch", height=min(320, 38 + 35 * len(tabla)))
    estilo.kpis([
        dict(icono="package", etiqueta="Unidades inspeccionadas", valor=f"{int(n.sum())}", sub=f"{len(n)} subgrupos"),
        dict(icono="circle-x", etiqueta="Defectuosas", valor=f"{int(d.sum())}", sub="fuera de especificación", color=estilo.ROJO),
        dict(icono="chart-column", etiqueta="p̄ = Σd / Σn", valor=f"{d.sum() / n.sum():.4f}", color=estilo.NARANJA),
    ])
    if d.sum() == 0:
        st.warning("Ninguna unidad está fuera de especificación: p̄ = 0 y los límites de la carta p colapsan en 0. "
                   "La carta no aporta información con estos datos; revise el LIE/LSE.")
    if st.button("Usar como datos por atributos (cartas p y np)", type="primary", key="va_usar"):
        st.session_state["attr"] = {"conteo": d, "n": n, "etiquetas": list(var["etiquetas"]), "que": "defectuosos",
                                    "constante": bool(np.allclose(n, n[0])),
                                    "nombre": f"Defectuosas de {var['nombre']}", "desde_variables": True,
                                    "lie": lie, "lse": lse}
        st.session_state["fase1_attr"] = None
        st.success(f"Listo: {len(n)} subgrupos con {int(d.sum())} unidades defectuosas en total.")
        st.rerun()


def _cartas():
    a = st.session_state["attr"]
    z = ui.config()["z"]
    sugerida, motivo = atributos.recomendar(a["que"], a["constante"])
    st.info(f"**Selección justificada:** carta **{sugerida}**. {motivo}")
    opciones = ["p", "np"] if a["que"] == "defectuosos" else ["c", "u"]
    ini = 0 if sugerida.startswith(opciones[0]) else 1
    if a["que"] == "defectuosos" and a["constante"]:
        ini = 1
    tipo = st.radio("Carta a construir", opciones, index=ini, horizontal=True)
    if tipo in ("np", "c") and not a["constante"]:
        st.error(f"La carta {tipo} exige tamaño de muestra constante; con n variable use la carta "
                 f"{'p' if tipo == 'np' else 'u'}.")
        return None
    metodo = "variables"
    if tipo == "p" and not a["constante"]:
        metodo = {"Método 1: límites variables": "variables", "Método 2: tamaño de muestra promedio": "promedio",
                  "Método 3: carta estandarizada": "estandarizada"}[
            st.radio("Tratamiento del n variable (módulo 4.8.1.2)", ["Método 1: límites variables",
                                                                    "Método 2: tamaño de muestra promedio",
                                                                    "Método 3: carta estandarizada"], horizontal=True)]
    st.session_state["attr_metodo"] = metodo
    st.caption("Fase I con las muestras iniciales (proceso supuesto calibrado y óptimo). Las muestras nuevas se "
               "evalúan con estos límites en la pestaña 4.")
    _fase1(a, tipo, z, metodo)
    return a, tipo, z, metodo


def _fase1(a, tipo, z, metodo):
    m = len(a["conteo"])
    if m < 1:
        st.error("No hay datos.")
        return
    hasta = st.slider("Subgrupos usados en Fase I", 1, m, m, key=f"hasta_a_{tipo}") if m > 1 else m
    conteo, n, et = a["conteo"][:hasta], a["n"][:hasta], a["etiquetas"][:hasta]
    k_ms = f"ms_a_{tipo}_{hasta}_{metodo}"
    c1, c2 = st.columns([3, 1])
    if c2.button("Cepillado automático", key=f"cep_a_{tipo}"):
        exc = set()
        for _ in range(20):
            r = _calcular(tipo, conteo, n, et, z, exc, metodo)
            c = r["cartas"][0]
            nuevos = {i + 1 for i, v in enumerate(c["valores"]) if (i + 1) not in exc and (v > c["lcs"][i] or v < c["lci"][i])}
            if not nuevos:
                break
            exc |= nuevos
        st.session_state[k_ms] = sorted(exc)
    if k_ms not in st.session_state:
        st.session_state[k_ms] = []
    excluir = c1.multiselect("Subgrupos excluidos del cálculo (cepillado)", list(range(1, hasta + 1)), key=k_ms,
                             placeholder="Ninguno")
    res = _calcular(tipo, conteo, n, et, z, excluir, metodo)
    carta = res["cartas"][0]
    fig, sen = ui.mostrar_carta(carta, excluir=excluir, clave=f"a1_{tipo}")
    params = ui.tabla_parametros(res["params"])
    centro_v = res.get("pbar", res.get("cbar", res.get("ubar")))
    nom_c = {"p": "p̄", "np": "n·p̄", "c": "c̄", "u": "ū"}[tipo]
    fuera_n = int(np.sum((carta["valores"] > carta["lcs"]) | (carta["valores"] < carta["lci"])))
    estilo.kpis([
        dict(icono="target", etiqueta=f"Línea central ({nom_c})", valor=f"{carta['lc'][-1]:.4g}",
             sub=(f"{100 * centro_v:.2f} % defectuoso" if tipo in ("p", "np") and centro_v is not None else "")),
        dict(icono="upload", etiqueta="LCS" + (" (varía con n)" if np.ptp(carta["lcs"]) > 0 else ""),
             valor=f"{np.max(carta['lcs']):.4g}", color=estilo.ROJO),
        dict(icono="download", etiqueta="LCI", valor=f"{np.min(carta['lci']):.4g}", color=estilo.ROJO),
        dict(icono="", etiqueta="Puntos fuera", valor=f"{fuera_n}", sub=f"de {len(carta['valores'])}",
             color=estilo.ROJO if fuera_n else estilo.VERDE),
        dict(icono="ban", etiqueta="Excluidos", valor=f"{len(excluir)}", sub="por cepillado", color=estilo.SUAVE),
    ])
    c1, c2 = st.columns([1, 2])
    c1.dataframe(params, hide_index=True, width="stretch")
    c2.dataframe(res["tabla"], hide_index=True, width="stretch", height=300)
    activas = sen[sen["_puntos"].apply(lambda p: not set(p) <= set(excluir))] if len(sen) else sen
    concl = [f"Carta {tipo} seleccionada: {atributos.recomendar(a['que'], a['constante'])[1]}"]
    if len(activas) == 0:
        msg = ("No hay puntos fuera de los límites ni patrones no aleatorios: el proceso está bajo control "
               "estadístico; la variabilidad se debe a causas comunes y su reducción depende de la administración "
               "(cambios en el sistema). Los límites pueden usarse en Fase II.")
        estilo.interpretacion("Diagnóstico automático: proceso bajo control estadístico", [msg, concl[0]], "ok")
        concl.append(msg)
    else:
        lineas = [f"Se detectaron **{len(activas)} señales** de falta de control: el proceso **NO** está bajo control."]
        for _, f in activas.head(6).iterrows():
            lineas.append(f"**{f['Regla']}** (puntos {f['Puntos']}): {f['Posibles causas (módulo)']}")
        lineas.append("Registre causa y acción en la bitácora, excluya esos subgrupos (cepillado) y recalcule.")
        estilo.interpretacion("Diagnóstico automático: proceso fuera de control", lineas, "mal")
        st.dataframe(activas.drop(columns=["_regla", "_puntos"]), hide_index=True, width="stretch")
        ui.bitacora(activas, f"attr_{tipo}")
        concl.append(f"Se detectaron {len(activas)} señales de falta de control; requieren identificar causas asignables.")
    if excluir:
        concl.append(f"Subgrupos excluidos por cepillado: {sorted(excluir)}.")
    centro = res.get("pbar", res.get("cbar", res.get("ubar")))
    st.session_state["fase1_attr"] = {"tipo": tipo, "centro": centro, "hasta": hasta, "metodo": metodo,
                                      "lcs": float(np.max(carta["lcs"])), "lci": float(np.min(carta["lci"])),
                                      "n": float(np.mean(n)), "en_control": len(activas) == 0,
                                      "n1_total": float(np.sum([v for i, v in enumerate(n) if (i + 1) not in excluir])),
                                      "d1_total": float(np.sum([v for i, v in enumerate(conteo) if (i + 1) not in excluir]))}
    tablas = [("Parámetros carta " + tipo, params), ("Datos y límites", res["tabla"])]
    if len(activas):
        tablas.append(("Señales", activas.drop(columns=["_regla", "_puntos"])))
    ui.boton_registrar(f"m3_f1_{tipo}", "Cartas por atributos", f"Carta {tipo} — Fase I", tablas=tablas,
                       figuras=[(f"Carta {tipo} Fase I", fig)], conclusiones=concl)


def _fase2(a, tipo, z, metodo):
    f1 = st.session_state.get("fase1_attr")
    if not f1 or f1["tipo"] != tipo:
        st.info("Complete primero la Fase I con este tipo de carta.")
        return
    nombre = {"p": "p̄", "np": "p̄", "c": "c̄", "u": "Ū"}[tipo]
    centro = st.number_input(f"{nombre} de Fase I (o valor estándar)", value=float(f1["centro"]), format="%.6f")
    lb = ui.libro()
    fuentes = ["Datos cargados que no se usaron en Fase I", "Subir archivo nuevo"]
    if lb and ui.hojas_de_datos(lb):
        hay_f2 = any(re.search(F2_ATTR, h, flags=re.I) for h in ui.hojas_de_datos(lb))
        fuentes.insert(0 if hay_f2 else 2, f"Hoja del libro {lb['nombre']}")
    fuente = st.radio("Muestras nuevas", fuentes, horizontal=True, key="f2a_fuente")
    if fuente.startswith("Hoja"):
        hojas = ui.hojas_de_datos(lb)
        hoja = st.selectbox("Hoja con las muestras nuevas", hojas, key="f2a_hoja",
                            index=ui.hoja_sugerida(hojas, [F2_ATTR, r"atribut|no ?conform|defect"]))
        df = ui.hoja_df(hoja, lb)
        from paginas.m1_datos import columnas_enteras
        num = columnas_enteras(df)
        if not num:
            st.info("Esa hoja no tiene columnas de conteo (números enteros).")
            return
        from paginas.m1_datos import sugerir_columnas_attr
        sug_c, sug_n = sugerir_columnas_attr(df, num)
        cc = st.selectbox("Columna del conteo", num, index=num.index(sug_c) if sug_c in num else 0, key="f2a_cc")
        op = ["(igual a Fase I)"] + [c for c in num if c != cc]
        cn = st.selectbox("Columna de n", op, index=op.index(sug_n) if sug_n in op else 0, key="f2a_cn")
        dfl = df.dropna(subset=[cc])
        conteo = datos.a_numerico(dfl[cc]).to_numpy(float)
        n = datos.a_numerico(dfl[cn]).to_numpy(float) if cn != op[0] else np.full(len(conteo), f1["n"])
        et = list(range(1, len(conteo) + 1))
    elif fuente.startswith("Datos"):
        h = f1["hasta"]
        conteo, n, et = a["conteo"][h:], a["n"][h:], a["etiquetas"][h:]
        if len(conteo) == 0:
            st.info("No quedan datos: reduzca los subgrupos usados en Fase I, o suba un archivo nuevo.")
            return
    else:
        arch = st.file_uploader("Archivo de Fase II", type=["csv", "xlsx", "xls"], key="f2a")
        ej = st.checkbox("Usar el ejemplo de Fase II del módulo (latas, 12 muestras de n = 40)")
        if ej:
            df = pd.read_csv(os.path.join(ui.CARPETA_EJEMPLOS, "latas_p_fase2.csv"))
        elif arch is not None:
            df = datos.leer_archivo(arch)
        else:
            return
        num = [c for c in df.columns if datos.a_numerico(df[c]).notna().mean() > 0.5]
        cc = st.selectbox("Columna del conteo", num, index=len(num) - 1)
        cn = st.selectbox("Columna de n", ["(igual a Fase I)"] + num)
        conteo = datos.a_numerico(df[cc]).to_numpy(float)
        n = datos.a_numerico(df[cn]).to_numpy(float) if cn != "(igual a Fase I)" else np.full(len(conteo), f1["n"])
        et = list(range(1, len(conteo) + 1))
    res = _calcular(tipo, conteo, n, et, z, None, metodo, estandar=centro)
    fig, sen = ui.mostrar_carta(res["cartas"][0], clave=f"a2_{tipo}")
    concl = []
    if len(sen):
        st.error("Señales de fuera de control en el monitoreo.")
        st.dataframe(sen.drop(columns=["_regla", "_puntos"]), hide_index=True, width="stretch")
        concl.append(f"Fase II: {len(sen)} señales de falta de control.")
    else:
        st.success("Monitoreo sin señales: el proceso se mantiene bajo control.")
        concl.append("Fase II: el proceso se mantiene bajo control.")
    if tipo in ("p", "np"):
        st.markdown("**Prueba de hipótesis: ¿cambió la fracción no conforme? (módulo 4.8.1)**  \n"
                    "H0: p1 = p2 ; H1: p1 ≠ p2 (o una cola).  Z0 = (p̂1 − p̂2)/√(p̄(1−p̄)(1/n1 + 1/n2)), "
                    "con p̄ = (n1·p̂1 + n2·p̂2)/(n1 + n2).")
        n1, d1 = f1["n1_total"], f1["d1_total"]
        n2, d2 = float(np.sum(n)), float(np.sum(conteo))
        p1, p2 = d1 / n1, d2 / n2
        pb = (d1 + d2) / (n1 + n2)
        z0 = (p1 - p2) / math.sqrt(pb * (1 - pb) * (1 / n1 + 1 / n2))
        alfa = st.number_input("α de la prueba", 0.001, 0.2, 0.05, key="alfa_h")
        from cep.estadistica import z_de_prob
        zc = z_de_prob(1 - alfa)
        tab = pd.DataFrame({"Concepto": ["n1 (Fase I)", "p̂1", "n2 (Fase II)", "p̂2", "p̄ combinado", "Z0",
                                         "Z crítico una cola (H1: p1 > p2)", "valor p (una cola)"],
                            "Valor": [n1, p1, n2, p2, pb, z0, zc, 1 - phi(z0)]})
        st.dataframe(tab, hide_index=True)
        if z0 > zc:
            txt = (f"Z0 = {z0:.3f} > {zc:.3f}: se rechaza H0; la fracción no conforme disminuyó de {p1:.4f} a {p2:.4f}. "
                   "Conviene recalcular los límites con los datos nuevos.")
        else:
            txt = f"Z0 = {z0:.3f} ≤ {zc:.3f}: no hay evidencia de que la fracción no conforme haya disminuido."
        st.info(txt)
        concl.append(txt)
    ui.boton_registrar(f"m3_f2_{tipo}", "Cartas por atributos", f"Carta {tipo} — Fase II con muestras nuevas", tablas=[("Datos Fase II", res["tabla"])],
                       figuras=[(f"Carta {tipo} Fase II", fig)], conclusiones=concl)


def _limites_attr(tipo, centro, n, z):
    """Límites de la carta para un tamaño n (en las unidades de la carta)."""
    if tipo == "p":
        sd = math.sqrt(centro * (1 - centro) / n)
        return centro + z * sd, max(centro - z * sd, 0.0)
    if tipo == "np":
        sd = math.sqrt(n * centro * (1 - centro))
        return n * centro + z * sd, max(n * centro - z * sd, 0.0)
    if tipo == "c":
        return centro + z * math.sqrt(centro), max(centro - z * math.sqrt(centro), 0.0)
    return centro + z * math.sqrt(centro / n), max(centro - z * math.sqrt(centro / n), 0.0)


def _capacidad_attr(a, f1):
    """Capacidad por atributos: con el proceso en control, la capacidad es el nivel promedio de no conformidad
    de la Fase I (p̄ para p/np; c̄ o Ū para c/u)."""
    tipo, centro = f1["tipo"], float(f1["centro"])
    if tipo in ("p", "np"):
        estilo.kpis([
            dict(icono="circle-x", etiqueta="Fracción no conforme p̄", valor=f"{100 * centro:.3f} %", sub="de la Fase I",
                 color=estilo.ROJO),
            dict(icono="circle-check", etiqueta="Fracción conforme 1 − p̄", valor=f"{100 * (1 - centro):.3f} %", color=estilo.VERDE),
            dict(icono="hash", etiqueta="PPM no conformes", valor=f"{1e6 * centro:,.0f}".replace(",", "."),
                 color=estilo.NARANJA)])
        txt = (f"Capacidad del proceso por atributos: p̄ = {centro:.4f} ({100 * centro:.2f} % de unidades no conformes, "
               f"{1e6 * centro:,.0f} PPM).").replace(",", ".")
    else:
        estilo.kpis([dict(icono="circle-x", etiqueta="Defectos promedio", valor=f"{centro:.4g}",
                          sub="c̄ por unidad de inspección" if tipo == "c" else "Ū por unidad", color=estilo.ROJO)])
        txt = f"Capacidad del proceso por atributos: {'c̄' if tipo == 'c' else 'Ū'} = {centro:.4g} defectos."
    puntos = [txt]
    if not f1.get("en_control"):
        puntos.append("La Fase I todavía tiene señales: este valor sólo describe el proceso cuando esté bajo control. "
                      "Primero se eliminan las causas especiales.")
    estilo.interpretacion("Capacidad por atributos", puntos, "alerta" if not f1.get("en_control") else "info")
    ui.boton_registrar("m3_cap", "Cartas por atributos", f"Capacidad del proceso por atributos (carta {tipo})",
                       conclusiones=puntos)


def _potencia_attr(a, f1, z):
    tipo, centro = f1["tipo"], float(f1["centro"])
    st.markdown("Curva OC de la carta (módulo 4.8.2): β = P(D ≤ ⌊n·LCS⌋ | p1) − P(D ≤ ⌊n·LCI⌋ | p1); potencia "
                "1 − β; ARL1 = 1/(1 − β); ATS1 = ARL1·t.")
    c1, c2, c3 = st.columns(3)
    n0 = c1.number_input("n de cada muestra" if tipo != "c" else "Unidades de inspección (c: 1)", 1.0, 1e7,
                         float(round(f1["n"])) if tipo != "c" else 1.0, key="pa_n0")
    nombre = "p1 (fracción no conforme después del cambio)" if tipo in ("p", "np") else "Defectos promedio después del cambio"
    defecto = min(2 * centro, 0.99) if tipo in ("p", "np") else 2 * centro
    v1 = c2.number_input(nombre, 0.0, 1e6 if tipo not in ("p", "np") else 0.9999, float(defecto), format="%.5f", key="pa_v1")
    unidades = ["horas", "días"]
    u_def = (a or {}).get("t_unidad") or "horas"
    cu1, cu2 = c3.columns(2)
    t = cu1.number_input("Tiempo entre muestras t", 0.001, 1e4, 1.0, key="pa_t")
    ut = cu2.selectbox("Unidad de t", unidades, index=unidades.index(u_def), key="pa_tu")
    u_corta = "h" if ut == "horas" else ("día" if t == 1 else "días")
    lcs, lci = _limites_attr(tipo, centro, n0, z)
    n_int = int(round(n0))
    r = diseno.beta_atributos(tipo, n_int, lcs, lci, [v1]).iloc[0]
    r_0 = diseno.beta_atributos(tipo, n_int, lcs, lci, [centro]).iloc[0]
    alfa = 1 - r_0["β"]
    pot = float(r["1−β"])
    estilo.kpis([
        dict(icono="zap", etiqueta="Potencia 1 − β", valor=f"{pot:.4f}", sub=f"cambio de {centro:.4g} a {v1:.4g}"),
        dict(icono="repeat", etiqueta="ARL1", valor=f"{1 / pot:.2f}" if pot > 0 else "∞", color="#344054"),
        dict(icono="timer", etiqueta="ATS1", valor=f"{t / pot:.2f}" if pot > 0 else "∞", sub=u_corta,
             color=estilo.ROJO),
        dict(icono="triangle-alert", etiqueta="ARL0", valor=f"{1 / alfa:.0f}" if alfa > 0 else "∞", sub=f"α real = {alfa:.5f}",
             color=estilo.SUAVE)])
    concl = [f"Carta {tipo} con n = {n_int}: si el nivel pasa de {centro:.4g} a {v1:.4g}, la potencia es {pot:.4f}; "
             f"ARL1 = {1 / pot if pot > 0 else math.inf:.2f} muestras y ATS1 = {t / pot if pot > 0 else math.inf:.2f} "
             f"{u_corta} (una muestra cada {t:g} {u_corta})."]
    estilo.interpretacion("Potencia de la carta por atributos", concl, "info")
    ui.boton_registrar("m3_pot", "Cartas por atributos", f"Potencia de la carta {tipo}", conclusiones=concl)
    return dict(tipo=tipo, centro=centro, n0=n_int, v1=v1, t=t, z=z, pot=pot, ut=ut, u="h" if ut == "horas" else "días")


def _carga_attr(c):
    if not c:
        return
    tipo, centro, n0, v1, t, z = c["tipo"], c["centro"], c["n0"], c["v1"], c["t"], c["z"]
    if tipo == "c":
        st.info("En la carta c la muestra es una unidad de inspección; para aumentar la carga use la carta u con más "
                "unidades por muestra.")
        return
    u = c.get("u", "h")
    st.markdown(f"Se mantiene la frecuencia (una muestra cada **{t:g} {u if not (u == 'días' and t == 1) else 'día'}**) y se aumenta el tamaño de muestra n: la "
                "carga muestral Cm = n/t sube, la potencia sube y el **ATS1 baja**. Cada opción se compara con lo que "
                "la empresa puede inspeccionar por día.")
    plan = st.session_state.get("plan_muestreo") or {}
    horas, prod = plan.get("horas"), plan.get("produccion")
    if c.get("ut", "horas") == "horas":
        k_dia = max(1, int(horas // t)) if horas else None
    else:
        k_dia = 1 / t
    c1, c2, c3 = st.columns(3)
    prob = c1.number_input("Probabilidad deseada de detectar el cambio", 0.01, 0.9999, 0.90, key="ca_pot")
    k = int(c2.number_input("…en alguna de las primeras k muestras", 1, 50, 2, key="ca_k"))
    pct = c3.number_input("Máximo a inspeccionar (% de la producción diaria)", 0.1, 100.0, 10.0, key="ca_pct",
                          help="Un muestreo no debe inspeccionar casi toda la producción: por defecto, hasta el 10 % "
                               "de la producción diaria del paso 8.")
    maximo = prod * pct / 100 if prod else None
    beta_req = diseno.beta_para_detectar(prob, k)

    def fila(n):
        lcs, lci = _limites_attr(tipo, centro, n, z)
        pot = 1 - float(diseno.beta_atributos(tipo, n, lcs, lci, [v1]).iloc[0]["β"])
        u_dia = round(n * k_dia, 2) if k_dia else None
        dentro = u_dia is None or maximo is None or u_dia <= maximo + 1e-9
        return {"n": n, "Cm = n/t": round(n / t, 3), "1 − β": round(pot, 4),
                "ARL1": round(1 / pot, 3) if pot > 0 else math.inf, f"ATS1 ({u})": round(t / pot, 3) if pot > 0 else math.inf,
                "Unidades por día": u_dia if u_dia is not None else "—",
                "% de la producción": f"{100 * u_dia / prod:.1f} %" if (u_dia and prod) else "—",
                "Dentro del plan": "Sí" if dentro else "No",
                "Logra el objetivo": "Sí" if pot >= 1 - beta_req - 1e-12 else "No"}

    n_max = int(maximo / k_dia + 1e-9) if (maximo and k_dia) else None
    A = f"ATS1 ({u})"
    candidatos = {max(1, int(round(n0 * f))) for f in (1, 1.25, 1.5, 2, 2.5, 3, 4)}
    if n_max and n_max >= n0:
        candidatos.add(n_max)
    n_obj = next((n for n in range(n0, min(n0 * 100, 200_000) + 1) if fila(n)["Logra el objetivo"] == "Sí"), None)
    if n_obj:
        candidatos.add(n_obj)
    tab = pd.DataFrame([fila(n) for n in sorted(candidatos)])
    st.caption(f"Objetivo: 1 − β^{k} = {prob:g} ⇒ 1 − β = {1 - beta_req:.4f} por muestra"
               + (f"; con {k_dia:g} muestra(s) por día y un máximo de {pct:g} % de la producción diaria ({int(maximo)} "
                  f"unidades), el plan permite hasta n = {n_max} por muestra." if n_max else "."))
    st.dataframe(tab, hide_index=True, width="stretch")
    validas = tab[(tab["Dentro del plan"] == "Sí") & (tab["Logra el objetivo"] == "Sí")]
    base = tab.iloc[0]
    if len(validas):
        fila_r = validas.iloc[0]
        if int(fila_r["n"]) == n0:
            txt = (f"Con el n actual ({n0}) ya se logra el objetivo (1 − β = {fila_r['1 − β']:.4f}); "
                   f"ATS1 = {fila_r[A]:.2f} {u}.")
        else:
            txt = (f"Aumentando n de {n0} a {int(fila_r['n'])} la potencia sube de {base['1 − β']:.4f} a "
                   f"{fila_r['1 − β']:.4f} y el ATS1 baja de {base[A]:.2f} a {fila_r[A]:.2f} {u}, dentro de lo que se "
                   "puede inspeccionar.")
        nivel = "ok"
    else:
        dentro_tab = tab[tab["Dentro del plan"] == "Sí"]
        if len(dentro_tab) and int(dentro_tab["n"].iloc[-1]) > n0:
            fila_r = dentro_tab.iloc[-1]
            p_txt = f" ({fila_r['% de la producción']} de la producción diaria)" if fila_r["% de la producción"] != "—" else ""
            txt = (f"Dentro del plan, el mayor tamaño posible es n = {int(fila_r['n'])}{p_txt}: la potencia sube de "
                   f"{base['1 − β']:.4f} a {fila_r['1 − β']:.4f} y el ATS1 baja de {base[A]:.2f} a "
                   f"{fila_r[A]:.2f} {u}. El objetivo ({prob:g} en {k} muestras) "
                   + (f"exigiría n = {n_obj} ({100 * n_obj * k_dia / prod:.0f} % de la producción diaria), fuera del plan."
                      if (n_obj and prod) else f"exigiría n = {n_obj}, fuera del plan." if n_obj
                      else "no se alcanza con un n razonable.")
                   + " La carta por atributos detecta cambios pequeños con mucha menos potencia que la carta por "
                   "variables de la misma característica.")
        else:
            txt = (f"Cada muestra ya usa todo lo que permite el plan (n = {n0}): para bajar el ATS1 hay que muestrear "
                   f"más seguido (ATS1 = t/(1 − β) = {1 / base['1 − β']:.2f}·t)." if base["1 − β"] > 0 else
                   "Ninguna opción detecta el cambio dentro del plan.")
        nivel = "alerta"
    st.session_state["plan_fase2_attr"] = {"tabla": tab, "texto": txt}
    estilo.interpretacion("Carga muestral de la carta por atributos", [txt], nivel)
    ui.boton_registrar("m3_carga", "Cartas por atributos", f"Incremento de la carga muestral de la carta {tipo}",
                       tablas=[("Carga muestral y ATS1", tab)], conclusiones=[txt])


def _pareto():
    st.markdown("El diagrama de Pareto (módulo 2.7.2) ayuda a priorizar: pocos tipos de defecto suelen explicar la "
                "mayoría de las pérdidas.")
    lb = ui.libro()
    hojas = ui.hojas_de_datos(lb) if lb else []
    opciones = [f"Hoja «{h}» del libro {lb['nombre']}" for h in hojas] + ["Subir otra tabla", "Datos ilustrativos"]
    ini = ui.hoja_sugerida(hojas, [r"pareto", r"motivo", r"causa", r"tipo de defecto"]) if hojas else len(opciones) - 1
    if hojas and not any(re.search(r"pareto|motivo|causa", h, flags=re.I) for h in hojas):
        ini = len(opciones) - 1
    origen = st.selectbox("Tabla de defectos", opciones, index=ini, key="par_origen")
    df = None
    if origen.startswith("Hoja"):
        df = ui.hoja_df(hojas[opciones.index(origen)], lb)
    elif origen.startswith("Subir"):
        arch = st.file_uploader("Tabla de defectos (columna de categoría y columna de frecuencia)",
                                type=["csv", "xlsx"], key="par")
        if arch is None:
            return
        df = datos.leer_archivo(arch)
    else:
        df = pd.read_csv(os.path.join(ui.CARPETA_EJEMPLOS, "pareto_defectos_ejemplo.csv"))
        st.caption("Mostrando datos ilustrativos (ficticios): no se usan en «Mejores condiciones» ni en el informe. "
                   "Suba su tabla de causas o edítela abajo.")
    df = st.data_editor(df, num_rows="dynamic", key=f"par_ed_{origen}", width="stretch")
    cols = list(df.columns)
    if len(cols) < 2:
        return
    numericas = [c for c in cols if datos.a_numerico(df[c]).notna().mean() > 0.5]
    i_cat = next((i for i, c in enumerate(cols) if c not in numericas), 0)
    i_frec = next((i for i, c in enumerate(cols) if c in numericas and i != i_cat), 1)
    cc = st.selectbox("Columna de categoría", cols, index=i_cat, key=f"par_cc_{origen}")
    cf = st.selectbox("Columna de frecuencia", cols, index=i_frec, key=f"par_cf_{origen}")
    t = atributos.pareto(df[cc].astype(str), datos.a_numerico(df[cf]).fillna(0))
    fig = graficos.pareto(t)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(t, hide_index=True)
    vitales = t[t["% acumulado"].shift(fill_value=0) < 80]["Categoría"].tolist()
    concl = [f"Los pocos vitales (hasta ~80 % acumulado) son: {', '.join(vitales)}. Concentrar las acciones de mejora en ellos."]
    st.info(concl[0])
    if origen.startswith("Datos ilustrativos"):
        st.session_state.pop("pareto_vitales", None)
        return
    st.session_state["pareto_vitales"] = {"vitales": vitales, "tabla": t}
    ui.boton_registrar("m3_pareto", "Cartas por atributos", "Diagrama de Pareto de defectos", tablas=[("Pareto", t)],
                       figuras=[("Diagrama de Pareto", fig)], conclusiones=concl)
