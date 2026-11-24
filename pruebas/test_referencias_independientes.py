"""
Casos de referencia independientes del propio programa.

Cada caso compara el resultado de Sigmora CEP Studio con un valor que NO sale de funciones del
proyecto, por una de tres vías:

  [T] Tablas de la presentación del curso «Muestreo para la inspección por atributos»
      (diapositiva 16, tabla de tamaño de muestra / letras código; diapositiva 17, tabla
      MIL-STD-105E de inspección normal, muestreo simple).
  [D] Derivación independiente desde la definición matemática, con integración numérica,
      con aritmética exacta (math.comb, fractions) o con las distribuciones de scipy, sin usar
      las funciones del proyecto.
  [S] Simulación de Monte Carlo: se fabrica un proceso o un lote con parámetros conocidos y se
      cuenta lo que ocurre, sin fórmulas.
"""
import math
from fractions import Fraction
from math import comb

import numpy as np
import pytest
from scipy import integrate, special, stats

from cep import atributos, capacidad, constantes, muestreo, variables

RNG = np.random.default_rng(20261124)


# ============================================================ cartas de control =====
# [D] Factores de la tabla de constantes derivados desde su definición, no copiados de otra tabla.
def d2_def(n):
    """d2 = E[R/σ] = ∫ 1 − Φ(x)^n − (1 − Φ(x))^n dx."""
    f = lambda x: 1 - stats.norm.cdf(x) ** n - stats.norm.sf(x) ** n  # noqa: E731
    return integrate.quad(f, -12, 12, limit=200)[0]


def d3_def(n):
    """d3 = DE[R/σ], con E[R²] = 2∫∫_{x<y} [1 − Φ(y)^n − (1−Φ(x))^n + (Φ(y) − Φ(x))^n] dy dx."""
    F = stats.norm.cdf

    def g(y, x):
        return 1 - F(y) ** n - (1 - F(x)) ** n + (F(y) - F(x)) ** n

    er2 = 2 * integrate.dblquad(g, -9, 9, lambda x: x, lambda x: 9, epsabs=1e-7)[0]
    return math.sqrt(er2 - d2_def(n) ** 2)


def c4_def(n):
    """c4 = E[S/σ] = √(2/(n−1))·Γ(n/2)/Γ((n−1)/2)."""
    return math.sqrt(2 / (n - 1)) * math.exp(special.gammaln(n / 2) - special.gammaln((n - 1) / 2))


@pytest.mark.parametrize("n", [2, 3, 5, 8, 10, 15, 20, 25])
def test_factores_d2_c4_A2_A3_B3_B4_desde_su_definicion(n):
    d2, c4 = d2_def(n), c4_def(n)
    assert constantes.factor("d2", n) == pytest.approx(d2, abs=6e-4)
    assert constantes.factor("c4", n) == pytest.approx(c4, abs=6e-5)
    assert constantes.factor("A2", n) == pytest.approx(3 / (d2 * math.sqrt(n)), abs=6e-4)
    assert constantes.factor("A3", n) == pytest.approx(3 / (c4 * math.sqrt(n)), abs=6e-4)
    b = 3 * math.sqrt(1 - c4 ** 2) / c4
    assert constantes.factor("B3", n) == pytest.approx(max(0.0, 1 - b), abs=6e-4)
    assert constantes.factor("B4", n) == pytest.approx(1 + b, abs=6e-4)


@pytest.mark.parametrize("n", [2, 5, 10])
def test_factores_D3_D4_desde_su_definicion(n):
    d2, d3 = d2_def(n), d3_def(n)
    assert constantes.factor("D4", n) == pytest.approx(1 + 3 * d3 / d2, abs=2e-3)
    assert constantes.factor("D3", n) == pytest.approx(max(0.0, 1 - 3 * d3 / d2), abs=2e-3)


def test_carta_xr_simulacion_proceso_conocido():  # [S]
    """Proceso N(μ = 10, σ = 2), subgrupos de 5: la Fase I debe recuperar σ y la tasa de falsas alarmas
    de los límites a 3σ debe ser ≈ 0,0027 (1/370)."""
    g = list(RNG.normal(10, 2, (3000, 5)))
    r = variables.fase1_xr(g, list(range(1, 3001)))
    assert r["sigma"] == pytest.approx(2, rel=0.02)
    assert r["media"] == pytest.approx(10, abs=0.03)
    nuevos = RNG.normal(10, 2, (400_000, 5)).mean(axis=1)
    fuera = np.mean((nuevos > r["params"]["LCS X̄"]) | (nuevos < r["params"]["LCI X̄"]))
    assert fuera == pytest.approx(0.0027, abs=0.0006)


def test_carta_xs_simulacion_proceso_conocido():  # [S]
    g = list(RNG.normal(50, 0.5, (3000, 10)))
    r = variables.fase1_xs(g, list(range(1, 3001)))
    assert r["sigma"] == pytest.approx(0.5, rel=0.02)


def test_carta_imr_simulacion_proceso_conocido():  # [S]
    r = variables.fase1_imr(RNG.normal(0, 3, 20_000))
    assert r["sigma"] == pytest.approx(3, rel=0.02)


def test_fraccion_no_conforme_por_simulacion():  # [S]
    """Proceso descentrado N(10,3; 0,25) con especificación 9,5 – 11: se cuentan las piezas fuera."""
    x = RNG.normal(10.3, 0.25, 4_000_000)
    r = capacidad.indices(10.3, 0.25, 11.0, 9.5)
    assert np.mean(x > 11.0) == pytest.approx(r["%PNC por LSE"], abs=2e-4)
    assert np.mean(x < 9.5) == pytest.approx(r["%PNC por LIE"], abs=2e-4)


def test_intervalo_cp_cobertura_por_simulacion():  # [S]
    """El IC del 95 % para Cp debe contener el Cp verdadero en ≈ 95 % de las muestras."""
    cp_real, n, aciertos, reps = 1.2, 50, 0, 4000
    for _ in range(reps):
        s = RNG.normal(0, 1, n).std(ddof=1)
        lo, hi = capacidad.intervalos_confianza(cp_real / s, None, n)["Cp"]
        aciertos += lo <= cp_real <= hi
    assert aciertos / reps == pytest.approx(0.95, abs=0.015)


# ===================================================== muestreo de aceptación =======
def _pa_binomial_exacta(n, c, p):
    p = Fraction(p).limit_denominator(10 ** 9)
    return float(sum(comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(c + 1)))


def _pa_hiper_exacta(N, D, n, c):
    return float(sum(Fraction(comb(D, x) * comb(N - D, n - x), comb(N, n)) for x in range(c + 1)))


@pytest.mark.parametrize("n,c,p", [(50, 3, 0.1), (80, 5, 0.06), (200, 0, 0.002), (500, 21, 0.03)])
def test_pa_binomial_aritmetica_exacta(n, c, p):  # [D]
    assert muestreo.pa_simple(n, c, p) == pytest.approx(_pa_binomial_exacta(n, c, p), abs=1e-10)


@pytest.mark.parametrize("N,D,n,c", [(500, 50, 50, 3), (80, 4, 20, 1), (1000, 13, 125, 0), (60, 12, 15, 2)])
def test_pa_hipergeometrica_aritmetica_exacta(N, D, n, c):  # [D]
    assert muestreo.pa_simple(n, c, D / N, "Hipergeométrica", N) == pytest.approx(
        _pa_hiper_exacta(N, D, n, c), abs=1e-12)


def test_pa_simple_simulacion_de_lotes():  # [S]
    N, D, n, c = 200, 9, 32, 1
    lote = np.r_[np.ones(D), np.zeros(N - D)]
    reps = 80_000
    acepta = sum(RNG.permutation(lote)[:n].sum() <= c for _ in range(reps))
    assert acepta / reps == pytest.approx(muestreo.pa_simple(n, c, D / N, "Hipergeométrica", N), abs=0.005)


@pytest.mark.parametrize("N,nivel,letra", [(1338, "II", "K"), (60_000, "II", "N"), (1000, "II", "J"),
                                           (100, "I", "D"), (5000, "III", "M"), (10, "II", "B")])
def test_letra_codigo_mil_std(N, nivel, letra):  # [T] presentación del curso, diapositiva 16
    assert muestreo.letra_codigo(N, nivel) == letra


@pytest.mark.parametrize("N,nac,n,ac,re", [
    (1338, 1.0, 125, 3, 4),   # K, 1,0
    (2000, 1.0, 125, 3, 4),   # K, 1,0
    (3000, 1.0, 125, 3, 4),   # K, 1,0
    (5000, 1.0, 200, 5, 6),   # L, 1,0
    (400, 2.5, 50, 3, 4),     # H, 2,5
    (200, 2.5, 32, 2, 3),     # G, 2,5
    (800, 0.65, 80, 1, 2),    # J, 0,65
    (60_000, 2.5, 500, 21, 22),  # N, 2,5
    (1000, 0.10, 125, 0, 1),  # J, 0,10 → flecha → K
])
def test_planes_mil_std_tabla_maestra(N, nac, n, ac, re):  # [T] presentación del curso, diapositiva 17
    r = muestreo.plan_mil_std(N, nac, "II")
    assert (r["n"], r["Ac"], r["Re"]) == (n, ac, re)
