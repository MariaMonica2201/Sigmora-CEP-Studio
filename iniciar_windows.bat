@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Sigmora CEP Studio
echo.
echo  Sigmora CEP Studio - Control Estadistico de Procesos
echo  ==========================================
echo.

set "PY="

rem 1) Lanzador oficial de Python para Windows (py.exe)
py -3 -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PY=py -3"
    goto :encontrado
)

rem 2) python en el PATH (se descarta el acceso directo de Microsoft Store, que falla)
python -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PY=python"
    goto :encontrado
)

rem 3) Instalaciones habituales (del mas nuevo al mas viejo)
for /f "delims=" %%D in ('dir /b /ad /o-n "%LocalAppData%\Programs\Python\Python3*" 2^>nul') do (
    if exist "%LocalAppData%\Programs\Python\%%D\python.exe" (
        set "PY="%LocalAppData%\Programs\Python\%%D\python.exe""
        goto :encontrado
    )
)
for /f "delims=" %%D in ('dir /b /ad /o-n "%ProgramFiles%\Python3*" 2^>nul') do (
    if exist "%ProgramFiles%\%%D\python.exe" (
        set "PY="%ProgramFiles%\%%D\python.exe""
        goto :encontrado
    )
)
for /f "delims=" %%D in ('dir /b /ad /o-n "C:\Python3*" 2^>nul') do (
    if exist "C:\%%D\python.exe" (
        set "PY="C:\%%D\python.exe""
        goto :encontrado
    )
)

echo  [ERROR] No se encontro Python en este computador.
echo.
echo  Para instalarlo (una sola vez):
echo    1. Entre a https://www.python.org/downloads/ y descargue Python 3.10 o superior.
echo    2. Ejecute el instalador y MARQUE la casilla "Add python.exe to PATH"
echo       en la primera pantalla. Luego pulse "Install Now".
echo    3. Cierre esta ventana y vuelva a hacer doble clic en iniciar_windows.bat.
echo.
echo  Si Windows le ofrece abrir Microsoft Store al escribir "python", desactive ese
echo  acceso directo en: Configuracion ^> Aplicaciones ^> Configuracion avanzada de
echo  aplicaciones ^> Alias de ejecucion de aplicaciones ^> apague "python.exe" y "python3.exe".
echo.
pause
exit /b 1

:encontrado
echo  Python encontrado:
%PY% --version
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if !errorlevel! neq 0 (
    echo.
    echo  [ERROR] Se necesita Python 3.10 o superior. Instale una version mas reciente desde
    echo  https://www.python.org/downloads/ y vuelva a intentarlo.
    pause
    exit /b 1
)

echo.
echo  Instalando o verificando las librerias (la primera vez tarda unos minutos)...
%PY% -m pip install --disable-pip-version-check --no-warn-script-location -q -r requirements.txt
if !errorlevel! neq 0 (
    echo.
    echo  [ERROR] No se pudieron instalar las librerias. Revise la conexion a internet
    echo  y vuelva a intentarlo. Tambien puede ejecutar manualmente en esta carpeta:
    echo      %PY% -m pip install -r requirements.txt
    pause
    exit /b 1
)

rem Evita que Streamlit pida un correo la primera vez que se ejecuta
if exist "%USERPROFILE%\.streamlit\credentials.toml" goto :sin_correo
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
> "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
>> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
:sin_correo

echo.
echo  Abriendo Sigmora CEP Studio en el navegador (http://localhost:8501)...
echo  Para cerrar el programa, cierre esta ventana.
echo.
%PY% -m streamlit run app.py --browser.gatherUsageStats false
echo.
echo  Sigmora CEP Studio se cerro. Si aparecio un error arriba, copielo y compartalo.
pause
