"""Módulo 0. Empresa y plan de muestreo (perfil configurable para cualquier empresa)."""
import re

import numpy as np
import pandas as pd
import streamlit as st

from cep import empresa
from paginas import estilo, ui


def perfil_activo():
    if st.session_state.get("perfil") is None:
        st.session_state["perfil"] = empresa.nuevo("Empresa nueva (en blanco)")
    return st.session_state["perfil"]


def render():
    """Vista completa (las tres partes en pestañas)."""
    estilo.encabezado("factory", "Empresa y plan de muestreo", "Perfil de la empresa, etapas del proceso, características de calidad, plan de muestreo y plantillas.", "Módulo 0")
    t1, t2, t3 = st.tabs(["Datos de la empresa y características", "Plan de muestreo", "Plantillas de recolección"])
    with t1:
        empresa_y_caracteristicas()
    with t2:
        plan()
    with t3:
        plantillas()


def _int(v):
    try:
        return int(float(v)) if v not in (None, "") and float(v) >= 1 else None
    except (TypeError, ValueError):
        return None


def _flt(v):
    try:
        return min(max(float(v), 0.25), 12.0) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def render_empresa():
    estilo.encabezado("factory", "Su empresa", "Modelo para llenar sólo los datos de la empresa (misión, visión, procesos, "
                      "productos…). Con ellos se arma el tablero de la empresa.", "Paso 2 · opcional")
    p = perfil_activo()
    if _tiene_empresa(p):
        tablero_empresa(p)
    else:
        estilo.interpretacion("Este paso es opcional", [
            "Descargue el **modelo de ficha**, llene los datos de la empresa y súbalo: el tablero se arma solo.",
            "Puede saltarlo e ir directo al **paso 3 (Datos)**: el análisis funciona sin registrar la empresa."], "info")
    empresa_y_caracteristicas()


def render_plan():
    estilo.encabezado("calendar", "Plan de muestreo", "Se calcula a partir de los datos cargados: tamaño de subgrupo y número de "
                      "subgrupos. Producción y jornada son opcionales.", "Paso 8")
    plan()


TEXTOS_EMPRESA = ["Misión", "Visión", "Política de calidad"]
LISTAS_EMPRESA = ["Productos o servicios", "Clientes / mercados"]


def _tiene_empresa(p):
    return any(str(p.get(k) or "").strip() for k in ["Empresa", "Misión", "Visión", "Etapas del proceso"])


def _lista(texto):
    return [x.strip() for x in re.split(r"[;\n]", str(texto or "")) if x.strip()]


def tablero_empresa(p):
    """Tablero de la empresa: se genera sólo con los datos de la ficha (paso 2)."""
    sub = " · ".join(x for x in [p.get("Sector / producto"), p.get("Ubicación"),
                                  f"NIT {p['NIT']}" if str(p.get("NIT") or "").strip() else ""] if x)
    estilo.cabecera_empresa(p.get("Foto de portada") or None, p.get("Empresa") or "Empresa sin nombre",
                            sub or "Complete la ficha para ver más datos.", "Tablero de la empresa",
                            logo_url=p.get("Logo") or None)
    etapas = estilo.etapas_de_texto(p.get("Etapas del proceso"))
    jornada = (f"{p.get('Hora de inicio de la jornada')}–{p.get('Hora de fin de la jornada')}"
               if p.get("Hora de inicio de la jornada") and p.get("Hora de fin de la jornada") else "—")
    horas = empresa._horas(p.get("Hora de inicio de la jornada"), p.get("Hora de fin de la jornada")) if jornada != "—" else None
    prod = p.get("Producción diaria")
    estilo.kpis([
        dict(icono="refresh-cw", etiqueta="Procesos", valor=f"{len(etapas)}", sub="registrados en la ficha"),
        dict(icono="package", etiqueta="Producción diaria", valor=f"{int(prod):,}".replace(",", ".") if prod else "—",
             sub="unidades por día", color="#344054"),
        dict(icono="timer", etiqueta="Jornada", valor=jornada, sub=f"{horas:g} horas" if horas else "horario",
             color=estilo.NARANJA),
        dict(icono="settings", etiqueta="Producción por hora", valor=f"{prod / horas:.0f}" if (prod and horas) else "—",
             sub="unidades/h (promedio)", color=estilo.DORADO),
        dict(icono="users", etiqueta="Trabajadores", valor=f"{int(p['Número de trabajadores'])}"
             if p.get("Número de trabajadores") else "—", sub="personas", color="#667085"),
    ])
    estilo.tarjetas_texto([("target", "Misión", p.get("Misión"), estilo.VERDE),
                           ("telescope", "Visión", p.get("Visión"), "#344054"),
                           ("circle-check", "Política de calidad", p.get("Política de calidad"), estilo.DORADO)])
    if p.get("Proceso u operación crítica"):
        st.markdown(f"**Proceso que se controla:** {p['Proceso u operación crítica']}")
    if etapas:
        estilo.seccion("refresh-cw", "Procesos de la empresa")
        estilo.flujo_proceso(p)
    c1, c2 = st.columns(2)
    for col, campo, ic in ((c1, "Productos o servicios", "shopping-cart"), (c2, "Clientes / mercados", "users")):
        with col:
            st.markdown(f"**{campo}**")
            items = _lista(p.get(campo))
            if items:
                estilo.chips(items)
            else:
                st.caption("Sin registrar.")


def empresa_y_caracteristicas():
    p = perfil_activo()
    estilo.seccion("folder-open", "A · Cargar la ficha de la empresa (opcional)")
    st.markdown("Descargue el **modelo de ficha**, llene **sólo los datos de la empresa** y súbalo: los campos de abajo "
                "y el tablero se llenan solos. Después puede editarlos.")
    c1, c2, c3 = st.columns([3, 1.2, 1], vertical_alignment="bottom")
    sub = c1.file_uploader("Ficha de empresa (.xlsx) o perfil (.json)", type=["xlsx", "json"])
    c2.download_button("Modelo de ficha (Excel)", empresa.ficha_excel(), file_name="modelo_ficha_empresa.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if c3.button("Empezar en blanco"):
        st.session_state["perfil"] = empresa.nuevo("Empresa nueva (en blanco)")
        st.session_state.pop("perfil_cargado", None)
        st.rerun()
    if sub is not None and st.session_state.get("perfil_cargado") != (sub.name, sub.size):
        try:
            nuevo = (empresa.desde_json(sub.getvalue()) if sub.name.lower().endswith(".json")
                     else empresa.desde_excel(sub.getvalue()))
        except Exception as e:  # noqa: BLE001
            st.error(f"No se pudo leer el archivo: {e}")
        else:
            st.session_state["perfil"] = nuevo
            st.session_state["perfil_cargado"] = (sub.name, sub.size)
            if not sub.name.lower().endswith(".json"):
                ui.guardar_libro(sub.name, sub.getvalue())
            st.rerun()
    if st.session_state.get("perfil_cargado"):
        st.success(f"Información cargada desde «{st.session_state['perfil_cargado'][0]}». Revise y edite abajo.")

    estilo.seccion("building-2", "B · Datos generales")
    c1, c2 = st.columns(2)
    for i, campo in enumerate(["Empresa", "NIT", "Sector / producto", "Ubicación", "Proceso u operación crítica"]):
        p[campo] = (c1 if i % 2 == 0 else c2).text_input(campo, p.get(campo) or "")
    estilo.seccion("image", "Fotografías de la empresa")
    st.caption("Reemplazan las fotografías genéricas del tablero. También se leen de la hoja «Fotos» de la ficha en "
               "Excel (primera imagen: foto de la empresa; segunda: logo).")
    f1, f2, f3 = st.columns([2, 2, 1.2])
    for col, campo, etiqueta in ((f1, "Foto de portada", "Foto de la empresa (planta, equipo, producto)"),
                                 (f2, "Logo", "Logo")):
        arch = col.file_uploader(etiqueta, type=["jpg", "jpeg", "png", "webp"], key=f"img_{campo}")
        if arch is not None and st.session_state.get(f"img_cargada_{campo}") != (arch.name, arch.size):
            try:
                p[campo] = empresa.imagen_data_uri(arch.getvalue(), 600 if campo == "Logo" else 1800)
                st.session_state[f"img_cargada_{campo}"] = (arch.name, arch.size)
            except Exception as e:  # noqa: BLE001
                col.error(f"No se pudo leer la imagen: {e}")
        if p.get(campo):
            col.image(p[campo], width=220 if campo == "Foto de portada" else 90)
    if (p.get("Foto de portada") or p.get("Logo")) and f3.button("Quitar fotografías", width="stretch"):
        p["Foto de portada"], p["Logo"] = "", ""
        for campo in ("Foto de portada", "Logo"):
            st.session_state.pop(f"img_cargada_{campo}", None)
    estilo.seccion("target", "C · Misión, visión y política de calidad")
    for campo in TEXTOS_EMPRESA:
        p[campo] = st.text_area(campo, p.get(campo) or "", height=80)
    estilo.seccion("shopping-cart", "D · Productos y clientes")
    c1, c2 = st.columns(2)
    p["Productos o servicios"] = c1.text_area("Productos o servicios (separados por ;)", p.get("Productos o servicios") or "",
                                             height=80)
    p["Clientes / mercados"] = c2.text_area("Clientes / mercados (separados por ;)", p.get("Clientes / mercados") or "",
                                           height=80)
    estilo.seccion("timer", "E · Operación")
    c1, c2, c3, c4 = st.columns(4)
    p["Hora de inicio de la jornada"] = c1.text_input("Inicio de la jornada (HH:MM)", p.get("Hora de inicio de la jornada") or "",
                                                      placeholder="p. ej. 06:00")
    p["Hora de fin de la jornada"] = c2.text_input("Fin de la jornada (HH:MM)", p.get("Hora de fin de la jornada") or "",
                                                   placeholder="p. ej. 16:00")
    p["Producción diaria"] = c3.number_input("Producción diaria (unidades)", 1, 10_000_000,
                                             _int(p.get("Producción diaria")), placeholder="p. ej. 1400")
    p["Número de trabajadores"] = c4.number_input("Número de trabajadores", 1, 1_000_000,
                                                  _int(p.get("Número de trabajadores")), placeholder="opcional")
    estilo.seccion("refresh-cw", "F · Procesos de la empresa")
    p["Etapas del proceso"] = st.text_area("Procesos en orden (numerados: «1. Proceso: descripción 2. …»)",
                                           p.get("Etapas del proceso", ""), height=110)
    st.session_state["perfil"] = p
    nombre = re.sub(r"[^A-Za-z0-9]+", "_", p.get("Empresa") or "empresa")[:40]
    c1, c2, _ = st.columns([1, 1, 2])
    c1.download_button("Guardar como ficha (Excel)", empresa.ficha_excel(p), file_name=f"ficha_{nombre}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    c2.download_button("Guardar perfil (.json)", empresa.a_json(p), file_name=f"perfil_{nombre}.json",
                       mime="application/json")


def _de_los_datos():
    """Lo que dicen los datos cargados en el paso 3: tipo, nombre, n, subgrupos (m) y total de unidades."""
    var, attr = st.session_state.get("var"), st.session_state.get("attr")
    if var:
        return dict(tipo="variable", nombre=var["nombre"], n=int(var["n"]), m=len(var["grupos"]),
                    total=int(sum(len(g) for g in var["grupos"])))
    if attr:
        n = np.asarray(attr["n"], dtype=float)
        return dict(tipo="atributo", nombre=attr["nombre"], n=max(1, int(round(float(n.mean())))), m=len(n),
                    total=int(n.sum()))
    return None


def plan():
    p = perfil_activo()
    d = _de_los_datos()
    estilo.seccion("folder-open", "1 · Lo que dicen sus datos")
    if d:
        estilo.kpis([
            dict(icono="ruler-dimension-line" if d["tipo"] == "variable" else "hash", etiqueta="Característica", valor=(lambda t: t if len(t) <= 30 else t[:29] + "…")(str(d["nombre"]).split(" (")[0]),
                 sub=f"datos por {d['tipo']}s"),
            dict(icono="puzzle", etiqueta="Tamaño de subgrupo n", valor=f"{d['n']}",
                 sub="unidades por subgrupo" + (" (promedio)" if d["tipo"] == "atributo" else ""), color="#344054"),
            dict(icono="repeat", etiqueta="Subgrupos cargados m", valor=f"{d['m']}", sub="muestras en el archivo",
                 color=estilo.NARANJA),
            dict(icono="package", etiqueta="Unidades inspeccionadas", valor=f"{d['total']:,}".replace(",", "."),
                 sub="n × m", color=estilo.VERDE),
        ])
    else:
        st.info("Aún no hay datos cargados. Cargue su archivo en el **paso 3 (Datos)** y el plan se calcula solo con "
                "el n y el número de subgrupos de sus datos. Mientras tanto puede planear con valores supuestos.")

    estilo.seccion("puzzle", "2 · Tamaño de subgrupo del plan")
    c1, _ = st.columns(2)
    n_plan = int(c1.number_input("Tamaño de subgrupo n del plan", 1, 10_000_000 if d and d["tipo"] == "atributo" else 25,
                                 d["n"] if d else 5, key="plan_n", help="Por defecto, el n de sus datos."))

    estilo.seccion("settings", "3 · Producción y jornada (opcional)")
    tiene_hora = bool(str(p.get("Hora de inicio de la jornada") or "").strip() and str(p.get("Hora de fin de la jornada") or "").strip())
    usar = st.toggle("La empresa tiene datos de producción y jornada", value=bool(p.get("Producción diaria") or p.get("Horas entre subgrupos")
                                or (st.session_state.get("var") or {}).get("t_datos")) or tiene_hora,
                     key="plan_usar_prod",
                     help="Actívelo sólo si conoce la producción diaria y el horario. Sin esto el plan se basa "
                          "únicamente en los datos cargados.")
    lote = h_ini = h_fin = intervalo = None
    if usar:
        st.markdown("Tabla de la presentación de capacidad: **60–300 → 10 %, 301–1000 → 5 %, 1001–5000 → 2 %, "
                    "> 5000 → 1 %**. Si no se produce por lotes, el lote es la producción de un día. "
                    "Llene sólo lo que tenga.")
        c1, c2, c3, c4 = st.columns(4)
        lote = c1.number_input("Producción diaria (unidades)", 1, 10_000_000, _int(p.get("Producción diaria")),
                               key="plan_lote", placeholder="p. ej. 1400")
        h_ini = c2.text_input("Inicio de la jornada (HH:MM)", p.get("Hora de inicio de la jornada") or "",
                              key="plan_hini", placeholder="p. ej. 06:00").strip() or None
        h_fin = c3.text_input("Fin de la jornada (HH:MM)", p.get("Hora de fin de la jornada") or "",
                              key="plan_hfin", placeholder="p. ej. 16:00").strip() or None
        t_datos = (st.session_state.get("var") or {}).get("t_datos")
        intervalo = c4.number_input("Horas entre subgrupos", 0.25, 12.0, _flt(p.get("Horas entre subgrupos") or t_datos), 0.25,
                                    key="plan_t", placeholder="p. ej. 1")
        if lote:
            p["Producción diaria"] = int(lote)
        if h_ini:
            p["Hora de inicio de la jornada"] = h_ini
        if h_fin:
            p["Hora de fin de la jornada"] = h_fin
        if intervalo:
            p["Horas entre subgrupos"] = float(intervalo)

    filas = []
    if d:
        filas += [("Subgrupos cargados m", d["m"]), ("Tamaño de subgrupo n de los datos", d["n"]),
                  ("Unidades inspeccionadas en los datos", d["total"])]
    filas.append(("Tamaño de subgrupo n del plan", n_plan))
    puntos, nivel = [], "info"
    if d:
        puntos.append(f"Sus datos tienen **{d['m']}** subgrupos de n = **{d['n']}** ({d['total']} unidades): "
                      f"el plan toma subgrupos de n = **{n_plan}**.")
    else:
        puntos.append(f"Plan con subgrupos de n = {n_plan}. Cargue datos en el paso 3 para tomar el n de sus datos.")
    pct = None
    if lote:
        pct = empresa.porcentaje_muestreo(lote)
        total = -(-int(pct * lote * 1e6) // 1_000_000)
        filas += [("Producción diaria (tamaño de lote)", int(lote)), ("% a muestrear (tabla de la presentación)", f"{100 * pct:g} %"),
                  ("Unidades a muestrear por día", total)]
    if h_ini and h_fin and intervalo:
        horas = empresa._horas(h_ini, h_fin)
        k = max(1, int(horas // intervalo))
        filas += [("Horas de jornada", f"{horas:g}"), ("Subgrupos por día (uno cada intervalo)", k),
                  ("Unidades del plan por día", n_plan * k)]
        puntos.append(f"Tomar un subgrupo de **{n_plan}** unidades cada **{intervalo:g} h** ({h_ini}–{h_fin}): "
                      f"**{k}** subgrupos y **{n_plan * k}** unidades por día.")
        if lote:
            n_tabla = min(25, max(2, -(-total // k)))
            filas.append(("Tamaño de subgrupo n sugerido por la tabla", n_tabla))
            if n_plan * k >= total:
                puntos.append(f"Se inspecciona {100 * n_plan * k / lote:.1f} % de la producción diaria: **cumple** la "
                              f"tabla ({100 * pct:g} % = {total} unidades/día).")
            else:
                puntos.append(f"Se inspecciona sólo {100 * n_plan * k / lote:.1f} % de la producción diaria: **no "
                              f"alcanza** la tabla ({total} unidades/día); suba n a {n_tabla} o reduzca las horas entre "
                              "subgrupos.")
                nivel = "alerta"
    elif lote:
        puntos.append(f"Según la tabla debe inspeccionar {total} unidades por día ({100 * pct:g} % de {int(lote)}). "
                      "Con el horario y las horas entre subgrupos se calcula cuántos subgrupos tomar por día.")
    elif usar:
        puntos.append("Escriba la producción diaria, el horario y las horas entre subgrupos para completar el plan.")
    puntos.append("En el paso 9 (Fase II) se evalúa este plan (potencia, ARL y ATS) y cuánto se puede aumentar la "
                  "carga muestral para bajar el ATS1 sin salirse de él.")
    tab = pd.DataFrame({"Concepto": [f for f, _ in filas], "Valor": [str(v) for _, v in filas]})

    estilo.seccion("clipboard-list", "4 · Plan resultante")
    st.dataframe(tab, hide_index=True)
    estilo.interpretacion("Plan de muestreo", puntos, nivel)
    horas_j = empresa._horas(h_ini, h_fin) if (h_ini and h_fin) else None
    st.session_state["plan_muestreo"] = {"n": n_plan, "t": intervalo, "horas": horas_j,
                                         "produccion": int(lote) if lote else None,
                                         "min_dia": total if lote else None}
    ui.boton_registrar("m0_plan", "Plan de muestreo", "Plan de muestreo y subgrupos racionales", tablas=[("Plan de muestreo", tab)],
                       conclusiones=[x.replace("**", "") for x in puntos])


def plantillas():
    p = perfil_activo()
    genericas = [{"Característica": "Medición", "Tipo": "Variable", "Unidad": ""},
                 {"Característica": "Defectuosos", "Tipo": "Atributo (defectuosos)", "Unidad": "unidades"},
                 {"Característica": "Defectos", "Tipo": "Atributo (defectos)", "Unidad": "defectos"}]
    vs = p.get("variables") or genericas
    nombres = [v["Característica"] for v in vs]
    elegida = st.selectbox("Característica", nombres,
                           help=None if p.get("variables") else "Plantillas genéricas; si registra la empresa (paso 2) "
                                                                 "aparecen sus propias características.")
    v = vs[nombres.index(elegida)]
    n = st.number_input("Tamaño de subgrupo n (sólo variables)", 1, 25,
                        int(st.session_state.get("plan_muestreo", {}).get("n", 5)))
    st.download_button(f"Plantilla Excel para «{elegida}»", empresa.plantilla_excel(v, int(n), p),
                       file_name=f"plantilla_{re.sub(r'[^A-Za-z0-9]+', '_', elegida)}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption("La plantilla trae una hoja de instrucciones y el formato exacto que lee el paso 3 (Datos).")


def portada_empresa(p):
    """Portada del inicio: texto a la izquierda y fotografía de la empresa (o una industrial genérica) a la derecha."""
    if _tiene_empresa(p):
        titulo = (p.get("Portada: título") or p.get("Empresa")) + "*.*"
        texto = (p.get("Portada: descripción") or p.get("Proceso u operación crítica") or p.get("Misión")
                 or "Control estadístico de procesos con los datos de su planta.")
        etiqueta = p.get("Sector / producto") or "Control estadístico de procesos"
        pie = "Fig. 01 \u2002" + (p.get("Empresa") or "Planta")[:40]
    else:
        titulo = "Del dato de planta a la decisión*.*"
        texto = "Cartas de control, capacidad, Fase II y muestreo de aceptación sobre sus propias mediciones."
        etiqueta = "Control estadístico de procesos"
        pie = "Fig. 01 \u2002Línea de ensamble"
    estilo.hero(titulo, texto, etiqueta, url_foto=p.get("Foto de portada") or None, pie_foto=pie)
