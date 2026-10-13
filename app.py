from flask import Flask, request, jsonify, render_template_string, send_from_directory
import subprocess
import os
import glob

app = Flask(__name__)

# Directorio donde se guardarán las canciones dentro del contenedor de Render
DOWNLOAD_DIR = os.path.abspath("downloads")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>KKBOX Downloader - Cloud</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 650px; margin: 40px auto; padding: 20px; background: #0f172a; color: #cbd5e1; }
        .card { background: #1e293b; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5); }
        h2 { margin-top: 0; color: #38bdf8; }
        input[type="text"] { width: 100%; padding: 12px; margin: 15px 0; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
        button { background: #0284c7; color: white; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold; font-size: 15px; }
        button:hover { background: #0369a1; }
        button:disabled { background: #475569; cursor: not-allowed; }
        pre { background: #090d16; color: #34d399; padding: 15px; overflow-x: auto; border-radius: 6px; min-height: 120px; font-family: 'Courier New', Courier, monospace; font-size: 13px; }
        .download-zone { margin-top: 20px; padding: 15px; background: #0284c7; border-radius: 6px; text-align: center; display: none; }
        .download-zone a { color: white; text-decoration: none; font-weight: bold; display: block; width: 100%; }
    </style>
</head>
<body>
    <div class="card">
        <h2>KKBOX Cloud Downloader</h2>
        <p>Inserta un enlace válido de KKBOX (canción, álbum o lista de reproducción):</p>
        <input type="text" id="url" placeholder="https://kkbox.fm...">
        <button id="btn-procesar" onclick="iniciarDescarga()">Procesar en Servidor</button>
        
        <h3>Registro del Servidor:</h3>
        <pre id="output">Consola lista. Esperando instrucciones...</pre>
        
        <div id="download-container" class="download-zone">
            <a id="download-link" href="#" target="_blank">📥 DESCARGAR ARCHIVO PROCESADO</a>
        </div>
    </div>

    <script>
        async function iniciarDescarga() {
            const urlInput = document.getElementById('url').value.strip();
            const outputBox = document.getElementById('output');
            const btn = document.getElementById('btn-procesar');
            const dlContainer = document.getElementById('download-container');
            
            if(!urlInput) {
                alert('Por favor, ingresa una URL válida.');
                return;
            }
            
            // Bloquear controles e inicializar estados
            btn.disabled = true;
            btn.innerText = "Procesando...";
            dlContainer.style.display = "none";
            outputBox.innerText = "[INFO] Conectando con OrpheusDL backend...\\n[INFO] Ejecutando decodificación de flujo de audio...\\n";
            
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: urlInput })
                });
                const data = await response.json();
                
                outputBox.innerText += `\\n[LOGS FINALES]:\\n${data.output}`;
                
                if (data.status === "success" && data.file_url) {
                    document.getElementById('download-link').href = data.file_url;
                    dlContainer.style.display = "block";
                    outputBox.innerText += "\\n\\n[ÉXITO] El archivo está listo para descargarse a tu dispositivo.";
                } else {
                    outputBox.innerText += "\\n\\n[ERROR] No se pudo recuperar ningún archivo final. Revisa los logs.";
                }
            } catch (err) {
                outputBox.innerText += `\\n\\n[ERROR CRÍTICO]: No se obtuvo respuesta del servidor backend.`;
            } finally {
                btn.disabled = false;
                btn.innerText = "Procesar en Servidor";
            }
        }
        String.prototype.strip = function() { return this.replace(/^\\s+|\\s+\$/g, ''); };
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({"status": "error", "output": "URL vacía o inválida."}), 400
        
    try:
        # Registrar los archivos actuales antes de ejecutar la descarga
        archivos_antes = set(glob.glob(os.path.join(DOWNLOAD_DIR, '**/*', '*.*'), recursive=True))
        
        # Moverse al directorio del módulo para ejecutarlo adecuadamente
        os.chdir('orpheusdl')
        result = subprocess.run(
            ['python', 'orpheus.py', url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        os.chdir('..') # Volver al directorio raíz de la app
        
        # Escanear los archivos después de la ejecución para detectar el nuevo contenido
        archivos_despues = set(glob.glob(os.path.join(DOWNLOAD_DIR, '**/*', '*.*'), recursive=True))
        nuevos_archivos = archivos_despues - archivos_antes
        
        if nuevos_archivos and result.returncode == 0:
            # Obtener el archivo más reciente generado
            ruta_absoluta_archivo = max(nuevos_archivos, key=os.path.getmtime)
            # Calcular la ruta relativa con respecto a la carpeta "downloads"
            ruta_relativa = os.path.relpath(ruta_absoluta_archivo, DOWNLOAD_DIR)
            
            return jsonify({
                "status": "success",
                "output": result.stdout,
                "file_url": f"/fetch-file/{ruta_relativa}"
            })
        else:
            return jsonify({
                "status": "failed",
                "output": result.stdout + "\n[ALERTA] No se detectaron nuevos archivos guardados en el directorio de salida."
            })
            
    except Exception as e:
        return jsonify({"status": "error", "output": str(e)}), 500

@app.route('/fetch-file/<path:filename>', methods=['GET'])
def fetch_file(filename):
    """Permite al navegador descargar los archivos del directorio interno del servidor"""
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
