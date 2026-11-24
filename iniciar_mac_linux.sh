#!/bin/bash
cd "$(dirname "$0")"
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "No se encontró Python 3.10 o superior. Descárguelo de https://www.python.org/downloads/ y vuelva a ejecutar este archivo."
  exit 1
fi
"$PY" -m pip install --disable-pip-version-check --no-warn-script-location -q -r requirements.txt || { echo "No se pudieron instalar las librerías."; exit 1; }
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
  mkdir -p "$HOME/.streamlit" && printf '[general]\nemail = ""\n' > "$HOME/.streamlit/credentials.toml"
fi
"$PY" -m streamlit run app.py --browser.gatherUsageStats false
