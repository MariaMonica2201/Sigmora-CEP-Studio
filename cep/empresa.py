"""
Perfil de empresa: hace que Sigmora CEP Studio sirva para cualquier empresa manufacturera.

Un perfil guarda los datos de la empresa, las etapas del proceso y el catálogo de
características de calidad (variables o atributos) con sus especificaciones.
Se guarda / carga como archivo JSON, de modo que cada empresa tiene el suyo.

También incluye el plan de muestreo sugerido a partir de la tabla de la
presentación "Análisis de capacidad de procesos" (¿Cómo y cuántas unidades
muestrear?, adaptación de MIL-STD-414, Doty 1991):
    Tamaño de lote 60–300 → 10 % · 301–1000 → 5 % · 1001–5000 → 2 % · > 5000 → 1 %
"Si no se produce por lotes, el lote puede considerarse como la producción de un día".
"""
import copy
import io
import json
import math

import pandas as pd

COLUMNAS_VARIABLES = ["Característica", "Unidad", "Tipo", "Etapa del proceso", "LIE", "Nominal", "LSE",
                      "Cómo se mide"]

PERFIL_VACIO = {
    "Empresa": "",
    "NIT": "",
    "Sector / producto": "",
    "Ubicación": "",
    "Misión": "",
    "Visión": "",
    "Política de calidad": "",
    "Productos o servicios": "",
    "Clientes / mercados": "",
    "Número de trabajadores": None,
    "Proceso u operación crítica": "",
    "Hora de inicio de la jornada": "",
    "Hora de fin de la jornada": "",
    "Producción diaria": None,
    "Horas entre subgrupos": None,
    "Etapas del proceso": "",
    "Portada: título": "",
    "Portada: descripción": "",
    "Foto de portada": "",
    "Logo": "",
    "variables": [],
}

PRESETS = {"Empresa nueva (en blanco)": PERFIL_VACIO}


def nuevo(preset):
    return copy.deepcopy(PRESETS[preset])


def variables_df(perfil):
    df = pd.DataFrame(perfil.get("variables", []), columns=COLUMNAS_VARIABLES)
    for c in ("LIE", "Nominal", "LSE"):  # numéricas: las vacías se ven en blanco (no «None»)
        df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    return df


def a_json(perfil):
    return json.dumps(perfil, ensure_ascii=False, indent=2, default=str).encode("utf-8")


# Modelo de la ficha: SOLO datos de la empresa (las especificaciones van en la hoja «Especificaciones» del libro de
# datos o se escriben en Capacidad).
CAMPOS_FICHA = ["Empresa", "NIT", "Sector / producto", "Ubicación", "Misión", "Visión", "Política de calidad",
                "Productos o servicios", "Clientes / mercados", "Número de trabajadores", "Proceso u operación crítica",
                "Hora de inicio de la jornada", "Hora de fin de la jornada", "Producción diaria"]
ALIAS_FICHA = {"horas entre subgrupos": "Horas entre subgrupos", "portada: título": "Portada: título",
               "portada: descripción": "Portada: descripción"}
CAMPOS_NUMERICOS = ("Producción diaria", "Horas entre subgrupos", "Número de trabajadores")
AYUDA_FICHA = {
    "Empresa": "Razón social o nombre comercial", "NIT": "Opcional", "Sector / producto": "Qué produce o qué servicio presta",
    "Ubicación": "Municipio, departamento", "Misión": "Texto de la misión", "Visión": "Texto de la visión",
    "Política de calidad": "Opcional", "Productos o servicios": "Separados por punto y coma (;)",
    "Clientes / mercados": "Separados por punto y coma (;)", "Número de trabajadores": "Número",
    "Proceso u operación crítica": "Proceso que se va a controlar", "Hora de inicio de la jornada": "HH:MM",
    "Hora de fin de la jornada": "HH:MM", "Producción diaria": "Unidades por día (número)"}


def _valor_ficha(p, campo):
    v = p.get(ALIAS_FICHA.get(campo.lower(), campo))
    return "" if v is None else v


def ficha_excel(perfil=None):
    """Modelo de ficha de empresa en Excel: hojas Empresa (Campo/Valor/Ayuda), Procesos e Instrucciones. Sirve en
    blanco o para guardar lo registrado; se vuelve a leer con desde_excel."""
    p = perfil or PERFIL_VACIO
    buf = io.BytesIO()
    import re as _re
    texto = str(p.get("Etapas del proceso") or "")
    partes = [x.strip() for x in _re.split(r"(?:^|\s)\d+\.\s+", texto) if x.strip()]
    etapas = [(x.split(":", 1)[0].strip(), x.split(":", 1)[1].strip() if ":" in x else "") for x in partes]
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame({"Campo": CAMPOS_FICHA, "Valor": [_valor_ficha(p, c) for c in CAMPOS_FICHA],
                      "Ayuda": [AYUDA_FICHA.get(c, "") for c in CAMPOS_FICHA]}).to_excel(xw, sheet_name="Empresa", index=False)
        pd.DataFrame(etapas or [("", "")], columns=["Proceso", "Descripción"]).to_excel(xw, sheet_name="Procesos",
                                                                                         index=False)
        pd.DataFrame({"Instrucciones": [
            "Modelo de ficha: sólo datos de la empresa. Todo es opcional.",
            "Hoja Empresa: escriba cada dato en la columna Valor (la columna Ayuda dice qué va).",
            "Hoja Procesos: un proceso por fila, en orden (nombre y descripción corta).",
            "Hoja Fotos (opcional): pegue la foto de la empresa (la primera imagen) y el logo (la segunda).",
            "En Sigmora CEP Studio: paso 2 (Empresa) → suba este archivo. Se arma el tablero de la empresa y los campos se "
            "pueden editar después."]}).to_excel(xw, sheet_name="Instrucciones", index=False)
        pd.DataFrame({"Fotos": ["Pegue aquí la foto de la empresa (primera imagen) y, debajo, el logo (segunda imagen). "
                                "Formatos JPG o PNG."]}).to_excel(xw, sheet_name="Fotos", index=False)
        for ws in xw.book.worksheets:
            for col in ws.columns:
                ancho = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(12, ancho + 2), 70)
    return buf.getvalue()


def imagen_data_uri(contenido, ancho_max=1800):
    """Convierte una imagen (bytes) en data URI JPEG/PNG reducida, para guardarla dentro del perfil."""
    import base64
    from PIL import Image
    im = Image.open(io.BytesIO(contenido))
    im.thumbnail((ancho_max, ancho_max))
    buf = io.BytesIO()
    if im.mode in ("RGBA", "LA", "P"):
        im.save(buf, format="PNG", optimize=True)
        tipo = "png"
    else:
        im.convert("RGB").save(buf, format="JPEG", quality=82, optimize=True)
        tipo = "jpeg"
    return f"data:image/{tipo};base64," + base64.b64encode(buf.getvalue()).decode()


def fotos_de_excel(contenido):
    """Imágenes pegadas en el Excel de la ficha (hoja «Fotos» primero): [foto de portada, logo]."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(contenido))
    except Exception:  # noqa: BLE001
        return []
    hojas = sorted(wb.worksheets, key=lambda ws: ws.title.strip().lower() != "fotos")
    salida = []
    for ws in hojas:
        imgs = sorted(getattr(ws, "_images", []), key=lambda im: getattr(getattr(im.anchor, "_from", None), "row", 0))
        for im in imgs:
            try:
                salida.append(imagen_data_uri(im._data()))
            except Exception:  # noqa: BLE001
                continue
    return salida[:2]


def desde_excel(contenido):
    """Lee una ficha de empresa en Excel (formato de ficha_excel). Tolera hojas o columnas faltantes."""
    hojas = pd.read_excel(io.BytesIO(contenido), sheet_name=None, dtype=object)
    norm = {str(k).strip().lower(): v for k, v in hojas.items()}
    base = copy.deepcopy(PERFIL_VACIO)
    emp = norm.get("empresa")
    if emp is not None and emp.shape[1] >= 2:
        validos = {c.lower(): ALIAS_FICHA.get(c.lower(), c) for c in CAMPOS_FICHA}
        validos.update(ALIAS_FICHA)
        validos.update({k.lower(): k for k in PERFIL_VACIO if k != "variables"})
        for campo, valor in zip(emp.iloc[:, 0], emp.iloc[:, 1]):
            c = validos.get(str(campo).strip().lower())
            if c and valor is not None and str(valor).strip() and str(valor) != "nan":
                if c in CAMPOS_NUMERICOS:
                    try:
                        num = float(str(valor).replace(",", ".").split()[0])
                    except (ValueError, IndexError):
                        continue
                    base[c] = num if c == "Horas entre subgrupos" else int(num)
                    continue
                v = valor.strftime("%H:%M") if hasattr(valor, "strftime") else str(valor).strip()
                base[c] = v
    et = norm.get("procesos", norm.get("etapas"))
    if et is not None and et.shape[1] >= 1:
        filas = []
        for _, r in et.iterrows():
            nom = str(r.iloc[0]).strip() if r.iloc[0] is not None and str(r.iloc[0]) != "nan" else ""
            des = str(r.iloc[1]).strip() if et.shape[1] > 1 and r.iloc[1] is not None and str(r.iloc[1]) != "nan" else ""
            if nom:
                filas.append(f"{len(filas) + 1}. {nom}" + (f": {des}" if des else ""))
        base["Etapas del proceso"] = " ".join(filas)
    car = norm.get("especificaciones", norm.get("características", norm.get("caracteristicas")))
    if car is not None and "Característica" in car.columns:
        vs = []
        for r in car.to_dict("records"):
            if r.get("Característica") is None or not str(r.get("Característica")).strip() or str(r.get("Característica")) == "nan":
                continue
            fila = {}
            for c in COLUMNAS_VARIABLES:
                v = r.get(c)
                if v is None or (isinstance(v, float) and v != v) or str(v) == "nan":
                    v = None
                elif c in ("LIE", "Nominal", "LSE"):
                    try:
                        v = float(str(v).replace(",", "."))
                    except ValueError:
                        v = None
                else:
                    v = str(v).strip()
                fila[c] = v
            fila["Tipo"] = fila.get("Tipo") or "Variable"
            vs.append(fila)
        base["variables"] = vs
    fotos = fotos_de_excel(contenido)
    if fotos:
        base["Foto de portada"] = fotos[0]
    if len(fotos) > 1:
        base["Logo"] = fotos[1]
    return base


def desde_json(contenido):
    p = json.loads(contenido)
    base = copy.deepcopy(PERFIL_VACIO)
    base.update(p)
    base.pop("Portada: ícono del producto", None)
    return base


def buscar_variable(perfil, nombre):
    """Devuelve la característica del perfil cuyo nombre coincide (sin distinguir mayúsculas)."""
    if not perfil or not nombre:
        return None
    n = str(nombre).strip().lower()
    for v in perfil.get("variables", []):
        c = str(v.get("Característica", "")).strip().lower()
        if c and (c == n or c in n or n in c):
            return v
    return None


def _num(v):
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)) or str(v).strip() == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def especificaciones(var):
    """(LIE, Nominal, LSE) numéricos o None."""
    if not var:
        return None, None, None
    return _num(var.get("LIE")), _num(var.get("Nominal")), _num(var.get("LSE"))


# ------------------------------------------------------------ plan de muestreo --
TABLA_PORCENTAJE = [(60, 300, 0.10), (301, 1000, 0.05), (1001, 5000, 0.02), (5001, math.inf, 0.01)]


def porcentaje_muestreo(tam_lote):
    for lo, hi, pct in TABLA_PORCENTAJE:
        if lo <= tam_lote <= hi:
            return pct
    return 1.0 if tam_lote < 60 else 0.01


def _hora(h, defecto):
    """'6', '06:00', '6.30' o '6:30 ' → horas decimales; si no se entiende, usa el valor por defecto."""
    try:
        partes = [int(x) for x in str(h).strip().replace(".", ":").split(":")[:2] if x.strip() != ""]
        if not partes:
            return defecto
        return partes[0] + (partes[1] / 60 if len(partes) > 1 else 0)
    except (TypeError, ValueError):
        return defecto


def _horas(h_ini, h_fin):
    return max(_hora(h_fin, 16.0) - _hora(h_ini, 6.0), 0.5)


def plan_muestreo(tam_lote, h_ini, h_fin, intervalo_h, subgrupos_objetivo=25):
    """Plan de muestreo diario sugerido.

    tam_lote: producción de un día (unidades, cajas, piezas…).
    intervalo_h: horas entre subgrupos.
    """
    pct = porcentaje_muestreo(tam_lote)
    total = math.ceil(pct * tam_lote)
    horas = _horas(h_ini, h_fin)
    k = max(1, int(horas // intervalo_h))
    n = min(25, max(2, math.ceil(total / k)))
    dias = math.ceil(subgrupos_objetivo / k)
    return {
        "Producción diaria (tamaño de lote)": tam_lote,
        "% a muestrear (tabla de la presentación)": f"{100 * pct:g} %",
        "Unidades a muestrear por día": total,
        "Horas de jornada": horas,
        "Subgrupos por día (uno cada intervalo)": k,
        "Tamaño de subgrupo n sugerido": n,
        "Unidades realmente inspeccionadas por día": n * k,
        f"Días para reunir {subgrupos_objetivo} subgrupos (Fase I)": dias,
    }


# ------------------------------------------------------------------ plantillas --
def plantilla_excel(var, n=5, perfil=None):
    """Plantilla Excel de recolección para una característica del perfil."""
    buf = io.BytesIO()
    tipo = str(var.get("Tipo", "Variable"))
    nombre = var.get("Característica", "Característica")
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        if tipo.startswith("Variable"):
            cols = ["Subgrupo", "Fecha", "Hora", "Lote", "Responsable"] + [f"X{i}" for i in range(1, n + 1)] + ["Observaciones"]
            pd.DataFrame([{c: (i + 1 if c == "Subgrupo" else None) for c in cols} for i in range(30)]).to_excel(
                xw, sheet_name="Datos", index=False)
            pasos = [f"Característica: {nombre} ({var.get('Unidad', '')}). {var.get('Cómo se mide', '')}",
                     f"Cada fila es un subgrupo racional: {n} unidades tomadas seguidas, en el mismo momento, máquina/cuadrilla y lote.",
                     "Anote las mediciones en X1…Xn. Escriba en Observaciones cualquier cambio (operario, lote, ajuste, lluvia…): "
                     "es la bitácora que permite identificar causas especiales.",
                     "En Sigmora CEP Studio: Módulo 1 → Subir archivo → Variable → Formato ancho → columnas X1…Xn."]
        else:
            defectos = "defectos" in tipo.lower()
            cols = ["Subgrupo", "Fecha", "Hora", "Lote",
                    "Unidades inspeccionadas (n)", "Defectos encontrados" if defectos else "Unidades defectuosas",
                    "Motivo principal", "Observaciones"]
            pd.DataFrame([{c: (i + 1 if c == "Subgrupo" else None) for c in cols} for i in range(30)]).to_excel(
                xw, sheet_name="Datos", index=False)
            pasos = [f"Característica: {nombre}. {var.get('Cómo se mide', '')}",
                     "Una fila por muestra (hora o día). n = unidades inspeccionadas; anote el conteo y el motivo.",
                     "En Sigmora CEP Studio: Módulo 1 → Subir archivo → Atributo → columna del conteo y columna de n."]
        info = [("Empresa", (perfil or {}).get("Empresa", "")), ("Característica", nombre),
                ("Unidad", var.get("Unidad", "")), ("LIE", var.get("LIE")), ("Nominal", var.get("Nominal")),
                ("LSE", var.get("LSE"))] + [(f"Paso {i}", p) for i, p in enumerate(pasos, 1)]
        pd.DataFrame(info, columns=["Campo", "Valor"]).to_excel(xw, sheet_name="Instrucciones", index=False)
    return buf.getvalue()
