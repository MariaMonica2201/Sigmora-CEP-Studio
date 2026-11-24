# Sigmora CEP Studio · Software de Control Estadístico de Procesos

Aplicación web local (Python + Streamlit) para el Trabajo Final Integrador de Control Estadístico de Procesos.
Todos los cálculos usan únicamente las fórmulas y procedimientos del material del curso: Módulo Académico
(Campuzano), hoja «Fórmulas control», presentaciones de capacidad y de muestreo de aceptación, y el artículo
del docente sobre el esquema DS-c.

## Repositorio y versión en línea

- Código fuente: https://github.com/MariaMonica2201/Sigmora-CEP-Studio
- Versión en línea (Streamlit Community Cloud, sin instalar): https://sigmora-cep-studio.streamlit.app

Para publicarla en Streamlit Community Cloud: en https://share.streamlit.io pulse «Create app», elija el
repositorio `MariaMonica2201/Sigmora-CEP-Studio`, rama `main`, archivo principal `app.py` y, en «Advanced
settings», Python 3.12. El archivo `.streamlit/config.toml` (tema, tipografías y `enableStaticServing`) y la
carpeta `static/` deben estar en el repositorio para que se vean las fuentes y las fotografías.

## Instalación (una sola vez)

1. Instale **Python 3.10 o superior** desde https://www.python.org (en Windows marque «Add Python to PATH»).
2. Abra una terminal en esta carpeta y ejecute:

   ```
   pip install -r requirements.txt
   ```

## Ejecución

- **Windows:** doble clic en `iniciar_windows.bat`. El archivo busca Python solo (lanzador `py`, `python` o la
  carpeta de instalación habitual), instala las librerías y abre el programa. Si dice que no encuentra Python,
  instálelo desde python.org marcando «Add python.exe to PATH» y, si Windows abre la Microsoft Store, apague los
  alias «python.exe» y «python3.exe» en Configuración → Aplicaciones → Configuración avanzada de aplicaciones →
  Alias de ejecución de aplicaciones.
- **Mac / Linux:** `bash iniciar_mac_linux.sh`.
- O desde la terminal: `streamlit run app.py`

Se abre el navegador en `http://localhost:8501` con los 13 pasos en la barra lateral, una barra superior con los datos activos y el botón de ajustes (límites Z_α/2 o α y reglas de patrones). Para cerrar, cierre la terminal.

## Librerías requeridas

streamlit, pandas, numpy, scipy, plotly, openpyxl (ver `requirements.txt`).

## Estructura del código (organizado por módulos)

```
app.py                  Punto de entrada y menú
cep/                    Cálculos (sin interfaz), cada función documentada con su fórmula
  constantes.py         Tabla de factores d2, D3, D4, c4, B3, B4, A2, A3
  estadistica.py        Normal, Binomial, Poisson, Hipergeométrica, Ji-cuadrada
  datos.py              Módulo 1: carga, limpieza, subgrupos, resúmenes
  variables.py          Módulo 2: X̄-R, X̄-S, I-MR, Fase I (cepillado) y Fase II
  atributos.py          Módulo 3: p (n fijo/variable, 3 métodos), np, c, u, Pareto
  patrones.py           Módulo 4: reglas de patrones no aleatorios (sección 4.5)
  supuestos.py          Módulo 4: prueba Ji-cuadrada de normalidad, histograma, independencia
  capacidad.py          Módulo 5: Cp, Cpk, Cpu, Cpl, %PNC, IC, ventana de operación
  diseno.py             Módulo 6: ARL0, ARL1, ATS, potencia, n, VEPNC, VPPNC, curva OC, DS-c
  muestreo.py           Módulo 7: planes simple y doble, OC, AOQ/AOQL, IQL, método matemático, MIL-STD-105E
  reporte.py            Módulo 8: exportación a Excel y HTML
  validacion.py         Revisión de entradas antes de calcular (n = 0, D > n, σ = 0, LIE ≥ LSE, …)
  empresa.py            Módulo 0: perfil de empresa (JSON), plan de muestreo (tabla 10/5/2/1 %), plantillas Excel
  graficos.py           Gráficos (plotly)
paginas/                Interfaz de cada paso (m0_empresa.py, m_requisitos.py, m1_datos.py … m8_reportes.py) y estilo.py
datos_ejemplo/          Datos de prueba de los ejemplos del Módulo Académico
pruebas/                Validación contra el módulo, pruebas automáticas (pytest) y decisiones metodológicas
```

## Flujo de uso (ruta guiada en 13 pasos)

La aplicación se recorre como un asistente: la barra lateral muestra los 13 pasos con su estado (listo o pendiente),
cada paso explica **qué necesita, qué hace y a qué paso se pasa después**, y los botones «Anterior / Siguiente»
llevan de un paso al otro.

1. **Requerimientos**: qué exige cada análisis, formatos aceptados, plantillas y lista de verificación.
2. **Empresa (opcional)**: ficha de la empresa (misión, visión, procesos, producción, jornada) y sus fotografías.
3. **Datos**: Excel/CSV o ejemplos; variable o atributo; subgrupos racionales.
4. **Especificaciones**: LIE, valor nominal y LSE del cliente.
5. **Supuestos**: normalidad Ji-cuadrada, independencia y estabilidad preliminar.
6. **Estabilidad (Fase I)**: cartas X̄-R, X̄-S (o I-MR si n = 1), patrones y cepillado.
7. **Capacidad**: Cp, Cpk, Cpu, Cpl, %PNC, intervalos y escenarios.
8. **Plan de muestreo**: n, horas entre subgrupos y unidades por día (tabla 10/5/2/1 %).
9. **Fase II**: monitoreo con muestras nuevas, potencia y carga muestral (ATS1).
10. **Cartas por atributos**: p, np, c, u repitiendo los pasos de estabilidad a carga muestral.
11. **Mejores condiciones**: proceso centrado, plan con menor ATS1 y causas a atacar.
12. **Muestreo de aceptación**: planes simple/doble, curva OC, AOQ/AOQL y MIL-STD-105E.
13. **Informe**: en cada paso pulse «Agregar al reporte»; aquí descargue Excel e informe HTML.

Los 13 pasos están en la barra lateral izquierda (con su estado: listo o pendiente). En el botón de ajustes (arriba a la derecha) se elige Z_α/2 (3 por defecto) o α, y los parámetros de las reglas de patrones.

### Formatos de entrada

- Variables, formato ancho: una fila por subgrupo, columnas X1…Xn.
- Variables, formato largo: columna de medición + columna de subgrupo.
- Variables, una columna en orden de producción (se agrupan cada n datos o se usan como individuales).
- Atributos: columna de conteo (defectuosos o defectos) y columna de n (o n constante).
- CSV con `;` o `,`, coma o punto decimal; Excel `.xlsx`.

## Validación

```
python pruebas/validacion_ejemplos_modulo.py
```

Compara 52 resultados del software con los ejemplos resueltos del módulo. Coinciden 47. De las 5
diferencias, 3 son errores aritméticos o de lectura de tabla en el texto del módulo y 2 son decisiones de
método (carta p con n variable y muestreo doble con lote finito). Para cada una el script rehace el paso
del módulo y la explicación está en `pruebas/DECISIONES_METODOLOGICAS.md`. Ningún cálculo se ajustó para
coincidir con el material. Las 52 comparaciones son ejemplos seleccionados, no una prueba exhaustiva.

Pruebas automáticas (cálculos, validación de entradas, casos de referencia independientes y recorrido
completo de la aplicación con Streamlit). Primero instale las dependencias del proyecto (incluyen
Streamlit y pytest) y después ejecute las pruebas, desde la carpeta del proyecto:

```
pip install -r requirements.txt
python -m pytest pruebas
```

`pruebas/test_referencias_independientes.py` compara con valores que no salen del programa: las tablas
MIL-STD-105E de la presentación de muestreo del curso, los factores de la tabla de constantes derivados
desde su definición matemática, aritmética exacta y simulación de Monte Carlo. Cada caso indica su origen.

## Supuestos y decisiones documentadas

- Carta I-MR: se construye con las fórmulas de X̄-R usando rangos móviles de 2 datos (d2, D3, D4 para n = 2),
  porque el enunciado la pide y el módulo no la desarrolla por separado.
- Independencia: diagrama de dispersión dato t vs t+1 (herramienta 2.7.4) y rachas/tendencias (4.5).
- Estratificación y mezcla (4.5.4 y 4.5.6): el módulo no fija un número de puntos; son parámetros configurables.
- Prueba Ji-cuadrada: las clases extremas se extienden a ±∞ para que las probabilidades sumen 1. Antes de
  concluir se verifica E ≥ 5 en toda clase, ν ≥ 1 y N ≥ 20; si no se cumple, la prueba se declara no
  aplicable. «No se rechaza H0» no demuestra normalidad.
- Potencia de la carta X̄: fórmula del módulo, 1 − β = P(Z ≥ |Z_α/2| − d·√n) (sólo la cola del lado del corrimiento).
- Muestreo doble con lote finito (hipergeométrica): se acepta si d1 ≤ c1 y la segunda muestra se toma de las
  N − n1 unidades restantes con D − d1 defectuosos.
- Carta p con n variable (Método 1): límites p̄ ± Z·√(p̄(1 − p̄)/n_i), centrados en p̄.
- MIL-STD-105E: muestreo simple, inspección normal, niveles generales I–III (tablas de la presentación de muestreo).

## Uso con cualquier empresa

- El software es genérico: se cargan los datos (Excel o CSV) y la portada, el resumen, las cartas, la capacidad y el
  informe se generan a partir de ellos. Registrar la empresa (paso 2) es opcional y se guarda como `.json`.
- **Sin especificaciones (LIE/LSE):** las cartas X̄-R, X̄-S, I-MR y los supuestos funcionan igual; Cp, Cpk y %PNC
  requieren LIE y/o LSE.
- **Atributos desde variables:** en el paso 10, con LIE/LSE, cada unidad fuera de especificación se cuenta como
  defectuosa y se arman las cartas p y np.
- Las plantillas Excel (paso 1) traen el formato que lee el paso 3.

## Diseño, fotografías y licencias

La interfaz no usa emojis ni adornos: rejilla de líneas finas, números en letra monoespaciada y un solo color de acento. Todo funciona sin internet (fotografías, tipografías e iconos
están dentro de la carpeta `static/`). Las fotos de la empresa se cambian en el paso 2 («Fotografías de la
empresa») o en la hoja «Fotos» de la ficha Excel; si no se cargan, se usan las fotografías genéricas de abajo.

- **Fotografías:** Unsplash, bajo la [Licencia Unsplash](https://unsplash.com/license) (uso libre, también
  comercial, sin atribución obligatoria). Archivos en `static/fotos/` y su origen:
  - `planta.jpg`: https://images.unsplash.com/photo-1513828583688-c52646db42da
  - `ingenieria.jpg`: https://images.unsplash.com/photo-1581091226825-a6a2a5aee158
  - `soldadura.jpg`: https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1
  - `calidad.jpg`: https://images.unsplash.com/photo-1581093588401-fbb62a02f120
  - `estanteria.jpg`: https://images.unsplash.com/photo-1587293852726-70cdb56c2866
  - `planos.jpg`: https://images.unsplash.com/photo-1581092160562-40aa08e78837
  - `equipo.jpg`: https://images.unsplash.com/photo-1581093196277-9f608bb3d4b6
  - `portada.jpg`: https://images.unsplash.com/photo-1567789884554-0b844b597180
  - `datos.jpg`: https://images.unsplash.com/photo-1551288049-bebda4e38f71
  - `analitica.jpg`: https://images.unsplash.com/photo-1460925895917-afdab827c52f
  - `impresion.jpg`: https://images.unsplash.com/photo-1611117775350-ac3950990985
  - `almacen.jpg`: https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d
  - `laboratorio.jpg`: https://images.unsplash.com/photo-1581093450021-4a7360e9a6b5
- **Tipografías:** IBM Plex Sans e IBM Plex Mono, licencia SIL Open Font License 1.1 (`static/fuentes/`).
- **Iconos de respaldo:** [Lucide](https://lucide.dev), licencia ISC (`paginas/iconos.py`).
