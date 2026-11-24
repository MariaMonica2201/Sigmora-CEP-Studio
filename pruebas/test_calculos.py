"""
Pruebas de los cálculos: muestreo doble, prueba Ji-cuadrada y las diferencias documentadas
contra el Módulo Académico.

Ejecutar desde la carpeta del proyecto:   python -m pytest pruebas
"""
import math
import os
import subprocess
import sys
from fractions import Fraction
from math import comb

import numpy as np
import pandas as pd
import pytest

from cep import capacidad, diseno, muestreo, supuestos
from cep.validacion import DatosInvalidos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------------------ plan doble ----
def pa_doble_exacta(N, D, n1, c1, n2, c2):
    """Enumeración exacta con fracciones: la 2ª muestra sale del lote restante (N − n1, D − d1)."""
    pa = Fraction(0)
    for d1 in range(0, min(D, n1) + 1):
        p1 = Fraction(comb(D, d1) * comb(N - D, n1 - d1), comb(N, n1))
        if d1 <= c1:
            pa += p1
        elif d1 <= c2:
            for d2 in range(0, c2 - d1 + 1):
                pa += p1 * Fraction(comb(D - d1, d2) * comb(N - n1 - (D - d1), n2 - d2), comb(N - n1, n2))
    return float(pa)


@pytest.mark.parametrize("N,p,n1,c1,n2,c2", [
    (80, 0.05, 20, 1, 10, 3),      # ejemplo del módulo 5.7.1
    (50, 0.10, 10, 0, 10, 2),
    (200, 0.03, 32, 1, 32, 4),
    (40, 0.20, 8, 1, 8, 3),
])
def test_pa_doble_hipergeometrica_usa_lote_restante(N, p, n1, c1, n2, c2):
    D = round(p * N)
    r = muestreo.pa_doble(n1, c1, n2, c2, p, "Hipergeométrica", N)
    assert r["Pa"] == pytest.approx(pa_doble_exacta(N, D, n1, c1, n2, c2), abs=1e-12)
    assert r["Pa"] == pytest.approx(r["Pa en 1ª muestra"] + r["Pa en 2ª muestra"])


def test_pa_doble_simulacion_de_lotes():
    """Simulación independiente: se arma el lote, se sacan n1 y luego n2 sin reposición."""
    rng = np.random.default_rng(7)
    N, D, n1, c1, n2, c2 = 80, 4, 20, 1, 10, 3
    lote = np.r_[np.ones(D), np.zeros(N - D)]
    acept = 0
    reps = 60_000
    for _ in range(reps):
        orden = rng.permutation(lote)
        d1 = orden[:n1].sum()
        if d1 <= c1 or (d1 <= c2 and d1 + orden[n1:n1 + n2].sum() <= c2):
            acept += 1
    r = muestreo.pa_doble(n1, c1, n2, c2, D / N, "Hipergeométrica", N)
    assert acept / reps == pytest.approx(r["Pa"], abs=0.004)


def test_pa_doble_lote_grande_se_acerca_a_binomial():
    hip = muestreo.pa_doble(50, 1, 50, 4, 0.03, "Hipergeométrica", 1_000_000)["Pa"]
    bin_ = muestreo.pa_doble(50, 1, 50, 4, 0.03, "Binomial")["Pa"]
    assert hip == pytest.approx(bin_, abs=1e-3)


def test_pa_doble_asn():
    r = muestreo.pa_doble(20, 1, 10, 3, 0.05)
    assert r["ASN"] == pytest.approx(20 * r["P1 (decidir con 1ª)"] + 30 * (1 - r["P1 (decidir con 1ª)"]))


def test_pa_doble_rechaza_muestras_mayores_que_el_lote():
    with pytest.raises(DatosInvalidos, match="n1 \\+ n2"):
        muestreo.pa_doble(50, 1, 40, 3, 0.05, "Hipergeométrica", 80)


# ------------------------------------------------------------ Ji-cuadrada --
def test_chi2_condiciones_cuando_es_aplicable():
    x = np.random.default_rng(3).normal(50, 2, 200)
    r = supuestos.chi2_normalidad(x)
    assert r["estado"] in ("no se rechaza", "se rechaza")
    assert r["gl"] == r["k_agrupadas"] - 2 - 1 >= 1
    assert (r["agrupada"]["Esperada (E)"] >= 5).all()
    assert r["agrupada"]["Esperada (E)"].sum() == pytest.approx(len(x))
    assert r["agrupada"]["Observada (O)"].sum() == len(x)
    assert set(r["condiciones"]["¿Cumple?"]) <= {"Sí", "Revisar"}


def test_chi2_no_rechazar_no_se_presenta_como_prueba_de_normalidad():
    x = np.random.default_rng(5).normal(0, 1, 300)
    r = supuestos.chi2_normalidad(x)
    assert r["normal"] is True or r["normal"] is np.True_
    assert "no demuestra" in r["conclusion"]


def test_chi2_rechaza_datos_claramente_no_normales():
    x = np.random.default_rng(1).exponential(1.0, 400)
    r = supuestos.chi2_normalidad(x)
    assert r["estado"] == "se rechaza"


def test_chi2_no_aplicable_con_pocos_datos():
    r = supuestos.chi2_normalidad([1.2, 1.5, 1.1, 1.9, 1.4, 1.6, 1.3, 1.8, 1.7, 1.0])
    assert r["estado"] == "no aplicable"
    assert r["normal"] is None
    assert math.isnan(r["chi2_tabla"])
    assert "20 datos" in r["conclusion"]


def test_chi2_sin_variabilidad():
    with pytest.raises(DatosInvalidos, match="variabilidad es nula"):
        supuestos.chi2_normalidad([5.0] * 40)


def test_chi2_k_invalido():
    with pytest.raises(DatosInvalidos, match="número de clases"):
        supuestos.chi2_normalidad(np.arange(30.0), k=50)


# ------------------------------------------- diferencias con el módulo -----
def test_potencia_xbar_usa_raiz_de_n():
    # Ladrillos b): Φ(0,65·√5 − 1,635) = Φ(−0,18) ≈ 0,428 (el módulo escribe 1,615 → 0,94684)
    assert diseno.potencia_xbar(0.65, 5, 1.635) == pytest.approx(0.4280, abs=5e-4)
    # parte c) del mismo ejemplo, que el módulo resuelve con √n: n = 9,11
    n, _ = diseno.n_para_potencia(0.7, 1.635, 0.68377)
    assert n == pytest.approx(9.11, abs=0.01)
    # coherencia: con ese n la potencia vuelve a 0,68377
    assert diseno.potencia_xbar(0.7, n, 1.635) == pytest.approx(0.68377, abs=1e-4)


def test_ventana_operacion_es_simetrica():
    vo = capacidad.ventana_operacion(4.5, 0.04, 90, 60)
    assert vo["X̄ mínimo (por LIE)"] - 60 == pytest.approx(90 - vo["X̄ máximo (por LSE)"])
    assert vo["X̄ mínimo (por LIE)"] == pytest.approx(67.878, abs=1e-3)
    # en el borde de la ventana el %PNC por cada límite es exactamente el objetivo
    r = capacidad.indices(vo["X̄ mínimo (por LIE)"], 4.5, 90, 60)
    assert r["%PNC por LIE"] == pytest.approx(0.04)


def test_mil_std_ejemplo_2_sigue_la_flecha_de_la_tabla():
    r = muestreo.plan_mil_std(1000, 0.10, "II")
    assert (r["letra inicial"], r["letra"], r["n"], r["Ac"], r["Re"]) == ("J", "K", 125, 0, 1)


def test_validacion_contra_el_modulo_sin_diferencias_sin_explicar():
    """El script de validación termina con error si aparece una diferencia que nadie ha clasificado."""
    salida = subprocess.run([sys.executable, os.path.join(RAIZ, "pruebas", "validacion_ejemplos_modulo.py")],
                            capture_output=True, text=True, cwd=RAIZ)
    assert salida.returncode == 0, salida.stdout + salida.stderr
    df = pd.read_csv(os.path.join(RAIZ, "pruebas", "resultado_validacion.csv"), sep=";", decimal=",",
                     encoding="utf-8-sig")
    assert "Sin explicar" not in set(df["Clasificación"])
    # en los errores del material, rehacer el paso del módulo da el valor del software
    err = df[df["Clasificación"] == "Error del material"]
    for _, f in err.iterrows():
        assert float(f["Recálculo del módulo"]) == pytest.approx(float(f["Valor del software"]), rel=1e-3)
    # en las decisiones de método, el procedimiento del módulo reproduce su propio número
    met = df[df["Clasificación"] == "Decisión de método"]
    for _, f in met.iterrows():
        assert float(f["Recálculo del módulo"]) == pytest.approx(float(f["Valor en el módulo"]), rel=2e-3)


# ---------------------------------------------- defectuosos en lote finito --
def test_defectuosos_en_lote_no_entero_se_informa():
    D, exacto, pe = muestreo.defectuosos_en_lote(0.03, 80)
    assert (D, exacto, pe) == (2, False, 0.025)
    aviso = muestreo.aviso_redondeo(0.03, 80)
    assert "2,4" in aviso and "D = 2" in aviso and "0,025" in aviso
    assert muestreo.aviso_redondeo(0.05, 80) is None  # 80 · 0,05 = 4 exacto


def test_hipergeometrica_usa_el_d_entero_informado():
    # con p' = 0,03 y N = 80 el cálculo es idéntico al de p' = 2/80 (el D que se informa)
    assert muestreo.pa_simple(20, 1, 0.03, "Hipergeométrica", 80) == muestreo.pa_simple(20, 1, 2 / 80, "Hipergeométrica", 80)
    r = muestreo.pa_doble(20, 1, 10, 3, 0.03, "Hipergeométrica", 80)
    assert r["D (defectuosos en el lote)"] == 2 and r["p' efectiva = D/N"] == 0.025


def test_curva_oc_hipergeometrica_solo_fracciones_enteras():
    oc = muestreo.curva_oc_simple(20, 1, np.linspace(0, 0.2, 57), "Hipergeométrica", 80)
    assert np.allclose(oc["p'"] * 80, np.round(oc["p'"] * 80))
    oc2 = muestreo.curva_oc_doble(20, 1, 10, 3, np.linspace(0, 0.2, 57), "Hipergeométrica", 80)
    assert np.allclose(oc2["p'"] * 80, np.round(oc2["p'"] * 80))


# ------------------------------------------------ obtener X̄'' (paso 9) ------
def test_media_por_pnc_produce_el_pnc_pedido():
    m = diseno.media_por_pnc(0.70077, 0.01, 44.0, "LSE")
    assert capacidad.indices(m, 0.70077, lse=44.0)["%PNC por LSE"] == pytest.approx(0.01)
    m = diseno.media_por_pnc(0.70077, 0.02, 38.0, "LIE")
    assert capacidad.indices(m, 0.70077, lie=38.0)["%PNC por LIE"] == pytest.approx(0.02)


def test_media_por_cpk_deja_el_cpk_pedido():
    m = diseno.media_por_cpk(0.70077, 1.0, 44.0, "LSE")
    assert capacidad.indices(m, 0.70077, 44.0, 38.0)["Cpk"] == pytest.approx(1.0)
    m = diseno.media_por_cpk(0.70077, 1.33, 38.0, "LIE")
    assert capacidad.indices(m, 0.70077, 44.0, 38.0)["Cpk"] == pytest.approx(1.33)
