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
    """Clona y configura OrpheusDL automáticamente si no se encuentra."""
    script_path = os.path.join(ORPHEUS_DIR, 'orpheus.py')
    if not os.path.exists(script_path):
        print("Clonando OrpheusDL y módulo KKBOX...")
        try:
            subprocess.run(["git", "clone", "https://github.com/OrfiTeam/OrpheusDL.git", ORPHEUS_DIR], check=True)
            kkbox_modules_dir = os.path.join(ORPHEUS_DIR, 'modules', 'kkbox')
            os.makedirs(os.path.dirname(kkbox_modules_dir), exist_ok=True)
            subprocess.run(["git", "clone", "https://github.com/uhwot/orpheusdl-kkbox.git", kkbox_modules_dir], check=True)
            
            requirements_path = os.path.join(ORPHEUS_DIR, 'requirements.txt')
            if os.path.exists(requirements_path):
                subprocess.run(["pip", "install", "-r", requirements_path], check=True)
        except Exception as e:
            print(f"Error al instalar OrpheusDL: {e}")

def setup_orpheus_config(task_download_dir):
    """Genera la configuración apuntando al directorio de la tarea específica."""
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

def run_orpheus_download(task_id, url):
    try:
        ensure_orpheus_installed()
        
        # Crear subdirectorio específico para la tarea
        task_download_dir = os.path.join(DOWNLOAD_FOLDER, task_id)
        os.makedirs(task_download_dir, exist_ok=True)

        setup_orpheus_config(task_download_dir)

        download_status[task_id] = {"progress": 15, "status": "Iniciando sesión en KKBOX..."}
        
        script_path = os.path.join(ORPHEUS_DIR, 'orpheus.py')
        if not os.path.exists(script_path):
            raise Exception("No se encontró orpheus.py.")

        download_status[task_id] = {"progress": 40, "status": "Descargando flujo FLAC Lossless..."}
        
        cmd = ["python3", script_path, url]
        process = subprocess.Popen(cmd, cwd=ORPHEUS_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        output_logs = []
        for line in process.stdout:
            cleaned_line = line.strip()
            if cleaned_line:
                output_logs.append(cleaned_line)
                print(cleaned_line)
            
        process.wait()

        # Búsqueda recursiva de archivos .flac en la carpeta de la tarea y en la base de Orpheus
        download_status[task_id] = {"progress": 80, "status": "Localizando archivo FLAC..."}
        
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
            last_log = output_logs[-1] if output_logs else "Sin detalles de salida"
            raise Exception(f"OrpheusDL no generó el archivo FLAC. Último mensaje: {last_log}")

        final_filename = f"kkbox_lossless_{task_id}.flac"
        final_filepath = os.path.join(DOWNLOAD_FOLDER, final_filename)
        
        # Mover/Renombrar archivo encontrado a la raíz de descargas
        os.rename(flac_file, final_filepath)

        download_status[task_id] = {
            "progress": 100,
            "status": "¡Descarga FLAC completada con éxito!",
            "download_url": f"/get-file/{final_filename}"
        }

    except Exception as e:
        download_status[task_id] = {"progress": 100, "status": f"Error: {str(e)}", "error": True}

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
    download_status[task_id] = {"progress": 5, "status": "Preparando tarea..."}
    
    thread = threading.Thread(target=run_orpheus_download, args=(task_id, url))
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
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/get-file/<filename>')
def get_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True, mimetype='audio/flac')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
