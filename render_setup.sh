#!/usr/bin/env bash
# Salir inmediatamente si algún comando en la secuencia falla
set -o errexit

echo "=== Iniciando la preparación del entorno OrpheusDL + KKBOX ==="

# 1. Clonar el framework base oficial de OrfiTeam usando la ruta explícita final
if [ ! -d "orpheusdl" ]; then
    echo "Clonando framework base OrpheusDL desde OrfiTeam..."
    git clone "https://github.com/OrfiTeam/OrpheusDL.git" orpheusdl
fi

# 2. Clonar el módulo de KKBOX de uhwot usando la ruta explícita final
if [ ! -d "orpheusdl/modules/kkbox" ]; then
    echo "Instalando módulo KKBOX desde uhwot..."
    git clone "https://github.com" orpheusdl/modules/kkbox
fi

# 3. Instalar todos los requerimientos base del sistema y Flask
echo "Instalando dependencias de Python..."
pip install --upgrade pip
pip install --prefer-binary -r orpheusdl/requirements.txt
pip install --prefer-binary flask gunicorn gevent

# 4. Inicializar nativamente la base de configuración de OrpheusDL
echo "Inicializando configuraciones base..."
cd orpheusdl
python orpheus.py settings refresh
cd ..

# 5. Inyectar los accesos y parámetros de desencripción en el settings.json
echo "Escribiendo archivo de configuración config/settings.json..."
mkdir -p orpheusdl/config

EMAIL="${KKBOX_EMAIL:-15cb1b133c@emailnox.live}"
PASS="${KKBOX_PASSWORD:-Mexico_2026}"
KC1="${KKBOX_KC1_KEY:-7f1a68f00b747f4ac1469c72e7ef492c}"
SECRET="${KKBOX_SECRET_KEY:-0ff29b7c9bd8fb60a3abd6b3d402b02c}"

cat <<EOT > orpheusdl/config/settings.json
{
    "global": {
        "download_path": "../downloads/",
        "download_quality": "hifi",
        "main_resolution": 2048,
        "search_limit": 10
    },
    "modules": {
        "kkbox": {
            "email": "${EMAIL}",
            "password": "${PASS}",
            "kc1_key": "${KC1}",
            "secret_key": "${SECRET}"
        }
    }
}
EOT
