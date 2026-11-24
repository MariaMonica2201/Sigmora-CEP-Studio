"""
Prueba automática del recorrido completo de la aplicación (Streamlit AppTest):
navegación por los 13 pasos, carga de datos (ejemplo del módulo y libro Excel), estados
de cada paso, mensajes de datos inválidos y generación de los informes Excel y HTML.

No abre un navegador: ejecuta app.py como lo haría Streamlit y revisa lo que muestra.
"""
import io
import os

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from cep import reporte

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(RAIZ, "app.py")

PASOS = ["1. Requerimientos", "2. Empresa", "3. Datos", "4. Especificaciones", "5. Supuestos",
         "6. Estabilidad (Fase I)", "7. Capacidad", "8. Plan de muestreo", "9. Fase II",
         "10. Cartas por atributos", "11. Mejores condiciones", "12. Muestreo de aceptación", "13. Informe"]


def nueva_app():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    return at


def ir(at, paso):
    at.radio(key="nav").set_value(paso).run()
    sin_excepciones(at, paso)
    return at


def sin_excepciones(at, donde=""):
    assert not at.exception, f"{donde}: " + " | ".join(e.message for e in at.exception)


def radio(at, etiqueta):
    return next(r for r in at.radio if r.label == etiqueta)


def boton(at, etiqueta):
    return next(b for b in at.button if b.label == etiqueta)


def registrar_todo(at, donde):
    """Pulsa todos los botones «Agregar / actualizar en el reporte» del paso actual."""
    claves = [b.key for b in at.button if b.key and b.key.startswith("reg_")]
    for k in claves:
        at.button(key=k).click().run()
        sin_excepciones(at, f"{donde} · {k}")
    return claves


def cargar_ejemplo(at, nombre=None, atributo=False):
    ir(at, "3. Datos")
    radio(at, "Origen de los datos").set_value("Usar datos de ejemplo del módulo").run()
    if nombre:
        sel = next(s for s in at.selectbox if s.label == "Conjunto de datos de ejemplo")
        sel.set_value(nombre).run()
    if atributo:
        radio(at, "Tipo de característica de calidad").set_value(
            "Atributo (se cuenta: defectuosos o defectos)").run()
    boton(at, "Usar estos datos para el análisis").click().run()
    sin_excepciones(at, "carga de datos")


# ----------------------------------------------------------------------------
def test_los_13_pasos_abren_sin_datos():
    at = nueva_app()
    sin_excepciones(at, "Inicio")
    opciones = at.radio(key="nav").options
    assert len(opciones) == 14  # Inicio + 13 pasos
    for paso in PASOS:
        ir(at, paso)
        assert not at.error, f"{paso}: {[e.value for e in at.error]}"
    # sin datos, los pasos que los necesitan lo dicen con un aviso (no con un error)
    ir(at, "6. Estabilidad (Fase I)")
    assert any("paso 3" in i.value for i in at.info)


def test_recorrido_completo_por_variables_y_atributos():
    at = nueva_app()

    # Paso 1: guía de requisitos (queda «visitado») y paso 2: ficha de la empresa
    ir(at, "1. Requerimientos")
    ir(at, "2. Empresa")
    next(t for t in at.text_input if t.label == "Empresa").set_value("Empresa de prueba").run()
    sin_excepciones(at, "Empresa")
    assert at.session_state["perfil"]["Empresa"] == "Empresa de prueba"

    # Paso 3: muestras iniciales (diámetros, 20 subgrupos de n = 5)
    cargar_ejemplo(at)
    var = at.session_state["var"]
    assert var["n"] == 5 and len(var["grupos"]) == 20 and var["constante"]

    # Paso 4: especificaciones. La tabla del paso es un editor de datos que AppTest no puede escribir;
    # se escribe en el perfil lo mismo que guarda esa tabla y se vuelve a abrir el paso.
    ir(at, "4. Especificaciones")
    perfil = at.session_state["perfil"]
    assert perfil["variables"], "el paso 4 debe crear la fila de la variable cargada"
    perfil["variables"][0].update({"LIE": 15.2, "Nominal": 15.95, "LSE": 16.7})
    at.session_state["perfil"] = perfil
    ir(at, "4. Especificaciones")
    assert not at.error

    # Paso 5: supuestos → queda registrado el resultado de la Ji-cuadrada
    ir(at, "5. Supuestos")
    assert at.session_state["normalidad_estado"] in ("no se rechaza", "se rechaza", "no aplicable")
    assert any("Condiciones de aplicación" in m.value for m in at.markdown)
    registrar_todo(at, "Supuestos")

    # Paso 6: Fase I
    ir(at, "6. Estabilidad (Fase I)")
    assert at.session_state["fase1_var"]
    f1 = at.session_state["fase1_var"]
    registrar_todo(at, "Fase I")

    # Paso 7: capacidad con LIE y LSE
    ir(at, "7. Capacidad")
    lie = next(n for n in at.number_input if n.label == "LIE")
    lse = next(n for n in at.number_input if n.label == "LSE")
    lie.set_value(15.2).run()
    lse.set_value(16.7).run()
    sin_excepciones(at, "Capacidad")
    assert not at.error
    registrar_todo(at, "Capacidad")

    # Pasos 8 y 9: plan de muestreo y Fase II
    for paso in ("8. Plan de muestreo", "9. Fase II"):
        ir(at, paso)
        assert not at.error, f"{paso}: {[e.value for e in at.error]}"
        registrar_todo(at, paso)

    # Paso 10: atributos (latas, n = 40)
    cargar_ejemplo(at, "Latas defectuosas, n = 40 (carta p/np, Fase I) — módulo 4.8.1", atributo=True)
    attr = at.session_state["attr"]
    assert len(attr["conteo"]) > 0 and attr["constante"]
    ir(at, "10. Cartas por atributos")
    assert not at.error, [e.value for e in at.error]
    registrar_todo(at, "Atributos")

    # Pasos 11 y 12
    ir(at, "11. Mejores condiciones")
    registrar_todo(at, "Mejores")
    ir(at, "12. Muestreo de aceptación")
    assert not at.error
    claves = registrar_todo(at, "Aceptación")
    assert "reg_m7_doble" in claves

    # Los datos de variables siguen activos después de cargar los atributos
    assert at.session_state["var"]["n"] == 5
    assert at.session_state["fase1_var"] == f1

    # Paso 13: informe con todas las secciones registradas
    ir(at, "13. Informe")
    rep = at.session_state["reporte"]
    modulos = {s["modulo"] for s in rep.values()}
    for m in ("Supuestos", "Cartas por variables", "Capacidad", "Muestreo de aceptación"):
        assert m in modulos, f"falta la sección {m}: {sorted(modulos)}"
    descargas = at.get("download_button")
    assert len(descargas) >= 2
    secciones = list(rep.values())
    xls = reporte.a_excel(secciones, {"Empresa": "Prueba"})
    hojas = pd.ExcelFile(io.BytesIO(xls)).sheet_names
    assert len(hojas) >= len(secciones)
    html = reporte.a_html(secciones, {"Empresa": "Prueba"})
    texto = html.decode("utf-8") if isinstance(html, bytes) else html
    assert texto.lstrip().lower().startswith("<!doctype html") and "Capacidad" in texto

    # Estados guardados por cada paso
    ss = at.session_state
    assert ss["perfil"]["Empresa"] and ss["var"] is not None and ss["attr"] is not None
    assert ss["normalidad_estado"] is not None and ss["fase1_var"] and ss["capacidad"]
    assert ss["plan_muestreo"] is not None and ss["fase1_attr"] and ss["reporte"]
    # el paso 9 queda «listo» sólo cuando el usuario elige un plan de Fase II; aquí no se elige ninguno

    # Navegación de vuelta por los 13 pasos con todos los datos cargados: ninguno falla
    for paso in PASOS:
        ir(at, paso)
        assert not at.error, f"{paso}: {[e.value for e in at.error]}"

    # Inicio: 12 de los 13 pasos aparecen completos (todos menos la elección del plan de Fase II)
    ir(at, "Inicio")
    assert any("12 de 13" in m.value and "completos" in m.value for m in at.markdown), \
        [m.value for m in at.markdown if "completos" in m.value]


def test_carga_desde_libro_excel():
    """Simula un libro Excel subido (varias hojas): el paso 3 lo ofrece como origen y arma los subgrupos."""
    rng = np.random.default_rng(11)
    med = pd.DataFrame(rng.normal(40.6, 0.7, (25, 5)).round(2), columns=[f"X{i}" for i in range(1, 6)])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as w:
        pd.DataFrame({"Nota": ["libro de prueba"]}).to_excel(w, sheet_name="Notas", index=False)
        med.to_excel(w, sheet_name="Mediciones", index=False)
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["libro"] = {"nombre": "prueba.xlsx", "bytes": buf.getvalue(), "hojas": ["Notas", "Mediciones"]}
    at.run()
    ir(at, "3. Datos")
    origen = radio(at, "Origen de los datos")
    assert origen.value.startswith("Libro ya cargado")
    assert next(s for s in at.selectbox if s.label == "Hoja").value == "Mediciones"
    boton(at, "Usar estos datos para el análisis").click().run()
    sin_excepciones(at, "libro")
    var = at.session_state["var"]
    assert var["n"] == 5 and len(var["grupos"]) == 25


def test_datos_sin_variabilidad_muestran_mensaje_claro():
    at = AppTest.from_file(APP, default_timeout=120)
    g = [np.array([5.0, 5.0, 5.0])] * 8
    at.session_state["var"] = {"grupos": g, "etiquetas": list(range(1, 9)), "individuales": np.concatenate(g),
                               "nombre": "Constante", "n": 3, "constante": True, "t_datos": None}
    at.run()
    for paso in ("5. Supuestos", "6. Estabilidad (Fase I)"):
        ir(at, paso)
        assert any("variabilidad es nula" in e.value for e in at.error), paso


def test_conteos_imposibles_muestran_mensaje_claro():
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["attr"] = {"conteo": np.array([2.0, 70.0, 3.0]), "n": np.array([50.0, 50.0, 50.0]),
                                "etiquetas": [1, 2, 3], "que": "defectuosos", "constante": True,
                                "nombre": "Defectuosos", "conteo_reconocido": True, "t_unidad": None}
    at.run()
    ir(at, "10. Cartas por atributos")
    assert any("más defectuosos que unidades" in e.value for e in at.error)


def test_plan_doble_hipergeometrico_en_la_app():
    at = nueva_app()
    ir(at, "12. Muestreo de aceptación")
    at.selectbox(key="dist_d").set_value("Hipergeométrica").run()
    at.number_input(key="N_d").set_value(80).run()
    sin_excepciones(at, "plan doble")
    tablas = [d.value for d in at.dataframe]
    pa = [t for t in tablas if "Parámetro" in t.columns and (t["Parámetro"].astype(str) == "Pa").any()]
    assert pa, "no se encontró la tabla del plan doble"
    valor = float(pa[0].loc[pa[0]["Parámetro"] == "Pa", "Valor"].iloc[0])
    assert valor == pytest.approx(0.98432, abs=1e-4)
    # n1 + n2 mayor que el lote: mensaje en vez de excepción
    at.number_input(key="N_d").set_value(25).run()
    sin_excepciones(at, "plan doble lote pequeño")
    assert any("no puede ser mayor que el lote" in e.value for e in at.error)


def test_lote_finito_avisa_el_redondeo_de_defectuosos():
    """80 · 0,03 = 2,4 defectuosos no existe: la app avisa que usa D = 2 y permite escribir D entero."""
    at = nueva_app()
    ir(at, "12. Muestreo de aceptación")
    at.selectbox(key="dist_d").set_value("Hipergeométrica").run()
    at.number_input(key="N_d").set_value(80).run()
    at.number_input(key="d_p").set_value(0.03).run()
    sin_excepciones(at, "redondeo")
    assert any("2,4 no es un número entero" in w.value and "D = 2" in w.value for w in at.warning)
    # con el número de defectuosos escrito directamente no hay aproximación
    at.radio(key="d_modo").set_value("Número de defectuosos D (entero)").run()
    at.number_input(key="d_D").set_value(3).run()
    sin_excepciones(at, "D entero")
    assert not any("no es un número entero" in w.value for w in at.warning)
    tabla = next(d.value for d in at.dataframe if "Parámetro" in d.value.columns
                 and (d.value["Parámetro"] == "Pa").any())
    assert tabla.loc[tabla["Parámetro"] == "D (defectuosos en el lote)", "Valor"].iloc[0] == "3"


def test_fase2_obtiene_la_nueva_media_de_datos_y_especificaciones():
    at = nueva_app()
    cargar_ejemplo(at)
    ir(at, "6. Estabilidad (Fase I)")
    ir(at, "7. Capacidad")
    next(n for n in at.number_input if n.label == "LIE").set_value(15.2).run()
    next(n for n in at.number_input if n.label == "LSE").set_value(16.7).run()
    ir(at, "9. Fase II")
    at.number_input(key="f2_t0").set_value(1.0).run()
    at.radio(key="modo_f2").set_value("Obtener X̄'' de los datos").run()
    sin_excepciones(at, "X̄'' de datos")
    var = at.session_state["var"]
    esperado = float(np.mean(np.concatenate(var["grupos"][-5:])))
    assert any(f"{esperado:.5g}" in c.value for c in at.caption)
    at.radio(key="modo_f2").set_value("Obtener X̄'' de las especificaciones").run()
    sin_excepciones(at, "X̄'' de especificaciones")
    assert any("Con esa media el proceso produciría 1 % de no conformes" in c.value for c in at.caption)
    at.radio(key="crit_f2").set_value("Cpk mínimo").run()
    sin_excepciones(at, "Cpk mínimo")
    assert any("3σ·Cpk" in c.value for c in at.caption)
