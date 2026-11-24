"""Módulo 6. Diseño de gráficos de control: ARL0, ARL1, ATS."""
import math

import numpy as np
import pandas as pd
import streamlit as st

from cep import capacidad, diseno, graficos
from cep.estadistica import alfa_de_z, z_alfa_medios
from paginas import estilo, ui


def _num_lista(texto, tipo=float):
    return [tipo(v) for v in texto.replace(";", " ").split() if v.strip()]


def render():
    estilo.encabezado("compass", "Diseño de gráficos de control", "ARL0, ARL1, ATS, potencia, tamaño de muestra, frecuencia, productos no conformes y esquema DS-c.", "Paso 9")
    tabs = st.tabs(["Carta X̄: ARL y ATS", "Diseñar n y frecuencia", "Productos no conformes hasta detectar",
                    "Cartas por atributos: curva OC y ARL", "Tamaño de muestra carta p", "Esquema DS-c (avanzado)"])
    f1 = st.session_state.get("fase1_var") or {}
    with tabs[0]:
        _xbar(f1)
    with tabs[1]:
        _disenar(f1)
    with tabs[2]:
        _pnc(f1)
    with tabs[3]:
        _atributos()
    with tabs[4]:
        _n_p()
    with tabs[5]:
        _dsc()


AYUDA_CORRIMIENTO = ("X̄'' es el cambio de media que usted quiere que la carta detecte. Puede escribirla, partir de "
                     "un corrimiento de d desviaciones (por defecto 1σ: X̄'' = X̄' + σ) u obtenerla con los datos "
                     "cargados o con las especificaciones; en cada caso la app muestra cómo la calculó.")
MODOS = ["d (en desviaciones estándar)", "Escribir la nueva media X̄''", "Obtener X̄'' de los datos",
         "Obtener X̄'' de las especificaciones"]


def _especificaciones_activas():
    cap = st.session_state.get("capacidad") or {}
    lie, lse = cap.get("lie"), cap.get("lse")
    if lie is None and lse is None:
        from cep import empresa
        from paginas import m0_empresa
        var = st.session_state.get("var") or {}
        pv = empresa.buscar_variable(m0_empresa.perfil_activo(), var.get("nombre", ""))
        if pv:
            lie, _, lse = empresa.especificaciones(pv)
    return lie, lse


def _media_de_datos(clave):
    var = st.session_state.get("var")
    if not var:
        st.info("Cargue datos en el paso 3 para usar esta opción.")
        return None
    grupos = var["grupos"]
    k_tot = len(grupos)
    k = int(st.number_input("Promediar los últimos k subgrupos cargados", 1, k_tot, min(5, k_tot), key=f"kd_{clave}",
                            help="Por ejemplo, las muestras nuevas de la Fase II o las más recientes."))
    ult = np.concatenate(grupos[-k:])
    m1 = float(np.mean(ult))
    st.caption(f"X̄'' = promedio de los subgrupos {k_tot - k + 1} a {k_tot} ({len(ult)} datos) = {m1:.5g}.")
    return m1


def _media_de_especificaciones(sigma, clave):
    lie, lse = _especificaciones_activas()
    lados = [x for x, v in (("LSE", lse), ("LIE", lie)) if v is not None]
    if not lados:
        st.info("Escriba el LIE y/o el LSE en el paso 4 o en el paso 7 para usar esta opción.")
        return None
    c1, c2, c3 = st.columns(3)
    lado = c1.radio("Hacia qué límite se corre la media", lados, horizontal=True, key=f"lado_{clave}")
    criterio = c2.radio("Criterio", ["% de no conformes", "Cpk mínimo"], horizontal=True, key=f"crit_{clave}")
    limite = lse if lado == "LSE" else lie
    if criterio.startswith("%"):
        pnc = c3.number_input("% de no conformes por ese límite", 0.01, 49.0, 1.0, 0.5, key=f"pnc_{clave}") / 100
        m1 = diseno.media_por_pnc(sigma, pnc, limite, lado)
        z = abs(m1 - limite) / sigma
        signo = "−" if lado == "LSE" else "+"
        st.caption(f"P(Z > z) = {100 * pnc:g} % ⇒ z = {z:.4f}; X̄'' = {lado} {signo} z·σ = {limite:g} {signo} "
                   f"{z:.4f}·{sigma:.5g} = {m1:.5g}. Con esa media el proceso produciría {100 * pnc:g} % de no "
                   f"conformes por el {lado}.")
    else:
        cpk = c3.number_input("Cpk mínimo aceptable", 0.0, 3.0, 1.0, 0.05, key=f"cpk_{clave}")
        m1 = diseno.media_por_cpk(sigma, cpk, limite, lado)
        signo = "−" if lado == "LSE" else "+"
        st.caption(f"{'Cpu = (LSE − X̄)/3σ' if lado == 'LSE' else 'Cpl = (X̄ − LIE)/3σ'} = {cpk:g} ⇒ X̄'' = {lado} "
                   f"{signo} 3σ·Cpk = {limite:g} {signo} 3·{sigma:.5g}·{cpk:g} = {m1:.5g}.")
    return m1


def _entrada_corrimiento(sigma, media, clave):
    st.caption(AYUDA_CORRIMIENTO)
    modo = st.radio("Corrimiento expresado como", MODOS, horizontal=True, key=f"modo_{clave}")
    if modo.startswith("d"):
        d = st.number_input("d = |X̄' − X̄''|/σ (corrimiento que se quiere detectar)", 0.0, 10.0, 1.0, 0.1,
                            key=f"d_{clave}", help=AYUDA_CORRIMIENTO)
        st.caption(f"Equivale a X̄'' = X̄' ± d·σ = {media:.5g} ± {d:g}·{sigma:.5g}.")
        return d, None
    c1, c2 = st.columns(2)
    m0 = c1.number_input("X̄' (media en control)", value=float(media), format="%.6f", key=f"m0_{clave}")
    if modo == MODOS[1]:
        m1 = c2.number_input("X̄'' (media que se quiere detectar)", value=float(media + sigma), format="%.6f",
                             key=f"m1_{clave}", help=AYUDA_CORRIMIENTO)
    else:
        m1 = _media_de_datos(clave) if modo == MODOS[2] else _media_de_especificaciones(sigma, clave)
        if m1 is None:
            return 0.0, None
        c2.metric("X̄'' obtenida", f"{m1:.5g}")
    d = abs(m0 - m1) / sigma
    st.caption(f"d = |{m0:.5g} − {m1:.5g}| / {sigma:.5g} = {d:.4f}")
    return d, m1


def _xbar(f1):
    st.markdown("ARL0 = 1/α (muestras promedio hasta una falsa alarma) · ARL1 = 1/(1−β) (muestras promedio hasta "
                "detectar el corrimiento) · ATS = ARL·t · Potencia: 1 − β = P(Z ≥ |Z_α/2| − d·√n).")
    c1, c2, c3, c4 = st.columns(4)
    sigma = c1.number_input("σ del proceso", value=float(f1.get("sigma", 1.0)), format="%.6f", min_value=1e-12, key="x_s")
    z = c2.number_input("Z_α/2 de la carta", value=float(ui.config()["z"]), format="%.4f", key="x_z")
    n0 = int(f1.get("n", 5)) if int(f1.get("n", 5)) > 1 else 5
    n = c3.number_input("Tamaño de muestra n", 1, 500, n0, key="x_n")
    t = c4.number_input("Tiempo entre muestras t (horas)", 0.001, 1000.0,
                        float((st.session_state.get("plan_muestreo") or {}).get("t") or 1.0), key="x_t")
    d, _ = _entrada_corrimiento(sigma, f1.get("media", 0.0), "x")
    r = diseno.desempeno_xbar(d, n, z, t)
    tab = ui.tabla_parametros(r)
    c1, c2 = st.columns([1, 2])
    c1.dataframe(tab, hide_index=True, width="stretch")
    pd_tab = diseno.prob_deteccion(r["β"], 10)
    c2.dataframe(pd_tab, hide_index=True, width="stretch")
    st.markdown("**Curvas de desempeño para distintos tamaños de muestra**")
    ns = _num_lista(st.text_input("Tamaños de muestra a comparar", "2 3 5 8 10", key="x_ns"), int)
    ds = np.round(np.arange(0, 3.01, 0.25), 2)
    series = {f"n = {k}": [diseno.desempeno_xbar(dd, k, z, t)["ARL1"] for dd in ds] for k in ns}
    fig = graficos.curva(ds, series, "ARL1 vs corrimiento d", "d (desviaciones estándar)", "ARL1 (muestras)", log_y=True)
    st.plotly_chart(fig, width="stretch")
    tdis = diseno.tabla_diseno_xbar([0.5, 1, 1.5, 2, 3], ns, z, t)
    with st.expander("Tabla de diseño (n × d)"):
        st.dataframe(tdis, hide_index=True, width="stretch")
    concl = [f"Con n = {n}, límites a ±{z:.3g}σ y una muestra cada {t:g} h: ARL0 = {r['ARL0']:.1f} muestras "
             f"(una falsa alarma cada {r['ATS0']:.1f} h en promedio).",
             f"Para un corrimiento de d = {d:.3g}σ la potencia es {r['1−β (potencia)']:.4f}; ARL1 = {r['ARL1']:.2f} "
             f"muestras y ATS1 = {r['ATS1']:.2f} h. Probabilidad de detectarlo en las 3 primeras muestras: "
             f"{1 - r['β'] ** 3:.4f}.",
             f"Carga muestral Cm = n/t = {n / t:.3g} unidades/h."]
    for c in concl:
        st.write("• " + c)
    ui.boton_registrar("m6_xbar", "Fase II", "Desempeño de la carta X̄ (ARL/ATS)",
                       tablas=[("Desempeño carta X̄", tab), ("Probabilidad de detección", pd_tab), ("Tabla de diseño", tdis)],
                       figuras=[("ARL1 vs corrimiento", fig)], conclusiones=concl)


def _disenar(f1):
    st.markdown("""Diseña la carta X̄ para detectar un corrimiento d con una probabilidad dada en las primeras k
muestras: 1 − β^k = P → β; luego n = [(|Z_α/2| + Z_(1−β))/d]² (hoja de fórmulas 2.4). La frecuencia se
ajusta con la carga muestral: Cm = n/t ⇒ t = n/Cm.""")
    c1, c2, c3 = st.columns(3)
    sigma = c1.number_input("σ", value=float(f1.get("sigma", 1.0)), format="%.6f", min_value=1e-12, key="dz_s")
    alfa = c2.number_input("Riesgo tipo I α", 0.0001, 0.5, 0.0027, format="%.4f", key="dz_a")
    media = c3.number_input("X̄' (línea central)", value=float(f1.get("media", 0.0)), format="%.6f", key="dz_m")
    d, _ = _entrada_corrimiento(sigma, media, "dz")
    c1, c2 = st.columns(2)
    prob = c1.number_input("Probabilidad deseada de detección", 0.01, 0.9999, 0.90, key="dz_p")
    k = c2.number_input("…en alguna de las primeras k muestras", 1, 50, 2, key="dz_k")
    if d <= 0:
        st.warning("El corrimiento debe ser mayor que cero.")
        return
    z = z_alfa_medios(alfa)
    beta = diseno.beta_para_detectar(prob, k)
    n_cal, z1b = diseno.n_para_potencia(d, z, 1 - beta)
    n_fin = max(1, math.ceil(n_cal - 1e-9))
    pot_real = diseno.potencia_xbar(d, n_fin, z)
    lcs, lci = media + z * sigma / math.sqrt(n_fin), media - z * sigma / math.sqrt(n_fin)
    tab = pd.DataFrame({"Concepto": ["Z_α/2", "β requerido = (1−P)^(1/k)", "1 − β requerido", "Z_(1−β)",
                                     "n calculado", "n a usar (entero superior)", "Potencia real con n",
                                     "ARL0", "ARL1 con n", "LCS", "LC", "LCI"],
                        "Valor": [z, beta, 1 - beta, z1b, n_cal, n_fin, pot_real, 1 / alfa_de_z(z), 1 / pot_real,
                                  lcs, media, lci]})
    st.dataframe(tab, hide_index=True)
    st.markdown("**Frecuencia de muestreo con carga muestral**")
    c1, c2 = st.columns(2)
    cm = c1.number_input("Carga muestral disponible Cm (unidades por hora)", 0.01, 1e6, 10.0, key="dz_cm")
    t = n_fin / cm
    c2.metric("Tiempo entre muestras t = n/Cm", f"{t:.3f} h ({t * 60:.1f} min)")
    concl = [f"Para detectar un corrimiento de {d:.3g}σ con probabilidad {prob:g} en las primeras {k} muestras "
             f"(α = {alfa:g}) se requiere n = {n_fin} (n calculado {n_cal:.2f}); potencia real {pot_real:.4f}.",
             f"Límites de control: LCI = {lci:.5g}, LC = {media:.5g}, LCS = {lcs:.5g}.",
             f"Con una carga muestral de {cm:g} unidades/h la muestra debe tomarse cada {t:.3f} h; ATS1 = "
             f"{t / pot_real:.3f} h y ATS0 = {t / alfa_de_z(z):.1f} h."]
    for c in concl:
        st.write("• " + c)
    ui.boton_registrar("m6_dis", "Fase II", "Diseño de la carta X̄ (n y frecuencia)", tablas=[("Diseño de la carta", tab)],
                       conclusiones=concl)


def _pnc(f1):
    st.markdown("""**Valor esperado de productos no conformes** hasta detectar el corrimiento en la muestra k
(VEPNC = TP·%PNC_corr·(1−β)·[t1 + t2·β + … + tk·β^(k−1)], con t_i = i·t) y **valor promedio**
(VPPNC = TP·ATS1·%PNC_corr). %PNC_corr es la fracción fuera de especificaciones con la media corrida.""")
    cap = st.session_state.get("capacidad") or {}
    c1, c2, c3 = st.columns(3)
    sigma = c1.number_input("σ", value=float(cap.get("sigma", f1.get("sigma", 1.0))), format="%.6f", min_value=1e-12, key="pn_s")
    lie = c2.number_input("LIE", value=float(cap.get("lie") if cap.get("lie") is not None else -3.0), format="%.6f", key="pn_lie")
    lse = c3.number_input("LSE", value=float(cap.get("lse") if cap.get("lse") is not None else 3.0), format="%.6f", key="pn_lse")
    c1, c2, c3 = st.columns(3)
    m0 = c1.number_input("X̄' (media en control)", value=float(cap.get("media", f1.get("media", 0.0))), format="%.6f", key="pn_m0")
    m1 = c2.number_input("X̄'' (media corrida)", value=float(cap.get("media", f1.get("media", 0.0)) + sigma), format="%.6f", key="pn_m1")
    z = c3.number_input("Z_α/2 de la carta", value=float(ui.config()["z"]), format="%.4f", key="pn_z")
    plan = st.session_state.get("plan_muestreo") or {}
    n_def = int(plan.get("n") or f1.get("n") or 5)
    t_def = float(plan.get("t") or 1.0)
    tp_def = (float(plan["produccion"]) / float(plan["horas"])) if (plan.get("produccion") and plan.get("horas")) else 500.0
    st.caption("n, t y TP vienen del plan de muestreo (paso 8): así el ATS1 coincide con el de la pestaña 5.")
    c1, c2, c3, c4 = st.columns(4)
    n = c1.number_input("n de monitoreo", 1, 500, n_def, key="pn_n")
    t = c2.number_input("t entre muestras (h)", 0.001, 100.0, t_def, key="pn_t")
    tp = c3.number_input("TP: velocidad de producción (u/h)", 0.0, 1e9, round(tp_def, 2), key="pn_tp")
    k = c4.number_input("Muestra k", 1, 100, 3, key="pn_k")
    d = abs(m0 - m1) / sigma
    pot = diseno.potencia_xbar(d, n, z)
    beta = 1 - pot
    pnc = capacidad.indices(m1, sigma, lse, lie)["%PNC total"]
    ve = diseno.vepnc(tp, pnc, beta, t, int(k))
    ats1 = t / pot if pot > 0 else math.inf
    vp = diseno.vppnc(tp, ats1, pnc)
    tab = pd.DataFrame({"Concepto": ["d", "1 − β", "β", "%PNC con la media corrida", "P(detectar en las k primeras)",
                                     f"VEPNC hasta la muestra {k}", "ATS1 (h)", "VPPNC (hasta la detección)"],
                        "Valor": [d, pot, beta, pnc, 1 - beta ** k, ve, ats1, vp]})
    st.dataframe(tab, hide_index=True)
    concl = [f"Con n = {n} cada {t:g} h y TP = {tp:g} u/h: si la media se corre a {m1:.5g} ({d:.2g}σ), el %PNC sube a "
             f"{100 * pnc:.4f} %. Hasta la muestra {k} se esperan {ve:.3g} unidades no conformes (VEPNC) y, en "
             f"promedio, {vp:.3g} unidades no conformes antes de detectar el corrimiento (VPPNC, ATS1 = {ats1:.2f} h)."]
    st.info(concl[0])
    ui.boton_registrar("m6_pnc", "Fase II", "Productos no conformes hasta la detección", tablas=[("VEPNC y VPPNC", tab)],
                       conclusiones=concl)


def _atributos():
    st.markdown("""Curva OC de la carta: β = P(D ≤ ⌊n·LCS⌋ | p) − P(D ≤ ⌊n·LCI⌋ | p) (Binomial para p/np; Poisson
para c/u). ARL0 = 1/α en el valor de control y ARL1 = 1/(1−β) para el valor corrido (módulo 4.8.2).""")
    f = st.session_state.get("fase1_attr") or {}
    tipos = ["p", "np", "c", "u"]
    tipo = st.radio("Carta", tipos, index=tipos.index(f.get("tipo", "p")), horizontal=True, key="oc_t")
    z = ui.config()["z"]
    c1, c2, c3 = st.columns(3)
    centro_def = float(f.get("centro", 0.05 if tipo in ("p", "np") else 4.0)) if f.get("tipo") == tipo else (0.05 if tipo in ("p", "np") else 4.0)
    centro = c1.number_input("Valor en control (p̄, c̄ o Ū)", value=centro_def, format="%.6f", key="oc_c")
    n = c2.number_input("n (unidades por muestra; c: 1)", 1.0, 1e6, float(f.get("n", 50.0)) if f.get("tipo") == tipo else (1.0 if tipo == "c" else 50.0), key="oc_n")
    t = c3.number_input("t entre muestras (h)", 0.001, 1000.0, 1.0, key="oc_tt")
    if tipo == "p":
        sd = math.sqrt(centro * (1 - centro) / n)
        lcs, lci, base = centro + z * sd, max(centro - z * sd, 0), centro
    elif tipo == "np":
        sd = math.sqrt(n * centro * (1 - centro))
        lcs, lci, base = n * centro + z * sd, max(n * centro - z * sd, 0), centro
    elif tipo == "c":
        lcs, lci, base = centro + z * math.sqrt(centro), max(centro - z * math.sqrt(centro), 0), centro
    else:
        lcs, lci, base = centro + z * math.sqrt(centro / n), max(centro - z * math.sqrt(centro / n), 0), centro
    st.caption(f"Límites: LCI = {lci:.5g}, LCS = {lcs:.5g}")
    valores = np.round(np.linspace(base * 0.25, base * 4, 16), 6) if base > 0 else np.linspace(0.01, 0.5, 16)
    if tipo in ("p", "np"):
        valores = valores[valores < 1]
    extra = st.text_input("Valores corridos a evaluar (separados por espacio, opcional)", "", key="oc_v")
    if extra.strip():
        valores = np.array(_num_lista(extra))
    oc = diseno.beta_atributos(tipo, int(round(n)), lcs, lci, list(valores))
    oc0 = diseno.beta_atributos(tipo, int(round(n)), lcs, lci, [base]).iloc[0]
    alfa = 1 - oc0["β"]
    oc["ATS = ARL·t"] = oc["ARL = 1/(1−β)"] * t
    st.metric("α real en control y ARL0", f"α = {alfa:.5f} · ARL0 = {1 / alfa if alfa > 0 else math.inf:.1f}")
    st.dataframe(oc, hide_index=True, width="stretch")
    fig = graficos.curva(oc["Parámetro"], {"β (curva OC)": oc["β"]}, "Curva OC de la carta", "Parámetro del proceso", "β")
    st.plotly_chart(fig, width="stretch")
    ui.boton_registrar("m6_oc", "Diseño", f"Curva OC y ARL de la carta {tipo}", tablas=[("Curva OC y ARL", oc)],
                       figuras=[("Curva OC", fig)],
                       conclusiones=[f"Carta {tipo}: α real = {alfa:.5f} (ARL0 = {1 / alfa if alfa > 0 else math.inf:.1f})."])


def _n_p():
    st.markdown("**Determinación del tamaño de muestra de la carta p (módulo 4.8.1.1)**")
    c1, c2 = st.columns(2)
    p = c1.number_input("p en control", 0.0001, 0.9999, 0.01, format="%.4f", key="np_p")
    L = c2.number_input("L (sigmas de los límites)", 1.0, 6.0, 3.0, key="np_L")
    c1, c2, c3 = st.columns(3)
    gamma = c1.number_input("Método 1: P(D ≥ 1) deseada", 0.01, 0.9999, 0.95, key="np_g")
    p1 = c2.number_input("p fuera de control (métodos 2 y 4)", 0.0001, 0.9999, 0.05, format="%.4f", key="np_p1")
    pot = c3.number_input("Método 4: potencia 1 − β", 0.01, 0.9999, 0.5, key="np_pot")
    filas = []
    for m, kw in ((1, {"gamma": gamma}), (2, {"L": L, "p1": p1}), (3, {"L": L}), (4, {"z": L, "potencia": pot, "p1": p1})):
        try:
            nn, txt = diseno.n_carta_p(p, m, **kw)
            filas.append({"Método": m, "n": nn, "n entero": math.ceil(nn), "Detalle": txt})
        except Exception as e:  # noqa: BLE001
            filas.append({"Método": m, "n": np.nan, "n entero": np.nan, "Detalle": str(e)})
    tab = pd.DataFrame(filas)
    st.dataframe(tab, hide_index=True, width="stretch")
    nn = st.number_input("Evaluar la potencia de la carta p con n =", 1, 100000, int(tab["n entero"].max()), key="np_n")
    st.write(f"1 − β = {diseno.potencia_carta_p(p, p1, nn, L):.4f} para detectar el paso de p = {p} a {p1}.")
    ui.boton_registrar("m6_np", "Diseño", "Tamaño de muestra de la carta p", tablas=[("Métodos de tamaño de muestra", tab)])


def _dsc():
    st.markdown("""**Esquema de muestreo doble para la carta c (DS-c)** — Campuzano, Carrión y Mosquera (2019),
*European J. Industrial Engineering*, 13(6). Se toma una muestra global (m1 + m2) de unidades de inspección; se
analiza primero m1: si x1 < WL el proceso está en control; si x1 > UCL1 está fuera de control; si
WL < x1 < UCL1 se analiza m2 y se decide con x1 + x2 frente a UCL2. Se sugiere ubicar los límites en x,5.""")
    c1, c2, c3, c4, c5 = st.columns(5)
    m1 = c1.number_input("m1", 0.01, 100.0, 0.5, key="ds_m1")
    m2 = c2.number_input("m2", 0.01, 100.0, 1.0, key="ds_m2")
    wl = c3.number_input("WL", 0.0, 1000.0, 2.5, key="ds_wl")
    u1 = c4.number_input("UCL1", 0.0, 1000.0, 6.5, key="ds_u1")
    u2 = c5.number_input("UCL2", 0.0, 1000.0, 9.5, key="ds_u2")
    c1, c2, c3 = st.columns(3)
    lam0 = c1.number_input("λ0 (no conformidades por unidad en control)", 0.01, 1000.0, 4.0, key="ds_l0")
    ucl_fp = c2.number_input("UCL de la carta c clásica de comparación (n = 1)", 0.0, 1000.0, 10.5, key="ds_fp")
    gammas = _num_lista(c3.text_input("Corrimientos γ (λ1 = γ·λ0)", "1 1.25 1.5 1.75 2 2.5 3", key="ds_g"))
    filas = []
    for g in gammas:
        ds = diseno.ds_c(m1, m2, wl, u1, u2, g * lam0)
        fp = diseno.fp_c(1.0, ucl_fp, g * lam0)
        filas.append({"γ": g, "λ": g * lam0, "ARL DS-c": ds["ARL"], "ASN DS-c": ds["ASN"], "ARL c clásica": fp["ARL"]})
    tab = pd.DataFrame(filas)
    st.dataframe(tab, hide_index=True, width="stretch")
    fig = graficos.curva(tab["γ"], {"DS-c": tab["ARL DS-c"], "c clásica": tab["ARL c clásica"]},
                         "Comparación de ARL", "γ = λ1/λ0", "ARL", log_y=True)
    st.plotly_chart(fig, width="stretch")
    st.caption("Con γ = 1 la fila muestra ARL0 (falsas alarmas); compare ARL1 de ambos esquemas con ARL0 y ASN "
               "similares para elegir el diseño.")
    ui.boton_registrar("m6_dsc", "Diseño", "Esquema DS-c vs carta c clásica", tablas=[("ARL y ASN", tab)],
                       figuras=[("ARL DS-c vs c clásica", fig)])
