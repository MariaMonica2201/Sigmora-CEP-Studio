"""Paso 9. Fase II: diseño del plan de monitoreo y control con muestras nuevas.

Fase I (pasos 6 y 10): con las muestras iniciales se calculan los límites suponiendo que el proceso está
calibrado y en su estado óptimo. Fase II: los límites quedan fijos y se evalúan muestras nuevas.

Diseño (hoja de fórmulas, secciones 2–5; módulo 4.6 y 4.7.1.3–4.7.1.4):
  d = |X̄' − X̄''|/σ ;  1 − β = P(Z ≥ |Z_α/2| − d·√n)
  ARL0 = 1/α, ARL1 = 1/(1 − β), ATS = ARL·t
  Detectar con probabilidad P en las k primeras muestras: 1 − β^k = P
  n = [(|Z_α/2| + Z_(1−β))/d]²
  Carga muestral Cm = n/t ; con Cm nueva: t = n/Cm
"""
import math

import numpy as np
import pandas as pd
import streamlit as st

from cep import diseno, graficos
from cep.estadistica import alfa_de_z
from paginas import estilo, m2_variables, m3_atributos, m6_diseno, ui


def render():
    estilo.encabezado("telescope", "Fase II · muestras nuevas", "Diseño del plan de monitoreo (potencia, ARL/ATS y carga "
                      "muestral) y control de las muestras nuevas con los límites fijos de la Fase I.", "Paso 9")
    estilo.interpretacion("Cómo se conecta con la Fase I", [
        "En la **Fase I** (pasos 6 y 10) las **muestras iniciales** fijaron los límites de control, suponiendo que el "
        "proceso estaba **calibrado y en su estado óptimo**.",
        "En la **Fase II** esos límites **no se recalculan**: se diseña cómo seguir muestreando (n y frecuencia) "
        "para detectar a tiempo un cambio en la media, y se grafican las **muestras nuevas**.",
        "Orden de trabajo: **4)** graficar las muestras nuevas con los límites de la Fase I, **5)** calcular con qué "
        "potencia se detecta un cambio en la media y **6)** incrementar la carga muestral para bajar el ATS1, "
        "dentro del plan de muestreo del paso 8. Para atributos, los mismos pasos están en el paso 10."], "info")
    t1, t2, t3, t4 = st.tabs(["4 · Monitoreo con muestras nuevas", "5 · Potencia para detectar un cambio en la media",
                              "6 · Incrementar la carga muestral (ATS1)", "Otras herramientas de diseño"])
    with t1:
        _control_variables()
    with t2:
        ctx = _potencia()
    with t3:
        if ctx:
            _carga(ctx)
        else:
            st.info("Complete primero la pestaña 5 (potencia).")
    with t4:
        f1 = st.session_state.get("fase1_var") or {}
        a, b = st.tabs(["Curvas ARL", "Productos no conformes"])
        with a:
            m6_diseno._xbar(f1)
        with b:
            m6_diseno._pnc(f1)


def _potencia():
    f1 = st.session_state.get("fase1_var")
    if not f1:
        st.info("Primero calcule los límites de la **Fase I** en el paso 6 (Cartas X̄) con sus muestras iniciales.")
        return
    var = st.session_state.get("var") or {}
    plan = st.session_state.get("plan_muestreo") or {}
    z = ui.config()["z"]
    media, sigma = float(f1["media"]), float(f1["sigma"])

    estilo.seccion("puzzle", "A · Punto de partida: el plan de las primeras cargas")
    c1, c2 = st.columns(2)
    n0 = int(c1.number_input("n del plan inicial", 1, 25, int(plan.get("n") or f1.get("n") or var.get("n") or 1),
                             key="f2_n0", help="Sale del paso 8 (Plan de muestreo) o de las muestras iniciales."))
    t_def = plan.get("t") or var.get("t_datos")
    t0 = c2.number_input("Horas entre subgrupos del plan inicial", 0.05, 24.0,
                         float(t_def) if t_def else None, 0.25, key="f2_t0",
                         placeholder="Escríbalo (o complételo en el paso 8)")
    if not t0:
        st.info("Escriba las horas entre subgrupos (o calcúlelas en el paso 8) para obtener el ATS.")
        return
    horas = plan.get("horas")
    k_dia = max(1, int(horas // t0)) if horas else None
    prod = plan.get("produccion")
    minimo = plan.get("min_dia")

    estilo.seccion("target", "B · Cambio de la media que se quiere detectar")
    st.caption("Potencia de la carta X̄: 1 − β = P(Z ≥ |Z_α/2| − d·√n), con d = |X̄' − X̄''|/σ.")
    d, _ = m6_diseno._entrada_corrimiento(sigma, media, "f2")
    c1, c2 = st.columns(2)
    prob = c1.number_input("Probabilidad deseada de detectarlo", 0.01, 0.9999, 0.90, key="f2_p")
    k = int(c2.number_input("…en alguna de las primeras k muestras", 1, 50, 2, key="f2_k"))
    if d <= 0:
        st.warning("El corrimiento debe ser mayor que cero.")
        return
    beta_req = diseno.beta_para_detectar(prob, k)
    n_cal, _ = diseno.n_para_potencia(d, z, 1 - beta_req)
    n_req = max(1, math.ceil(n_cal - 1e-9))
    r0 = diseno.desempeno_xbar(d, n0, z, t0)
    estilo.kpis([
        dict(icono="zap", etiqueta="Potencia 1 − β (plan inicial)", valor=f"{r0['1−β (potencia)']:.3f}",
             sub=f"n = {n0}, d = {d:.3g}σ"),
        dict(icono="repeat", etiqueta="ARL1", valor=f"{r0['ARL1']:.2f}", sub="muestras hasta detectar", color="#344054"),
        dict(icono="timer", etiqueta="ATS1", valor=f"{r0['ATS1']:.2f} h", sub=f"una muestra cada {t0:g} h",
             color=estilo.ROJO),
        dict(icono="triangle-alert", etiqueta="ATS0", valor=f"{r0['ATS0']:.0f} h", sub="entre falsas alarmas", color=estilo.SUAVE),
        dict(icono="package", etiqueta="Carga muestral Cm", valor=f"{n0 / t0:.3g} u/h", sub="n/t", color=estilo.NARANJA),
    ])
    st.caption(f"Objetivo: 1 − β^{k} = {prob:g} ⇒ β = {beta_req:.4f}, 1 − β = {1 - beta_req:.4f}; "
               f"n = [(|Z_α/2| + Z_(1−β))/d]² = {n_cal:.2f} ⇒ n = {n_req}.")

    concl0 = [f"Plan inicial n = {n0} cada {t0:g} h: para un cambio de {d:.3g}σ en la media la potencia es "
              f"{r0['1−β (potencia)']:.4f} (β = {r0['β']:.4f}); ARL1 = {r0['ARL1']:.2f} muestras y ATS1 = {r0['ATS1']:.2f} h. "
              f"ARL0 = {r0['ARL0']:.0f} (una falsa alarma cada {r0['ATS0']:.0f} h).",
              f"Para detectarlo con probabilidad {prob:g} en las primeras {k} muestras se requiere 1 − β = "
              f"{1 - beta_req:.4f}, es decir n = {n_req} (n calculado {n_cal:.2f})."]
    estilo.interpretacion("Potencia del plan inicial", concl0, "info")
    pd_tab = diseno.prob_deteccion(r0["β"], 10)
    with st.expander("Probabilidad de detectar el cambio muestra a muestra"):
        st.dataframe(pd_tab, hide_index=True, width="stretch")
    ui.boton_registrar("m9_potencia", "Fase II", "Potencia para detectar un cambio en la media",
                       tablas=[("Desempeño del plan inicial", ui.tabla_parametros(r0)), ("Probabilidad de detección", pd_tab)],
                       conclusiones=concl0)
    return dict(media=media, sigma=sigma, z=z, n0=n0, t0=t0, horas=horas, k_dia=k_dia, prod=prod, minimo=minimo, d=d,
                beta_req=beta_req, n_req=n_req, r0=r0)


def _carga(c):
    media, sigma, z, n0, t0, horas, k_dia, prod, minimo, d, beta_req, n_req, r0 = (
        c[k] for k in ("media", "sigma", "z", "n0", "t0", "horas", "k_dia", "prod", "minimo", "d", "beta_req", "n_req",
                       "r0"))
    estilo.seccion("trending-up", "C · Incrementar la carga muestral para bajar el ATS1")
    st.markdown("Se mantiene la frecuencia del plan inicial (una muestra cada "
                f"**{t0:g} h**) y se aumenta n: la carga muestral **Cm = n/t** sube, la potencia sube y el **ATS1 "
                "baja**. Cada opción se compara con el plan de muestreo del paso 8.")
    maximo = st.number_input("Máximo de unidades que la empresa puede inspeccionar por día (opcional)", 1,
                             10_000_000, None, key="f2_max", placeholder="Déjelo vacío si no hay límite")
    tope = min(25, max(n_req, n0 + 5))
    filas = []
    for n in range(n0, tope + 1):
        r = diseno.desempeno_xbar(d, n, z, t0)
        u_dia = n * k_dia if k_dia else None
        dentro = (n <= 25 and (u_dia is None or ((prod is None or u_dia <= prod) and (maximo is None or u_dia <= maximo))))
        filas.append({"n": n, "t (h)": t0, "Cm = n/t (u/h)": round(n / t0, 3),
                      "1 − β": round(r["1−β (potencia)"], 4), "ARL1": round(r["ARL1"], 3), "ATS1 (h)": round(r["ATS1"], 3),
                      "Unidades por día": u_dia if u_dia is not None else "—",
                      "% de la producción": f"{100 * u_dia / prod:.1f} %" if (u_dia and prod) else "—",
                      "Cumple el mínimo de la tabla": ("Sí" if u_dia >= minimo else "No") if (u_dia and minimo) else "—",
                      "Dentro del plan": "Sí" if dentro else "No",
                      "Logra el objetivo": "Sí" if r["1−β (potencia)"] >= 1 - beta_req - 1e-12 else "No"})
    tab = pd.DataFrame(filas)
    st.dataframe(tab, hide_index=True, width="stretch")
    fig = graficos.curva(tab["n"], {"ATS1 (h)": tab["ATS1 (h)"]}, "ATS1 al aumentar n (misma frecuencia)",
                         "Tamaño de muestra n", "ATS1 (horas)")
    st.plotly_chart(fig, width="stretch")
    validas = tab[(tab["Dentro del plan"] == "Sí") & (tab["Logra el objetivo"] == "Sí")]
    if len(validas):
        n_rec = int(validas["n"].iloc[0])
        nota_rec = f"n = {n_rec} es el menor tamaño que logra el objetivo dentro del plan."
        nivel = "ok"
    else:
        dentro_tab = tab[tab["Dentro del plan"] == "Sí"]
        n_rec = int(dentro_tab["n"].iloc[-1]) if len(dentro_tab) else n0
        nota_rec = (f"Ningún n hasta {tope} logra el objetivo dentro del plan; el mayor posible es n = {n_rec}. "
                    "Reduzca la probabilidad deseada, aumente k o amplíe la carga permitida.")
        nivel = "alerta"

    estilo.seccion("circle-check", "D · Plan elegido para la Fase II")
    c1, c2 = st.columns(2)
    opciones = list(tab["n"])
    n2 = int(c1.selectbox("n para la Fase II", opciones, index=opciones.index(n_rec), key="f2_n2"))
    t2 = float(c2.number_input("Horas entre subgrupos en la Fase II", 0.05, 24.0, float(t0), 0.25, key="f2_t2"))
    r2 = diseno.desempeno_xbar(d, n2, z, t2)
    cm0 = n0 / t0
    t_misma = n2 / cm0
    r_misma = diseno.desempeno_xbar(d, n2, z, t_misma)
    lcs, lci = media + z * sigma / math.sqrt(n2), media - z * sigma / math.sqrt(n2)
    st.session_state["plan_fase2"] = {"n": n2, "t": t2, "d": d, "ATS1": r2["ATS1"], "potencia": r2["1−β (potencia)"]}
    resumen = pd.DataFrame({
        "Concepto": ["n", "t (h)", "Cm = n/t (u/h)", "1 − β", "ARL1", "ATS1 (h)", "ATS0 (h)",
                     "Unidades por día", "LCS carta X̄", "LC", "LCI carta X̄"],
        "Plan inicial": [n0, t0, n0 / t0, r0["1−β (potencia)"], r0["ARL1"], r0["ATS1"], r0["ATS0"],
                         n0 * k_dia if k_dia else np.nan, media + z * sigma / math.sqrt(n0), media,
                         media - z * sigma / math.sqrt(n0)],
        "Plan de Fase II": [n2, t2, n2 / t2, r2["1−β (potencia)"], r2["ARL1"], r2["ATS1"], r2["ATS0"],
                            n2 * max(1, int(horas // t2)) if horas else np.nan, lcs, media, lci]})
    st.dataframe(resumen, hide_index=True, width="stretch")
    puntos = [nota_rec,
              f"Con n = {n2} cada {t2:g} h la potencia para un cambio de {d:.3g}σ pasa de {r0['1−β (potencia)']:.3f} a "
              f"{r2['1−β (potencia)']:.3f}, y el ATS1 baja de **{r0['ATS1']:.2f} h** a **{r2['ATS1']:.2f} h**.",
              f"La carga muestral sube de {cm0:.3g} a {n2 / t2:.3g} unidades/h.",
              f"Si en cambio se mantuviera la misma carga ({cm0:.3g} u/h), n = {n2} exigiría una muestra cada "
              f"{t_misma:.2f} h (t = n/Cm) y el ATS1 sería {r_misma['ATS1']:.2f} h.",
              f"Límites de la carta X̄ para n = {n2} (con X̿ y σ de la Fase I): LCI = {lci:.5g}, LC = {media:.5g}, "
              f"LCS = {lcs:.5g}."]
    if horas:
        u2 = n2 * max(1, int(horas // t2))
        puntos.append(f"Se inspeccionan {u2} unidades por día" + (f" ({100 * u2 / prod:.1f} % de la producción)" if prod
                                                                   else "") + ".")
    estilo.interpretacion("Plan de Fase II", puntos, nivel)
    ui.boton_registrar("m9_diseno", "Fase II", "Incremento de la carga muestral para bajar el ATS1",
                       tablas=[("Incremento de la carga muestral", tab), ("Plan inicial vs plan de Fase II", resumen)],
                       figuras=[("ATS1 vs n", fig)], conclusiones=[x.replace("**", "") for x in puntos])


def _control_variables():
    var, f1 = st.session_state.get("var"), st.session_state.get("fase1_var")
    if not var or not f1:
        st.info("Primero calcule la **Fase I** (paso 6) con las muestras iniciales.")
        return
    p2 = st.session_state.get("plan_fase2")
    if p2:
        st.caption(f"Plan de Fase II elegido: n = {p2['n']} cada {p2['t']:g} h. Las muestras nuevas se grafican "
                   "con X̿ y σ de la Fase I; los límites se ajustan al n de las muestras nuevas.")
    m2_variables._fase2(var, f1["tipo"], ui.config()["z"])


def _control_atributos():
    a, f1 = st.session_state.get("attr"), st.session_state.get("fase1_attr")
    if not a or not f1:
        st.info("Primero calcule la **Fase I** de la carta p/np/c/u (paso 10) con las muestras iniciales.")
        return
    m3_atributos._fase2(a, f1["tipo"], ui.config()["z"], st.session_state.get("attr_metodo", "variables"))
