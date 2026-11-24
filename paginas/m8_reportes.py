"""Módulo 8. Reportes."""
import datetime as dt

import streamlit as st

from cep import reporte
from paginas import estilo, ui


def render():
    estilo.encabezado("file-text", "Reportes", "Reúne tablas, gráficos y conclusiones de cada módulo y los exporta a Excel e informe HTML.", "Paso 13")
    with st.expander("Datos generales del estudio", expanded=True):
        c1, c2 = st.columns(2)
        g = ui.estado("datos_generales", {})
        perfil, plan = st.session_state.get("perfil") or {}, st.session_state.get("plan_muestreo")
        g.setdefault("Empresa", perfil.get("Empresa", ""))
        g.setdefault("Proceso / operación crítica", perfil.get("Proceso u operación crítica", ""))
        g.setdefault("Producto", perfil.get("Sector / producto", ""))
        if plan:
            g.setdefault("Plan de muestreo (subgrupo, frecuencia)", f"n = {plan['n']}" + (f" cada {plan['t']:g} h" if plan.get("t") else ""))
        g["Empresa"] = c1.text_input("Empresa (puede anonimizarse)", g.get("Empresa", ""))
        g["Proceso / operación crítica"] = c2.text_input("Proceso / operación crítica", g.get("Proceso / operación crítica", ""))
        g["Producto"] = c1.text_input("Producto", g.get("Producto", ""))
        g["Variable de calidad"] = c2.text_input("Variable de calidad", g.get("Variable de calidad", st.session_state.get("nombre_var", "")))
        g["Plan de muestreo (subgrupo, frecuencia)"] = c1.text_input("Plan de muestreo (tamaño de subgrupo y frecuencia)",
                                                                     g.get("Plan de muestreo (subgrupo, frecuencia)", ""))
        g["Equipo"] = c2.text_input("Equipo desarrollador", g.get("Equipo", ""))
        g["Fecha"] = c1.text_input("Fecha", g.get("Fecha", dt.date.today().isoformat()))
        st.session_state["datos_generales"] = g

    rep = ui.estado("reporte", {})
    var = st.session_state.get("var")
    if var is not None:  # la carta I-MR sólo aplica con n = 1; X̄-R / X̄-S sólo con n ≥ 2
        no_aplica = [k for k in rep if k.startswith("m2_") and (("I-MR" in k) == (var["n"] > 1))]
        for k in no_aplica:
            del rep[k]
    if not rep:
        st.info("Aún no hay secciones. En cada paso use el botón «Agregar / actualizar en el reporte».")
        return
    pasos = ["Datos", "Especificaciones", "Supuestos", "Cartas por variables", "Capacidad", "Plan de muestreo",
             "Fase II", "Diseño", "Cartas por atributos", "Mejores condiciones", "Muestreo de aceptación"]
    orden = sorted(rep.items(), key=lambda kv: (pasos.index(kv[1]["modulo"]) if kv[1]["modulo"] in pasos else 99,
                                                kv[1]["modulo"]))
    elegidas = []
    st.markdown("**Secciones disponibles**")
    for clave, s in orden:
        c1, c2 = st.columns([6, 1])
        if c1.checkbox(f"{s['modulo']} — {s['titulo']}  ({len(s['tablas'])} tablas, {len(s['figuras'])} figuras)",
                       True, key=f"chk_{clave}"):
            elegidas.append(s)
        if c2.button("Quitar", key=f"del_{clave}", help="Quitar del reporte"):
            del rep[clave]
            st.rerun()
    notas = st.text_area("Conclusiones generales y propuestas de mejora (juicio de ingeniería del equipo)",
                         st.session_state.get("notas_finales", ""), height=150)
    st.session_state["notas_finales"] = notas
    secciones = list(elegidas)
    if notas.strip():
        secciones.append(reporte.nueva_seccion("Conclusiones", "Conclusiones generales y propuestas de mejora",
                                               conclusiones=[t for t in notas.splitlines() if t.strip()]))
    c1, c2 = st.columns(2)
    c1.download_button("Descargar Excel (tablas)", reporte.a_excel(secciones, g),
                       file_name="reporte_CEP.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    c2.download_button("Descargar informe HTML (tablas + gráficos)", reporte.a_html(secciones, g, foto_portada=(st.session_state.get("perfil") or {}).get("Foto de portada")),
                       file_name="informe_CEP.html", mime="text/html", type="primary")
    st.caption("El informe HTML se abre sin internet en cualquier navegador; desde allí puede imprimirse a PDF. "
               "Las tablas y figuras salen numeradas para citarlas en el informe APA. Cada gráfico de la app "
               "también puede descargarse como PNG con la cámara de la barra del gráfico.")
    st.divider()
    st.subheader("Vista previa")
    nt = nf = 0
    for s in secciones:
        st.markdown(f"### {s['modulo']} — {s['titulo']}")
        for nombre, df in s["tablas"]:
            nt += 1
            st.markdown(f"*Tabla {nt}. {nombre}*")
            st.dataframe(df, hide_index=True, width="stretch")
        for nombre, fig in s["figuras"]:
            nf += 1
            st.markdown(f"*Figura {nf}. {nombre}*")
            st.plotly_chart(fig, width="stretch", key=f"prev_{nf}_{s['titulo']}")
        for c in s["conclusiones"]:
            st.write("• " + c)
