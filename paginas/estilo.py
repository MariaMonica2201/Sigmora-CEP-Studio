"""
Identidad visual de Sigmora CEP Studio: hoja de estilos y componentes HTML (encabezados con fotografía, tarjetas de
indicadores, diagrama del proceso, cuadros de interpretación).

Sólo presentación: aquí no hay cálculos estadísticos.
- Iconos de línea: Lucide (ISC), en paginas/iconos.py.
- Fotografías: static/fotos (Unsplash License, ver README). Se sirven sin internet desde /app/static.
- Tipografías: IBM Plex Sans y IBM Plex Mono (SIL Open Font License), en static/fuentes.
"""
import html
import re

import streamlit as st

from paginas.iconos import ICONOS

# Paleta: tinta casi negra sobre papel cálido, líneas finas y un solo acento (naranja señal). Verde y rojo sólo
# para estados (bajo control / fuera de control).
TINTA = "#0e0e0c"
TEXTO = "#0e0e0c"
SUAVE = "#6b6a64"
ACENTO = "#d9480f"
VERDE = "#1f7a4d"
VERDE_OSC = "#185f3c"
ROJO = "#c0261c"
NARANJA = "#b54708"
DORADO = ACENTO      # nombre heredado: ahora es el acento
AZUL_NOCHE = TINTA

RUTA_FOTOS = "app/static/fotos"
PASO_TEXTO = ""            # «Paso N de 13», lo define app.py
DESPUES_ENCABEZADO = None   # app.py lo define: barra de pasos y guía que van justo debajo de la foto del paso

# Emojis heredados (en datos guardados o en llamadas antiguas) → icono de línea equivalente.
EMOJI_ICONO = {
    "📦": "package", "🔢": "hash", "🎯": "target", "✅": "circle-check", "📈": "trending-up", "📐": "ruler",
    "🏆": "trophy", "📏": "ruler-dimension-line", "🔁": "repeat", "❌": "circle-x", "🏭": "factory",
    "🗂️": "folder-open", "🔭": "telescope", "📍": "map-pin", "⚙️": "settings", "⏱️": "timer",
    "📋": "clipboard-list", "🧪": "flask-conical", "🗓️": "calendar", "📑": "file-text", "↔️": "move-horizontal",
    "📊": "chart-column", "⚡": "zap", "🧩": "puzzle", "🔄": "refresh-cw", "🏢": "building-2", "⬇️": "download",
    "🧭": "compass", "⚠️": "triangle-alert", "🚫": "ban", "🧹": "brush", "🏠": "house", "💧": "droplet",
    "🔎": "search", "🔍": "search", "🗑️": "trash-2", "👥": "users", "📂": "folder-open", "🛒": "shopping-cart",
    "💾": "save", "➕": "plus", "💡": "lightbulb", "⛔": "octagon-alert", "🚨": "triangle-alert", "📌": "map-pin",
    "σ": "sigma", "🤝": "users",
}

# Fotografía de cada página (clave: palabra del título del encabezado).
FOTOS_MODULO = [
    ("requer", "planos"), ("empresa", "planta"), ("plan de muestreo", "equipo"), ("gestión de datos", "analitica"),
    ("datos", "analitica"), ("especific", "ingenieria"), ("supuesto", "laboratorio"), ("variables", "planos"),
    ("capacidad", "calidad"), ("fase ii", "impresion"), ("diseño", "impresion"), ("atributos", "estanteria"),
    ("mejores", "soldadura"), ("aceptación", "almacen"), ("reporte", "analitica"), ("informe", "analitica"),
]


def icono(nombre, tam=20, clase="ico"):
    """SVG de línea para un nombre de icono (o un emoji heredado). Devuelve "" si no se reconoce."""
    nombre = str(nombre or "").strip()
    nombre = EMOJI_ICONO.get(nombre, EMOJI_ICONO.get(nombre.replace("️", ""), nombre))
    cuerpo = ICONOS.get(nombre)
    if not cuerpo:
        return ""
    return (f'<span class="icw"><svg class="{clase}" width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{cuerpo}</svg></span>')


def logo(tam=12, uid="a", claro=False):
    """Marca mínima: un cuadrado del color de acento."""
    return f'<i class="cep-logo" style="width:{tam}px;height:{tam}px"></i>'


CSS = """
<style>
:root{--tinta:#0e0e0c;--texto:#0e0e0c;--suave:#6b6a64;--tenue:#9a988f;--linea:#d9d7d0;--linea2:#e6e4dd;--fondo:#f3f2ee;
--papel:#f7f6f3;--hover:#eae8e2;--acento:#d9480f;--ok:#1f7a4d;--alerta:#b54708;--mal:#c0261c;--info:#3a3935;
--sans:'IBM Plex Sans',-apple-system,'Segoe UI',Arial,sans-serif;--mono:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;}
html,body,[data-testid="stAppViewContainer"]{background:var(--fondo);}
body,p,li,label,input,textarea,button,[data-testid="stMarkdownContainer"]{font-family:var(--sans);}
h1,h2,h3,h4{font-family:var(--sans) !important;font-weight:500 !important;letter-spacing:-.02em;color:var(--tinta);}
svg.ico{flex:0 0 auto;vertical-align:-.18em;} .icw{display:inline-flex;align-items:center;flex:0 0 auto;}
.mono,.cep-mono{font-family:var(--mono);}
header[data-testid="stHeader"]{display:none !important;}
.st-key-sin_traduccion{display:none !important;}
[data-testid="stMainBlockContainer"],.block-container{padding:0 2.5rem 2rem !important;max-width:1440px;}
/* ---------- barra lateral: marca + pasos ---------- */
section[data-testid="stSidebar"]{border-right:1px solid var(--linea);width:244px !important;min-width:244px !important;}
section[data-testid="stSidebar"] > div{padding-top:0;}
[data-testid="stSidebarHeader"],[data-testid="stSidebarCollapseButton"]{display:none !important;}
[data-testid="stSidebarUserContent"]{padding:0 0 2rem !important;}
.cep-logo{display:inline-block;background:var(--acento);flex:0 0 auto;}
.cep-marca-sub{font-family:var(--mono);font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;color:var(--suave);margin-left:-.25rem;}
.cep-top-marca{display:flex;align-items:center;gap:.6rem;height:48px;padding:0 1.25rem;border-bottom:1px solid var(--tinta);
  font-family:var(--mono);font-weight:500;font-size:.82rem;letter-spacing:.02em;color:var(--tinta);}
.cep-lab{font-family:var(--mono);font-size:.68rem;letter-spacing:.07em;text-transform:uppercase;color:var(--suave);}
.cep-side-lab{padding:1rem 1.25rem .5rem;}
[data-testid="stSidebarContent"]{padding:0 !important;}
.st-key-nav{width:100% !important;}
.st-key-nav [data-testid="stWidgetLabel"]{display:none !important;}
.st-key-nav [role="radiogroup"]{gap:0;flex-direction:column;width:100%;}
.st-key-nav [role="radiogroup"] > div{width:100%;}
.st-key-nav [data-testid="stRadioOption"]{display:flex;width:100%;padding:.36rem 1.25rem !important;margin:0 !important;
  color:var(--suave);transition:background .12s;cursor:pointer;}
.st-key-nav [data-testid="stRadioOption"] > div{width:100%;}
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child:not([data-testid]){display:none !important;}
.st-key-nav [data-testid="stMarkdownContainer"]{width:100%;}
.st-key-nav p{color:inherit !important;font-size:.84rem;display:flex;align-items:center;width:100%;margin:0;gap:0;}
.st-key-nav p code{font-family:var(--mono);background:none !important;color:var(--tenue);padding:0;font-size:.7rem;
  width:2rem;flex:0 0 2rem;}
.st-key-nav p .stMarkdownColoredText{margin-left:auto;font-size:.62rem;}
.st-key-nav [data-testid="stRadioOption"]:hover{background:var(--hover);color:var(--tinta);}
.st-key-nav [data-testid="stRadioOption"]:has(input:checked){background:var(--hover);color:var(--tinta);
  box-shadow:inset 2px 0 0 var(--acento);}
.st-key-nav [data-testid="stRadioOption"]:has(input:checked) p{font-weight:500;}
.st-key-nav [data-testid="stRadioOption"]:has(input:checked) code{color:var(--acento);}
/* ---------- barra superior ---------- */
.st-key-topbar{position:sticky !important;top:0;z-index:999;background:var(--fondo);margin:-1rem 0 0 !important;
  height:48px !important;min-height:48px;display:flex !important;align-items:center !important;justify-content:center;
  box-shadow:0 0 0 2.5rem var(--fondo);clip-path:inset(0 -2.5rem);}
.st-key-topbar:after{content:"";position:absolute;left:-2.5rem;right:-2.5rem;bottom:0;height:1px;background:var(--tinta);}
.st-key-topbar > div{width:100%;}
.cep-meta{display:flex;gap:1.4rem;align-items:center;font-family:var(--mono);font-size:.74rem;color:var(--suave);white-space:nowrap;
  overflow:hidden;}
.cep-meta b{color:var(--tinta);font-weight:500;}
.cep-meta .sq{display:inline-block;width:7px;height:7px;background:var(--ok);margin-right:.45rem;vertical-align:1px;}
.cep-meta .sq.no{background:var(--tenue);}
.st-key-topbar [data-testid="stPopover"] button{background:transparent;border:1px solid var(--linea);min-height:32px;height:32px;}
/* ---------- portada ---------- */
.cep-hero{display:grid;grid-template-columns:5fr 7fr;margin:0 -2.5rem;border-bottom:1px solid var(--tinta);min-height:500px;}
.cep-hero .l{padding:3.2rem 2.5rem 2.4rem;border-right:1px solid var(--tinta);display:flex;flex-direction:column;}
.cep-hero h1{font-size:clamp(2.6rem,4.4vw,4rem) !important;line-height:1 !important;letter-spacing:-.035em;margin:1.3rem 0 0;padding:0;
  font-weight:500 !important;}
.cep-hero h1.largo{font-size:clamp(2rem,2.8vw,2.7rem) !important;line-height:1.06 !important;}
.cep-hero h1 em{font-style:normal;color:var(--acento);}
.cep-hero p{font-size:1.02rem;color:#3a3935;max-width:440px;margin:1.3rem 0 0;line-height:1.55;}
.cep-hero .r{background:#2a2a28 center/cover no-repeat;position:relative;min-height:320px;}
.cep-hero .cap{position:absolute;left:0;bottom:0;background:var(--fondo);padding:.45rem .9rem;border-top:1px solid var(--tinta);
  border-right:1px solid var(--tinta);}
.cep-strip{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(0,1fr);margin:0 -2.5rem;border-bottom:1px solid var(--tinta);}
.cep-strip > div{padding:1rem 1.4rem 1.05rem;border-right:1px solid var(--linea);}
.cep-strip > div:first-child{padding-left:2.5rem;} .cep-strip > div:last-child{border-right:0;}
.cep-strip .v{font-family:var(--mono);font-size:1.6rem;letter-spacing:-.02em;margin-top:.3rem;line-height:1.15;color:var(--tinta);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.cep-strip .v.t{font-family:var(--sans);font-size:1.05rem;font-weight:500;padding-top:.45rem;white-space:normal;}
.cep-strip .s{font-family:var(--mono);font-size:.7rem;color:var(--suave);margin-top:.15rem;}
@media (max-width:900px){.cep-strip{grid-auto-flow:row;grid-template-columns:repeat(2,1fr);} .cep-hero{grid-template-columns:1fr;} .cep-hero .l{border-right:0;border-bottom:1px solid var(--tinta);}}
/* ---------- índice de pasos ---------- */
.cep-idx{display:grid;grid-template-columns:4fr 8fr;margin:0 -2.5rem;border-bottom:1px solid var(--tinta);}
.cep-idx .side{padding:2rem 2.5rem;border-right:1px solid var(--tinta);}
.cep-idx .side h2{font-size:1.7rem;line-height:1.12;margin:.8rem 0 0;padding:0;}
.cep-idx .side p{color:var(--suave);margin:.8rem 0 0;}
.cep-idx table{width:100%;border-collapse:collapse;}
.cep-idx td{padding:.62rem 1.2rem;border-bottom:1px solid var(--linea);font-size:.9rem;vertical-align:middle;}
.cep-idx tr:last-child td{border-bottom:0;}
.cep-idx td.n{font-family:var(--mono);color:var(--tenue);width:56px;font-size:.8rem;}
.cep-idx td.d{font-family:var(--mono);font-size:.76rem;color:var(--suave);}
.cep-idx td.e{width:130px;white-space:nowrap;}
.cep-idx tr.act td{background:var(--hover);} .cep-idx tr.act td.n{color:var(--acento);}
.sq{display:inline-block;width:7px;height:7px;margin-right:.5rem;vertical-align:1px;background:var(--tenue);}
.sq.ok{background:var(--ok);} .sq.act{background:var(--acento);}
@media (max-width:900px){.cep-idx{grid-template-columns:1fr;} .cep-idx .side{border-right:0;border-bottom:1px solid var(--tinta);}}
/* ---------- encabezado de cada paso ---------- */
.cep-mod{margin:1.8rem 0 1.2rem;}
.cep-mod h1{font-size:clamp(1.8rem,2.6vw,2.3rem) !important;margin:.5rem 0 0;padding:0;line-height:1.1;letter-spacing:-.025em;}
.cep-mod p{margin:.45rem 0 0;color:var(--suave);font-size:.95rem;max-width:820px;}
.cep-guia{display:grid;grid-template-columns:repeat(3,1fr);margin:0 0 1.2rem;border:1px solid var(--linea);}
.cep-guia div{padding:.75rem 1rem;font-size:.84rem;line-height:1.45;color:#3a3935;}
.cep-guia div+div{border-left:1px solid var(--linea);}
.cep-guia .k{display:block;font-family:var(--mono);font-size:.66rem;font-weight:500;letter-spacing:.07em;text-transform:uppercase;
  color:var(--suave);margin-bottom:.3rem;}
.cep-guia b:not(.k){font-weight:500;color:var(--tinta);}
.cep-guia div.sig .k{color:var(--acento);}
@media (max-width:900px){.cep-guia{grid-template-columns:1fr;} .cep-guia div+div{border-left:0;border-top:1px solid var(--linea);}}
/* ---------- secciones ---------- */
.cep-sec{display:flex;align-items:baseline;gap:.8rem;margin:2rem 0 .8rem;padding-top:.7rem;border-top:1px solid var(--tinta);
  font-weight:500;font-size:1.05rem;color:var(--tinta);}
.cep-sec .k{font-family:var(--mono);font-size:.68rem;letter-spacing:.07em;color:var(--suave);text-transform:uppercase;}
.cep-eyebrow{font-family:var(--mono);font-size:.68rem;letter-spacing:.07em;text-transform:uppercase;color:var(--suave);
  margin:2.6rem 0 .5rem;padding-top:.8rem;border-top:1px solid var(--tinta);}
.cep-h2{font-size:1.55rem;font-weight:500;color:var(--tinta);line-height:1.15;margin:0 0 .4rem;letter-spacing:-.02em;max-width:820px;}
.cep-lead{color:var(--suave);font-size:.92rem;line-height:1.5;max-width:720px;margin-bottom:1.1rem;}
/* ---------- indicadores ---------- */
.cep-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin:.4rem 0 1.2rem;border:1px solid var(--linea);}
.cep-kpi{padding:.8rem 1rem .85rem;border-right:1px solid var(--linea);min-width:0;}
.cep-kpi:last-child{border-right:0;}
.cep-kpi .lab{font-family:var(--mono);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;color:var(--suave);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.cep-kpi .val{font-family:var(--mono);font-size:1.4rem;color:var(--c,var(--tinta));line-height:1.2;margin-top:.3rem;
  letter-spacing:-.02em;word-break:break-word;}
.cep-kpi .sub{font-family:var(--mono);font-size:.68rem;color:var(--tenue);margin-top:.15rem;}
/* ---------- interpretación ---------- */
.cep-ins{border:1px solid var(--c);padding:.75rem 1rem .8rem;margin:.6rem 0 1.1rem;background:transparent;}
.cep-ins h4{margin:0 0 .35rem;font-family:var(--mono) !important;font-size:.7rem;font-weight:500 !important;letter-spacing:.07em;
  text-transform:uppercase;color:var(--c);padding:0;}
.cep-ins h4 a{display:none !important;}
.cep-ins ul{margin:0;padding:0;list-style:none;}
.cep-ins li{padding:.32rem 0;font-size:.88rem;line-height:1.5;color:#2b2a27;border-top:1px solid var(--linea2);}
.cep-ins li:first-child{border-top:0;padding-top:0;}
.cep-ins.ok{--c:var(--ok);} .cep-ins.alerta{--c:var(--alerta);} .cep-ins.mal{--c:var(--mal);} .cep-ins.info{--c:var(--linea);}
.cep-ins.info h4{color:var(--suave);}
/* ---------- banda fotográfica ---------- */
.cep-banda{display:grid;grid-template-columns:7fr 5fr;margin:2.6rem -2.5rem 0;border-top:1px solid var(--tinta);border-bottom:1px solid var(--tinta);}
.cep-banda .f{min-height:280px;background:#2a2a28 center/cover no-repeat;border-right:1px solid var(--tinta);}
.cep-banda .t{padding:2rem 2.5rem;display:flex;flex-direction:column;justify-content:flex-end;}
.cep-banda h3{font-size:1.6rem;line-height:1.15;margin:.7rem 0 0;padding:0;}
.cep-banda p{color:var(--suave);margin:.6rem 0 0;font-size:.92rem;}
/* ---------- empresa ---------- */
.cep-emp{display:grid;grid-template-columns:5fr 7fr;border:1px solid var(--tinta);margin:.4rem 0 1.2rem;}
.cep-emp .tx{padding:1.6rem 1.6rem 1.4rem;display:flex;flex-direction:column;justify-content:flex-end;gap:.2rem;border-right:1px solid var(--tinta);}
.cep-emp .ft{min-height:230px;background:#2a2a28 center/cover no-repeat;}
.cep-emp .logo{width:56px;height:56px;background:#fff center/contain no-repeat;border:1px solid var(--linea);margin-bottom:auto;}
.cep-emp h1{margin:.5rem 0 0;font-size:1.8rem !important;line-height:1.1;padding:0;}
.cep-emp p{margin:.35rem 0 0;color:var(--suave);font-size:.92rem;}
.cep-mv{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin:.6rem 0 1.2rem;border:1px solid var(--linea);}
.cep-mv .t{padding:.9rem 1rem;} .cep-mv .t+.t{border-left:1px solid var(--linea);}
.cep-mv .h{font-family:var(--mono);font-size:.66rem;letter-spacing:.07em;text-transform:uppercase;color:var(--suave);margin-bottom:.4rem;}
.cep-mv .x{color:var(--tinta);font-size:.95rem;line-height:1.5;}
.cep-mv .x.vacio{color:var(--tenue);font-size:.85rem;}
.cep-chips{display:flex;flex-wrap:wrap;gap:.35rem;margin:.3rem 0;}
.cep-chips span{border:1px solid var(--linea);color:var(--tinta);padding:.2rem .6rem;font-size:.8rem;font-family:var(--mono);}
/* ---------- diagrama de proceso ---------- */
.cep-flujo{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(150px,1fr);border:1px solid var(--linea);overflow-x:auto;
  margin:.4rem 0 1rem;}
.cep-paso{padding:.85rem .9rem;border-right:1px solid var(--linea);}
.cep-paso:last-child{border-right:0;}
.cep-paso .n{font-family:var(--mono);font-size:.66rem;color:var(--tenue);letter-spacing:.06em;}
.cep-paso .t{font-weight:500;color:var(--tinta);font-size:.92rem;line-height:1.2;margin-top:.35rem;}
.cep-paso .d{font-size:.78rem;color:var(--suave);margin-top:.35rem;line-height:1.45;}
.cep-paso .ctq{display:inline-block;margin:.5rem .2rem 0 0;font-family:var(--mono);font-size:.66rem;padding:.1rem .4rem;
  border:1px solid var(--ok);color:var(--ok);}
.cep-paso .ctq.at{border-color:var(--mal);color:var(--mal);}
/* ---------- tarjetas varias ---------- */
.cep-mods{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));border:1px solid var(--linea);}
.cep-mc{padding:.9rem 1rem;border-right:1px solid var(--linea);border-bottom:1px solid var(--linea);}
.cep-mc .top{font-family:var(--mono);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;color:var(--suave);}
.cep-mc b{display:block;margin-top:.35rem;color:var(--tinta);font-weight:500;} .cep-mc small{color:var(--suave);font-size:.8rem;line-height:1.45;}
.cep-check{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));border:1px solid var(--linea);margin:.4rem 0 1rem;}
.cep-check > div{display:flex;gap:.7rem;align-items:flex-start;padding:.7rem .9rem;border-right:1px solid var(--linea);
  border-bottom:1px solid var(--linea);}
.cep-check i{width:7px;height:7px;flex:0 0 7px;margin-top:.45rem;background:var(--tenue);}
.cep-check .si i{background:var(--ok);} .cep-check b{display:block;font-size:.86rem;color:var(--tinta);font-weight:500;}
.cep-check small{color:var(--suave);font-size:.78rem;}
.cep-req{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));border-top:1px solid var(--tinta);}
.cep-req .t{padding:1rem 1.2rem 1rem 0;border-bottom:1px solid var(--linea);}
.cep-req .h{display:flex;align-items:baseline;gap:.6rem;color:var(--tinta);font-weight:500;font-size:1rem;}
.cep-req .h span.p{margin-left:auto;font-family:var(--mono);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;color:var(--tenue);}
.cep-req ul{margin:.4rem 0 0 1rem;padding:0;} .cep-req li{font-size:.85rem;line-height:1.5;margin:.2rem 0;color:#3a3935;}
.cep-tabla{width:100%;border-collapse:collapse;border:1px solid var(--linea);font-size:.86rem;margin-bottom:1rem;}
.cep-tabla th{text-align:left;padding:.5rem .8rem;font-family:var(--mono);font-size:.66rem;font-weight:500;letter-spacing:.06em;
  text-transform:uppercase;color:var(--suave);border-bottom:1px solid var(--tinta);}
.cep-tabla td{padding:.5rem .8rem;border-top:1px solid var(--linea2);color:var(--tinta);}
.cep-tabla td:first-child{font-weight:500;white-space:nowrap;}
.cep-ruta .p{display:grid;grid-template-columns:44px 1fr;gap:.8rem;padding:.7rem 0;border-top:1px solid var(--linea);}
.cep-ruta .n{font-family:var(--mono);font-size:.8rem;color:var(--tenue);}
.cep-ruta .b b{font-weight:500;} .cep-ruta .b small{display:block;color:var(--suave);font-size:.84rem;margin-top:.15rem;}
.cep-ruta .b em{display:block;font-style:normal;font-family:var(--mono);font-size:.7rem;color:var(--acento);margin-top:.3rem;}
/* ---------- widgets nativos ---------- */
div[data-testid="stMetric"]{border:1px solid var(--linea);padding:.7rem .9rem;}
div[data-testid="stMetricValue"]{font-family:var(--mono);}
.stTabs [data-baseweb="tab-list"]{gap:0;border-bottom:1px solid var(--tinta);background:transparent;}
.stTabs [data-baseweb="tab"]{padding:.5rem .9rem;height:auto;background:transparent;border:1px solid transparent;border-bottom:0;
  margin-bottom:-1px;}
.stTabs [data-baseweb="tab"] p{font-size:.84rem;color:var(--suave);}
.stTabs [aria-selected="true"]{border-color:var(--tinta);background:var(--fondo);}
.stTabs [aria-selected="true"] p{color:var(--tinta);font-weight:500;}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}
div[data-testid="stPlotlyChart"]{border:1px solid var(--linea);background:var(--papel);padding:.4rem .4rem .2rem;}
[data-testid="stMain"] div[data-testid="stExpander"] details{border-color:var(--linea);background:transparent;}
[data-testid="stMain"] div[data-testid="stExpander"] summary p{font-weight:500;font-size:.88rem;}
.stButton>button,.stDownloadButton>button,[data-testid="stBaseButton-secondary"]{font-weight:500;border-color:var(--tinta);
  background:transparent;}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:var(--tinta);border-color:var(--tinta);color:var(--fondo);}
.stButton>button[kind="primary"]:hover,.stDownloadButton>button[kind="primary"]:hover{background:var(--acento);border-color:var(--acento);color:#fff;}
[data-testid="stAlert"] > div{background:transparent !important;border:1px solid var(--linea);color:var(--tinta);}
[data-testid="stAlertContentWarning"]{border-left:0;} [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p{font-size:.88rem;}
[data-testid="stAlert"] svg{display:none;}
div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) > div{border-color:var(--alerta);}
div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) > div{border-color:var(--mal);}
div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) > div{border-color:var(--ok);}
[data-testid="stDataFrame"]{border:1px solid var(--linea);}
[data-testid="stCaptionContainer"]{font-size:.8rem;}
hr{border-color:var(--linea) !important;}
[data-tag]{background:transparent !important;border:1px solid var(--tinta) !important;color:var(--tinta) !important;}
[data-tag] span{color:var(--tinta) !important;font-family:var(--mono);font-size:.76rem;}
[data-tag] button{color:var(--tinta) !important;}
[data-testid="stProgress"] [role="progressbar"] > div{height:3px !important;}
[data-testid="stProgress"] [role="progressbar"] > div > div > div{background:var(--tinta) !important;}
/* ---------- pie ---------- */
.cep-pie{margin:4rem -2.5rem 0;border-top:1px solid var(--tinta);padding:1rem 2.5rem 0;display:flex;justify-content:space-between;
  gap:1rem;flex-wrap:wrap;font-family:var(--mono);font-size:.7rem;color:var(--suave);}
</style>
"""


_SIN_TRADUCCION = """<script>
(function () {
  // El traductor automático del navegador (p. ej. Chrome) cambia el texto de la página por su cuenta:
  // traduce «LIE» como «MENTIRA», «n» como «norte», y al reemplazar nodos rompe la interfaz
  // (error «NotFoundError: removeChild»). Se marca la página como no traducible.
  var d = window.parent.document;
  d.documentElement.setAttribute("translate", "no");
  d.documentElement.classList.add("notranslate");
  if (d.body) { d.body.setAttribute("translate", "no"); d.body.classList.add("notranslate"); }
  if (!d.querySelector('meta[name="google"][content="notranslate"]')) {
    var m = d.createElement("meta"); m.name = "google"; m.content = "notranslate"; d.head.appendChild(m);
  }
})();
</script>"""


def aplicar():
    st.markdown(CSS, unsafe_allow_html=True)
    with st.container(key="sin_traduccion"):
        st.html(_SIN_TRADUCCION, unsafe_allow_javascript=True)


def _e(t):
    return html.escape(str(t if t is not None else ""))


def _md(t):
    """Escapa el texto y convierte **negrita** en <b>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _e(t))


def foto(nombre):
    return f"{RUTA_FOTOS}/{nombre}.jpg"


def _fondo(url):
    return f"background-image:url('{url}')" if url else ""


def _foto_modulo(titulo):
    t = str(titulo).lower()
    return foto(next((f for clave, f in FOTOS_MODULO if clave in t), "planta"))


def hero(titulo, texto, etiqueta="", url_foto=None, cifras=None, pie_foto="Fig. 01  Planta de producción"):
    """Portada partida: texto a la izquierda y fotografía grande a la derecha; debajo, franja de cifras.
    `titulo` admite *texto* para el punto o la palabra en color de acento."""
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", _e(titulo))
    largo = ' class="largo"' if len(str(titulo)) > 42 else ""
    st.markdown(f'<div class="cep-hero"><div class="l"><div class="cep-lab">{_e(etiqueta)}</div><h1{largo}>{t}</h1>'
                f'<p>{_e(texto)}</p></div><div class="r" style="{_fondo(url_foto or foto("portada"))}">'
                f'<div class="cap cep-lab">{_e(pie_foto)}</div></div></div>', unsafe_allow_html=True)
    if cifras:
        franja(cifras)


def franja(cifras):
    """Franja de cifras a todo el ancho: lista de (valor, etiqueta) o (valor, etiqueta, detalle[, color])."""
    celdas = []
    for c in cifras:
        v, k = c[0], c[1]
        sub = c[2] if len(c) > 2 else ""
        col = f' style="color:{c[3]}"' if len(c) > 3 and c[3] else ""
        txt = " t" if re.search(r"[a-zA-Zñáéíóú]{4,}", str(v)) else ""
        celdas.append(f'<div><div class="cep-lab">{_e(k)}</div><div class="v{txt}"{col}>{_e(v)}</div>'
                      f'<div class="s">{_e(sub)}</div></div>')
    st.markdown(f'<div class="cep-strip">{"".join(celdas)}</div>', unsafe_allow_html=True)


def indice_pasos(titulo, texto, filas):
    """Índice de la ruta: filas (número, paso, detalle, estado: 'ok'|'act'|'', texto del estado)."""
    tr = "".join(f'<tr class="{"act" if e == "act" else ""}"><td class="n">{int(n):02d}</td><td>{_e(p)}</td>'
                 f'<td class="d">{_e(d)}</td><td class="e"><span class="sq {e}"></span><span class="cep-lab">{_e(et)}</span></td></tr>'
                 for n, p, d, e, et in filas)
    st.markdown(f'<div class="cep-idx"><div class="side"><div class="cep-lab">Ruta de trabajo</div><h2>{_e(titulo)}</h2>'
                f'<p>{_md(texto)}</p></div><table>{tr}</table></div>', unsafe_allow_html=True)


def banda(nombre_foto, etiqueta, titulo, texto=""):
    """Fotografía grande a sangre con un bloque de texto a la derecha."""
    st.markdown(f'<div class="cep-banda"><div class="f" style="{_fondo(foto(nombre_foto))}"></div><div class="t">'
                f'<div class="cep-lab">{_e(etiqueta)}</div><h3>{_e(titulo)}</h3><p>{_md(texto)}</p></div></div>',
                unsafe_allow_html=True)


def encabezado(icono_, titulo, subtitulo="", etiqueta=""):
    """Encabezado de cada paso: ruta en monoespaciada, título y una línea de descripción."""
    st.markdown(f'<div class="cep-mod"><div class="cep-lab">{_e(PASO_TEXTO or etiqueta)}</div><h1>{_e(titulo)}</h1>'
                f'<p>{_e(subtitulo)}</p></div>', unsafe_allow_html=True)
    global DESPUES_ENCABEZADO
    if DESPUES_ENCABEZADO is not None:
        fn, DESPUES_ENCABEZADO = DESPUES_ENCABEZADO, None
        fn()


def seccion(icono_, titulo):
    st.markdown(f'<div class="cep-sec"><span>{_e(titulo)}</span></div>', unsafe_allow_html=True)


def kpis(items):
    """items: lista de dict(icono, etiqueta, valor, sub, color). El color sólo se usa para estados (verde/rojo)."""
    def _c(i):
        c = str(i.get("color", "")).lower()
        return f"--c:{c}" if c in (VERDE.lower(), ROJO.lower(), "#2f7d4f", "#b42318") else ""
    tarjetas = "".join(
        f'<div class="cep-kpi" style="{_c(i)}"><div class="lab">{_e(i["etiqueta"])}</div><div class="val">{_e(i["valor"])}</div>'
        f'<div class="sub">{_e(i.get("sub", ""))}</div></div>' for i in items)
    st.markdown(f'<div class="cep-kpis">{tarjetas}</div>', unsafe_allow_html=True)


def interpretacion(titulo, puntos, nivel="info"):
    """Cuadro de lectura automática con borde fino del color del estado. nivel: ok, alerta, mal, info."""
    lis = "".join(f"<li>{_md(p)}</li>" for p in puntos if p)
    st.markdown(f'<div class="cep-ins {nivel}"><h4>{_e(titulo)}</h4><ul>{lis}</ul></div>', unsafe_allow_html=True)


ICONOS_ETAPA = [("traslado", "package"), ("transport", "package"), ("lav", "droplet"), ("selecc", "search"),
                ("empa", "package"), ("almac", "building-2"), ("recib", "download"), ("mezcl", "refresh-cw"),
                ("corta", "scissors"), ("ensam", "settings"), ("inspec", "scan-line"), ("calib", "ruler"),
                ("despach", "package"), ("control", "clipboard-check"), ("medic", "ruler-dimension-line")]


def etapas_de_texto(texto):
    """Separa el texto «1. Recepción: … 2. Proceso: …» en [(nombre, descripción)]."""
    partes = re.split(r"(?:^|\s)(\d+)\.\s+", str(texto or "").strip())
    etapas = []
    for i in range(2, len(partes), 2):
        bloque = partes[i].strip().rstrip(".")
        nombre, _, desc = bloque.partition(":")
        etapas.append((nombre.strip(), desc.strip()))
    if not etapas and str(texto or "").strip():
        etapas = [(l.strip(), "") for l in re.split(r"[\n;→>]+", str(texto)) if l.strip()]
    return etapas


def _icono(nombre):
    n = nombre.lower()
    return next((ic for clave, ic in ICONOS_ETAPA if clave in n), "settings")


def flujo_proceso(perfil):
    etapas = etapas_de_texto(perfil.get("Etapas del proceso", ""))
    if not etapas:
        st.info("Escriba las etapas del proceso en el paso 2 (por ejemplo «1. Recepción: … 2. Empaque: …») para ver el diagrama.")
        return
    variables = perfil.get("variables", [])
    piezas = []
    for k, (nombre, desc) in enumerate(etapas, 1):
        clave = nombre.lower().split()[0][:5] if nombre else ""
        ctq = [v for v in variables if clave and clave in str(v.get("Etapa del proceso", "")).lower()]
        chips_ = "".join(f'<span class="ctq{" at" if str(v.get("Tipo", "")).startswith("Atrib") else ""}">'
                         f'{_e(v["Característica"])}</span>' for v in ctq)
        corta = desc if len(desc) <= 110 else desc[:107].rsplit(" ", 1)[0] + "…"
        piezas.append(f'<div class="cep-paso"><div class="n">{k:02d} →</div><div class="t">{_e(nombre)}</div>'
                      f'<div class="d">{_e(corta)}</div>{chips_}</div>')
    st.markdown('<div class="cep-flujo">' + "".join(piezas) + "</div>", unsafe_allow_html=True)


def tarjetas_modulos(items):
    """items: lista de (icono, título, descripción, listo:bool)."""
    t = "".join(f'<div class="cep-mc"><div class="top"><span class="sq {"ok" if ok else ""}"></span>'
                f'{"Con resultados" if ok else "Pendiente"}</div><b>{_e(ti)}</b><small>{_e(de)}</small></div>'
                for ic, ti, de, ok in items)
    st.markdown(f'<div class="cep-mods">{t}</div>', unsafe_allow_html=True)


def stepper(pasos, actual, hechos):
    """Compatibilidad: la ruta de pasos ahora vive en la barra lateral."""
    return


def guia_paso(necesita, hace, siguiente):
    st.markdown(f'<div class="cep-guia"><div><b class="k">Necesita</b>{_md(necesita)}</div><div><b class="k">Hace</b>'
                f'{_md(hace)}</div><div class="sig"><b class="k">Después</b>{_md(siguiente)}</div></div>', unsafe_allow_html=True)


def checklist(items):
    """items: (texto, cumple, detalle)."""
    h = "".join(f'<div class="{"si" if ok else ""}"><i></i><span><b>{_e(t)}</b>'
                f'<small>{_e(d)}</small></span></div>' for t, ok, d in items)
    st.markdown(f'<div class="cep-check">{h}</div>', unsafe_allow_html=True)


def tarjetas_requisitos(grupos):
    h = "".join(f'<div class="t"><div class="h"><span>{_e(t)}</span><span class="p">{_e(paso)}</span></div><ul>'
                + "".join(f"<li>{_md(x)}</li>" for x in items) + "</ul></div>" for ic, t, paso, items in grupos)
    st.markdown(f'<div class="cep-req">{h}</div>', unsafe_allow_html=True)


def tabla_simple(columnas, filas):
    h = "".join(f"<th>{_e(c)}</th>" for c in columnas)
    b = "".join("<tr>" + "".join(f"<td>{_e(x)}</td>" for x in f) + "</tr>" for f in filas)
    st.markdown(f'<table class="cep-tabla"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>', unsafe_allow_html=True)


def ruta(pasos):
    """Lista numerada de pasos: [(número, título, descripción, resultado)]."""
    h = "".join(f'<div class="p"><div class="n">{int(n):02d}</div><div class="b"><b>{_e(t)}</b><small>{_e(d)}</small>'
                f'<em>{_e(r)}</em></div></div>' for n, t, d, r in pasos)
    st.markdown(f'<div class="cep-ruta">{h}</div>', unsafe_allow_html=True)


def marca_html(claro=False):
    return f'<div class="cep-top-marca">{logo()}<span>Sigmora</span><span class="cep-marca-sub">CEP Studio</span></div>'


def titulo_seccion(eyebrow, titulo, lead=""):
    st.markdown(f'<div class="cep-eyebrow">{_e(eyebrow)}</div><div class="cep-h2">{_e(titulo)}</div>'
                + (f'<div class="cep-lead">{_md(lead)}</div>' if lead else ""), unsafe_allow_html=True)


def funciones(items):
    """Compatibilidad con versiones anteriores (ya no se usa en el inicio)."""
    return


def cta(titulo, texto, nombre_foto="equipo"):
    banda(nombre_foto, "Siguiente", titulo, texto)


def pie(empresa, pasos):
    import datetime as _dt
    st.markdown(f'<div class="cep-pie"><span>Sigmora CEP Studio · Control estadístico de procesos'
                f'{" · " + _e(empresa) if empresa else ""}</span>'
                f'<span>Fotografías: Unsplash · Tipografía: IBM Plex · {_dt.date.today().year}</span></div>',
                unsafe_allow_html=True)


def cabecera_empresa(foto_url, nombre, subtitulo, etiqueta="", logo_url=None):
    """Cabecera del tablero de la empresa: texto a la izquierda y su fotografía (o una genérica) a la derecha."""
    lg = f'<div class="logo" style="{_fondo(logo_url)}"></div>' if logo_url else ""
    st.markdown(f'<div class="cep-emp"><div class="tx">{lg}<div class="cep-lab">{_e(etiqueta)}</div><h1>{_e(nombre)}</h1>'
                f'<p>{_e(subtitulo)}</p></div><div class="ft" style="{_fondo(foto_url or foto("planta"))}"></div></div>',
                unsafe_allow_html=True)


def tarjetas_texto(items):
    """items: (icono, título, texto, color). Texto vacío se muestra como «Sin registrar»."""
    h = "".join(f'<div class="t"><div class="h">{_e(t)}</div>'
                f'<div class="x{"" if str(x or "").strip() else " vacio"}">'
                f'{_e(x) if str(x or "").strip() else "Sin registrar."}</div></div>'
                for ic, t, x, c in items)
    st.markdown(f'<div class="cep-mv">{h}</div>', unsafe_allow_html=True)


def chips(lista):
    if lista:
        st.markdown('<div class="cep-chips">' + "".join(f"<span>{_e(x)}</span>" for x in lista) + "</div>",
                    unsafe_allow_html=True)
