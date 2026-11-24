"""Módulo 4. Validación de supuestos."""
import numpy as np
import pandas as pd
import streamlit as st

from cep import graficos, patrones, supuestos, validacion, variables
from paginas import estilo, ui


def render():
    estilo.encabezado("flask-conical", "Validación de supuestos", "Normalidad, independencia, estabilidad preliminar, patrones no aleatorios y causas especiales.", "Paso 5")
    if not ui.requiere("var", "Cargue una variable en el paso 3 (Datos): la validación de supuestos aplica a datos por variables."):
        return
    var = st.session_state["var"]
    x = np.asarray(var["individuales"], float)
    t1, t2, t3 = st.tabs(["Normalidad (Ji-cuadrada)", "Independencia", "Estabilidad y causas especiales"])
    with t1:
        _normalidad(x, var)
    with t2:
        _independencia(x, var)
    with t3:
        _estabilidad(x, var)


def _normalidad(x, var):
    st.markdown("""**Prueba de bondad de ajuste Ji-cuadrada (módulo 2.6)**
- H0: los datos se ajustan a una distribución normal · H1: no se ajustan.
- k = 1 + 3,3·log10(N) clases; E_i = N·p_i; se unen clases con E_i < 5; ν = k − r − 1 (r = 2).
- Se acepta H0 si χ²_obs ≤ χ²_(α, ν).
- Condiciones: toda clase con E ≥ 5, ν ≥ 1 y al menos 20 datos. **No rechazar H0 no demuestra que los datos sean
  normales:** sólo indica que no hay evidencia suficiente en su contra.""")
    c1, c2 = st.columns(2)
    alfa = c1.number_input("Nivel de significancia α", 0.001, 0.2, 0.05, key="alfa_chi")
    k_auto = supuestos.numero_clases(len(x))
    k = c2.number_input("Número de clases k", 3, 40, k_auto, help=f"Sugerido por la fórmula: {k_auto}")
    try:
        r = supuestos.chi2_normalidad(x, alfa=alfa, k=int(k))
    except validacion.DatosInvalidos as e:
        st.error(str(e))
        st.session_state["normalidad"] = None
        st.session_state["normalidad_estado"] = None
        return
    estilo.kpis([
        dict(icono="hash", etiqueta="Datos N", valor=f"{len(x)}", sub=f"k = {int(k)} clases · h = {r['info']['h']:.4g}"),
        dict(icono="map-pin", etiqueta="Media X̄", valor=f"{r['media']:.5g}", color="#344054"),
        dict(icono="sigma", etiqueta="Desviación S", valor=f"{r['s']:.4g}", color="#667085"),
        dict(icono="χ²", etiqueta="χ² observado", valor=f"{r['chi2_obs']:.3f}", sub=f"ν = {r['gl']} grados de libertad",
             color=estilo.VERDE if r["normal"] else estilo.ROJO),
        dict(icono="ruler-dimension-line", etiqueta=f"χ² crítico (α = {alfa:g})", valor=f"{r['chi2_tabla']:.3f}" if np.isfinite(r["chi2_tabla"]) else "—",
             sub="se acepta H0 si χ²obs ≤ χ²crítico", color=estilo.DORADO),
    ])
    st.markdown("**Condiciones de aplicación**")
    st.dataframe(r["condiciones"], hide_index=True, width="stretch")
    st.markdown("**Clases originales**")
    st.dataframe(r["detalle"], hide_index=True, width="stretch")
    st.markdown("**Clases agrupadas (E ≥ 5) y estadístico**")
    st.dataframe(r["agrupada"], hide_index=True, width="stretch")
    fig = graficos.chi2_barras(r["agrupada"])
    st.plotly_chart(fig, width="stretch")
    fig_h = graficos.histograma_capacidad(x, r["media"], r["s"], nbins=int(k), titulo="Histograma con curva normal ajustada")
    st.plotly_chart(fig_h, width="stretch")
    if r["normal"] is None:
        cierre = ("Sin una prueba aplicable, los %PNC del paso 7 (Capacidad) dependen de suponer la normal: "
                  "reúna más datos antes de darles peso.")
    elif r["normal"]:
        cierre = "Se pueden usar la carta X̄ y los índices de capacidad con la distribución normal."
    else:
        cierre = ("Los %PNC del paso 7 (Capacidad) calculados con la normal deben tomarse con precaución; revise datos "
                  "atípicos o mezcla de poblaciones (estratificación).")
    estilo.interpretacion("Conclusión de la prueba de normalidad", [
        r["conclusion"], *r["advertencias"], f"Forma del histograma: {supuestos.forma_histograma(x)}", cierre],
        "ok" if r["normal"] else "alerta")
    st.session_state["normalidad"] = r["normal"]
    st.session_state["normalidad_estado"] = r["estado"]
    ui.boton_registrar("m4_normal", "Supuestos", "Validación de normalidad (Ji-cuadrada)",
                       tablas=[("Condiciones de aplicación", r["condiciones"]),
                               ("Prueba Ji-cuadrada (clases agrupadas)", r["agrupada"])],
                       figuras=[("Observadas vs esperadas", fig), ("Histograma con normal ajustada", fig_h)],
                       conclusiones=[r["conclusion"], *r["advertencias"], f"Forma del histograma: {supuestos.forma_histograma(x)}"])


def _independencia(x, var):
    st.markdown("""Las cartas de control suponen que las observaciones (o subgrupos) son **independientes**:
el valor de una no depende del de la anterior. Se verifica con:
1. **Diagrama de dispersión** de cada dato contra el siguiente (módulo 2.7.4). Una nube sin forma indica
   independencia; una nube alargada (ascendente o descendente) indica dependencia entre datos consecutivos.
2. **Rachas y tendencias** en el orden de producción (módulo 4.5.2 y 4.5.3): muchas observaciones seguidas a
   un mismo lado de la media o subiendo/bajando sugieren autocorrelación o cambios graduales.""")
    nivel = st.radio("Analizar", ["Datos individuales", "Medias de subgrupo"] if var["n"] > 1 else ["Datos individuales"],
                     horizontal=True)
    serie = x if nivel == "Datos individuales" else np.array([np.mean(g) for g in var["grupos"]])
    a, b = supuestos.pares_consecutivos(serie)
    fig_d = graficos.dispersion_consecutivos(a, b)
    fig_t = graficos.serie_tiempo(serie, "Orden de producción")
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_d, width="stretch")
    c2.plotly_chart(fig_t, width="stretch")
    c = ui.config()
    lc = float(np.median(serie))
    rachas = patrones.analizar(serie, lc, np.inf, -np.inf, k_tendencia=c["k_tend"], k_corrimiento=c["k_corr"],
                               k_estratificacion=10 ** 9, k_mezcla=10 ** 9)
    concl = []
    if len(rachas):
        st.warning("Se encontraron rachas o tendencias que sugieren falta de independencia o cambios graduales:")
        st.dataframe(rachas.drop(columns=["_regla", "_puntos"]), hide_index=True, width="stretch")
        concl.append(f"Se encontraron {len(rachas)} rachas/tendencias en el orden de producción "
                     "(posible dependencia entre datos consecutivos o desplazamientos del proceso).")
    else:
        st.success(f"No hay rachas de {c['k_corr']} o más puntos a un lado de la mediana ni tendencias de "
                   f"{c['k_tend']} o más puntos: no hay evidencia de dependencia en el orden de producción.")
        concl.append("No se encontraron rachas ni tendencias: se acepta el supuesto de independencia.")
    nota = st.text_area("Juicio de ingeniería sobre el diagrama de dispersión (se incluye en el reporte)",
                        "La nube de puntos no muestra una relación clara entre datos consecutivos.")
    concl.append(nota)
    ui.boton_registrar("m4_indep", "Supuestos", "Validación de independencia",
                       tablas=[("Rachas y tendencias", rachas.drop(columns=["_regla", "_puntos"]) if len(rachas) else
                                pd.DataFrame({"Resultado": ["Sin rachas ni tendencias"]}))],
                       figuras=[("Dato t vs dato t+1", fig_d), ("Orden de producción", fig_t)], conclusiones=concl)


def _estabilidad(x, var):
    st.markdown("""**Estabilidad preliminar:** antes de calcular la capacidad, el proceso debe estar bajo control
estadístico (módulo 3.3). Aquí se construye la carta preliminar con todos los datos y se resumen los patrones
no aleatorios (sección 4.5) con sus posibles causas especiales.""")
    z = ui.config()["z"]
    if var["n"] > 1 and var["constante"]:
        res = variables.fase1_xr(var["grupos"], var["etiquetas"], z)
    elif var["n"] > 1:
        g = [gg for gg in var["grupos"] if len(gg) == var["n"]]
        res = variables.fase1_xr(g, list(range(1, len(g) + 1)), z)
    else:
        res = variables.fase1_imr(x, None, z)
    todas, figs = [], []
    for i, carta in enumerate(res["cartas"]):
        fig, sen = ui.mostrar_carta(carta, clave=f"est_{i}")
        figs.append((carta["nombre"] + " preliminar", fig))
        if len(sen):
            sen.insert(0, "Carta", carta["nombre"])
            todas.append(sen)
    concl = []
    if todas:
        s = pd.concat(todas, ignore_index=True)
        st.error(f"El proceso presenta {len(s)} señales: no está en control estadístico en forma preliminar.")
        st.dataframe(s.drop(columns=["_regla", "_puntos"]), hide_index=True, width="stretch")
        st.markdown("**Identificación y justificación de causas especiales** — complete la bitácora:")
        ui.bitacora(s, "estab")
        concl.append(f"Estabilidad preliminar: {len(s)} señales de causas especiales. Deben investigarse y justificarse "
                     "antes de estimar la capacidad.")
        tabla = s.drop(columns=["_regla", "_puntos"])
    else:
        st.success("Sin señales: el proceso es estable en forma preliminar (sólo causas comunes).")
        concl.append("Estabilidad preliminar: sin señales de causas especiales.")
        tabla = pd.DataFrame({"Resultado": ["Sin señales"]})
    st.markdown("**Guía de patrones (módulo 4.5)**")
    st.dataframe(pd.DataFrame({"Patrón": list(patrones.CAUSAS_TIPICAS), "Causas típicas": list(patrones.CAUSAS_TIPICAS.values())}),
                 hide_index=True, width="stretch")
    st.caption("Los patrones cíclicos (4.5.5) se identifican visualmente: picos y valles que se repiten a intervalos "
               "regulares (turnos, días, temperatura).")
    ui.boton_registrar("m4_estab", "Supuestos", "Estabilidad preliminar y causas especiales", tablas=[("Señales", tabla)],
                       figuras=figs, conclusiones=concl)
