"""Paso 1. Requerimientos: qué datos e información necesita cada análisis, y qué tiene ya la empresa."""
import streamlit as st

from cep import empresa
from paginas import estilo, m0_empresa

REQUISITOS = [
    ("building-2", "Información de la empresa (opcional)", "Paso 2", [
        "Sólo datos de la empresa: nombre, sector, ubicación, misión, visión y política de calidad.",
        "Procesos en orden (de dónde entra la materia prima hasta el despacho), productos y clientes.",
        "Jornada y producción diaria (las usa el plan de muestreo del paso 8).",
        "Con esto se arma el tablero de la empresa; no es obligatorio para analizar.",
    ]),
    ("ruler", "Especificaciones del cliente", "Paso 4", [
        "LIE, valor nominal (objetivo) y LSE de cada característica, según la orden o ficha técnica del cliente.",
        "Pueden venir en la hoja «Especificaciones» del libro de datos.",
    ]),
    ("ruler-dimension-line", "Datos por variables (se miden)", "Pasos 3, 5 y 6", [
        "Mediciones numéricas en el orden en que se produjeron (fecha y hora).",
        "Subgrupos racionales de n unidades consecutivas (n de 2 a 25), o datos individuales (carta I-MR).",
        "Bitácora: lote, responsable, máquina o cuadrilla y cualquier cambio (sirve para hallar causas especiales).",
    ]),
    ("hash", "Datos por atributos (se cuentan)", "Pasos 3 y 10", [
        "Por cada muestra: unidades inspeccionadas n y número de defectuosos (cartas p, np) o de defectos (cartas c, u).",
        "Criterio claro de qué es defectuoso o defecto (por ejemplo, fuera de la especificación de la característica).",
        "O bien: datos por variables + LIE/LSE. Cada unidad fuera de especificación cuenta como defectuosa (cartas p y np).",
    ]),
    ("target", "Capacidad del proceso", "Pasos 5 y 7", [
        "Proceso bajo control estadístico (Fase I del paso 6 terminada).",
        "Datos aproximadamente normales (prueba Ji-cuadrada del paso 5).",
        "LIE y/o LSE de la característica (paso 4). Sin ellos no se calculan Cp, Cpk ni %PNC.",
        "Cuantos más datos, más estrecho el intervalo de confianza de Cp y Cpk (módulo 3.3.4).",
    ]),
    ("calendar", "Plan de muestreo", "Paso 8", [
        "Se calcula después de las cartas de Fase I, con el n y los subgrupos de sus muestras iniciales.",
        "Opcional: producción diaria, jornada y horas entre subgrupos para la tabla 10/5/2/1 %.",
    ]),
    ("compass", "Fase II: muestras nuevas y diseño", "Paso 9", [
        "Límites de la Fase I (calculados con las muestras iniciales, suponiendo el proceso calibrado y óptimo).",
        "Muestras nuevas tomadas después de la Fase I, con el mismo formato (o con el n del plan rediseñado).",
        "Corrimiento de la media que interesa detectar (en σ) y la probabilidad deseada de detectarlo.",
        "Producción y jornada, para saber cuánta carga muestral (n/t) cabe en el plan.",
    ]),
    ("hash", "Atributos (repite 2 a 6)", "Paso 10", [
        "Muestras iniciales con n y conteos para la Fase I; muestras nuevas para la Fase II.",
        "El cambio de p (o de c, u) que interesa detectar, para la potencia y la carga muestral.",
    ]),
    ("trophy", "Mejores condiciones", "Paso 11", [
        "Se arma sola con los resultados: especificaciones, capacidad, plan de Fase II y atributos.",
    ]),
    ("package", "Muestreo de aceptación", "Paso 12", [
        "Tamaño del lote N.",
        "Nivel de calidad aceptable (NCA) y nivel de calidad límite (NCL), con los riesgos α y β.",
        "Para MIL-STD-105E: nivel de inspección (I, II o III).",
    ]),
]

FORMATOS = [
    ("Excel o CSV, formato ancho", "Una fila por subgrupo y columnas X1 … Xn. Es el formato de las plantillas."),
    ("Excel o CSV, formato largo", "Una columna con la medición y otra con el número de subgrupo."),
    ("Una sola columna", "Mediciones en orden de producción; se agrupan cada n datos o se usan como individuales."),
    ("Atributos", "Columna del conteo y columna de n (o n constante)."),
]


def ui_plan(pl):
    return f"n = {pl['n']}" + (f" cada {pl['t']:g} h" if pl.get("t") else "")


def _estado():
    """(obligatorios, opcionales): listas de comprobaciones (texto, cumple, detalle)."""
    p = st.session_state.get("perfil") or {}
    vs = p.get("variables", [])
    var_v = [v for v in vs if v.get("Tipo") == "Variable"]
    con_spec = [v for v in var_v if any(x is not None for x in (empresa.especificaciones(v)[0], empresa.especificaciones(v)[2]))]
    var, attr = st.session_state.get("var"), st.session_state.get("attr")
    obligatorios = [
        ("Muestras iniciales cargadas (Fase I)", bool(var or attr), (f"variable «{var['nombre']}»" if var else "") +
         (" · " if var and attr else "") + (f"atributo «{attr['nombre']}»" if attr else "") or "cárguelas en el paso 3"),
    ]
    n_et = len(estilo.etapas_de_texto(p.get("Etapas del proceso")))
    opcionales = [
        ("Nombre de la empresa", bool(str(p.get("Empresa", "")).strip()), p.get("Empresa") or "opcional"),
        ("Misión y visión", bool(str(p.get("Misión") or "").strip() and str(p.get("Visión") or "").strip()),
         "registradas" if str(p.get("Misión") or "").strip() else "opcional"),
        ("Procesos", n_et > 0, f"{n_et} procesos" if n_et else "opcional"),
        ("Producción y jornada", bool(p.get("Producción diaria")), f"{p.get('Producción diaria')} unidades/día"
         if p.get("Producción diaria") else "opcional: la usa el plan de muestreo"),
        ("Especificaciones (LIE/LSE)", len(con_spec) > 0,
         f"{len(con_spec)} de {len(var_v)} variables con especificación" if var_v else "opcional: también en el paso 7"),
        ("Plan de muestreo", st.session_state.get("plan_muestreo") is not None,
         ui_plan(st.session_state["plan_muestreo"]) if st.session_state.get("plan_muestreo")
         else "se calcula en el paso 8, después de las cartas"),
    ]
    return obligatorios, opcionales


def render():
    estilo.encabezado("clipboard-list", "Requerimientos", "Qué información y qué datos necesita cada análisis, en qué formato, y "
                      "qué tiene ya su empresa.", "Paso 1")
    m0_empresa.perfil_activo()
    obligatorios, opcionales = _estado()
    hechos = sum(1 for _, ok, _ in obligatorios if ok)
    estilo.seccion("circle-check", f"Lo indispensable · {hechos} de {len(obligatorios)} listos")
    st.progress(hechos / len(obligatorios))
    estilo.checklist(obligatorios)
    estilo.seccion("building-2", "Opcional: empresa, especificaciones y plan")
    st.caption("Nada de esto es obligatorio para empezar. La empresa (paso 2) arma su tablero; las especificaciones "
               "se usan en Capacidad y el plan de muestreo se calcula en el paso 8.")
    estilo.checklist(opcionales)

    estilo.seccion("map-pin", "Qué se necesita para cada análisis")
    estilo.tarjetas_requisitos(REQUISITOS)

    estilo.seccion("folder-open", "Formatos de archivo aceptados")
    estilo.tabla_simple(["Formato", "Descripción"], FORMATOS)

    estilo.seccion("download", "Plantillas de recolección")
    st.caption("Descargue la plantilla, llénela en planta y súbala en el paso 3.")
    m0_empresa.plantillas()
    faltan = [t for t, ok, _ in obligatorios if not ok]
    if faltan:
        estilo.interpretacion("Lo que falta antes de analizar", [f"**{t}**" for t in faltan] +
                              ["Siga al paso 2 (Empresa, opcional) o directo al paso 3 (Datos)."], "alerta")
    else:
        estilo.interpretacion("Todo listo", ["Tiene las muestras iniciales. Siga al paso 5 (Supuestos) o, si son atributos, al paso 10."], "ok")
