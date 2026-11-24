"""
Funciones de probabilidad usadas en todo el programa.

Equivalen a buscar valores en las tablas del Módulo Académico
(Tabla 2 Normal, Tabla 3 Binomial, Tabla 4 Poisson, tabla Ji-cuadrada),
pero calculadas con precisión mediante scipy.
"""
import math

from scipy import stats


# ---------------------------------------------------------------- Normal ----
def phi(z: float) -> float:
    """P(Z <= z) para Z ~ N(0, 1)."""
    return float(stats.norm.cdf(z))


def z_de_prob(p: float) -> float:
    """Valor z tal que P(Z <= z) = p."""
    return float(stats.norm.ppf(p))


def z_alfa_medios(alfa: float) -> float:
    """Z_{alfa/2}: valor tal que P(Z > Z_{alfa/2}) = alfa/2 (límites bilaterales)."""
    return float(stats.norm.ppf(1 - alfa / 2))


def alfa_de_z(z_alfa_2: float) -> float:
    """Riesgo tipo I (tasa de falsa alarma) de unos límites a +-Z_{alfa/2} sigmas."""
    return float(2 * (1 - stats.norm.cdf(abs(z_alfa_2))))


# -------------------------------------------------------------- Discretas ---
def binom_cdf(x, n, p):
    """P(X <= x) para X ~ Binomial(n, p)."""
    return float(stats.binom.cdf(x, n, p))


def binom_pmf(x, n, p):
    return float(stats.binom.pmf(x, n, p))


def poisson_cdf(x, lam):
    """P(X <= x) para X ~ Poisson(lam)."""
    return float(stats.poisson.cdf(x, lam))


def poisson_pmf(x, lam):
    return float(stats.poisson.pmf(x, lam))


def hiper_cdf(x, N, K, n):
    """P(X <= x) hipergeométrica: lote N, K defectuosos en el lote, muestra n."""
    return float(stats.hypergeom.cdf(x, N, K, n))


def hiper_pmf(x, N, K, n):
    return float(stats.hypergeom.pmf(x, N, K, n))


# ------------------------------------------------------------ Ji-cuadrada ---
def chi2_critico(alfa: float, gl: int) -> float:
    """Valor de tabla chi^2_{alfa, gl} (cola derecha)."""
    return float(stats.chi2.ppf(1 - alfa, gl))


def chi2_cola_derecha(valor: float, gl: int) -> float:
    """P(chi^2_gl >= valor)."""
    return float(stats.chi2.sf(valor, gl))


def fmt(x, dec=4):
    """Formato numérico corto para tablas y conclusiones."""
    if x is None:
        return "—"
    try:
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return "∞" if (isinstance(x, float) and math.isinf(x)) else "—"
    except Exception:
        pass
    if isinstance(x, (int,)) and not isinstance(x, bool):
        return f"{x:,}".replace(",", ".")
    return f"{x:.{dec}f}"
