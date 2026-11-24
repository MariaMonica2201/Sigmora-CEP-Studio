"""Módulo 2. Gráficos de control por variables (Fase I y Fase II)."""
import numpy as np
import pandas as pd
import streamlit as st

from cep import datos, variables
from paginas import estilo, ui


def render():
    estilo.encabezado("trending-up", "Gráficos de control por variables", "Fase I con las muestras iniciales: cartas X̄-R, X̄-S (o I-MR si n = 1), zonas A/B/C, patrones y cepillado.", "Paso 6")
    if not ui.requiere("var", "Primero cargue y defina una variable en el paso 3 (Datos)."):
        return
    var = st.session_state["var"]
    z = ui.config()["z"]
    n = var["n"]
    st.caption(f"Variable: **{var['nombre']}** · subgrupos: {len(var['grupos'])} · n = {n} · Z_α/2 = {z:.3f}")

    if n == 1:
        opciones = ["I-MR"]
        sugerida, motivo = "I-MR", "n = 1 (mediciones individuales): carta de individuos y rangos móviles."
    elif n >= 10:
        opciones = ["X̄-R", "X̄-S"]
        sugerida, motivo = "X̄-S", "n ≥ 10: la desviación S aprovecha mejor la información que el rango (módulo 4.7.2)."
    else:
        opciones = ["X̄-R", "X̄-S"]
        sugerida, motivo = "X̄-R", "n pequeño (2–9): la carta X̄-R es la más común y el rango es eficiente (módulo 4.7)."
    st.info(f"Carta sugerida: **{sugerida}** — {motivo}")
    tipo = st.radio("Tipo de carta", opciones, index=opciones.index(sugerida), horizontal=True)
    if n > 1:
        st.caption(f"La carta I-MR sólo aplica a mediciones individuales (n = 1). Con subgrupos de n = {n} se usan "
                   "X̄-R o X̄-S; tratar los datos subagrupados como individuales produce falsas señales de "
                   "estratificación y corrimiento.")
    if tipo != "I-MR" and n > 25:
        st.error("La tabla de constantes llega a n = 25.")
        return

    estilo.interpretacion("Fase I · muestras iniciales", [
        "Con las **muestras iniciales** se construyen los límites de control **suponiendo que el proceso está "
        "calibrado y en su estado óptimo** (sólo causas comunes).",
        "Si aparecen señales, se investigan y se cepillan hasta dejar límites confiables. Esos límites quedan "
        "**fijos** y con ellos se evalúan las **muestras nuevas** en el **paso 9 · Fase II**."], "info")
    _fase1(var, tipo, z)


def _datos_tipo(var, tipo):
    if tipo == "I-MR":
        x = var["individuales"]
        return x, list(range(1, len(x) + 1))
    g = [(gg, e) for gg, e in zip(var["grupos"], var["etiquetas"]) if len(gg) == var["n"]]
    return [a for a, _ in g], [b for _, b in g]


def _funcion(tipo):
    return {"X̄-R": variables.fase1_xr, "X̄-S": variables.fase1_xs, "I-MR": variables.fase1_imr}[tipo]


def _fase1(var, tipo, z):
    d, et = _datos_tipo(var, tipo)
    m = len(d)
    st.markdown("En Fase I se estiman los límites con datos históricos. Los puntos con causa especial identificada "
                "se excluyen (*cepillado*) y los límites se recalculan hasta que el proceso quede bajo control "
                "(módulo 4.5.1 y 4.7.1.2).")
    if m < 2:
        st.error(("La carta I-MR necesita al menos 2 datos (para el primer rango móvil)." if tipo == "I-MR" else
                  "Se necesitan al menos 2 subgrupos completos para estimar los límites de Fase I.") if m else
                 "No hay datos.")
        return
    hasta = (st.slider("Datos/subgrupos usados en Fase I (el resto queda disponible para Fase II)",
                       2, m, m, key=f"hasta_{tipo}") if m > 2 else m)
    d1, et1 = d[:hasta], et[:hasta]
    clave_exc = f"exc_{tipo}"
    exc_actual = [e for e in ui.estado(clave_exc, []) if e <= hasta]
    c1, c2 = st.columns([3, 1])
    k_ms = f"ms_{tipo}_{hasta}"
    if c2.button("Cepillado automático", help="Quita iterativamente los puntos fuera de límites y recalcula."):
        exc, hist = variables.cepillado_automatico(_funcion(tipo), d1, et1, z)
        st.session_state[k_ms] = sorted(exc)
        st.session_state["hist_cep"] = hist
    if k_ms not in st.session_state:
        st.session_state[k_ms] = exc_actual
    excluir = c1.multiselect("Puntos excluidos del cálculo (número de punto)", list(range(1, hasta + 1)), key=k_ms,
                             placeholder="Ninguno")
    st.session_state[clave_exc] = excluir
    if st.session_state.get("hist_cep"):
        st.caption("Iteraciones del cepillado: " + " → ".join(str(h) for h in st.session_state["hist_cep"]) +
                   ". Verifique que cada punto excluido tenga una causa asignable; si no la tiene, el módulo "
                   "recomienda concentrarse en el patrón en lugar de eliminar puntos de forma arbitraria.")
    if len(excluir) > max(2, 0.1 * hasta):
        st.warning(f"Se están excluyendo {len(excluir)} puntos. El módulo advierte que eliminar muchos puntos deja "
                   "pocos datos para límites confiables: analice el patrón y la causa común detrás de ellos.")

    res = _funcion(tipo)(d1, et1, z=z, excluir=excluir)
    figs, todas = [], []
    for i, carta in enumerate(res["cartas"]):
        fig, sen = ui.mostrar_carta(carta, excluir=excluir, clave=f"f1_{tipo}_{i}")
        figs.append((f"{carta['nombre']} (Fase I)", fig))
        if len(sen):
            sen.insert(0, "Carta", carta["nombre"])
            todas.append(sen)
    params = ui.tabla_parametros(res["params"])
    lims = res["cartas"][0]
    estilo.kpis([
        dict(icono="target", etiqueta=f"Línea central {lims['nombre']}", valor=f"{lims['lc'][-1]:.5g}"),
        dict(icono="upload", etiqueta="LCS", valor=f"{lims['lcs'][-1]:.5g}", color=estilo.ROJO),
        dict(icono="download", etiqueta="LCI", valor=f"{lims['lci'][-1]:.5g}", color=estilo.ROJO),
        dict(icono="sigma", etiqueta="σ estimada", valor=f"{res['sigma']:.5g}", sub=f"n = {res['n']}", color="#344054"),
        dict(icono="ban", etiqueta="Excluidos", valor=f"{len(excluir)}", sub="por cepillado", color=estilo.SUAVE),
    ])
    st.markdown("**Parámetros y límites de control**")
    st.dataframe(params, hide_index=True, width="stretch")

    senales = pd.concat(todas, ignore_index=True) if todas else pd.DataFrame()
    # para el diagnóstico no se cuentan los puntos que ya fueron excluidos
    activas = senales[senales["_puntos"].apply(lambda p: not set(p) <= set(excluir))] if len(senales) else senales
    concl = []
    orden = ("R" if tipo == "X̄-R" else "S" if tipo == "X̄-S" else "MR")
    concl.append(f"Se analiza primero la carta {orden} porque los límites de la carta de medias dependen de ella "
                 "(módulo 4.7.1.2).")
    if len(activas) == 0:
        concl.append(f"Con {res['params'].get('Subgrupos usados (k)', res['params'].get('Observaciones usadas'))} "
                     "puntos usados, no hay puntos fuera de los límites ni patrones no aleatorios: el proceso está bajo "
                     "control estadístico (sólo causas comunes). Los límites pueden usarse en Fase II.")
        estilo.interpretacion("Diagnóstico automático: proceso bajo control estadístico", [
            concl[-1], concl[0],
            f"Media del proceso X̿ = **{res['media']:.5g}** y σ = **{res['sigma']:.5g}**: pase al paso 7 (Capacidad)."], "ok")
    else:
        lineas = [f"Se detectaron **{len(activas)} señales** de falta de control: el proceso **NO** está bajo control "
                  "estadístico. Hay causas especiales que deben identificarse y eliminarse."]
        for _, f in activas.head(6).iterrows():
            lineas.append(f"**{f.get('Carta', '')} · {f['Regla']}** (puntos {f['Puntos']}): {f['Posibles causas (módulo)']}")
        lineas.append("Anote la causa y la acción de cada señal en la bitácora; luego excluya esos puntos "
                      "(cepillado) y recalcule los límites (módulo 4.5.1).")
        estilo.interpretacion("Diagnóstico automático: proceso fuera de control", lineas, "mal")
        concl.append(f"Se detectaron {len(activas)} señales de falta de control (ver tabla de señales).")
        vista = activas.drop(columns=["_regla", "_puntos"])
        st.dataframe(vista, hide_index=True, width="stretch")
        ui.bitacora(activas, f"var_{tipo}")
    if excluir:
        concl.append(f"Puntos excluidos por cepillado: {sorted(excluir)}.")
    concl.append(f"Estimación de la media del proceso X̿ = {res['media']:.5g} y de la desviación estándar "
                 f"σ = {res['sigma']:.5g} (para capacidad y diseño).")
    st.session_state["fase1_var"] = {"media": res["media"], "sigma": res["sigma"], "n": res["n"], "tipo": tipo,
                                     "en_control": len(activas) == 0, "params": res["params"], "hasta": hasta,
                                     "excluir": list(excluir)}
    bit = st.session_state.get(f"bit_var_{tipo}", {})
    tabla_bit = pd.DataFrame([{"Señal": k, "Causa": v["causa"], "Acción": v["accion"]} for k, v in bit.items()
                              if v.get("causa") or v.get("accion")])
    tablas = [("Parámetros y límites Fase I", params)]
    if len(activas):
        tablas.append(("Señales de falta de control", activas.drop(columns=["_regla", "_puntos"])))
    if len(tabla_bit):
        tablas.append(("Bitácora de causas especiales", tabla_bit))
    ui.boton_registrar(f"m2_f1_{tipo}", "Cartas por variables", f"Carta {tipo} — Fase I", tablas=tablas, figuras=figs,
                       conclusiones=concl)


def _fase2(var, tipo, z):
    f1 = st.session_state.get("fase1_var")
    if not f1 or f1["tipo"] != tipo:
        st.info("Complete primero la Fase I con este mismo tipo de carta.")
        return
    if not f1["en_control"]:
        st.warning("La Fase I todavía muestra señales de falta de control. Lo correcto es estabilizar el proceso "
                   "(o justificar el cepillado) antes de monitorear con estos límites.")
    st.markdown("En Fase II los límites **no se recalculan**: se usan X̿' y σ' de la Fase I (o valores estándar) "
                "para vigilar la producción futura. El tamaño de muestra del monitoreo puede ser distinto al de la "
                "Fase I (módulo 4.7.1, nota sobre n).")
    c1, c2 = st.columns(2)
    media = c1.number_input("X̿' (línea central)", value=float(f1["media"]), format="%.6f")
    sigma = c2.number_input("σ' (desviación estándar del proceso)", value=float(f1["sigma"]), format="%.6f", min_value=1e-12)
    lb = ui.libro()
    fuentes = ["Datos cargados que no se usaron en Fase I", "Subir archivo nuevo"]
    if lb and ui.hojas_de_datos(lb):
        import re
        hay_f2 = any(re.search(r"fase ?(ii|2)|nuevas|monitoreo", h, flags=re.I) and not re.search(r"atribut", h, flags=re.I)
                     for h in ui.hojas_de_datos(lb))
        fuentes.insert(0 if hay_f2 else 2, f"Hoja del libro {lb['nombre']}")
    fuente = st.radio("Muestras nuevas", fuentes, horizontal=True, key="f2v_fuente")
    d, et = _datos_tipo(var, tipo)
    df = None
    if fuente.startswith("Hoja"):
        hojas = ui.hojas_de_datos(lb)
        hoja = st.selectbox("Hoja con las muestras nuevas", hojas, key="f2v_hoja",
                            index=ui.hoja_sugerida(hojas, [r"^(?!.*atribut).*fase ?(ii|2)", r"^(?!.*atribut).*(nuevas|monitoreo)"]))
        df = ui.hoja_df(hoja, lb)
    elif fuente.startswith("Datos cargados"):
        d2, et2 = d[f1["hasta"]:], et[f1["hasta"]:]
        if len(d2) == 0:
            st.info("No quedan datos: en la Fase I reduzca el control deslizante «Datos/subgrupos usados en Fase I».")
            return
    else:
        arch = st.file_uploader("Archivo de Fase II (mismo formato que en Fase I)", type=["csv", "xlsx", "xls"], key="f2v")
        if arch is None:
            return
        df = datos.leer_archivo(arch)
    if df is not None:
        num = [c for c in df.columns if datos.a_numerico(df[c]).notna().mean() > 0.5]
        if tipo == "I-MR":
            cv = st.selectbox("Columna de la medición", num, index=len(num) - 1)
            d2 = datos.a_numerico(df[cv]).dropna().to_numpy(float)
            et2 = list(range(1, len(d2) + 1))
        else:
            from paginas.m1_datos import _raiz_columna
            grupos = {}
            for c in num:
                if c.lower() not in ("subgrupo", "muestra", "orden", "id"):
                    grupos.setdefault(_raiz_columna(c), []).append(c)
            defecto = [c for c in num if c.lower() not in ("subgrupo", "muestra", "orden", "id")]
            if len(grupos) > 1:
                claves = list(grupos)
                base = str(var["nombre"]).lower()
                ini = next((i for i, g in enumerate(claves) if base.startswith(g.lower())), 0)
                g = st.selectbox("Característica (la misma de la Fase I)", claves, index=ini, key="f2v_carac")
                defecto = grupos[g]
            obs = st.multiselect("Columnas de observaciones (cada fila un subgrupo)", num, default=defecto,
                                 key=f"f2v_obs_{'|'.join(defecto)}")
            if not obs:
                return
            d2, et2 = datos.subgrupos_desde_filas(df, obs)
            nm, _ = datos.tamano_constante(d2)
            d2 = [g for g in d2 if len(g) == nm]
            et2 = list(range(1, len(d2) + 1))
    res = variables.fase2(tipo, d2, et2, media, sigma, z)
    st.caption(f"n de monitoreo = {res['n']}")
    figs, todas = [], []
    for i, carta in enumerate(res["cartas"]):
        fig, sen = ui.mostrar_carta(carta, clave=f"f2_{tipo}_{i}")
        figs.append((carta["nombre"], fig))
        if len(sen):
            sen.insert(0, "Carta", carta["nombre"])
            todas.append(sen)
    lim = pd.DataFrame([{"Carta": c["nombre"], "LCI": c["lci"][0], "LC": c["lc"][0], "LCS": c["lcs"][0]}
                        for c in res["cartas"]])
    st.dataframe(lim, hide_index=True)
    concl = [f"Muestras nuevas con n = {res['n']}: se grafican con X̿' = {media:.4g} y σ' = {sigma:.4g} de la Fase I y "
             "los límites para ese mismo n: " + "; ".join(f"{c['nombre']}: LCI = {c['lci'][0]:.4g}, LCS = {c['lcs'][0]:.4g}"
                                                       for c in res["cartas"]) + "."]
    n_plan = (st.session_state.get("plan_muestreo") or {}).get("n")
    if n_plan and int(n_plan) != int(res["n"]):
        st.warning(f"Las muestras nuevas tienen n = {res['n']}, distinto del plan de muestreo (n = {n_plan}). Los límites "
                   f"se calculan para n = {res['n']}; si el monitoreo debe seguir el plan, cargue muestras de n = {n_plan}.")
    if todas:
        sen = pd.concat(todas, ignore_index=True)
        primero = min(min(p) for p in sen["_puntos"])
        st.error(f"Señal de fuera de control en el monitoreo (primer punto con señal: {primero}). Detenga y busque la "
                 "causa asignable.")
        st.dataframe(sen.drop(columns=["_regla", "_puntos"]), hide_index=True, width="stretch")
        ui.bitacora(sen, f"var2_{tipo}")
        concl.append(f"En Fase II se detectaron {len(sen)} señales; la primera en el punto {primero}.")
        tablas = [("Límites Fase II", lim), ("Señales Fase II", sen.drop(columns=["_regla", "_puntos"]))]
    else:
        st.success("Todos los puntos de monitoreo están dentro de los límites y sin patrones: el proceso se mantiene "
                   "bajo control.")
        concl.append(f"En Fase II ({len(d2)} muestras) el proceso se mantiene bajo control estadístico.")
        tablas = [("Límites Fase II", lim)]
    ui.boton_registrar(f"m2_f2_{tipo}", "Fase II", f"Carta {tipo} — Fase II con muestras nuevas", tablas=tablas,
                       figuras=figs, conclusiones=concl)
