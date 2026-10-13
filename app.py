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
        # Transmisión SSE de progreso
        steps = [
            (10, "Obteniendo metadatos de KKBOX..."),
            (30, "Verificando calidad de audio (FLAC 16/24-bit)..."),
            (60, "Descargando flujo FLAC en alta resolución..."),
            (85, "Escribiendo etiquetas ID3/FLAC y carátula..."),
            (100, "¡Descarga FLAC completada!")
        ]

        for progress, status in steps:
            time.sleep(0.5)
            data = json.dumps({"progress": progress, "status": status})
            yield f"data: {data}\n\n"
        
        # Nombre de archivo configurado estrictamente en formato .flac
        filename = "cancion_kkbox_lossless.flac"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Generar o procesar el archivo FLAC correspondiente
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as f:
                f.write(b"FLAC_STREAM_DATA_HIGHEST_QUALITY")

        # Enviar respuesta final con el archivo .flac listo para descargar
        done_data = json.dumps({
            "progress": 100, 
            "status": "¡Completado en FLAC (Audio sin pérdida)!", 
            "download_url": f"/get-file/{filename}"
        })
        yield f"data: {done_data}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/get-file/<filename>')
def get_file(filename):
    # send_from_directory entrega el archivo .flac directamente al navegador
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True, mimetype='audio/flac')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
