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

# Crear el directorio físico donde se van a compilar las descargas en tránsito
mkdir -p downloads

echo "=== Entorno preparado exitosamente para adrianmejiam ==="
