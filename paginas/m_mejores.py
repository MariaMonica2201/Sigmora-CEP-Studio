"""Paso 11. Mejores condiciones: reúne lo calculado y propone la mejor forma de operar y de vigilar el proceso."""
import math

import numpy as np
import pandas as pd
import streamlit as st

from cep import capacidad, diseno, empresa
from paginas import estilo, ui


def render():
    estilo.encabezado("trophy", "Mejores condiciones", "Compara la condición actual con la mejor alcanzable: proceso "
                      "centrado en el nominal, plan de monitoreo con menor ATS1 y causas de no conformidad a atacar.",
                      "Paso 11")
    filas, puntos = [], []
    var, f1 = st.session_state.get("var"), st.session_state.get("fase1_var")
    cap = st.session_state.get("capacidad")
    perfil = st.session_state.get("perfil") or {}

    # ------------------------------------------------------------------ proceso (variables)
    if f1 and cap and (cap.get("lie") is not None or cap.get("lse") is not None):
        pv = empresa.buscar_variable(perfil, (var or {}).get("nombre"))
        _, nom, _ = empresa.especificaciones(pv)
        lie, lse, sigma, media = cap.get("lie"), cap.get("lse"), float(cap["sigma"]), float(cap["media"])
        if nom is None and lie is not None and lse is not None:
            nom = (lie + lse) / 2
        act = capacidad.indices(media, sigma, lse, lie)
        filas += [("Media del proceso", f"{media:.4g}", f"{nom:.4g}" if nom is not None else "—"),
                  ("Cpk", f"{act['Cpk']:.3f}", "")]
        if nom is not None:
            mej = capacidad.indices(nom, sigma, lse, lie)
            filas[-1] = ("Cpk", f"{act['Cpk']:.3f}", f"{mej['Cpk']:.3f}")
            filas.append(("%PNC (fuera de especificación)", f"{100 * act['%PNC total']:.4f} %",
                          f"{100 * mej['%PNC total']:.4f} %"))
            filas.append(("PPM no conformes", f"{act['PPM no conformes']:.0f}", f"{mej['PPM no conformes']:.0f}"))
            puntos.append(f"**Centrar el proceso en el nominal ({nom:g})**: hoy la media es {media:.4g} "
                          f"({media - nom:+.3g}). Centrado, el Cpk pasa de {act['Cpk']:.3f} a {mej['Cpk']:.3f} y los "
                          f"no conformes de {act['PPM no conformes']:.0f} a {mej['PPM no conformes']:.0f} PPM, con la "
                          "misma variabilidad.")
        if "Cp" in act and np.isfinite(act["Cp"]) and act["Cp"] < 1.33:
            puntos.append(f"El Cp es {act['Cp']:.3f} (< 1,33): además de centrar hay que **reducir la variabilidad** "
                          "(causas comunes: método, materia prima, mano de obra, máquina).")
        if not f1.get("en_control"):
            puntos.append("La Fase I todavía tiene señales: la primera condición es eliminar las causas especiales.")
    elif var:
        puntos.append("Para comparar con el nominal complete las especificaciones (paso 4), la Fase I (paso 6) y la "
                      "capacidad (paso 7).")

    # ------------------------------------------------------------------ monitoreo (Fase II)
    plan, p2 = st.session_state.get("plan_muestreo") or {}, st.session_state.get("plan_fase2")
    if p2 and f1:
        z = ui.config()["z"]
        r0 = diseno.desempeno_xbar(p2["d"], int(plan.get("n") or f1.get("n") or 1), z, float(plan.get("t") or p2["t"]))
        filas += [("Plan de monitoreo (n, t)", f"n = {plan.get('n')} cada {plan.get('t') or p2['t']:g} h",
                   f"n = {p2['n']} cada {p2['t']:g} h"),
                  (f"Potencia para un cambio de {p2['d']:.3g}σ", f"{r0['1−β (potencia)']:.3f}", f"{p2['potencia']:.3f}"),
                  ("ATS1 (horas hasta detectar)", f"{r0['ATS1']:.2f}", f"{p2['ATS1']:.2f}")]
        puntos.append(f"**Vigilar con n = {p2['n']} cada {p2['t']:g} h**: el ATS1 baja de {r0['ATS1']:.2f} h a "
                      f"{p2['ATS1']:.2f} h, dentro del plan de muestreo (paso 9).")
    elif f1:
        puntos.append("Diseñe el plan de Fase II (paso 9, pestañas 5 y 6) para conocer el mejor plan de monitoreo.")

    # ------------------------------------------------------------------ atributos
    fa = st.session_state.get("fase1_attr")
    if fa:
        estado = "bajo control" if fa.get("en_control") else "con señales de falta de control"
        if fa["tipo"] in ("p", "np"):
            filas.append(("Fracción no conforme p̄", f"{100 * fa['centro']:.2f} %", "Bajarla centrando el proceso y reduciendo su variabilidad"))
        puntos.append(f"Atributos: la carta {fa['tipo']} está {estado}.")
    pa = st.session_state.get("plan_fase2_attr")
    if pa:
        puntos.append(pa["texto"])
    par = st.session_state.get("pareto_vitales")
    if par and par.get("vitales"):
        puntos.append(f"**Atacar primero: {', '.join(par['vitales'])}** (pocos vitales del Pareto, ~80 % de los casos).")

    if not filas and not puntos:
        st.info("Todavía no hay resultados. Siga los pasos 3 a 10 y vuelva aquí: esta página se arma sola.")
        return
    tab = pd.DataFrame(filas, columns=["Indicador", "Condición actual", "Mejor condición"]) if filas else None
    if tab is not None:
        estilo.seccion("chart-column", "Actual frente a la mejor condición")
        st.dataframe(tab, hide_index=True, width="stretch")
    estilo.seccion("trophy", "Recomendaciones")
    estilo.interpretacion("Mejores condiciones de operación y control", puntos, "ok")
    ui.boton_registrar("m_mejores", "Mejores condiciones", "Mejores condiciones de operación y control",
                       tablas=[("Actual vs mejor condición", tab)] if tab is not None else None,
                       conclusiones=[x.replace("**", "") for x in puntos])
