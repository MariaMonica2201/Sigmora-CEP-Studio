"""
Pruebas de validación de entradas: los cálculos deben rechazar datos sin sentido con un
mensaje claro (DatosInvalidos) en lugar de dividir entre cero o devolver NaN.
"""
import io

import numpy as np
import pandas as pd
import pytest

from cep import atributos, capacidad, datos, diseno, muestreo, variables
from cep.validacion import DatosInvalidos

G5 = [np.array([10.0, 10.2, 9.9, 10.1, 10.0]) + 0.1 * i for i in range(10)]
ET = list(range(1, 11))


# ---------------------------------------------------------- tamaños -------
@pytest.mark.parametrize("llamada", [
    lambda: muestreo.pa_simple(0, 1, 0.05),
    lambda: muestreo.pa_doble(0, 1, 10, 3, 0.05),
    lambda: muestreo.pa_doble(20, 1, 0, 3, 0.05),
    lambda: atributos.carta_np([1, 2, 3], 0, [1, 2, 3]),
    lambda: atributos.carta_p([1, 2, 3], [50, 0, 50], [1, 2, 3]),
    lambda: atributos.carta_u([1, 2, 3], [5, 0, 5], [1, 2, 3]),
    lambda: diseno.potencia_xbar(1.0, 0, 3.0),
])
def test_tamano_cero(llamada):
    with pytest.raises(DatosInvalidos):
        llamada()


def test_muestra_mayor_que_el_lote():
    with pytest.raises(DatosInvalidos, match="no puede ser mayor que el lote"):
        muestreo.pa_simple(120, 2, 0.05, "Hipergeométrica", 100)


def test_fraccion_fuera_de_rango():
    with pytest.raises(DatosInvalidos, match="entre 0 y 1"):
        muestreo.pa_simple(50, 1, 1.5)


# ---------------------------------------------------------- conteos -------
def test_defectuosos_mayores_que_n():
    with pytest.raises(DatosInvalidos, match="más defectuosos que unidades.*subgrupos 2"):
        atributos.carta_p([3, 60, 4], 50, [1, 2, 3])


def test_conteos_negativos():
    with pytest.raises(DatosInvalidos, match="negativos"):
        atributos.carta_c([3, -1, 4], [1, 2, 3])


def test_defectos_pueden_superar_n_en_carta_u():
    # en defectos (Poisson) una unidad puede tener varios: no es un error
    r = atributos.carta_u([12, 8, 15], 5, [1, 2, 3])
    assert r["ubar"] == pytest.approx(35 / 15)


def test_carta_np_exige_n_constante():
    with pytest.raises(DatosInvalidos, match="tamaño de muestra constante"):
        atributos.carta_np([1, 2], np.array([50, 60]), [1, 2])


def test_p_barra_cero_avisa_y_no_divide_entre_cero():
    r = atributos.carta_p([0, 0, 0, 0], 50, [1, 2, 3, 4])
    assert "Advertencia" in r["params"]
    with pytest.raises(DatosInvalidos, match="estandarizada"):
        atributos.carta_p([0, 0, 0, 0], np.array([50, 60, 50, 40]), [1, 2, 3, 4], metodo="estandarizada")


# ---------------------------------------------------------- subgrupos -----
def test_subgrupos_vacios():
    with pytest.raises(DatosInvalidos, match="vacíos"):
        variables.fase1_xr([np.array([1.0, 2.0]), np.array([])], [1, 2])


def test_subgrupos_de_tamano_distinto():
    with pytest.raises(DatosInvalidos, match="tamaños distintos"):
        variables.fase1_xr([np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0])], [1, 2])


def test_subgrupo_fuera_de_tabla():
    with pytest.raises(DatosInvalidos, match="fuera de la tabla"):
        variables.fase1_xs([np.arange(30.0), np.arange(30.0) + 1], [1, 2])


def test_un_solo_subgrupo():
    with pytest.raises(DatosInvalidos, match="al menos 2"):
        variables.fase1_xr([G5[0]], [1])


def test_excluir_todos_los_subgrupos():
    with pytest.raises(DatosInvalidos, match="Quedan 1 subgrupos"):
        variables.fase1_xr(G5, ET, excluir=set(range(2, 11)))


def test_cepillado_automatico_no_se_queda_sin_datos():
    g = [np.array([10.0, 10.1, 10.0]), np.array([10.1, 10.0, 10.1]), np.array([20.0, 20.1, 20.2])]
    exc, _ = variables.cepillado_automatico(variables.fase1_xr, g, [1, 2, 3], 3.0)
    assert len(g) - len(exc) >= 2


# ------------------------------------------------- variabilidad nula ------
def test_desviacion_cero_en_fase1():
    g = [np.array([5.0, 5.0, 5.0])] * 6
    with pytest.raises(DatosInvalidos, match="variabilidad es nula"):
        variables.fase1_xr(g, list(range(1, 7)))
    with pytest.raises(DatosInvalidos, match="variabilidad es nula"):
        variables.fase1_xs(g, list(range(1, 7)))
    with pytest.raises(DatosInvalidos, match="variabilidad es nula"):
        variables.fase1_imr([5.0] * 10)


def test_desviacion_cero_en_capacidad_y_fase2():
    with pytest.raises(DatosInvalidos, match="variabilidad es nula"):
        capacidad.indices(10.0, 0.0, 12.0, 8.0)
    with pytest.raises(DatosInvalidos, match="variabilidad es nula"):
        variables.fase2("X̄-R", G5, ET, 10.0, 0.0)


# ------------------------------------------------- especificaciones -------
@pytest.mark.parametrize("lie,lse", [(12.0, 8.0), (10.0, 10.0)])
def test_especificaciones_invertidas(lie, lse):
    with pytest.raises(DatosInvalidos, match="invertidos"):
        capacidad.indices(10.0, 0.5, lse, lie)
    with pytest.raises(DatosInvalidos, match="invertidos"):
        capacidad.ventana_operacion(0.5, 0.01, lse, lie)


def test_sin_especificaciones():
    with pytest.raises(DatosInvalidos, match="al menos un límite"):
        capacidad.indices(10.0, 0.5)


def test_especificacion_unilateral_es_valida():
    r = capacidad.indices(10.0, 0.5, lse=12.0)
    assert r["Cpk"] == pytest.approx(2 / 1.5)


# ------------------------------------------------- datos insuficientes ----
def test_imr_con_un_dato():
    with pytest.raises(DatosInvalidos, match="al menos 2"):
        variables.fase1_imr([3.0])


def test_intervalos_con_un_dato():
    with pytest.raises(DatosInvalidos, match="al menos 2 datos"):
        capacidad.intervalos_confianza(1.2, 1.1, 1)


def test_disenar_plan_ltpd_menor_que_nac():
    with pytest.raises(DatosInvalidos, match="NAC < LTPD"):
        muestreo.disenar_plan(0.05, 0.02, 0.05, 0.10)


# --------------------------------------------------- carga de archivos ----
class Subido(io.BytesIO):
    """Imita el archivo que entrega st.file_uploader (tiene .name y .getvalue())."""

    def __init__(self, nombre, contenido):
        super().__init__(contenido)
        self.name = nombre


def test_lee_csv_con_punto_y_coma_y_coma_decimal():
    f = Subido("datos.csv", "X1;X2\n10,5;10,7\n10,6;10,4\n".encode("utf-8"))
    df = datos.leer_archivo(f)
    assert df.shape == (2, 2)
    assert df["X1"].iloc[0] == pytest.approx(10.5)


def test_lee_csv_con_coma_y_punto_decimal():
    df = datos.leer_archivo(Subido("datos.csv", b"X1,X2\n10.5,10.7\n10.6,10.4\n"))
    assert df["X2"].sum() == pytest.approx(21.1)


def test_lee_excel_con_varias_hojas():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as w:
        pd.DataFrame({"Notas": ["x"]}).to_excel(w, sheet_name="Notas", index=False)
        pd.DataFrame({"X1": [1.0, 2.0], "X2": [3.0, 4.0]}).to_excel(w, sheet_name="Mediciones", index=False)
    f = Subido("libro.xlsx", buf.getvalue())
    assert datos.hojas_excel(io.BytesIO(buf.getvalue())) == ["Notas", "Mediciones"]
    df = datos.leer_archivo(f, hoja="Mediciones")
    assert list(df.columns) == ["X1", "X2"]


def test_numeros_escritos_como_texto():
    s = datos.a_numerico(pd.Series(["10,5", "1.234,5", "1,234.5", "abc", ""]))
    assert s.tolist()[:3] == [10.5, 1234.5, 1234.5]
    assert s.isna().tolist()[3:] == [True, True]


def test_subgrupos_desde_filas_quitan_vacios():
    df = pd.DataFrame({"X1": [1.0, None, 3.0], "X2": [2.0, None, 4.0]})
    g, et = datos.subgrupos_desde_filas(df, ["X1", "X2"])
    assert len(g) == 2 and et == [1, 3]  # se conserva el número de fila original
