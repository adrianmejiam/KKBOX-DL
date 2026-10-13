import os
import time
import json
from flask import Flask, render_template, request, Response, send_from_directory, jsonify

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(app.root_path, 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream-download')
def stream_download():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No se proporcionó ninguna URL"}), 400

    def generate():
        # Simulación de progreso de descarga (reemplazar/integrar con la lógica del backend de KKBOX)
        for progress in range(0, 101, 10):
            time.sleep(0.4) # Simula el tiempo de descarga
            data = json.dumps({"progress": progress, "status": f"Descargando... {progress}%"})
            yield f"data: {data}\n\n"
        
        # Nombre de archivo simulado para la descarga final
        filename = "cancion_kkbox.mp3"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Asegurar archivo de prueba si no se ha generado uno real
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write("Contenido multimedia simulado de KKBOX")

        # Notificar finalización y enviar nombre del archivo listo
        done_data = json.dumps({"progress": 100, "status": "¡Completado!", "download_url": f"/get-file/{filename}"})
        yield f"data: {done_data}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/get-file/<filename>')
def get_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
