"""
Validación del software contra los ejemplos resueltos del Módulo Académico y de la
hoja de fórmulas. Ejecutar desde la carpeta del proyecto:

    python pruebas/validacion_ejemplos_modulo.py

Genera la tabla `pruebas/resultado_validacion.csv` (evidencia de ejecución).

Cada comparación queda en una de tres clases:
  - "Coincide": el software reproduce el valor escrito en el módulo.
  - "Error del material": el valor escrito no sale del propio procedimiento del módulo; la
    columna «Recálculo del módulo» rehace ese paso y coincide con el software.
  - "Decisión de método": el módulo y el software siguen procedimientos distintos; la
    columna «Recálculo del módulo» reproduce el número del módulo con SU procedimiento, para
    mostrar que la diferencia se entiende. La justificación está en
    pruebas/DECISIONES_METODOLOGICAS.md.
Ningún cálculo del software se ajustó para que coincida con el material.
"""
import math
import os
import sys

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from cep import atributos, capacidad, diseno, muestreo, variables  # noqa: E402
from cep.estadistica import hiper_cdf, hiper_pmf, phi  # noqa: E402

EJ = os.path.join(RAIZ, "datos_ejemplo")
filas = []


def comparar(ejemplo, concepto, modulo, software, tol=0.01, nota="", clase=None, recalculo=None):
    ok = abs(modulo - software) <= tol * max(abs(modulo), 1e-9)
    if ok:
        clase = "Coincide"
    elif clase is None:
        clase = "Sin explicar"  # una diferencia nueva que nadie ha revisado: debe investigarse
    filas.append({"Ejemplo": ejemplo, "Concepto": concepto, "Valor en el módulo": modulo,
                  "Valor del software": round(float(software), 6), "¿Coincide?": "Sí" if ok else "No",
                  "Clasificación": clase,
                  "Recálculo del módulo": "" if recalculo is None else round(float(recalculo), 6), "Nota": nota})


# ---- Capacidad (cap. 3, ejemplo 1) ----
r = capacidad.indices(0.738, 0.169 / 2.326, 0.9, 0.5)
comparar("Cap. 3 ej. 1 (R̄=0,169, n=5)", "σ = R̄/d2", 0.0726, r["σ"])
comparar("Cap. 3 ej. 1", "Cp", 0.9182, r["Cp"])
comparar("Cap. 3 ej. 1", "Cpu", 0.7438, r["Cpu"])
comparar("Cap. 3 ej. 1", "Cpl", 1.09, r["Cpl"])
comparar("Cap. 3 ej. 1", "%PNC por LSE", 0.01287, r["%PNC por LSE"], tol=0.05)
rc = capacidad.escenario_centrado(0.0726, 0.9, 0.5)
comparar("Cap. 3 ej. 1.c (centrado)", "%PNC total", 0.00588, rc["%PNC total"], tol=0.05)
vo = capacidad.ventana_operacion(0.0726, 0.01, 0.9, 0.5)
comparar("Cap. 3 ej. 1.d", "Ventana: X̄ máx", 0.731, vo["X̄ máximo (por LSE)"])
comparar("Cap. 3 ej. 1.d", "Ventana: X̄ mín", 0.669, vo["X̄ mínimo (por LIE)"])
r3 = capacidad.indices(77, 4.5, 90, 60)
comparar("Cap. 3 ej. 3 (75 ± 15)", "Cp", 1.11, r3["Cp"])
comparar("Cap. 3 ej. 3", "Cpu", 0.9629, r3["Cpu"])
comparar("Cap. 3 ej. 3", "Cpl", 1.2592, r3["Cpl"])
vo3 = capacidad.ventana_operacion(4.5, 0.04, 90, 60)
comparar("Cap. 3 ej. 3", "Ventana: X̄ máx", 82.125, vo3["X̄ máximo (por LSE)"])
comparar("Cap. 3 ej. 3", "Ventana: X̄ mín", 60.7875, vo3["X̄ mínimo (por LIE)"],
         clase="Error del material", recalculo=60 + 1.75069 * 4.5,
         nota="El módulo plantea −1,75069 = (60 − X̄)/4,5, que da X̄ = 60 + 7,878 = 67,878. El 60,7875 escrito no "
              "sale de esa ecuación; además la ventana debe ser simétrica: 90 − 7,875 = 82,125 y 60 + 7,875 = 67,875.")

# ---- Diseño (cap. 4, ejemplo Ladrillos y CIA) ----
comparar("Ladrillos b)", "VEPNC con β = 0,05316 (3 muestras)", 16.95, diseno.vepnc(500, 0.06426, 0.05316, 0.5, 3))
n, _ = diseno.n_para_potencia(0.7, 1.635, 0.68377)
comparar("Ladrillos c)", "n para 1−β = 0,68377, d = 0,7", 9.11, n)
comparar("Ladrillos c)", "β para detectar con 90 % en 2 muestras", 0.31623, diseno.beta_para_detectar(0.9, 2))
comparar("Cap. 4.6", "ARL0 con α = 0,0027", 370, 1 / 0.0027)
pot = diseno.potencia_xbar(0.65, 5, 1.635)
comparar("Ladrillos b)", "1 − β (d = 0,65, n = 5, Z = 1,635)", 0.94684, pot, tol=0.01,
         clase="Error del material", recalculo=phi(0.65 * math.sqrt(5) - 1.635),
         nota="El módulo escribe Φ(0,65·√5 − 1,635) = Φ(1,615), pero 0,65·√5 = 1,453 y 1,453 − 1,635 = −0,18, "
              "así que 1 − β = Φ(−0,18) = 0,428. El 1,615 sale de 0,65·5 − 1,635 (se usó 5 en lugar de √5). "
              "La parte c) del mismo ejemplo sí usa √n (n = 9,11) y el software la reproduce.")

# ---- Carta p (latas, n = 40) ----
la = pd.read_csv(os.path.join(EJ, "latas_p_fase1.csv"))
rp = atributos.carta_p(la["Defectuosas"], 40, la["Muestra"].tolist())
comparar("Carta p latas (Fase I)", "p̄", 0.227, rp["pbar"])
comparar("Carta p latas (Fase I)", "LCS", 0.4256982, rp["params"]["LCS"])
comparar("Carta p latas (Fase I)", "LCI", 0.0283018, rp["params"]["LCI"])
rp2 = atributos.carta_p(la["Defectuosas"], 40, la["Muestra"].tolist(), excluir={2, 24})
comparar("Carta p latas (tras cepillar 2 y 24)", "p̄", 0.20543478, rp2["pbar"])
comparar("Carta p latas (tras cepillar 2 y 24)", "LCS", 0.39707781, rp2["params"]["LCS"])
comparar("Carta p latas (tras cepillar 2 y 24)", "LCI", 0.01379176, rp2["params"]["LCI"])

# ---- Carta p n variable (módems) ----
mo = pd.read_csv(os.path.join(EJ, "modems_p_n_variable.csv"))
rm = atributos.carta_p(mo["Defectuosos"], mo["n"].to_numpy(), mo["Subgrupo"].tolist())
comparar("Carta p módems (límites variables)", "p̄ = 856/38800", 0.02206, rm["pbar"])
p1_ = 53 / 2000
comparar("Carta p módems", "LCS subgrupo 1 (n=2000)", 0.0372745, rm["cartas"][0]["lcs"][0], tol=0.02,
         clase="Decisión de método", recalculo=p1_ + 3 * math.sqrt(p1_ * (1 - p1_) / 2000),
         nota="La tabla del módulo centra cada límite en la p_i del propio subgrupo (0,0265 ± 3·√(0,0265·0,9735/2000)). "
              "El software usa p̄ = 856/38800, como la fórmula 4.8.1.2 (p̄ ± 3√(p̄(1−p̄)/n_i)). Con p_i cada punto "
              "queda siempre en el centro de sus propios límites y la carta nunca podría dar una señal.")

# ---- Carta np (duraznos, n = 300) ----
du = pd.read_csv(os.path.join(EJ, "duraznos_np.csv"))
rn = atributos.carta_np(du["Golpeados"], 300, du["Envio"].tolist())
comparar("Carta np duraznos", "LC = n·p̄", 28.2, rn["params"]["LC = np̄"], tol=0.03,
         nota="El módulo muestra 21 envíos pero divide entre k = 25.")

# ---- Carta c (circuitos) ----
ci = pd.read_csv(os.path.join(EJ, "circuitos_c.csv"))
rc_ = atributos.carta_c(ci["Disconformidades"], ci["Muestra"].tolist())
comparar("Carta c circuitos", "LCS", 33.2108605, rc_["params"]["LCS"])
comparar("Carta c circuitos", "LCI", 6.48144717, rc_["params"]["LCI"])
rc2 = atributos.carta_c(ci["Disconformidades"], ci["Muestra"].tolist(), excluir={6, 20})
comparar("Carta c circuitos (sin 6 y 20)", "c̄", 19.67, rc2["cbar"])
comparar("Carta c circuitos (sin 6 y 20)", "LCS", 32.9708014, rc2["params"]["LCS"])

# ---- Carta u (computadoras, n = 5) ----
cu = pd.read_csv(os.path.join(EJ, "computadoras_u.csv"))
ru = atributos.carta_u(cu["Defectos"], 5, cu["Muestra"].tolist())
comparar("Carta u computadoras", "Ū", 1.93, ru["ubar"])
comparar("Carta u computadoras", "LCS", 3.79386695, ru["params"]["LCS"])
comparar("Carta u computadoras", "LCI", 0.06613305, ru["params"]["LCI"])

# ---- Curva OC de la carta p (n = 50, LCS = 0,3697, LCI = 0,0303) ----
oc = diseno.beta_atributos("p", 50, 0.3697, 0.0303, [0.01, 0.05, 0.3])
comparar("OC carta p (módulo 4.8.2)", "β con p = 0,01", 0.08943531, oc.loc[0, "β"])
comparar("OC carta p", "β con p = 0,05", 0.72056825, oc.loc[1, "β"])
comparar("OC carta p", "β con p = 0,3", 0.85943972, oc.loc[2, "β"])

# ---- Tamaño de muestra carta p ----
comparar("Carta p diseño, método 1", "n (p = 0,01, γ = 0,95)", 300, diseno.n_carta_p(0.01, 1, gamma=0.95)[0], tol=0.01)
comparar("Carta p diseño, método 2", "n (p = 0,01, p1 = 0,05, L = 3)", 56, diseno.n_carta_p(0.01, 2, L=3, p1=0.05)[0])
comparar("Carta p diseño, método 3", "n (p = 0,05, L = 3)", 171, diseno.n_carta_p(0.05, 3, L=3)[0])

# ---- Muestreo de aceptación ----
comparar("Cap. 5 plan n=50, c=3, p'=0,1", "Pa binomial", 0.25029, muestreo.pa_simple(50, 3, 0.1))
comparar("Cap. 5 plan n=50, c=3, N=500", "Pa hipergeométrica", 0.235858, muestreo.pa_simple(50, 3, 0.1, "Hipergeométrica", 500))
for p, v in ((0.02, 0.9945), (0.06, 0.6521), (0.1, 0.1769)):
    comparar("Curva OC n = 80, c = 5", f"Pa con p' = {p}", v, muestreo.pa_simple(80, 5, p))


def pa_doble_como_modulo(N=80, D=4, n1=20, n2=10, c2=3):
    """Árbol del ejemplo 5.7.1 tal como está escrito: sólo d1 = 0 acepta en la 1ª muestra y la 2ª
    muestra se calcula con el lote completo (N = 80, D = 4)."""
    pa = hiper_pmf(0, N, D, n1)
    for d1 in range(1, c2 + 1):
        pa += hiper_pmf(d1, N, D, n1) * hiper_cdf(c2 - d1, N, D, n2)
    return pa


comparar("Plan doble (N=80, p=5 %)", "Pa", 0.9604, muestreo.pa_doble(20, 1, 10, 3, 0.05, "Hipergeométrica", 80)["Pa"],
         tol=0.01, clase="Decisión de método", recalculo=pa_doble_como_modulo(),
         nota="El software acepta en la 1ª muestra si d1 ≤ c1 = 1 (definición de c1 en 5.7.1 y ejemplo Ac/Re de la "
              "presentación) y toma la 2ª muestra del lote restante: N − n1 = 60 unidades con D − d1 defectuosos. "
              "El árbol del módulo envía d1 = 1 a la 2ª muestra y calcula la 2ª muestra con el lote completo "
              "(80 unidades, 4 defectuosos), como si las primeras 20 piezas se devolvieran al lote.")
r = muestreo.plan_mil_std(60000, 2.5, "II")
comparar("MIL-STD ej. 1 (60 000, NAC 2,5)", "n", 500, r["n"])
comparar("MIL-STD ej. 1", "Ac", 21, r["Ac"])
r = muestreo.plan_mil_std(90000, 2.5, "II")
comparar("CSP ej. (90 000, NAC 2,5)", "n", 500, r["n"])
comparar("CSP ej.", "Pa con AOQL 2 % (n=500, c=21)", 0.99939, muestreo.pa_simple(500, 21, 0.02), tol=0.001)
r = muestreo.plan_mil_std(1000, 0.10, "II")
comparar("MIL-STD ej. 2 (1 000, NAC 0,10)", "n", 200, r["n"], clase="Error del material", recalculo=125,
         nota="Lote 1 000, nivel II ⇒ letra J. En la tabla maestra (diapositiva 17), la celda J / 0,10 es una flecha ↓ "
              "y el primer plan debajo es K: n = 125, Ac = 0, Re = 1. El n = 200 del texto corresponde a la fila L, que "
              "es el plan de NAC 0,065.")

# ---- Carta X̄-R con los diámetros ----
di = pd.read_csv(os.path.join(EJ, "diametro_agujeros_XR.csv"))
g = [row.to_numpy(float) for _, row in di[["X1", "X2", "X3", "X4", "X5"]].iterrows()]
rx = variables.fase1_xr(g, list(range(1, 21)))
comparar("Diámetros (módulo 2.6)", "X̿", 15.954, rx["media"])

df = pd.DataFrame(filas)
salida = os.path.join(RAIZ, "pruebas", "resultado_validacion.csv")
df.to_csv(salida, index=False, sep=";", decimal=",", encoding="utf-8-sig")
pd.set_option("display.width", 200, "display.max_colwidth", 60, "display.max_rows", 200)
print(df[["Ejemplo", "Concepto", "Valor en el módulo", "Valor del software", "Clasificación"]].to_string(index=False))
cuenta = df["Clasificación"].value_counts()
print(f"\nCoinciden {(df['¿Coincide?'] == 'Sí').sum()} de {len(df)} comparaciones. Detalle en {salida}")
for clase in ("Error del material", "Decisión de método", "Sin explicar"):
    print(f"  {clase}: {int(cuenta.get(clase, 0))}")
dif = df[df["Clasificación"] != "Coincide"]
for _, f in dif.iterrows():
    if f["Recálculo del módulo"] != "":
        print(f"  - {f['Ejemplo']} / {f['Concepto']}: módulo {f['Valor en el módulo']}, software "
              f"{f['Valor del software']}, recálculo {f['Recálculo del módulo']}")
if int(cuenta.get("Sin explicar", 0)):
    sys.exit(1)
