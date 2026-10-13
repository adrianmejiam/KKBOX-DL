#!/usr/bin/env bash
# Salir inmediatamente si un comando falla
set -o errexit

echo "=== Preparando entorno definitivo OrpheusDL + KKBOX ==="

# 1. Clonar el repositorio base oficial desde OrfiTeam
if [ ! -d "orpheusdl" ]; then
    echo "Clonando framework base OrpheusDL desde OrfiTeam..."
    git clone https://github.com orpheusdl
fi

# 2. Clonar el módulo de KKBOX desde el usuario uhwot
if [ ! -d "orpheusdl/modules/kkbox" ]; then
    echo "Instalando módulo KKBOX desde uhwot..."
    git clone https://github.com orpheusdl/modules/kkbox
fi

# 3. Instalar requerimientos base del sistema y Flask para el entorno web
echo "Instalando dependencias de Python..."
pip install -r orpheusdl/requirements.txt
pip install flask gunicorn

# 4. Forzar la inicialización nativa de la base de datos de configuraciones de Orpheus
echo "Inicializando configuración base de OrpheusDL..."
cd orpheusdl
python orpheus.py settings refresh
cd ..

# 5. Inyectar de forma dinámica las credenciales del usuario y llaves de la API
echo "Escribiendo archivo de configuración config/settings.json..."
mkdir -p orpheusdl/config
cat <<EOT > orpheusdl/config/settings.json
{
    "global": {
        "download_path": "../downloads/",
        "download_quality": "high",
        "main_resolution": 2048,
        "search_limit": 10
    },
    "kkbox": {
        "email": "${KKBOX_EMAIL}",
        "password": "${KKBOX_PASSWORD}",
        "kc1_key": "${KKBOX_KC1_KEY}",
        "secret_key": "${KKBOX_SECRET_KEY}"
    }
}
EOT

# Crear el directorio donde se almacenarán temporalmente las descargas
mkdir -p downloads

echo "=== Configuración de entorno finalizada con éxito ==="
