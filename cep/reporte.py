"""
Módulo 8. Reportes: tablas, gráficos, conclusiones preliminares y exportación.

Cada módulo de la app registra sus resultados como una "sección" con tablas,
figuras y conclusiones. Aquí se exportan a Excel (una hoja por tabla) y a un
informe HTML autónomo que se abre en cualquier navegador y se puede imprimir a PDF.
"""
import datetime as _dt
import html
import io
import re

import pandas as pd


def nueva_seccion(modulo, titulo, tablas=None, figuras=None, conclusiones=None):
    return {"modulo": modulo, "titulo": titulo, "tablas": tablas or [], "figuras": figuras or [],
            "conclusiones": conclusiones or [], "hora": _dt.datetime.now().strftime("%Y-%m-%d %H:%M")}


def _hoja(nombre, usados):
    base = re.sub(r"[\[\]\*\?/\\:]", "", nombre)[:28] or "Hoja"
    nom, i = base, 2
    while nom in usados:
        nom = f"{base[:25]}_{i}"
        i += 1
    usados.add(nom)
    return nom


def a_excel(secciones, datos_generales=None):
    """Devuelve bytes de un libro Excel con un índice y una hoja por tabla."""
    buf = io.BytesIO()
    usados = set()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        indice = []
        generales = [("Software", "Sigmora CEP Studio")] + list((datos_generales or {}).items())
        pd.DataFrame(generales, columns=["Campo", "Valor"]).to_excel(
            xw, sheet_name=_hoja("Datos generales", usados), index=False)
        xw.book.properties.creator = "Sigmora CEP Studio"
        xw.book.properties.title = "Reporte de control estadístico de procesos"
        for s in secciones:
            for nombre, df in s["tablas"]:
                hoja = _hoja(f"{s['modulo'][:9]} {nombre}", usados)
                _limpio(df).to_excel(xw, sheet_name=hoja, index=False)
                indice.append({"Módulo": s["modulo"], "Sección": s["titulo"], "Tabla": nombre, "Hoja": hoja})
            if s["conclusiones"]:
                hoja = _hoja(f"{s['modulo'][:9]} conclusiones", usados)
                pd.DataFrame({"Conclusiones preliminares": s["conclusiones"]}).to_excel(xw, sheet_name=hoja, index=False)
                indice.append({"Módulo": s["modulo"], "Sección": s["titulo"], "Tabla": "Conclusiones", "Hoja": hoja})
        pd.DataFrame(indice or [{"Módulo": "—", "Sección": "Sin resultados", "Tabla": "", "Hoja": ""}]).to_excel(
            xw, sheet_name=_hoja("Indice", usados), index=False)
    return buf.getvalue()


def _limpio(df):
    d = df.copy()
    for c in d.columns:
        if str(c).startswith("_"):
            d = d.drop(columns=c)
    return d


_RAIZ = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))


def _b64(ruta):
    import base64
    try:
        with open(ruta, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError:
        return ""


def _fuentes_css():
    """Tipografías incrustadas (IBM Plex Sans y Mono, SIL OFL) para que el informe se vea igual sin internet."""
    import os
    css = []
    for fam, archivo, peso in (("Plex", "ibm-plex-sans-latin-400-normal", 400), ("Plex", "ibm-plex-sans-latin-500-normal", 500),
                               ("PlexMono", "ibm-plex-mono-latin-400-normal", 400),
                               ("PlexMono", "ibm-plex-mono-latin-500-normal", 500)):
        b = _b64(os.path.join(_RAIZ, "static", "fuentes", archivo + ".woff2"))
        if b:
            css.append(f"@font-face{{font-family:'{fam}';font-weight:{peso};"
                       f"src:url(data:font/woff2;base64,{b}) format('woff2');}}")
    return "\n".join(css)


def _foto_portada(foto=None):
    import os
    if foto and str(foto).startswith("data:image"):
        return foto
    b = _b64(os.path.join(_RAIZ, "static", "fotos", "portada.jpg"))
    return f"data:image/jpeg;base64,{b}" if b else ""


def a_html(secciones, datos_generales=None, titulo="Informe de Control Estadístico de Procesos", foto_portada=None):
    """Informe HTML autónomo (incluye plotly.js, tipografías y fotografía para funcionar sin internet)."""
    foto = _foto_portada(foto_portada)
    partes = [f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title>
<style>
{_fuentes_css()}
body{{font-family:Plex,'Segoe UI',Arial,sans-serif;max-width:1120px;margin:auto;padding:0 40px 60px;color:#0e0e0c;
background:#f3f2ee;line-height:1.5;font-size:14px}}
.lab,th,td,.tabla-n{{font-family:PlexMono,Menlo,Consolas,monospace}}
.lab{{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:#6b6a64}}
.portada{{display:grid;grid-template-columns:5fr 7fr;margin:0 -40px 0;border-bottom:1px solid #0e0e0c;min-height:380px}}
.portada .l{{padding:40px 40px 32px;border-right:1px solid #0e0e0c;display:flex;flex-direction:column}}
.portada h1{{font-weight:500;margin:18px 0 24px;font-size:40px;line-height:1.02;letter-spacing:-.03em}}
.portada h1 i{{font-style:normal;color:#d9480f}}
.portada .f{{background:#2a2a28 url('{foto}') center/cover no-repeat}}
.portada .l .lab:last-child{{margin-top:auto}}
h2{{font-weight:500;color:#0e0e0c;font-size:24px;letter-spacing:-.02em;margin:52px 0 10px;padding-top:12px;
border-top:1px solid #0e0e0c;line-height:1.15}}
h2 small{{display:block;font-family:PlexMono,Menlo,monospace;font-size:11px;font-weight:400;letter-spacing:.07em;
text-transform:uppercase;color:#6b6a64;margin-bottom:8px}}
h3{{font-size:11px;font-family:PlexMono,Menlo,monospace;font-weight:500;letter-spacing:.07em;text-transform:uppercase;
margin:0 0 6px;color:#1f7a4d}}
table{{border-collapse:collapse;margin:6px 0 18px;font-size:12px;border:1px solid #d9d7d0;font-variant-numeric:tabular-nums}}
th,td{{border-bottom:1px solid #e6e4dd;padding:6px 12px;text-align:right}}
th{{color:#6b6a64;font-size:10.5px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid #0e0e0c}}
td:first-child,th:first-child{{text-align:left}} td:first-child{{font-family:Plex,Arial,sans-serif;font-size:13px}}
.concl{{border:1px solid #1f7a4d;padding:12px 16px;margin:10px 0 18px}}
.concl ul{{margin:0;padding:0;list-style:none}} .concl li{{padding:6px 0;border-top:1px solid #e6e4dd}}
.concl li:first-child{{border-top:0;padding-top:2px}}
.meta{{width:calc(100% + 80px);margin:0 -40px 0;border:0;border-bottom:1px solid #0e0e0c}}
.meta th{{width:30%;padding:9px 12px 9px 40px;border-bottom:1px solid #d9d7d0;border-right:1px solid #d9d7d0;
text-align:left;font-family:PlexMono,Menlo,monospace;font-size:10.5px}}
.meta td{{text-align:left;font-family:Plex,Arial,sans-serif;font-size:14px;padding:9px 16px;border-bottom:1px solid #d9d7d0}}
.tabla-n{{color:#6b6a64;font-size:11px;margin:18px 0 4px;letter-spacing:.04em}} .tabla-n b{{color:#0e0e0c;font-weight:500}}
.plotly-graph-div{{border:1px solid #d9d7d0;background:#f7f6f3}}
.pie{{margin:60px -40px 0;padding:14px 40px 0;border-top:1px solid #0e0e0c;color:#6b6a64;font-size:11px;
font-family:PlexMono,Menlo,monospace;display:flex;justify-content:space-between}}
@media print{{.plotly-graph-div{{page-break-inside:avoid}} h2{{page-break-after:avoid}}}}
</style></head><body><div class="portada"><div class="l"><div class="lab">Sigmora CEP Studio · Informe de control estadístico</div>
<h1>{html.escape(titulo)}<i>.</i></h1><div class="lab">Generado el {_dt.datetime.now().strftime('%d/%m/%Y %H:%M')}</div></div>
<div class="f"></div></div>"""]
    if datos_generales:
        partes.append("<table class='meta'>" + "".join(
            f"<tr><th>{html.escape(str(k))}</th><td>{html.escape(str(v))}</td></tr>" for k, v in datos_generales.items()
            if str(v).strip()) + "</table>")
    nt = nf = 0
    incluir_js = True
    for s in secciones:
        partes.append(f"<h2><small>{html.escape(s['modulo'])}</small>{html.escape(s['titulo'])}</h2>")
        for nombre, df in s["tablas"]:
            nt += 1
            partes.append(f"<p class='tabla-n'><b>Tabla {nt}.</b> {html.escape(nombre)}</p>")
            partes.append(_limpio(df).to_html(index=False, float_format=lambda v: f"{v:.5g}", border=0))
        for nombre, fig in s["figuras"]:
            nf += 1
            partes.append(f"<p class='tabla-n'><b>Figura {nf}.</b> {html.escape(nombre)}</p>")
            partes.append(fig.to_html(full_html=False, include_plotlyjs=incluir_js))
            incluir_js = False
        if s["conclusiones"]:
            partes.append("<div class='concl'><h3>Conclusiones preliminares</h3><ul>" +
                          "".join(f"<li>{html.escape(c)}</li>" for c in s["conclusiones"]) + "</ul></div>")
    partes.append("<div class='pie'><span>Sigmora CEP Studio · Control estadístico de procesos</span>"
                  f"<span>{_dt.date.today().year}</span></div></body></html>")
    return "\n".join(partes).encode("utf-8")
