#!/usr/bin/env bash
# Salir inmediatamente si un comando falla
set -o errexit

echo "=== Preparando entorno definitivo OrpheusDL + KKBOX ==="

# 1. Clonar el repositorio base usando la URL absoluta completa de OrfiTeam
if [ ! -d "orpheusdl" ]; then
    echo "Clonando framework base OrpheusDL desde OrfiTeam..."
    git clone https://github.com orpheusdl
fi

# 2. Clonar el módulo específico usando la URL absoluta completa de chuchungman
if [ ! -d "orpheusdl/modules/kkbox" ]; then
    echo "Instalando módulo KKBOX desde chuchungman..."
    git clone https://github.com orpheusdl/modules/kkbox
fi

# 3. Instalar requerimientos base del sistema y Flask para la interfaz web
echo "Instalando dependencias de Python..."
pip install -r orpheusdl/requirements.txt
pip install flask gunicorn

# 4. Inyectar de forma dinámica las credenciales y llaves fijas de la API
echo "Escribiendo archivo de configuración config/settings.json..."
mkdir -p orpheusdl/config
cat <<EOT > orpheusdl/config/settings.json
{
    "global": {
        "download_quality": "high",
        "main_resolution": 2048,
        "output_dir": "../downloads"
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
