"""
Gráficos (plotly) usados por la aplicación y los reportes.
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

import plotly.io as pio

AZUL = "#0e0e0c"      # tinta: serie principal
ROJO = "#c0261c"
NARANJA = "#d9480f"   # acento
VERDE = "#1f7a4d"
GRIS = "#9a988f"
DORADO = "#b54708"
TEXTO = "#0e0e0c"
PALETA = [AZUL, NARANJA, VERDE, "#6b6a64", ROJO, "#3a3935", "#c9c7bf", GRIS]
_MONO = "IBM Plex Mono, Menlo, Consolas, monospace"
_SANS = "IBM Plex Sans, Segoe UI, Arial, sans-serif"

# Plantilla visual propia de Sigmora CEP Studio para todos los gráficos: fondo transparente, rejilla tenue, números en monoespaciada
_t = go.layout.Template(pio.templates["plotly_white"])
_t.layout.update(
    font=dict(family=_MONO, size=11, color="#6b6a64"),
    title=dict(font=dict(family=_SANS, size=14, color=TEXTO, weight=500), x=0.005, xanchor="left"),
    colorway=PALETA, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(bgcolor="#0e0e0c", bordercolor="#0e0e0c", font=dict(color="#f3f2ee", family=_MONO, size=11)),
    xaxis=dict(gridcolor="rgba(0,0,0,0)", zerolinecolor="#d9d7d0", linecolor="#0e0e0c", ticks="outside", tickcolor="#d9d7d0",
               title=dict(font=dict(family=_SANS, size=12, color="#6b6a64"))),
    yaxis=dict(gridcolor="#e6e4dd", zerolinecolor="#d9d7d0", linecolor="rgba(0,0,0,0)",
               title=dict(font=dict(family=_SANS, size=12, color="#6b6a64"))),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, family=_SANS, color="#3a3935"), orientation="h",
                yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=56),
)
pio.templates["cep"] = _t
pio.templates.default = "cep"

ZONAS = [("C", "rgba(14,14,12,0.025)"), ("B", "rgba(14,14,12,0.045)"), ("A", "rgba(14,14,12,0.07)")]


def _banda(fig, x, lo, hi, color, forma, nombre, mostrar):
    fig.add_trace(go.Scatter(x=x, y=lo, mode="lines", line=dict(width=0, shape=forma), hoverinfo="skip",
                             showlegend=False, legendgroup="zonas"))
    fig.add_trace(go.Scatter(x=x, y=hi, mode="lines", line=dict(width=0, shape=forma), fill="tonexty",
                             fillcolor=color, hoverinfo="skip", name=nombre, showlegend=mostrar, legendgroup="zonas"))


def carta_control(carta, senales=None, excluidos=None, titulo=None, altura=430, zonas=True):
    """Dibuja una carta de control con LC, LCS, LCI, zonas A/B/C sombreadas, puntos fuera y puntos con patrón.

    Zonas: la distancia entre la LC y cada límite se divide en tres franjas iguales (C junto a la LC, luego B y A
    junto al límite), como en la lectura de patrones de la sección 4.5.
    senales:   conjunto de índices (1..k) con algún patrón no aleatorio.
    excluidos: conjunto de índices excluidos del cálculo de límites (cepillado).
    """
    x = list(range(1, len(carta["valores"]) + 1))
    y = np.asarray(carta["valores"], float)
    lc, lcs, lci = (np.asarray(carta[k], float) for k in ("lc", "lcs", "lci"))
    forma = "hv" if (_varia(lcs) or _varia(lci)) else "linear"
    fig = go.Figure()
    if zonas:
        sup, inf = (lcs - lc) / 3, (lc - lci) / 3
        for k, (letra, col) in enumerate(ZONAS):
            _banda(fig, x, lc + k * sup, lc + (k + 1) * sup, col, forma, f"Zona {letra}", True)
            _banda(fig, x, lc - (k + 1) * inf, lc - k * inf, col, forma, f"Zona {letra}", False)
    fig.add_trace(go.Scatter(x=x, y=lcs, mode="lines", name="LCS", line=dict(color=ROJO, dash="dash", width=1.2, shape=forma)))
    fig.add_trace(go.Scatter(x=x, y=lc, mode="lines", name="LC", line=dict(color=AZUL, width=1)))
    fig.add_trace(go.Scatter(x=x, y=lci, mode="lines", name="LCI", line=dict(color=ROJO, dash="dash", width=1.2, shape=forma)))
    etiquetas = [str(e) for e in carta.get("etiquetas", x)]
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=carta["nombre"],
                             line=dict(color=AZUL, width=1.4),
                             marker=dict(size=6, color="#f3f2ee", line=dict(color=AZUL, width=1.3)), text=etiquetas,
                             hovertemplate="Punto %{x} · subgrupo %{text}<br><b>%{y:.5g}</b><extra></extra>"))
    fuera = [i for i in range(len(y)) if not np.isnan(y[i]) and (y[i] > lcs[i] or y[i] < lci[i])]
    if senales:
        idx = [i - 1 for i in sorted(senales) if (i - 1) not in fuera and i - 1 < len(y)]
        if idx:
            fig.add_trace(go.Scatter(x=[x[i] for i in idx], y=y[idx], mode="markers", name="Patrón no aleatorio",
                                     marker=dict(color=NARANJA, size=13, symbol="diamond",
                                                 line=dict(color="#f3f2ee", width=1.5))))
    if fuera:
        fig.add_trace(go.Scatter(x=[x[i] for i in fuera], y=y[fuera], mode="markers", hoverinfo="skip",
                                 showlegend=False, marker=dict(color="rgba(180,35,24,0.22)", size=28)))
        fig.add_trace(go.Scatter(x=[x[i] for i in fuera], y=y[fuera], mode="markers", name="Fuera de control",
                                 marker=dict(color=ROJO, size=13, line=dict(color="#f3f2ee", width=2))))
    if excluidos:
        idx = [i - 1 for i in sorted(excluidos) if i - 1 < len(y)]
        fig.add_trace(go.Scatter(x=[x[i] for i in idx], y=y[idx], mode="markers", name="Excluido (cepillado)",
                                 marker=dict(color=GRIS, size=17, symbol="circle-open", line=dict(width=2.5))))
    for nombre, arr, col in (("LCS", lcs, ROJO), ("LC", lc, VERDE), ("LCI", lci, ROJO)):
        if not _varia(arr):
            fig.add_annotation(x=x[-1], y=arr[-1], text=f"<b>{nombre}</b> {arr[-1]:.5g}", showarrow=False,
                               xanchor="left", xshift=8, font=dict(size=11, color=col),
                               bgcolor="rgba(243,242,238,0.9)")
    if zonas and not _varia(lcs) and not _varia(lci):
        for k, (letra, _) in enumerate(ZONAS):
            for centro in (lc[0] + (k + 0.5) * (lcs[0] - lc[0]) / 3, lc[0] - (k + 0.5) * (lc[0] - lci[0]) / 3):
                fig.add_annotation(x=0, xref="paper", y=centro, text=letra, showarrow=False, xanchor="left", xshift=3,
                                   font=dict(size=10, color=GRIS), opacity=0.8)
    n_f = len(fuera)
    sub = (f"<span style='color:{ROJO}'>● {n_f} punto(s) fuera de control</span>" if n_f
           else f"<span style='color:{VERDE}'>● Todos los puntos dentro de los límites</span>")
    fig.update_layout(title=dict(text=f"{titulo or carta['nombre']}<br><sup>{sub}</sup>"), height=altura,
                      margin=dict(l=55, r=125, t=95, b=45), xaxis_title="Número de subgrupo / muestra",
                      legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right", font=dict(size=11),
                                  traceorder="reversed"),
                      hovermode="closest")
    return fig


def _varia(a):
    a = np.asarray(a, float)
    return not np.allclose(a, a[0])


def histograma_capacidad(x, media, sigma, lse=None, lie=None, vn=None, nbins=None, titulo="Histograma y especificaciones"):
    """Histograma con curva normal (X̄, σ); la zona fuera de especificaciones se sombrea en rojo."""
    x = np.asarray(x, float)
    fig = go.Figure()
    lo = min(x.min(), (lie if lie is not None else x.min()), media - 4 * sigma)
    hi = max(x.max(), (lse if lse is not None else x.max()), media + 4 * sigma)
    if lie is not None or lse is not None:
        fig.add_vrect(x0=lie if lie is not None else lo, x1=lse if lse is not None else hi,
                      fillcolor="rgba(14,14,12,0.03)", line_width=0, layer="below")
    fig.add_trace(go.Histogram(x=x, nbinsx=nbins, histnorm="probability density", name="Datos",
                               marker=dict(color="rgba(14,14,12,0.55)", line=dict(color="#f3f2ee", width=1.2))))
    xs = np.linspace(lo, hi, 500)
    ys = stats.norm.pdf(xs, media, sigma)
    for cond, nom in ((xs <= lie if lie is not None else None, "Fuera (bajo LIE)"),
                      (xs >= lse if lse is not None else None, "Fuera (sobre LSE)")):
        if cond is not None and cond.any():
            fig.add_trace(go.Scatter(x=xs[cond], y=ys[cond], mode="lines", fill="tozeroy", line=dict(width=0),
                                     fillcolor="rgba(180,35,24,0.35)", name=nom, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name="Normal (X̄, σ)", line=dict(color=TEXTO, width=2.4)))
    for val, nom, col in ((lie, "LIE", ROJO), (lse, "LSE", ROJO), (vn, "VN", VERDE), (media, "X̄", DORADO)):
        if val is not None:
            fig.add_vline(x=val, line=dict(color=col, width=2.2, dash="dash" if nom in ("LIE", "LSE") else "dot"),
                          annotation_text=f"<b>{nom}</b> {val:.4g}", annotation_font_color=col,
                          annotation_position="bottom right" if nom == "X̄" else "top")
    fig.update_layout(title=titulo, height=420, bargap=0.03, legend=dict(orientation="h", y=-0.2),
                      yaxis_title="Densidad")
    return fig


def medidor(valor, nombre, maximo=2.0, ayuda=""):
    """Indicador de barra (bullet) para un índice de capacidad con las clases de la presentación
    (< 0,67 · 0,67–1 · 1–1,33 · > 1,33): franjas grises y marca en 1,33."""
    v = float(valor) if valor is not None and np.isfinite(valor) else 0.0
    color = VERDE if v >= 1.33 else (TEXTO if v >= 1 else ROJO)
    tope = max(maximo, v * 1.1)
    fig = go.Figure(go.Indicator(
        mode="number+gauge", value=v, number=dict(valueformat=".3f", font=dict(size=28, color=color, family=_MONO)),
        domain=dict(x=[0.3, 1], y=[0.15, 0.75]),
        title=dict(text=f"{nombre}<br><span style='font-size:10px;color:{GRIS}'>{ayuda}</span>",
                   font=dict(size=14, family=_SANS, color=TEXTO), align="left"),
        gauge=dict(shape="bullet", axis=dict(range=[0, tope], tickvals=[0, 0.67, 1, 1.33, maximo],
                                             tickfont=dict(size=10, family=_MONO, color=GRIS), tickcolor="#d9d7d0"),
                   bar=dict(color=color, thickness=0.32), bgcolor="rgba(0,0,0,0)", borderwidth=0,
                   steps=[dict(range=[0, 0.67], color="#dedcd5"), dict(range=[0.67, 1], color="#e6e4dd"),
                          dict(range=[1, 1.33], color="#ecebe5"), dict(range=[1.33, tope], color="#f1f0ec")],
                   threshold=dict(line=dict(color=NARANJA, width=2), thickness=0.9, value=1.33))))
    fig.update_layout(height=150, margin=dict(l=16, r=24, t=16, b=16))
    return fig


def dona(valores, etiquetas, titulo, colores=None, centro=""):
    fig = go.Figure(go.Pie(values=valores, labels=etiquetas, hole=0.62, sort=False,
                           marker=dict(colors=colores or PALETA, line=dict(color="#f3f2ee", width=2)),
                           textinfo="percent", hovertemplate="%{label}: %{value:,}<extra></extra>"))
    fig.update_layout(title=titulo, height=320, margin=dict(l=10, r=10, t=55, b=10),
                      annotations=[dict(text=centro, showarrow=False, font=dict(size=15, color=TEXTO))],
                      legend=dict(orientation="v", x=1, y=0.5))
    return fig


def dispersion_consecutivos(a, b, titulo="Dato t vs dato t+1 (independencia)"):
    fig = go.Figure(go.Scatter(x=a, y=b, mode="markers", marker=dict(color=AZUL, size=7)))
    fig.update_layout(title=titulo, xaxis_title="x(t)", yaxis_title="x(t+1)", height=380)
    return fig


def serie_tiempo(x, titulo="Datos en orden de producción"):
    xx = np.asarray(x, float)
    fig = go.Figure(go.Scatter(x=list(range(1, len(xx) + 1)), y=xx, mode="lines+markers", line=dict(color=AZUL)))
    fig.add_hline(y=float(np.mean(xx)), line=dict(color=VERDE), annotation_text="media")
    fig.update_layout(title=titulo, height=320, xaxis_title="Orden")
    return fig


def chi2_barras(agrupada):
    etiquetas = [f"{a:.4g}–{b:.4g}" for a, b in zip(agrupada["Desde"], agrupada["Hasta"])]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=etiquetas, y=agrupada["Observada (O)"], name="Observada", marker_color="#c9c7bf"))
    fig.add_trace(go.Scatter(x=etiquetas, y=agrupada["Esperada (E)"], name="Esperada (normal)", mode="lines+markers",
                             line=dict(color=ROJO)))
    fig.update_layout(title="Frecuencias observadas vs esperadas (prueba Ji-cuadrada)", height=360,
                      legend=dict(orientation="h", y=-0.25))
    return fig


def curva(xs, series, titulo, xt, yt, log_y=False, altura=380):
    """series: dict nombre -> lista de y"""
    fig = go.Figure()
    for nom, ys in series.items():
        fig.add_trace(go.Scatter(x=list(xs), y=list(ys), mode="lines+markers", name=nom))
    fig.update_layout(title=titulo, xaxis_title=xt, yaxis_title=yt, height=altura,
                      legend=dict(orientation="h", y=-0.25))
    if log_y:
        fig.update_yaxes(type="log")
    return fig


def pareto(df):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    vitales = df["% acumulado"].shift(fill_value=0) < 80
    fig.add_trace(go.Bar(x=df["Categoría"], y=df["Frecuencia"], name="Frecuencia", text=df["Frecuencia"],
                         textposition="outside",
                         marker=dict(color=[VERDE if v else "#c9c7bf" for v in vitales])), secondary_y=False)
    fig.add_trace(go.Scatter(x=df["Categoría"], y=df["% acumulado"], name="% acumulado", mode="lines+markers",
                             line=dict(color=DORADO, width=3), marker=dict(size=9, color=DORADO,
                                                                            line=dict(color="#f3f2ee", width=2))),
                  secondary_y=True)
    fig.add_hline(y=80, line=dict(color=ROJO, dash="dot", width=1.5), secondary_y=True,
                  annotation_text="80 %", annotation_position="top left")
    fig.update_yaxes(range=[0, 105], secondary_y=True, title_text="% acumulado")
    fig.update_layout(title="Diagrama de Pareto<br><sup>Barras oscuras: categorías vitales (hasta el 80 % acumulado)</sup>", height=420, legend=dict(orientation="h", y=-0.3))
    return fig
