#!/usr/bin/env bash
# Salir si ocurre un error
set -o errexit

echo "=== Iniciando la preparación del entorno ==="

# 1. Clonar el repositorio base de OrpheusDL si no existe
if [ ! -d "orpheusdl" ]; then
    echo "Clonando OrpheusDL..."
    git clone https://github.com orpheusdl
fi

# 2. Clonar el módulo de KKBOX dentro de la carpeta correspondiente
if [ ! -d "orpheusdl/modules/kkbox" ]; then
    echo "Instalando módulo KKBOX..."
    git clone https://github.com orpheusdl/modules/kkbox
fi

# 3. Instalar todas las dependencias de Python
echo "Instalando dependencias de Python..."
pip install -r orpheusdl/requirements.txt
pip install flask gunicorn

# 4. Crear una configuración base por defecto de forma dinámica
echo "Generando archivo de configuración inicial..."
mkdir -p orpheusdl/config
cat <<EOT > orpheusdl/config/settings.json
{
    "global": {
        "download_quality": "high",
        "main_resolution": 2048
    },
    "kkbox": {
        "email": "${KKBOX_EMAIL}",
        "password": "${KKBOX_PASSWORD}",
        "kc1_key": "${KKBOX_KC1_KEY}",
        "secret_key": "${KKBOX_SECRET_KEY}"
    }
}
EOT

echo "=== Entorno preparado con éxito ==="
