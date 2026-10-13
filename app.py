import os
import json
import time
import subprocess
import threading
from flask import Flask, render_template, request, Response, send_from_directory, jsonify

app = Flask(__name__)
BASE_DIR = app.root_path
ORPHEUS_DIR = os.path.join(BASE_DIR, 'orpheus_base')
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
    """Genera la configuración interna con tus credenciales de KKBOX."""
    config_dir = os.path.join(ORPHEUS_DIR, 'config')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'settings.json')

    settings = {
        "download_quality": "hifi",
        "download_path": task_download_dir,
        "modules": {
            "kkbox": {
                "email": "15cb1b133c@emailnox.live",
                "password": "Mexico_2026",
                "kc1_key": "7f1a68f00b747f4ac1469c72e7ef492c",
                "secret_key": "0ff29b7c9bd8fb60a3abd6b3d402b02c"
            }
        }
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
        download_status[task_id]["status"] = "Descargando flujo FLAC Lossless..."
        add_log(f"[+] Procesando URL: {url}")
        
        cmd = ["python3", script_path, url]
        process = subprocess.Popen(cmd, cwd=ORPHEUS_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            cleaned_line = line.strip()
            if cleaned_line:
                add_log(f"[MOTOR] {cleaned_line}")
                if "100%" in cleaned_line or "Downloading" in cleaned_line:
                    download_status[task_id]["progress"] = 65
            
        process.wait()

        download_status[task_id]["progress"] = 85
        download_status[task_id]["status"] = "Empaquetando archivo de audio..."
        add_log("[+] Buscando archivo .flac generado...")
        
        flac_file = None
        search_dirs = [task_download_dir, DOWNLOAD_FOLDER, ORPHEUS_DIR]
        
        for s_dir in search_dirs:
            if os.path.exists(s_dir):
                for root, dirs, files in os.walk(s_dir):
                    for file in files:
                        if file.endswith('.flac') and not file.startswith('kkbox_lossless_'):
                            flac_file = os.path.join(root, file)
                            break
                    if flac_file:
                        break
            if flac_file:
                break

        if not flac_file:
            last_log = logs[-1] if logs else "Sin salida"
            raise Exception(f"No se generó el archivo FLAC. Último log: {last_log}")

        final_filename = f"kkbox_lossless_{task_id}.flac"
        final_filepath = os.path.join(DOWNLOAD_FOLDER, final_filename)
        os.rename(flac_file, final_filepath)

        add_log(f"[+] Archivo listado correctamente: {final_filename}")

        download_status[task_id] = {
            "progress": 100,
            "status": "¡Descarga FLAC completada con éxito!",
            "download_url": f"/get-file/{final_filename}",
            "logs": logs
        }

    except Exception as e:
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
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No se proporcionó ninguna URL"}), 400

    task_id = str(int(time.time()))
    download_status[task_id] = {"progress": 5, "status": "Preparando tarea...", "logs": ["[+] Tarea registrada."]}
    
    thread = threading.Thread(target=run_download_task, args=(task_id, url))
    thread.daemon = True
    thread.start()

    return jsonify({"task_id": task_id})

@app.route('/check-progress/<task_id>')
def check_progress(task_id):
    def generate():
        while task_id in download_status:
            status_data = download_status[task_id]
            yield f"data: {json.dumps(status_data)}\n\n"
            if status_data.get("progress") >= 100 or status_data.get("error"):
                break
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/get-file/<filename>')
def get_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True, mimetype='audio/flac')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
