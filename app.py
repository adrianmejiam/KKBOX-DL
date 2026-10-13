import os
import time
import json
import subprocess
import threading
from flask import Flask, render_template, request, Response, send_from_directory, jsonify

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(app.root_path, 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

download_status = {}

@app.route('/')
def index():
    return render_template('index.html')

def run_orpheus_download(task_id, url):
    try:
        download_status[task_id] = {"progress": 15, "status": "Inicializando OrpheusDL para KKBOX..."}
        
        # Directorio de salida temporal para la tarea
        output_dir = os.path.join(DOWNLOAD_FOLDER, task_id)
        os.makedirs(output_dir, exist_ok=True)

        download_status[task_id] = {"progress": 40, "status": "Descargando flujo FLAC Lossless..."}
        
        # Comando para ejecutar orpheusdl apuntando a la URL
        # OrpheusDL utiliza el módulo kkbox instalado previamente desde github
        cmd = ["orpheusdl", "-d", output_dir, url]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            # Puedes depurar o interpretar la salida de orpheusdl si lo requieres
            print(line.strip())
            
        process.wait()

        if process.returncode != 0:
            raise Exception("OrpheusDL finalizó con errores durante la extracción.")

        download_status[task_id] = {"progress": 85, "status": "Empaquetando archivo FLAC..."}
        
        # Buscar el archivo .flac generado dentro de la carpeta de salida
        flac_file = None
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.flac'):
                    flac_file = os.path.join(root, file)
                    break

        if not flac_file:
            raise Exception("No se encontró ningún archivo FLAC generado en la salida.")

        # Mover el archivo a la carpeta principal de descargas con un nombre limpio
        final_filename = f"kkbox_lossless_{task_id}.flac"
        final_filepath = os.path.join(DOWNLOAD_FOLDER, final_filename)
        os.rename(flac_file, final_filepath)

        download_status[task_id] = {
            "progress": 100,
            "status": "¡Descarga FLAC completada con éxito!",
            "download_url": f"/get-file/{final_filename}"
        }

    except Exception as e:
        download_status[task_id] = {"progress": 100, "status": f"Error: {str(e)}", "error": True}

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
