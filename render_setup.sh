#!/usr/bin/env bash
# Salir inmediatamente si algún comando en la secuencia falla
set -o errexit

echo "=== Iniciando la preparación del entorno OrpheusDL + KKBOX ==="

# Instalar dependencias del sistema necesarias para procesar carátulas y audio (FFmpeg y librerías de imagen)
echo "Instalando dependencias del sistema operativo..."
apt-get update && apt-get install -y ffmpeg libjpeg-dev zlib1g-dev || echo "Aviso: No se pudieron instalar paquetes apt (puede no ser Debian/Ubuntu)."

# 1. Clonar el framework base oficial de OrfiTeam
if [ ! -d "orpheusdl" ]; then
    echo "Clonando framework base OrpheusDL desde OrfiTeam..."
    git clone "https://github.com/OrfiTeam/OrpheusDL.git" orpheusdl
fi

# 2. Clonar el módulo de KKBOX de uhwot
if [ ! -d "orpheusdl/modules/kkbox" ]; then
    echo "Instalando módulo KKBOX desde uhwot..."
    mkdir -p orpheusdl/modules
    git clone "https://github.com/uhwot/orpheusdl-kkbox.git" orpheusdl/modules/kkbox
fi

# 3. Instalar dependencias de Python
echo "Instalando dependencias de Python..."
pip install --upgrade pip
if [ -f "orpheusdl/requirements.txt" ]; then
    pip install -r orpheusdl/requirements.txt
fi
pip install flask gunicorn mutagen yt-dlp Pillow ffmpeg-python

# 4. Inicializar nativamente la base de configuración de OrpheusDL
echo "Inicializando configuraciones base..."
cd orpheusdl
python3 orpheus.py settings refresh || true
cd ..

# 5. Inyectar los accesos y parámetros en el settings.json
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
        "search_limit": 10,
        "embed_cover": true,
        "save_cover": true,
        "save_lyrics": true
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

# Crear el directorio físico de descargas
mkdir -p downloads

echo "=== Entorno preparado exitosamente ==="
