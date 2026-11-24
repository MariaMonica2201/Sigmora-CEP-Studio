# Decisiones metodológicas y diferencias con el Módulo Académico

El script `pruebas/validacion_ejemplos_modulo.py` compara 52 resultados del software con los ejemplos
resueltos del Módulo Académico y de la presentación de muestreo. Coinciden 47. Las 5 diferencias se
revisaron una por una contra el texto del módulo **antes** de decidir; ningún cálculo se cambió para que
coincidiera con el material. Para cada diferencia, el script rehace el paso del módulo (columna
«Recálculo del módulo») y así muestra de dónde sale cada número.

| # | Ejemplo | Módulo | Software | Clasificación |
|---|---------|--------|----------|---------------|
| 1 | Cap. 3 ej. 3, ventana de operación, X̄ mínimo | 60,7875 | 67,878 | Error aritmético del material |
| 2 | Ladrillos b), potencia de la carta X̄ | 0,94684 | 0,428 | Error aritmético del material |
| 3 | MIL-STD-105E ej. 2 (lote 1 000, NAC 0,10) | n = 200 | n = 125, Ac 0, Re 1 | Error de lectura de la tabla |
| 4 | Carta p de módems con n variable, LCS del subgrupo 1 | 0,03727 | 0,03191 | Decisión de método |
| 5 | Plan doble, lote N = 80, p' = 5 % | 0,9604 | 0,9843 | Decisión de método |

## 1. Ventana de operación (capítulo 3, ejemplo 3)

El módulo plantea, para el límite inferior, `−1,75069 = (60 − X̄)/4,5`. Despejando: X̄ = 60 + 1,75069·4,5 =
**67,878**. El texto escribe 60,7875, que no sale de esa ecuación. Una comprobación independiente: con
la media centrada entre límites, la ventana debe ser simétrica. Por el LSE el módulo obtiene 90 − 7,875 =
82,125, así que por el LIE debe dar 60 + 7,875 = 67,875.

**Decisión:** se mantiene el cálculo del software. La prueba `test_ventana_operacion_es_simetrica` verifica
además que en el borde de la ventana el %PNC por cada límite es exactamente el objetivo (4 %).

## 2. Potencia de la carta X̄ (ejemplo Ladrillos y CIA, parte b)

La fórmula del módulo es 1 − β = P(Z ≤ d·√n − |Z_α/2|), con d = 0,65, n = 5 y Z_α/2 = 1,635. El texto
escribe `Φ(0,65·√5 − 1,635) = Φ(1,615) = 0,94684`. Pero 0,65·√5 = 1,453 y 1,453 − 1,635 = −0,18, así que
1 − β = Φ(−0,18) = **0,428**. El 1,615 sale de 0,65·5 − 1,635: se usó 5 en lugar de √5.

Que el procedimiento correcto es con √n lo confirma el mismo ejemplo: la parte c) despeja n con
`−0,47827 = 0,7·√n + …` y obtiene n = 9,11, valor que el software reproduce. Con n = 9,11 la potencia del
software vuelve a dar exactamente 0,68377 (prueba `test_potencia_xbar_usa_raiz_de_n`). La razón
estadística: la carta X̄ grafica medias de n datos, cuya desviación es σ/√n.

**Decisión:** se mantiene d·√n. El β = 0,05316 y el VEPNC = 16,95 del texto heredan el error; el software
reproduce el VEPNC cuando recibe ese mismo β, lo que confirma que la fórmula del VEPNC está bien.

## 3. MIL-STD-105E, ejemplo 2 (lote de 1 000 piezas, NAC 0,10, nivel II)

Lote de 1 000 con nivel II da la letra **J** (n = 80). En la tabla maestra de inspección normal
(diapositiva 17 de la presentación de muestreo) la celda J / 0,10 es una flecha hacia abajo. El primer
plan debajo de la flecha está en la fila **K**: n = 125, Ac = 0, Re = 1. El n = 200 del texto corresponde a
la fila L, que es el plan de la columna 0,065.

**Decisión:** se mantiene la lectura de la tabla (prueba `test_mil_std_ejemplo_2_sigue_la_flecha_de_la_tabla`).
Las partes b) y c) del ejemplo usan n = 200 y cambian si se usa n = 125.

## 4. Carta p con tamaño de muestra variable (módems, 4.8.1.2, Método 1)

La fórmula del módulo es LC = p̄ y LCS/LCI = p̄ ± 3·√(p̄(1 − p̄)/n_i), con p̄ = ΣD/Σn = 856/38 800 = 0,02206.
La tabla resuelta del ejemplo, en cambio, centra cada límite en la p_i del propio subgrupo:
0,0265 ± 3·√(0,0265·0,9735/2000) = 0,0372745 / 0,0157255. El script reproduce ese número.

Con límites centrados en p_i, cada punto queda siempre en el centro de sus propios límites y la carta
nunca podría señalar un subgrupo fuera de control. Por eso la conclusión «no hay puntos fuera de los
límites» del ejemplo es automática y no informa nada.

**Decisión:** se usa p̄, como dice la fórmula del módulo.

## 5. Muestreo doble con lote finito (5.7.1, lote de 80 artículos, p' = 5 %)

Plan n1 = 20, c1 = 1, n2 = 10, c2 = 3; el lote tiene D = 4 defectuosos.

- **Regla de decisión.** El módulo define c1 como «número de aceptación de la primera muestra», y la
  presentación de muestreo da el ejemplo Ac = 1, Re = 4: se acepta si d1 ≤ c1. El árbol del ejemplo sólo
  acepta con d1 = 0 y envía d1 = 1 a la segunda muestra.
- **Segunda muestra.** Las 20 piezas de la primera muestra ya salieron del lote. La segunda muestra se
  toma de las **N − n1 = 60** piezas restantes, que tienen **D − d1** defectuosos. El ejemplo calcula la
  segunda muestra con el lote completo (80 piezas, 4 defectuosas), como si las primeras 20 volvieran al lote.

El software (versión anterior) tenía este mismo segundo problema: calculaba la segunda muestra con N y D
originales. Daba 0,9630 y por eso «coincidía» con el 0,9604 del módulo dentro de la tolerancia del 1 %,
aunque por una razón equivocada. Ahora:

Pa = P(d1 ≤ c1) + Σ_{d1 = c1+1}^{c2} P(d1) · H(c2 − d1; N − n1, D − d1, n2) = **0,9843**

El script reproduce el 0,9604 del módulo con su árbol (sólo d1 = 0 acepta y la segunda muestra usa el lote
completo). El valor del software se comprueba de dos maneras independientes: enumeración exacta con
fracciones y simulación de 60 000 lotes sacando las piezas sin reposición (pruebas
`test_pa_doble_hipergeometrica_usa_lote_restante` y `test_pa_doble_simulacion_de_lotes`). Con Binomial o
Poisson (lotes grandes o flujo de lotes) la fracción defectuosa no cambia y la segunda muestra usa la misma p'.

**Decisión:** regla d1 ≤ c1 y segunda muestra del lote restante.

## Prueba Ji-cuadrada de normalidad

El procedimiento es el del módulo (2.6). Se añadieron controles antes de concluir:

- Toda clase agrupada debe tener frecuencia esperada E ≥ 5 (se unen clases vecinas, como en el módulo).
- Grados de libertad ν = k − r − 1 ≥ 1, con r = 2 parámetros estimados (media y S). Hacen falta al menos
  r + 2 = 4 clases, cada una con E ≥ 5, es decir, **N ≥ 20 datos**. Con menos datos la prueba se declara
  «no aplicable» y no se emite un resultado.
- Datos con variabilidad (S > 0); la independencia se revisa en su propia pestaña.
- Con N < 50 o ν ≤ 2 se advierte que la prueba tiene poca potencia.

**Interpretación.** «No se rechaza H0» significa que los datos no contradicen la normalidad con el nivel α
elegido. No demuestra que los datos sean normales: con pocos datos la prueba sólo detecta alejamientos
grandes. La conclusión de la app y del informe lo dice con esas palabras.

## Validación de entradas

Los cálculos (`cep/validacion.py`) rechazan con un mensaje claro, en lugar de dividir entre cero o
devolver NaN:

- tamaños de muestra o de lote iguales a cero, negativos o no enteros; muestras mayores que el lote;
- defectuosos mayores que el tamaño de muestra y conteos negativos (en defectos, carta c/u, una unidad
  puede tener varios: no se exige conteo ≤ n);
- subgrupos vacíos, de tamaños distintos, con n fuera de la tabla de constantes (2 a 25) o menos de 2
  subgrupos para estimar límites (también después de excluir puntos);
- desviación estándar cero (R̄, S̄, MR̄ o σ = 0);
- LIE ≥ LSE;
- datos insuficientes: I-MR con un dato, intervalos de confianza con un dato, Ji-cuadrada con N < 20.

Con p̄ = 0, p̄ = 1 o c̄ = 0 la carta se dibuja pero avisa que sus límites colapsan en la línea central.

## Pruebas automáticas

```
python -m pytest pruebas
```

- `test_calculos.py`: muestreo doble (enumeración exacta y simulación), Ji-cuadrada, las cinco diferencias
  con el módulo y el script de validación (falla si aparece una diferencia sin clasificar).
- `test_validacion_entradas.py`: cada caso de datos inválidos y la lectura de archivos CSV/Excel.
- `test_recorrido_app.py`: ejecuta la aplicación completa sin navegador: abre los 13 pasos, carga datos
  (ejemplo del módulo y libro Excel de varias hojas), recorre variables y atributos, revisa los estados
  de cada paso, los mensajes ante datos inválidos y la generación de los informes Excel y HTML.

## Defectuosos enteros en lotes finitos (hipergeométrica)

Un lote real tiene un número entero de defectuosos D. Si se escribe una fracción p' con p'·N no entero
(por ejemplo 80 · 0,03 = 2,4), el programa usa D = round(p'·N) = 2 y **lo avisa en pantalla**, indicando la
fracción efectiva D/N = 0,025. Para evitar la aproximación, en los planes simple y doble se puede escribir
D directamente. Las curvas OC y AOQ con lote finito se evalúan sólo en fracciones D/N con D entero.
Los mismos avisos aparecen para NAC y LTPD cuando el lote es finito.
