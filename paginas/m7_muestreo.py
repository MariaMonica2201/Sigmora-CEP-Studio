"""Módulo 7. Muestreo de aceptación y diseño de planes de muestreo."""
import numpy as np
import pandas as pd
import streamlit as st

from cep import graficos, muestreo
from paginas import estilo, ui


def render():
    estilo.encabezado("package", "Muestreo de aceptación", "Planes simple y doble, curva OC, AOQ/AOQL, diseño por método matemático y MIL-STD-105E.", "Paso 12")
    tabs = st.tabs(["Plan simple: Pa, curva OC, AOQ", "Plan doble", "Diseño por método matemático",
                    "MIL-STD-105E", "Conceptos"])
    with tabs[0]:
        _simple()
    with tabs[1]:
        _doble()
    with tabs[2]:
        _disenar()
    with tabs[3]:
        _mil()
    with tabs[4]:
        _conceptos()


def _dist(clave):
    c1, c2 = st.columns(2)
    dist = c1.selectbox("Distribución", muestreo.DISTRIBUCIONES, key=f"dist_{clave}",
                        help="Hipergeométrica = exacta para un lote aislado (curva tipo A); Binomial = lotes grandes o "
                             "flujo de lotes (tipo B); Poisson = aproximación si la Binomial resulta compleja.")
    N = c2.number_input("Tamaño del lote N", 2, 10_000_000, 1000, key=f"N_{clave}")
    return dist, N


def _calidad_lote(clave, dist, N, defecto, etiqueta):
    """Fracción defectuosa del lote. Con lote finito (hipergeométrica) se puede escribir el número entero de
    defectuosos D; si se escribe la fracción y p'·N no es entero, se avisa la aproximación usada."""
    if dist != "Hipergeométrica":
        return st.number_input(etiqueta, 0.0, 1.0, float(defecto), format="%.5f", key=f"{clave}_p")
    modo = st.radio("Calidad del lote expresada como", ["Fracción p'", "Número de defectuosos D (entero)"],
                    horizontal=True, key=f"{clave}_modo")
    if modo.startswith("Número"):
        D = st.number_input(f"Defectuosos en el lote D (de N = {N})", 0, int(N), min(int(round(defecto * N)), int(N)),
                            key=f"{clave}_D")
        st.caption(f"p' = D/N = {D}/{N} = {D / N:.5g} (exacta).")
        return D / N
    p = st.number_input(etiqueta, 0.0, 1.0, float(defecto), format="%.5f", key=f"{clave}_p")
    _avisar_redondeo(p, N)
    return p


def _avisar_redondeo(p, N, nombre="p'"):
    aviso = muestreo.aviso_redondeo(p, N, nombre)
    if aviso:
        st.warning(aviso)


def _simple():
    dist, N = _dist("s")
    c1, c2, c3, c4 = st.columns(4)
    n = c1.number_input("n (tamaño de muestra)", 1, 100000, 80, key="s_n")
    c = c2.number_input("c (número de aceptación)", 0, 10000, 5, key="s_c")
    nac = c3.number_input("NAC / AQL (fracción)", 0.0001, 0.9999, 0.02, format="%.4f", key="s_nac")
    ltpd = c4.number_input("LTPD (fracción)", 0.0001, 0.9999, 0.07, format="%.4f", key="s_ltpd")
    if n > N:
        st.error("n no puede ser mayor que N.")
        return
    p_act = _calidad_lote("s", dist, N, st.session_state.get("pnc_m7", 0.05),
                          "Fracción no conforme del proceso p' (p. ej. %PNC del paso 7)")
    if dist == "Hipergeométrica":
        _avisar_redondeo(nac, N, "NAC")
        _avisar_redondeo(ltpd, N, "LTPD")
        st.caption("Curvas OC y AOQ del lote finito: se evalúan sólo en fracciones D/N con D entero.")
    pa = muestreo.pa_simple(n, c, p_act, dist, N)
    rg = muestreo.riesgos(n, c, nac, ltpd, dist, N)
    aoql, p_aoql = muestreo.aoql(n, c, dist, N)
    iql = muestreo.iql(n, c, dist, N)
    m = st.number_input("Número de lotes del pedido (probabilidad de aceptarlos todos = Pa^m)", 1, 1000, 1, key="s_m")
    tab = pd.DataFrame({"Indicador": [f"Pa con p' = {p_act:g}", f"P(aceptar los {m} lotes) = Pa^{m}",
                                      "Pa(NAC) = 1 − α", "α (riesgo del productor)", "β = Pa(LTPD) (riesgo del consumidor)",
                                      f"AOQ con p' = {p_act:g}", "AOQL (peor calidad de salida promedio)",
                                      "p' en el que ocurre el AOQL", "IQL (Pa = 0,5)"],
                        "Valor": [pa, pa ** m, rg["Pa(NAC) = 1 − α"], rg["α (riesgo del productor)"],
                                  rg["β = Pa(LTPD) (riesgo del consumidor)"], pa * p_act * (N - n) / N, aoql, p_aoql, iql]})
    st.dataframe(tab, hide_index=True)
    pmax = max(ltpd * 2, iql * 2.5, 0.05)
    ps = np.linspace(0, min(pmax, 1), 60)
    oc = muestreo.curva_oc_simple(n, c, ps, dist, N)
    fig = graficos.curva(oc["p'"], {"Pa": oc["Pa"]}, f"Curva OC — plan n = {n}, c = {c} ({dist})", "p' (fracción defectuosa)", "Pa")
    fig.add_vline(x=nac, line=dict(dash="dot", color="green"), annotation_text="NAC")
    fig.add_vline(x=ltpd, line=dict(dash="dot", color="red"), annotation_text="LTPD")
    fig2 = graficos.curva(oc["p'"], {"AOQ": oc["AOQ"]}, "Curva AOQ (inspección con rectificación)", "p'", "AOQ")
    fig2.add_hline(y=aoql, line=dict(dash="dot"), annotation_text=f"AOQL = {aoql:.4f}")
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig, width="stretch")
    c2.plotly_chart(fig2, width="stretch")
    with st.expander("Tabla de la curva OC"):
        st.dataframe(oc, hide_index=True)
    concl = [f"Plan n = {n}, c = {c}: con p' = {p_act:g} el lote se acepta con probabilidad {pa:.4f}.",
             f"Riesgo del productor α = {rg['α (riesgo del productor)']:.4f} en NAC = {nac:g}; riesgo del consumidor "
             f"β = {rg['β = Pa(LTPD) (riesgo del consumidor)']:.4f} en LTPD = {ltpd:g}.",
             f"Con rectificación, la calidad de salida nunca será peor que AOQL = {aoql:.4f}."]
    ui.boton_registrar("m7_simple", "Muestreo de aceptación", f"Plan de muestreo simple n = {n}, c = {c}",
                       tablas=[("Indicadores del plan", tab), ("Curva OC", oc)], figuras=[("Curva OC", fig), ("Curva AOQ", fig2)],
                       conclusiones=concl)


def _doble():
    st.markdown("Se acepta si d1 ≤ c1; se rechaza si d1 > c2; si c1 < d1 ≤ c2 se toma la segunda muestra y se acepta "
                "si d1 + d2 ≤ c2. ASN = n1·P1 + (n1 + n2)(1 − P1).")
    dist, N = _dist("d")
    c1, c2, c3, c4 = st.columns(4)
    n1 = c1.number_input("n1", 1, 100000, 20, key="d_n1")
    k1 = c2.number_input("c1", 0, 10000, 1, key="d_c1")
    n2 = c3.number_input("n2", 1, 100000, 10, key="d_n2")
    k2 = c4.number_input("c2", 0, 10000, 3, key="d_c2")
    p = _calidad_lote("d", dist, N, 0.05, "p'")
    if k2 < k1:
        st.error("c2 debe ser mayor o igual que c1.")
        return
    if dist == "Hipergeométrica" and n1 + n2 > N:
        st.error(f"n1 + n2 = {n1 + n2} no puede ser mayor que el lote N = {N}.")
        return
    if dist == "Hipergeométrica":
        st.caption("Lote finito: la segunda muestra se toma de las N − n1 unidades que quedan, con D − d1 defectuosos "
                   "(D = p'·N).")
    r = muestreo.pa_doble(n1, k1, n2, k2, p, dist, N)
    tab = ui.tabla_parametros(r)
    st.dataframe(tab, hide_index=True)
    ps = np.linspace(0, min(1, max(0.2, 4 * (k2 + 1) / (n1 + n2))), 50)
    oc = muestreo.curva_oc_doble(n1, k1, n2, k2, ps, dist, N)
    fig = graficos.curva(oc["p'"], {"Pa total": oc["Pa"], "Pa en 1ª muestra": oc["Pa 1ª muestra"]},
                         "Curva OC del plan doble", "p'", "Pa")
    fig2 = graficos.curva(oc["p'"], {"ASN": oc["ASN"]}, "Curva ASN (número promedio de muestra)", "p'", "ASN")
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig, width="stretch")
    c2.plotly_chart(fig2, width="stretch")
    ui.boton_registrar("m7_doble", "Muestreo de aceptación", f"Plan doble n1={n1}, c1={k1}, n2={n2}, c2={k2}",
                       tablas=[("Resultado del plan doble", tab), ("Curvas OC y ASN", oc)],
                       figuras=[("OC plan doble", fig), ("ASN plan doble", fig2)],
                       conclusiones=[f"Con p' = {p:g}: Pa = {r['Pa']:.4f} y ASN = {r['ASN']:.1f} unidades."])


def _disenar():
    st.markdown("**Método matemático** (ecuaciones 5.5 a 5.12): usa NAC, LTPD, riesgo del productor α y del "
                "consumidor β.")
    c1, c2, c3, c4 = st.columns(4)
    nac = c1.number_input("NAC (fracción)", 0.0001, 0.9, 0.02, format="%.4f", key="m_nac")
    ltpd = c2.number_input("LTPD (fracción)", 0.0002, 0.99, 0.07, format="%.4f", key="m_ltpd")
    a = c3.number_input("α (productor)", 0.001, 0.5, 0.05, key="m_a")
    b = c4.number_input("β (consumidor)", 0.001, 0.5, 0.10, key="m_b")
    if ltpd <= nac:
        st.error("LTPD debe ser mayor que NAC.")
        return
    r = muestreo.disenar_plan(nac, ltpd, a, b)
    st.dataframe(r["pasos"], hide_index=True)
    dist, N = _dist("m")
    n_plan, c_plan = r["n_plan"], r["c_plan"]
    c1, c2 = st.columns(2)
    n_plan = c1.number_input("n final (ajustable)", 1, 100000, n_plan, key="m_nf")
    c_plan = c2.number_input("c final (ajustable)", 0, 10000, c_plan, key="m_cf")
    rg = muestreo.riesgos(n_plan, c_plan, nac, ltpd, dist, N)
    ok_a = rg["α (riesgo del productor)"] <= a + 1e-9
    ok_b = rg["β = Pa(LTPD) (riesgo del consumidor)"] <= b + 1e-9
    verif = pd.DataFrame({"Riesgo": ["α real", "β real"],
                          "Valor": [rg["α (riesgo del productor)"], rg["β = Pa(LTPD) (riesgo del consumidor)"]],
                          "Objetivo": [a, b], "¿Cumple?": ["Sí" if ok_a else "No", "Sí" if ok_b else "No"]})
    st.dataframe(verif, hide_index=True)
    if not (ok_a and ok_b):
        st.info("Ajuste n y c (normalmente aumentar n y c) hasta que ambos riesgos se cumplan.")
    concl = [f"Plan diseñado: n = {n_plan}, c = {c_plan} (n = {r['n']:.2f}, c = {r['c']:.2f} por el método matemático). "
             f"α real = {rg['α (riesgo del productor)']:.4f}, β real = {rg['β = Pa(LTPD) (riesgo del consumidor)']:.4f}."]
    st.success(concl[0])
    ui.boton_registrar("m7_disenar", "Muestreo de aceptación", "Diseño de plan de muestreo (método matemático)",
                       tablas=[("Pasos del método matemático", r["pasos"]), ("Verificación de riesgos", verif)],
                       conclusiones=concl)


def _mil():
    st.markdown("**MIL-STD-105E (ANSI/ASQC Z1.4, ISO 2859)** — muestreo simple, inspección normal. "
                "Pasos: NAC → nivel de inspección → tamaño de lote → letra código → tabla maestra (siguiendo las flechas).")
    c1, c2, c3 = st.columns(3)
    N = c1.number_input("Tamaño del lote", 2, 10_000_000, 60000, key="mil_N")
    nivel = c2.selectbox("Nivel general de inspección", ["I", "II", "III"], index=1, key="mil_nv")
    nac = c3.selectbox("NAC (%)", muestreo.NAC_COLUMNAS, index=muestreo.NAC_COLUMNAS.index(2.5), key="mil_nac")
    r = muestreo.plan_mil_std(N, nac, nivel)
    for p in r["pasos"]:
        st.write("• " + p)
    st.success(f"Plan: n = {r['n']}, Ac = {r['Ac']}, Re = {r['Re']}")
    if nac <= 10:
        p = st.number_input("Evaluar Pa para una fracción defectuosa p'", 0.0, 1.0, nac / 100, format="%.5f", key="mil_p")
        m = st.number_input("Lotes del pedido", 1, 1000, 1, key="mil_m")
        pa = muestreo.pa_simple(r["n"], r["Ac"], p)
        st.write(f"Pa = {pa:.5f}; probabilidad de aceptar los {m} lotes = {pa ** m:.5f}")
    st.caption("NAC > 10 en la tabla se expresa en defectos por cada 100 unidades.")
    with st.expander("Ver tabla maestra (inspección normal)"):
        st.dataframe(muestreo.tabla_mil_std(), hide_index=True)
    with st.expander("Reglas de cambio entre inspección normal, rigurosa y reducida"):
        st.markdown("""- **Normal → rigurosa:** 2 de 5 lotes consecutivos rechazados.
- **Rigurosa → normal:** 5 lotes consecutivos aceptados.
- **Normal → reducida:** 10 lotes previos aceptados, total de defectuosos ≤ número límite, producción estable y autorización.
- **Reducida → normal:** un lote rechazado, producción irregular u otra condición que lo justifique.
- **Suspensión:** 5 lotes consecutivos rechazados bajo inspección rigurosa.""")
    ui.boton_registrar("m7_mil", "Muestreo de aceptación", "Plan MIL-STD-105E", tablas=[("Plan MIL-STD", pd.DataFrame({"Paso": r["pasos"]}))],
                       conclusiones=[f"Para lotes de {N} unidades, nivel {nivel} y NAC {nac} %: n = {r['n']}, "
                                     f"Ac = {r['Ac']}, Re = {r['Re']}."])


def _conceptos():
    st.markdown("""
- **NAC (AQL):** máximo porcentaje defectuoso que se considera satisfactorio como promedio del proceso del proveedor.
- **LTPD:** el nivel de calidad más pobre que el consumidor está dispuesto a aceptar en un lote individual.
- **α (riesgo del productor):** rechazar un lote bueno (calidad NAC). **β (riesgo del consumidor):** aceptar un lote malo (calidad LTPD).
- **Curva OC:** probabilidad de aceptar el lote en función de su fracción defectuosa; muestra el poder discriminatorio del plan.
- **AOQ / AOQL:** calidad de salida promedio con inspección rectificadora; el AOQL es la peor calidad promedio posible.
- **IQL:** fracción defectuosa con probabilidad de aceptación 0,5.
- **Defectos:** críticos (hacen el artículo peligroso), mayores (lo vuelven inútil), menores (lo hacen menos útil).
- El muestreo de aceptación **dictamina lotes, no controla el proceso**: el control y la mejora se hacen con las cartas de control.
""")
