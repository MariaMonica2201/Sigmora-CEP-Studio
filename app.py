"""
Sigmora CEP Studio: Software de Control Estadístico de Procesos.

Ejecutar con:   streamlit run app.py

Estructura:
  cep/        Cálculos (sin interfaz): un archivo por tema, documentado con las
              fórmulas de control estadístico de procesos.
  paginas/    Interfaz de cada módulo (0 a 8) y la identidad visual (estilo.py).
  datos_ejemplo/  Datos de prueba de los ejemplos del Módulo Académico.
"""
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cep import atributos, capacidad, constantes, graficos, validacion
from paginas import (estilo, m0_empresa, m1_datos, m2_variables, m3_atributos, m4_supuestos, m5_capacidad, m6_diseno,
                     m7_muestreo, m8_reportes, m9_fase2, m_especificaciones, m_mejores,
                     m_requisitos, ui)

st.set_page_config(page_title="Sigmora CEP Studio · Control Estadístico de Procesos", page_icon=":material/monitoring:", layout="wide",
                   initial_sidebar_state="expanded")
estilo.aplicar()

# Ruta guiada: cada paso dice qué necesita, qué hace y a qué paso se pasa después.
PASOS = [
    dict(clave="1. Requerimientos", icono="clipboard-list", corto="Requisitos", render=m_requisitos.render, opcional=True,
         hecho=lambda ss: "1. Requerimientos" in ss.get("visitados", set()),
         necesita="Nada: es una guía de consulta.",
         hace="Explica qué datos exige cada análisis, los formatos aceptados y ofrece plantillas de recolección.",
         despues="**Paso 2 · Empresa (opcional):** llenar el modelo con los datos de la empresa."),
    dict(clave="2. Empresa", icono="factory", corto="Empresa", render=m0_empresa.render_empresa, opcional=True,
         hecho=lambda ss: bool((ss.get("perfil") or {}).get("Empresa")),
         necesita="Nada obligatorio: el modelo de ficha con los datos de la empresa (opcional).",
         hace="Registra sólo los datos de la empresa (misión, visión, procesos, productos, jornada y producción) y "
              "arma el tablero de la empresa.",
         despues="**Paso 3 · Datos:** cargar las muestras iniciales."),
    dict(clave="3. Datos", icono="folder-open", corto="Datos", render=m1_datos.render,
         hecho=lambda ss: bool(ss.get("var") or ss.get("attr")),
         necesita="Archivo Excel o CSV con las muestras iniciales (mediciones o conteos).",
         hace="Lee, limpia y arma los subgrupos racionales; identifica si es variable o atributo.",
         despues="**Paso 4 · Especificaciones:** LIE, nominal y LSE del cliente."),
    dict(clave="4. Especificaciones", icono="ruler", corto="Especif.", render=m_especificaciones.render,
         hecho=lambda ss: any(v.get("LIE") is not None or v.get("LSE") is not None
                              for v in (ss.get("perfil") or {}).get("variables", [])),
         necesita="La orden o ficha técnica del cliente (o la hoja «Especificaciones» del libro).",
         hace="(1) Especificaciones del cliente y valor nominal; compara sus datos con ellas.",
         despues="**Paso 5 · Supuestos:** normalidad e independencia antes de las cartas."),
    dict(clave="5. Supuestos", icono="flask-conical", corto="Supuestos", render=m4_supuestos.render,
         hecho=lambda ss: ss.get("normalidad_estado") is not None,
         necesita="Datos por variables del paso 3.",
         hace="Prueba Ji-cuadrada de normalidad, independencia y estabilidad preliminar.",
         despues="**Paso 6 · Estabilidad (Fase I):** ¿el proceso está calibrado y estable?"),
    dict(clave="6. Estabilidad (Fase I)", icono="trending-up", corto="Fase I", render=m2_variables.render,
         hecho=lambda ss: bool(ss.get("fase1_var")),
         necesita="Muestras iniciales por variables (paso 3), con los supuestos revisados (paso 5).",
         hace="(2) ¿Está calibrado y estable? Cartas X̄-R o X̄-S (I-MR si n = 1) con las muestras iniciales; patrones "
              "y cepillado. Los límites quedan fijos para la Fase II.",
         despues="**Paso 7 · Capacidad:** con el proceso estable, compararlo con las especificaciones."),
    dict(clave="7. Capacidad", icono="target", corto="Capacidad", render=m5_capacidad.render,
         hecho=lambda ss: bool(ss.get("capacidad")),
         necesita="Proceso estable (paso 6), σ de la Fase I y LIE/LSE (paso 4).",
         hace="(3) Capacidad: Cp, Cpk, Cpu, Cpl, %PNC, intervalos de confianza y escenarios.",
         despues="**Paso 8 · Plan de muestreo:** cuánto y cada cuánto muestrear."),
    dict(clave="8. Plan de muestreo", icono="calendar", corto="Muestreo", render=m0_empresa.render_plan,
         hecho=lambda ss: ss.get("plan_muestreo") is not None,
         necesita="Las muestras iniciales (n y subgrupos); producción y jornada si la empresa las tiene.",
         hace="Plan de las primeras cargas: n, horas entre subgrupos y unidades por día (tabla 10/5/2/1 %).",
         despues="**Paso 9 · Fase II:** monitoreo, potencia y carga muestral."),
    dict(clave="9. Fase II", icono="telescope", corto="Fase II", render=m9_fase2.render,
         hecho=lambda ss: bool(ss.get("plan_fase2")),
         necesita="Límites de la Fase I (paso 6), el plan del paso 8 y las muestras nuevas.",
         hace="(4) Monitoreo con muestras nuevas sobre los límites de la Fase I, (5) potencia para detectar un cambio "
              "en la media y (6) incremento de la carga muestral para bajar el ATS1.",
         despues="**Paso 10 · Atributos:** repetir los pasos 2 a 6 con las cartas p, np, c o u."),
    dict(clave="10. Cartas por atributos", icono="hash", corto="Atributos", render=m3_atributos.render,
         hecho=lambda ss: bool(ss.get("fase1_attr")),
         necesita="Conteos de defectuosos o defectos y n, o datos por variables con LIE/LSE.",
         hace="(7) Atributos repitiendo 2 a 6: estabilidad (Fase I), capacidad, Fase II, potencia y carga muestral.",
         despues="**Paso 11 · Mejores condiciones:** cómo operar y vigilar mejor."),
    dict(clave="11. Mejores condiciones", icono="trophy", corto="Mejores", render=m_mejores.render,
         hecho=lambda ss: "11. Mejores condiciones" in ss.get("visitados", set()),
         necesita="Los resultados de los pasos 4 a 10.",
         hace="(8) Compara la condición actual con la mejor: proceso centrado en el nominal, plan con menor ATS1 y "
              "causas vitales a atacar.",
         despues="**Paso 12 · Muestreo de aceptación** para los lotes."),
    dict(clave="12. Muestreo de aceptación", icono="package", corto="Aceptación", render=m7_muestreo.render,
         hecho=lambda ss: "12. Muestreo de aceptación" in ss.get("visitados", set()),
         necesita="Tamaño de lote, NCA, NCL y riesgos α y β.",
         hace="Planes simple y doble, curva OC, AOQ/AOQL y MIL-STD-105E.",
         despues="**Paso 13 · Informe:** exportar los resultados."),
    dict(clave="13. Informe", icono="file-text", corto="Informe", render=m8_reportes.render,
         hecho=lambda ss: bool(ss.get("reporte")),
         necesita="Las secciones que agregó en cada paso con «Agregar al reporte».",
         hace="Reúne tablas, gráficos y conclusiones y los exporta a Excel e informe HTML.",
         despues="Presentar el informe y seguir la Fase II con nuevas muestras."),
]
INICIO = "Inicio"
OPCIONES = [INICIO] + [p["clave"] for p in PASOS]
ICONOS = {INICIO: "house", **{p["clave"]: p["icono"] for p in PASOS}}


def ir_a(clave):
    st.session_state["nav"] = clave


CORTOS = {INICIO: "Inicio", **{p["clave"]: p["corto"] for p in PASOS}}

perfil = m0_empresa.perfil_activo()
var, attr = st.session_state.get("var"), st.session_state.get("attr")

def _hechos():
    return {i for i, p in enumerate(PASOS) if p["hecho"](st.session_state)}


# ---------------------------------------------------- barra lateral: marca y los 13 pasos con su estado
_HECHOS_NAV = _hechos()


def _etiqueta_nav(k):
    """Etiqueta fija de cada paso. El estado (listo / pendiente) se dibuja con CSS: si la etiqueta cambiara,
    Streamlit recrearía el radio y la navegación volvería al inicio."""
    if k == INICIO:
        return "`00` Inicio"
    i = OPCIONES.index(k) - 1
    return f"`{i + 1:02d}` {PASOS[i]['corto']}"


def _css_estado_nav():
    reglas = [f'.st-key-nav [role="radiogroup"] > div:nth-child({i + 2}) p::after{{content:"\\25A0";color:var(--ok);}}'
              for i in _HECHOS_NAV]
    reglas.insert(0, '.st-key-nav [role="radiogroup"] > div:not(:first-child) p::after{content:"\\25A1";color:var(--tenue);'
                     'margin-left:auto;font-size:.62rem;}')
    return "<style>" + "".join(reglas) + "</style>"


with st.sidebar:
    st.markdown(estilo.marca_html() + _css_estado_nav(), unsafe_allow_html=True)
    st.markdown('<div class="cep-lab cep-side-lab">Ruta de trabajo</div>', unsafe_allow_html=True)
    eleccion = st.radio("Navegación", OPCIONES, key="nav", label_visibility="collapsed", format_func=_etiqueta_nav)

# ---------------------------------------------------- barra superior: datos activos y ajustes
with st.container(key="topbar"):
    c_meta, c_conf = st.columns([14, 1], vertical_alignment="center")
    with c_conf.popover("", icon=":material/tune:", help="Ajustes", width="stretch"):
        st.markdown(f"**{perfil.get('Empresa') or 'Empresa sin nombre'}**")
        st.caption(" · ".join(x for x in [f"Variable «{var['nombre']}» ({len(var['grupos'])} subgrupos)" if var else "",
                                           f"Atributo «{attr['nombre']}» ({len(attr['conteo'])} muestras)" if attr else ""]
                              if x) or "Sin datos activos: cárguelos en el paso 3.")
        st.divider()
        ui.barra_lateral_config(st)
    _z = (st.session_state.get("config") or {}).get("z", 3.0)
    _meta = []
    if var:
        _meta.append(f'<span><span class="sq"></span>{estilo._e(var["nombre"])}</span>'
                     f'<span>n <b>{var["n"]}</b></span><span>k <b>{len(var["grupos"])}</b></span>')
    if attr:
        _meta.append(f'<span><span class="sq"></span>{estilo._e(attr["nombre"])}</span>'
                     f'<span>muestras <b>{len(attr["conteo"])}</b></span>')
    if not _meta:
        _meta.append('<span><span class="sq no"></span>Sin datos activos</span>')
    _meta.append(f'<span>Z<sub>α/2</sub> <b>{_z:.2f}</b></span>')
    if perfil.get("Empresa"):
        _meta.append(f'<span style="margin-left:auto">{estilo._e(perfil["Empresa"])}</span>')
    c_meta.markdown(f'<div class="cep-meta">{"".join(_meta)}</div>', unsafe_allow_html=True)
st.session_state.setdefault("visitados", set()).add(eleccion)


def _barra_navegacion(i, abajo=False):
    c1, c2, c3 = st.columns([1, 3, 1])
    if i > 0:
        c1.button(PASOS[i - 1]['corto'], icon=":material/arrow_back:", on_click=ir_a, args=(PASOS[i - 1]["clave"],), key=f"ant_{abajo}",
                  width="stretch")
    else:
        c1.button("Inicio", icon=":material/arrow_back:", on_click=ir_a, args=(INICIO,), key=f"ant_{abajo}", width="stretch")
    if abajo:
        c2.markdown(f"<div class='cep-lab' style='text-align:center;padding-top:.6rem'>"
                    f"{i + 1:02d} / {len(PASOS)}</div>", unsafe_allow_html=True)
    if i < len(PASOS) - 1:
        c3.button(PASOS[i + 1]['corto'], icon=":material/arrow_forward:", icon_position="right", on_click=ir_a, args=(PASOS[i + 1]["clave"],), key=f"sig_{abajo}",
                  type="primary", width="stretch")


def _tablero_datos():
    """Resumen que se genera solo a partir de los datos cargados en el paso 3 (variables y/o atributos)."""
    var, attr = st.session_state.get("var"), st.session_state.get("attr")
    if not (var or attr):
        return
    estilo.titulo_seccion("Sus datos", "Resumen generado a partir de lo que cargó",
                          f"Fuente: {st.session_state.get('df_nombre') or 'datos cargados'}.")
    figs = []
    if var:
        x = np.asarray(var["individuales"], float)
        medias = [float(np.mean(g)) for g in var["grupos"]]
        estilo.kpis([
            dict(icono="ruler-dimension-line", etiqueta="Característica", valor=str(var["nombre"])[:22], sub="datos por variables"),
            dict(icono="repeat", etiqueta="Subgrupos m", valor=f"{len(var['grupos'])}", sub=f"de n = {var['n']}",
                 color="#344054"),
            dict(icono="hash", etiqueta="Datos N", valor=f"{len(x)}", color=estilo.NARANJA),
            dict(icono="map-pin", etiqueta="Media X̄", valor=f"{x.mean():.5g}", color=estilo.VERDE),
            dict(icono="sigma", etiqueta="Desviación S", valor=f"{x.std(ddof=1):.4g}" if len(x) > 1 else "—",
                 color="#667085"),
            dict(icono="move-horizontal", etiqueta="Mínimo – máximo", valor=f"{x.min():.4g} – {x.max():.4g}", color=estilo.DORADO),
        ])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(1, len(medias) + 1)), y=medias, mode="lines+markers",
                                 name="Media del subgrupo" if var["n"] > 1 else "Dato",
                                 line=dict(color="#344054", width=2.5), marker=dict(size=8)))
        fig.add_hline(y=float(x.mean()), line=dict(color=graficos.VERDE, width=2, dash="dash"),
                      annotation_text=f"X̄ = {x.mean():.4g}")
        fig.update_layout(title=f"{var['nombre']}: " + ("media de cada subgrupo" if var["n"] > 1 else "datos en orden"),
                          height=340, xaxis_title="Subgrupo", showlegend=False)
        figs.append(fig)
    if attr:
        conteo, n = np.asarray(attr["conteo"], float), np.asarray(attr["n"], float)
        tasa = conteo / n
        simb = "p" if attr["que"] == "defectuosos" else "u"
        estilo.kpis([
            dict(icono="hash", etiqueta="Característica", valor=str(attr["nombre"])[:22], sub=f"{attr['que']}"),
            dict(icono="repeat", etiqueta="Muestras", valor=f"{len(conteo)}", color="#344054"),
            dict(icono="package", etiqueta="Total inspeccionado Σn", valor=f"{n.sum():,.0f}".replace(",", "."),
                 color=estilo.NARANJA),
            dict(icono="circle-x", etiqueta=f"Total {attr['que']}", valor=f"{conteo.sum():,.0f}".replace(",", "."),
                 color=estilo.ROJO),
            dict(icono="chart-column", etiqueta=f"{simb}̄ global", valor=f"{conteo.sum() / n.sum():.4f}", color=estilo.DORADO),
        ])
        fig = go.Figure(go.Bar(x=list(range(1, len(tasa) + 1)), y=tasa, marker_color="rgba(180,35,24,0.7)",
                               name=f"{simb} por muestra"))
        fig.add_hline(y=float(conteo.sum() / n.sum()), line=dict(color=graficos.TEXTO, width=2, dash="dash"),
                      annotation_text=f"{simb}̄ = {conteo.sum() / n.sum():.4f}")
        fig.update_layout(title=f"{attr['nombre']}: {simb} por muestra", height=340, xaxis_title="Muestra",
                          showlegend=False)
        figs.append(fig)
    for col, fig in zip(st.columns(len(figs)), figs):
        col.plotly_chart(fig, width="stretch")


def _tablero_analisis():
    f1v, cap = st.session_state.get("fase1_var"), st.session_state.get("capacidad")
    if not (var or attr):
        return
    estilo.titulo_seccion("Resultados", "Análisis activo", "Resumen de los datos y resultados que ya calculó.")
    items = []
    if var:
        x = np.asarray(var["individuales"], float)
        items += [dict(icono="ruler-dimension-line", etiqueta=var["nombre"][:28], valor=f"{x.mean():.4g}", sub=f"media de {len(x)} datos"),
                  dict(icono="move-horizontal", etiqueta="Desviación estándar", valor=f"{x.std(ddof=1):.4g}" if len(x) > 1 else "—",
                       sub="muestral (S)", color="#344054")]
    if f1v:
        items.append(dict(icono="circle-check" if f1v["en_control"] else "triangle-alert", etiqueta=f"Fase I {f1v['tipo']}",
                          valor="Bajo control" if f1v["en_control"] else "Con señales",
                          sub=f"σ estimada = {f1v['sigma']:.4g}",
                          color=estilo.VERDE if f1v["en_control"] else estilo.ROJO))
    if attr:
        pb = float(np.sum(attr["conteo"]) / np.sum(attr["n"])) if attr["que"] == "defectuosos" else None
        items.append(dict(icono="hash", etiqueta=attr["nombre"][:28],
                          valor=f"{100 * pb:.2f} %" if pb is not None else f"{np.mean(attr['conteo']):.3g}",
                          sub="proporción promedio p̄" if pb is not None else "defectos promedio", color=estilo.NARANJA))
    estilo.kpis(items)
    if cap:
        r = capacidad.indices(cap["media"], cap["sigma"], cap["lse"], cap["lie"])
        cols = st.columns(3)
        for col, k in zip(cols, ["Cp", "Cpk"]):
            if k in r and np.isfinite(r[k]):
                col.plotly_chart(graficos.medidor(r[k], k, ayuda="marca en 1,33"), width="stretch", key=f"g_{k}")


def _cifras_inicio():
    """Franja de cifras del inicio: se arma con los datos y resultados ya calculados."""
    f1v, cap, pf2 = st.session_state.get("fase1_var"), st.session_state.get("capacidad"), st.session_state.get("plan_fase2")
    c = []
    if var:
        x = np.asarray(var["individuales"], float)
        c.append((f"{x.mean():.3f}", "Media X̄", f"N = {len(x)} · k = {len(var['grupos'])}"))
        if f1v:
            c.append((f"{f1v['sigma']:.3f}", "σ estimada", f"Fase I {f1v['tipo']}"))
            c.append(("Bajo control" if f1v["en_control"] else "Con señales", "Estabilidad", "Fase I",
                      estilo.VERDE if f1v["en_control"] else estilo.ROJO))
        elif len(x) > 1:
            c.append((f"{x.std(ddof=1):.3f}", "Desviación S", "muestral"))
    if cap:
        r = capacidad.indices(cap["media"], cap["sigma"], cap["lse"], cap["lie"])
        for k in ("Cp", "Cpk"):
            if k in r and np.isfinite(r[k]):
                c.append((f"{r[k]:.2f}", k, "capacidad", estilo.ACENTO if k == "Cpk" else None))
        if np.isfinite(r.get("PPM no conformes", np.nan)):
            c.append((f"{r['PPM no conformes']:.0f}", "PPM", "fuera de especificación"))
    if pf2:
        c.append((f"{pf2['ATS1']:.2f} h", "ATS1", f"n = {pf2['n']} cada {pf2['t']:g} h"))
    if attr:
        conteo, n = np.asarray(attr["conteo"], float), np.asarray(attr["n"], float)
        simb = "p̄" if attr["que"] == "defectuosos" else "ū"
        c.append((f"{conteo.sum() / n.sum():.4f}", simb, f"{len(conteo)} muestras"))
    return c or [("13", "Pasos", "de los datos al informe"), ("I · II", "Fases", "cartas de control"),
                 ("Cp · Cpk", "Capacidad", "con LIE y LSE"), ("ARL · ATS", "Diseño", "potencia y carga muestral"),
                 ("MIL-STD", "Aceptación", "105E, simple y doble")]


def _detalle_paso(i):
    """Texto corto de la fila del índice: un resultado si ya existe; si no, lo que hace el paso."""
    ss = st.session_state
    f1v, cap = ss.get("fase1_var"), ss.get("capacidad")
    if i == 2 and var:
        return f"{len(var['individuales'])} datos · {len(var['grupos'])} subgrupos de n = {var['n']}"
    if i == 5 and f1v:
        return f"{f1v['tipo']} {'bajo control' if f1v['en_control'] else 'con señales'}"
    if i == 6 and cap:
        try:
            r = capacidad.indices(cap["media"], cap["sigma"], cap["lse"], cap["lie"])
        except validacion.DatosInvalidos:
            return BREVE[i]
        return " · ".join(f"{k} {r[k]:.2f}" for k in ("Cp", "Cpk") if k in r and np.isfinite(r[k]))
    if i == 7 and ss.get("plan_muestreo"):
        pm = ss["plan_muestreo"]
        return f"n = {pm.get('n')}" + (f" cada {pm['t']:g} h" if pm.get("t") else "")
    if i == 8 and ss.get("plan_fase2"):
        p2 = ss["plan_fase2"]
        return f"n = {p2['n']} · ATS1 {p2['ATS1']:.2f} h"
    if i == 9 and ss.get("fase1_attr"):
        return f"Carta {ss['fase1_attr'].get('tipo', '')}".strip()
    return BREVE[i]


BREVE = ["Formatos y plantillas", "Ficha, misión y procesos", "Excel o CSV, subgrupos racionales",
         "LIE, nominal y LSE", "Normalidad e independencia", "X̄-R, X̄-S o I-MR", "Cp, Cpk, %PNC",
         "n, frecuencia y unidades por día", "Monitoreo, potencia y ATS1", "Cartas p, np, c y u",
         "Proceso centrado y mejor plan", "Simple, doble y MIL-STD-105E", "HTML y Excel"]


def inicio():
    m0_empresa.portada_empresa(perfil)
    estilo.franja(_cifras_inicio())
    hechos = _hechos()
    sig = next((p for i, p in enumerate(PASOS) if i not in hechos and not p.get("opcional")), PASOS[-1])
    i_sig = PASOS.index(sig)
    filas = [(k + 1, p["clave"].split(". ", 1)[1], _detalle_paso(k),
              "ok" if k in hechos else ("act" if k == i_sig else ""),
              "listo" if k in hechos else ("siguiente" if k == i_sig else ("opcional" if p.get("opcional") else "pendiente")))
             for k, p in enumerate(PASOS)]
    estilo.indice_pasos("Trece pasos, cada uno usa el resultado del anterior.",
                        f"**{len(hechos)} de {len(PASOS)}** completos. Siguiente: **{sig['clave']}**.", filas)
    st.write("")
    c1, c2, c3, _ = st.columns([1.2, 1.2, 1.4, 3], vertical_alignment="center")
    c1.button(f"Continuar: {sig['corto']}", icon=":material/arrow_forward:", icon_position="right", type="primary",
              on_click=ir_a, args=(sig["clave"],), width="stretch")
    c2.button("Cargar datos", on_click=ir_a, args=(PASOS[2]["clave"],), width="stretch", key="ini_datos")
    c3.button("Registrar la empresa (opcional)", on_click=ir_a, args=(PASOS[1]["clave"],), width="stretch")

    if m0_empresa._tiene_empresa(perfil):
        estilo.titulo_seccion("Empresa", "Tablero de la empresa")
        m0_empresa.tablero_empresa(perfil)
    _tablero_datos()
    _tablero_analisis()
    estilo.banda("planta", "Fig. 02  Método", "Primero estabilidad, después capacidad.",
                 "Los límites de la Fase I quedan fijos; con ellos se vigilan las muestras nuevas y se diseña "
                 "el plan de la Fase II.")
    st.write("")
    with st.expander("Tabla de constantes para cartas por variables (Tabla 1 del módulo)"):
        st.dataframe(constantes.tabla_dataframe(), hide_index=True)


if eleccion == INICIO:
    inicio()
else:
    i = OPCIONES.index(eleccion) - 1
    paso = PASOS[i]


    def _tras_encabezado(i=i, paso=paso):
        estilo.guia_paso(paso["necesita"], paso["hace"], paso["despues"])
        _barra_navegacion(i)

    estilo.PASO_TEXTO = f"{i + 1:02d} / {paso['clave'].split('. ', 1)[1]}" + (" · opcional" if paso.get("opcional") else "")
    estilo.DESPUES_ENCABEZADO = _tras_encabezado
    try:
        paso["render"]()
    except validacion.DatosInvalidos as e:
        # los cálculos rechazan datos sin sentido con un mensaje claro en lugar de un error técnico
        st.error(f"No se puede calcular con estos datos. {e}")
    estilo.DESPUES_ENCABEZADO, estilo.PASO_TEXTO = None, ""
    st.write("")
    _barra_navegacion(i, abajo=True)
estilo.pie(perfil.get("Empresa") or "", [p["clave"] for p in PASOS])
