import os
import json
import time
import subprocess
import threading
import traceback
import shutil
from flask import Flask, render_template, request, send_from_directory, jsonify

app = Flask(__name__)
BASE_DIR = app.root_path
ORPHEUS_DIR = os.path.join(BASE_DIR, 'orpheusdl')
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def ensure_orpheus_installed():
    """Clona y configura las herramientas base automáticamente si no están en el entorno."""
    script_path = os.path.join(ORPHEUS_DIR, 'orpheus.py')
    if not os.path.exists(script_path):
        try:
            subprocess.run(["git", "clone", "https://github.com/OrfiTeam/OrpheusDL.git", ORPHEUS_DIR], check=True)
            kkbox_modules_dir = os.path.join(ORPHEUS_DIR, 'modules', 'kkbox')
            os.makedirs(os.path.dirname(kkbox_modules_dir), exist_ok=True)
            subprocess.run(["git", "clone", "https://github.com/uhwot/orpheusdl-kkbox.git", kkbox_modules_dir], check=True)
            
            requirements_path = os.path.join(ORPHEUS_DIR, 'requirements.txt')
            if os.path.exists(requirements_path):
                subprocess.run(["pip", "install", "-r", requirements_path], check=True)
        except Exception as e:
            print(f"Error al inicializar el entorno: {e}")

def setup_orpheus_config(task_download_dir):
    """Configura de manera segura settings.json asegurando que las credenciales y rutas persistan."""
    script_path = os.path.join(ORPHEUS_DIR, 'orpheus.py')
    config_dir = os.path.join(ORPHEUS_DIR, 'config')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'settings.json')

    if not os.path.exists(config_path):
        try:
            subprocess.run(["python3", script_path, "settings", "refresh"], cwd=ORPHEUS_DIR, check=True)
        except Exception as e:
            print(f"Aviso al refrescar configuraciones base: {e}")

    settings = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception:
            settings = {}

    if "global" not in settings:
        settings["global"] = {}
    
    settings["global"]["download_path"] = task_download_dir
    settings["global"]["download_quality"] = "hifi"
    settings["global"]["main_resolution"] = 2048
    settings["global"]["search_limit"] = 10
    settings["global"]["track_filename_format"] = "{track_number} - {artist} - {name}"
    settings["global"]["album_format"] = "{album_artist}/{album}"
    settings["global"]["embed_cover"] = True
    settings["global"]["save_cover"] = True
    settings["global"]["save_lyrics"] = True

    email = os.environ.get("KKBOX_EMAIL", "15cb1b133c@emailnox.live")
    password = os.environ.get("KKBOX_PASSWORD", "Mexico_2026")
    kc1_key = os.environ.get("KKBOX_KC1_KEY", "7f1a68f00b747f4ac1469c72e7ef492c")
    secret_key = os.environ.get("KKBOX_SECRET_KEY", "0ff29b7c9bd8fb60a3abd6b3d402b02c")

    if "modules" not in settings:
        settings["modules"] = {}

    settings["modules"]["kkbox"] = {
        "email": email,
        "password": password,
        "kc1_key": kc1_key,
        "secret_key": secret_key
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

download_status = {}

def run_download_task(task_id, url):
    try:
        logs = []
        def add_log(msg):
            logs.append(msg)
            download_status[task_id]["logs"] = list(logs)

        ensure_orpheus_installed()
        
        task_download_dir = os.path.join(DOWNLOAD_FOLDER, task_id)
        os.makedirs(task_download_dir, exist_ok=True)

        setup_orpheus_config(task_download_dir)

        download_status[task_id] = {"progress": 15, "status": "Iniciando sesión en KKBOX...", "logs": logs}
        add_log("[+] Autenticando cuenta de KKBOX...")

        script_path = os.path.join(ORPHEUS_DIR, 'orpheus.py')
        if not os.path.exists(script_path):
            raise Exception("No se pudo cargar el script de descarga.")

        download_status[task_id]["progress"] = 35
        download_status[task_id]["status"] = "Descargando audio y carátula en alta calidad..."
        add_log(f"[+] Procesando URL: {url}")
        
        cmd = ["python3", script_path, url]
        process = subprocess.Popen(cmd, cwd=ORPHEUS_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            cleaned_line = line.strip()
            if cleaned_line:
                add_log(f"[MOTOR] {cleaned_line}")
                if "Downloading" in cleaned_line:
                    download_status[task_id]["progress"] = 60
                elif "100%" in cleaned_line or "skipped" in cleaned_line.lower():
                    download_status[task_id]["progress"] = 85
        
        process.wait()

        download_status[task_id]["progress"] = 90
        download_status[task_id]["status"] = "Verificando archivo de audio y carátula..."
        add_log("[+] Localizando archivo de audio descargado...")
        
        audio_file = None
        candidate_files = []
        
        # Búsqueda global y recursiva en todas las carpetas posibles de la app
        search_roots = [task_download_dir, DOWNLOAD_FOLDER, ORPHEUS_DIR]
        for s_dir in search_roots:
            if os.path.exists(s_dir):
                for root, dirs, files in os.walk(s_dir):
                    for file in files:
                        if file.lower().endswith(('.flac', '.m4a', '.mp3', '.ogg', '.wav')):
                            full_path = os.path.join(root, file)
                            candidate_files.append((full_path, os.path.getmtime(full_path)))

        if candidate_files:
            # Ordenar estrictamente por fecha de modificación: el archivo más reciente (el que se acaba de descargar) queda primero
            candidate_files.sort(key=lambda x: x[1], reverse=True)
            audio_file = candidate_files[0][0]

        if not audio_file:
            last_log = logs[-1] if logs else "Sin salida"
            raise Exception(f"No se generó ningún archivo de audio. Último log: {last_log}")

        original_filename = os.path.basename(audio_file)
        
        # Generar nombre único para la entrega web combinando el task_id con el nombre real de la pista
        safe_filename = f"{task_id}_{original_filename}"
        final_filepath = os.path.join(DOWNLOAD_FOLDER, safe_filename)
        
        if audio_file != final_filepath:
            if os.path.exists(final_filepath):
                os.remove(final_filepath)
            shutil.copy(audio_file, final_filepath)

        add_log(f"[+] Archivo listo con carátula integrada: {safe_filename}")

        download_status[task_id] = {
            "progress": 100,
            "status": "¡Descarga completada con éxito!",
            "download_url": f"/get-file/{safe_filename}",
            "logs": logs
        }

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[ERROR CRÍTICO] {error_trace}")
        download_status[task_id] = {
            "progress": 100, 
            "status": f"Error: {str(e)}", 
            "error": True,
            "logs": download_status.get(task_id, {}).get("logs", []) + [f"[ERROR] {str(e)}"]
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-download', methods=['POST'])
def start_download():
    data = request.json or {}
    url = data.get('url')
    if not url:
        return jsonify({"error": "No se proporcionó ninguna URL"}), 400

    task_id = str(int(time.time()))
    download_status[task_id] = {"progress": 5, "status": "Preparando tarea...", "logs": ["[+] Tarea registrada."]}
    
    thread = threading.Thread(target=run_download_task, args=(task_id, url))
    thread.daemon = True
    thread.start()

    return jsonify({"task_id": task_id})

@app.route('/get-progress-json/<task_id>')
def get_progress_json(task_id):
    if task_id in download_status:
        return jsonify(download_status[task_id])
    return jsonify({"error": "Tarea no encontrada"}), 404

@app.route('/get-file/<filename>')
def get_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
