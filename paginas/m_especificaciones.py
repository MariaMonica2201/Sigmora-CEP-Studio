"""Paso 4. Especificaciones del cliente: LIE, valor nominal y LSE de cada característica."""
import io

import numpy as np
import pandas as pd
import streamlit as st

from cep import capacidad, empresa
from paginas import estilo, m0_empresa, ui

ESP = ("LIE", "Nominal", "LSE")


def _num(v):
    try:
        return float(str(v).strip().replace(",", ".")) if str(v).strip() not in ("", "None", "nan") else None
    except ValueError:
        return None


def render():
    estilo.encabezado("ruler", "Especificaciones del cliente", "Límites de especificación (LIE, LSE) y valor nominal de "
                      "cada característica: contra ellos se mide la capacidad y se buscan las mejores condiciones.",
                      "Paso 4")
    p = m0_empresa.perfil_activo()
    st.markdown("Escriba lo que pide el **cliente** (orden de producción o ficha técnica): **LIE**, **valor nominal** "
                "(el objetivo) y **LSE**. Si el libro de datos trae la hoja **«Especificaciones»**, la tabla ya viene "
                "llena. Deje vacío lo que no aplique (por ejemplo, sólo un peso mínimo → sólo LIE).")
    var = st.session_state.get("var")
    if var and not empresa.buscar_variable(p, var["nombre"]):
        p.setdefault("variables", []).append({"Característica": str(var["nombre"]).split(" (")[0], "Unidad": "",
                                              "Tipo": "Variable", "LIE": None, "Nominal": None, "LSE": None})
    df = empresa.variables_df(p)
    for c in ESP:  # como texto: las celdas vacías se ven en blanco (no «None»)
        df[c] = pd.Series([("" if pd.isna(v) else f"{v:g}") for v in df[c]], index=df.index, dtype="object")
    df = df.fillna("")
    ed = st.data_editor(df, num_rows="dynamic", width="stretch", key="ed_esp", column_config={
        "Tipo": st.column_config.SelectboxColumn(options=["Variable", "Atributo (defectuosos)", "Atributo (defectos)"]),
        **{c: st.column_config.TextColumn(c, help="Número; déjelo vacío si no aplica.") for c in ESP}})
    p["variables"] = [{k: (_num(v) if k in ESP else (None if v is None or (isinstance(v, float) and np.isnan(v))
                                                     or str(v) == "" else v)) for k, v in r.items()}
                      for r in ed.to_dict("records") if str(r.get("Característica") or "").strip()]
    st.session_state["perfil"] = p
    errores = [v["Característica"] for v in p["variables"] if v.get("LIE") is not None and v.get("LSE") is not None
               and v["LIE"] >= v["LSE"]]
    if errores:
        st.error("El LIE debe ser menor que el LSE en: " + ", ".join(errores))
    buf = io.BytesIO()
    empresa.variables_df(p).to_excel(buf, index=False, sheet_name="Especificaciones")
    st.download_button("Descargar especificaciones (Excel)", buf.getvalue(), file_name="especificaciones.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if not var:
        st.info("Cargue las muestras iniciales en el paso 3 para comparar sus datos con las especificaciones.")
        return
    pv = empresa.buscar_variable(p, var["nombre"])
    lie, nom, lse = empresa.especificaciones(pv)
    x = np.asarray(var["individuales"], float)
    estilo.seccion("search", f"Sus datos frente a las especificaciones · {var['nombre']}")
    if lie is None and lse is None:
        st.info("Escriba arriba el LIE y/o el LSE de esta característica.")
        return
    if nom is None and lie is not None and lse is not None:
        nom = (lie + lse) / 2
        st.caption(f"Sin valor nominal: se usa el centro de la tolerancia (LIE + LSE)/2 = {nom:g}.")
    fuera = int(np.sum((x < lie) if lie is not None else 0) + np.sum((x > lse) if lse is not None else 0))
    s = float(np.std(x, ddof=1)) if len(x) > 1 else float("nan")
    items = [dict(icono="map-pin", etiqueta="Media de los datos X̄", valor=f"{x.mean():.4g}", sub=f"{len(x)} datos"),
             dict(icono="target", etiqueta="Valor nominal", valor=f"{nom:g}" if nom is not None else "—",
                  sub="objetivo del cliente", color="#344054"),
             dict(icono="move-horizontal", etiqueta="Especificación", valor=f"{lie if lie is not None else '—'} – "
                  f"{lse if lse is not None else '—'}", sub="LIE – LSE", color=estilo.NARANJA),
             dict(icono="circle-x", etiqueta="Datos fuera de especificación", valor=f"{fuera}",
                  sub=f"{100 * fuera / len(x):.2f} % de los datos", color=estilo.ROJO if fuera else estilo.VERDE)]
    estilo.kpis(items)
    puntos = []
    if nom is not None and np.isfinite(s) and s > 0:
        desv = (x.mean() - nom) / s
        puntos.append(f"La media está a {x.mean() - nom:+.4g} del valor nominal ({desv:+.2f} desviaciones estándar).")
        puntos.append("Si la media coincide con el nominal el proceso está **centrado**; si no, hay un "
                      "**descentramiento** que baja el Cpk (paso 7) y que se corrige en «Mejores condiciones» (paso 11).")
        if lie is not None or lse is not None:
            r_act = capacidad.indices(float(x.mean()), s, lse, lie)
            puntos.append(f"Referencia rápida con S de los datos: %PNC estimado = {100 * r_act['%PNC total']:.4f} %. "
                          "La capacidad oficial se calcula en el paso 7 con la σ de la Fase I.")
    puntos.append("Que el proceso sea **estable** (calibrado, sólo causas comunes) se verifica en el paso 6 con las "
                  "cartas de Fase I.")
    estilo.interpretacion("Lectura", puntos, "info")
    tabla = pd.DataFrame({"Concepto": ["Característica", "LIE", "Nominal", "LSE", "Media de los datos", "Datos fuera"],
                          "Valor": [str(v) if v is not None else "—" for v in
                                    (var["nombre"], lie, nom, lse, round(float(x.mean()), 5), fuera)]})
    ui.boton_registrar("m_esp", "Especificaciones", "Especificaciones del cliente y valor nominal",
                       tablas=[("Especificaciones", empresa.variables_df(p)), ("Datos frente a especificaciones", tabla)],
                       conclusiones=[t.replace("**", "") for t in puntos])
