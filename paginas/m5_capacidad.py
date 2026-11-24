"""Módulo 5. Capacidad del proceso."""
import numpy as np
import pandas as pd
import streamlit as st

from cep import capacidad, empresa, graficos, supuestos
from cep.constantes import factor
from paginas import estilo, ui


def render():
    estilo.encabezado("target", "Capacidad del proceso", "Cp, Cpk, Cpl, Cpu, fracción no conforme, intervalos y escenarios frente a especificaciones.", "Paso 7")
    var = st.session_state.get("var")
    modo = st.radio("Origen de X̄ y σ", ["Datos cargados", "Ingreso manual (ejercicios o datos externos)"],
                    horizontal=True, index=0 if var is not None else 1)
    x = None
    if modo.startswith("Datos"):
        if var is None:
            st.info("Cargue una variable en el paso 3 (Datos) o use el ingreso manual.")
            return
        x = np.asarray(var["individuales"], float)
        f1 = st.session_state.get("fase1_var")
        opciones = []
        if f1:
            et = {"X̄-R": "σ = R̄/d2 (Fase I, carta X̄-R)", "X̄-S": "σ = S̄/c4 (Fase I, carta X̄-S)",
                  "I-MR": "σ = MR̄/d2 (Fase I, carta I-MR)"}[f1["tipo"]]
            opciones.append(et)
        if var["n"] > 1:
            opciones += ["σ = R̄/d2 (todos los subgrupos)", "σ = S̄/c4 (todos los subgrupos)"]
        opciones.append("σ = S global de todos los datos")
        fuente = st.selectbox("Estimación de σ", opciones,
                              help="Lo recomendado es usar σ de la Fase I con el proceso bajo control.")
        if "Fase I" in fuente:
            media, sigma = f1["media"], f1["sigma"]
            if not f1.get("en_control", True):
                st.warning("La Fase I aún tiene señales de falta de control: la capacidad sólo es válida con el "
                           "proceso estable (módulo 3.3).")
        elif "R̄" in fuente:
            g = [gg for gg in var["grupos"] if len(gg) == var["n"]]
            rbar = np.mean([np.ptp(gg) for gg in g])
            media, sigma = float(np.mean([np.mean(gg) for gg in g])), rbar / factor("d2", var["n"])
        elif "S̄" in fuente:
            g = [gg for gg in var["grupos"] if len(gg) == var["n"]]
            sbar = np.mean([np.std(gg, ddof=1) for gg in g])
            media, sigma = float(np.mean([np.mean(gg) for gg in g])), sbar / factor("c4", var["n"])
        else:
            media, sigma = float(x.mean()), float(x.std(ddof=1))
        n_ic = len(x)
    else:
        c1, c2, c3 = st.columns(3)
        media = c1.number_input("X̄ (media del proceso)", value=0.738, format="%.6f")
        sig_modo = c2.selectbox("σ a partir de", ["σ directa", "R̄ y n", "S̄ y n"])
        if sig_modo == "σ directa":
            sigma = c3.number_input("σ", value=0.0726, format="%.6f", min_value=1e-12)
        else:
            barra = c3.number_input("R̄" if sig_modo.startswith("R") else "S̄", value=0.169, format="%.6f")
            nn = st.number_input("n de los subgrupos", 2, 25, 5)
            sigma = barra / factor("d2" if sig_modo.startswith("R") else "c4", nn)
            st.caption(f"σ = {sigma:.6f}")
        n_ic = st.number_input("Número total de datos (para intervalos de confianza)", 2, 100000, 100)

    st.markdown("**Especificaciones**")
    pv = empresa.buscar_variable(st.session_state.get("perfil"), (var or {}).get("nombre"))
    lie0, _, lse0 = empresa.especificaciones(pv)
    if pv is not None:
        st.caption(f"Especificaciones tomadas de la hoja «Especificaciones» del libro para «{pv['Característica']}»"
                   + ("" if (lie0 is not None or lse0 is not None) else ": aún vacías, escríbalas aquí") + ".")
    if x is None:
        lie0, lse0 = 0.5, 0.9
    c1, c2, c3, c4 = st.columns(4)
    usa_lie = c1.checkbox("Tiene LIE", pv is None or lie0 is not None or lse0 is None)
    lie = c2.number_input("LIE", value=lie0, format="%.6f", placeholder="Escriba el LIE") if usa_lie else None
    usa_lse = c3.checkbox("Tiene LSE", pv is None or lse0 is not None or lie0 is None)
    lse = c4.number_input("LSE", value=lse0, format="%.6f", placeholder="Escriba el LSE") if usa_lse else None
    if (usa_lie and lie is None) or (usa_lse and lse is None):
        st.info("Escriba los límites de especificación del cliente/diseño (o desmarque el que no exista).")
        return
    if lie is None and lse is None:
        st.warning("Indique al menos un límite de especificación.")
        return
    if lie is not None and lse is not None and lse <= lie:
        st.error("El LSE debe ser mayor que el LIE.")
        return
    st.caption(f"X̄ = {media:.6g} · σ = {sigma:.6g}")
    if st.session_state.get("normalidad") is False:
        st.warning("La prueba Ji-cuadrada (paso 5) rechazó la normalidad: los %PNC calculados con la normal deben "
                   "tomarse con precaución.")
    elif st.session_state.get("normalidad_estado") == "no aplicable":
        st.info("La prueba Ji-cuadrada (paso 5) no fue aplicable por falta de datos: los %PNC suponen la normal sin "
                "haberla verificado.")

    r = capacidad.indices(media, sigma, lse, lie)
    tabla = capacidad.tabla_indices(r)
    interp = capacidad.interpretar(r)
    gk = [k for k in ("Cp", "Cpk", "Cpu", "Cpl") if k in r and r[k] is not None and np.isfinite(r[k])]
    ayudas = {"Cp": "potencial (sólo variación)", "Cpk": "real (variación y centrado)", "Cpu": "frente al LSE",
              "Cpl": "frente al LIE"}
    cols_m = st.columns(2) if len(gk) > 1 else [st.container()]
    for j, k in enumerate(gk):
        col = cols_m[j % len(cols_m)]
        col.plotly_chart(graficos.medidor(r[k], k, ayuda=ayudas[k]), width="stretch", key=f"med_{k}")
    pnc = r.get("%PNC total")
    estilo.kpis([
        dict(icono="map-pin", etiqueta="Media X̄", valor=f"{media:.5g}"),
        dict(icono="sigma", etiqueta="Desviación σ", valor=f"{sigma:.4g}", color="#344054"),
        dict(icono="", etiqueta="Fracción no conforme", valor=f"{100 * pnc:.4f} %" if pnc is not None else "—",
             sub=f"≈ {1e6 * pnc:,.0f} ppm".replace(",", ".") if pnc is not None else "", color=estilo.ROJO),
        dict(icono="ruler", etiqueta="Clase de Cp", valor=f"Clase {capacidad.clase_cp(r['Cp'])[0]}" if "Cp" in r else "—",
             sub=capacidad.clase_cp(r["Cp"])[1].split(":")[-1].strip() if "Cp" in r else "requiere LIE y LSE", color=estilo.DORADO),
    ])
    c1, c2 = st.columns([1, 2])
    c1.dataframe(tabla, hide_index=True, width="stretch", height=560)
    vn = (lse + lie) / 2 if (lse is not None and lie is not None) else None
    fig = graficos.histograma_capacidad(x if x is not None else np.array([media]), media, sigma, lse, lie, vn,
                                        nbins=supuestos.numero_clases(len(x)) if x is not None else None,
                                        titulo="Distribución del proceso frente a las especificaciones")
    if x is None:
        fig.data = fig.data[1:]
    c2.plotly_chart(fig, width="stretch")
    cpk = r.get("Cpk")
    nivel = "ok" if cpk is not None and cpk >= 1.33 else ("alerta" if cpk is not None and cpk >= 1 else "mal")
    with c2:
        estilo.interpretacion("Interpretación automática de la capacidad", interp, nivel)

    with st.expander("Intervalos de confianza para Cp y Cpk", expanded=True):
        alfa = st.number_input("α", 0.001, 0.2, 0.05, key="alfa_ic")
        ic = capacidad.intervalos_confianza(r.get("Cp"), r["Cpk"], int(n_ic), alfa)
        tic = pd.DataFrame([{"Índice": k, "Estimado": r[k], "Límite inferior": v[0], "Límite superior": v[1]}
                            for k, v in ic.items()])
        st.dataframe(tic, hide_index=True)
        st.caption(f"Con {int(n_ic)} datos y {100 * (1 - alfa):.0f} % de confianza. Cp y Cpk son estimaciones puntuales "
                   "sujetas a fluctuación estadística (módulo 3.3.4).")

    extras = []
    if lse is not None and lie is not None:
        with st.expander("Escenario: proceso centrado en el valor nominal"):
            rc = capacidad.escenario_centrado(sigma, lse, lie)
            tc = capacidad.tabla_indices(rc)
            st.dataframe(tc, hide_index=True)
            st.info(f"Centrando el proceso el %PNC pasaría de {100 * r['%PNC total']:.4f} % a "
                    f"{100 * rc['%PNC total']:.4f} %. Centrar suele ser más económico que reducir la variabilidad.")
            extras.append(("Escenario centrado", tc))
        with st.expander("Escenario: media corrida ±1,5σ del valor nominal (hoja de fórmulas 1.6)"):
            filas = []
            for nom, m in (("VN − 1,5σ", vn - 1.5 * sigma), ("VN + 1,5σ", vn + 1.5 * sigma)):
                rr = capacidad.indices(m, sigma, lse, lie)
                filas.append({"Escenario": nom, "X̄": m, "Cpk": rr["Cpk"], "%PNC total": rr["%PNC total"]})
            tm = pd.DataFrame(filas)
            st.dataframe(tm, hide_index=True)
            extras.append(("Escenario media corrida 1,5σ", tm))
    with st.expander("Ventana de operación"):
        obj = st.number_input("Fracción no conforme máxima permitida por cada límite", 0.0001, 0.5, 0.01, format="%.4f")
        vo = capacidad.ventana_operacion(sigma, obj, lse, lie)
        tv = ui.tabla_parametros(vo)
        st.dataframe(tv, hide_index=True)
        if vo["X̄ máximo (por LSE)"] is not None and vo["X̄ mínimo (por LIE)"] is not None:
            st.info(f"La media debe mantenerse entre {vo['X̄ mínimo (por LIE)']:.5g} y {vo['X̄ máximo (por LSE)']:.5g} "
                    f"para que el %PNC por cada límite sea ≤ {100 * obj:.2f} %.")
        extras.append(("Ventana de operación", tv))

    conclusiones = list(interp)
    ui.boton_registrar("m5_cap", "Capacidad", "Análisis de capacidad del proceso",
                       tablas=[("Índices de capacidad y fracción no conforme", tabla), ("Intervalos de confianza", tic)] + extras,
                       figuras=[("Proceso vs especificaciones", fig)], conclusiones=conclusiones)
    st.session_state["capacidad"] = {"media": media, "sigma": sigma, "lse": lse, "lie": lie}

