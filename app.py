from flask import Flask, request, jsonify, render_template_string, send_from_directory
import subprocess
import os
import glob
import zipfile

app = Flask(__name__)

# Directorio absoluto donde se guardarán las canciones dentro del contenedor de Render
DOWNLOAD_DIR = os.path.abspath("downloads")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KKBOX Cloud Downloader</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 650px; margin: 40px auto; padding: 20px; background: #0f172a; color: #cbd5e1; }
        .card { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); position: relative; padding-bottom: 60px; }
        h2 { margin-top: 0; color: #38bdf8; text-align: center; }
        
        /* Opciones de tipo de descarga */
        .options-container { display: flex; justify-content: space-between; margin: 20px 0 10px 0; gap: 10px; }
        .option-box { flex: 1; text-align: center; padding: 12px; background: #1e293b; border: 2px solid #475569; border-radius: 8px; cursor: pointer; transition: all 0.3s ease; }
        .option-box:hover { border-color: #38bdf8; background: #1e293b; }
        .option-box.active { border-color: #38bdf8; background: #0369a1; color: white; font-weight: bold; }
        
        input[type="text"] { width: 100%; padding: 12px; margin: 15px 0; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 14px; }
        button { background: #0284c7; color: white; padding: 14px 20px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px; transition: background 0.2s; }
        button:hover { background: #0369a1; }
        button:disabled { background: #475569; cursor: not-allowed; }
        
        pre { background: #090d16; color: #34d399; padding: 15px; overflow-x: auto; border-radius: 6px; min-height: 120px; font-family: 'Courier New', Courier, monospace; font-size: 13px; margin-top: 20px; }
        .download-zone { margin-top: 20px; padding: 15px; background: #10b981; border-radius: 6px; text-align: center; display: none; animation: fadeIn 0.5s ease; }
        .download-zone a { color: white; text-decoration: none; font-weight: bold; display: block; width: 100%; font-size: 15px; }
        
        /* Crédito del desarrollador */
        .footer { position: absolute; bottom: 15px; right: 30px; font-size: 12px; color: #64748b; font-style: italic; }
        .footer span { color: #38bdf8; font-weight: bold; font-style: normal; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="card">
        <h2>KKBOX Cloud Downloader</h2>
        <p style="text-align: center; margin-bottom: 5px;">Selecciona el tipo de contenido que deseas procesar:</p>
        
        <div class="options-container">
            <div id="opt-track" class="option-box active" onclick="selectOption('track')">🎵 Canción Individual</div>
            <div id="opt-album" class="option-box" onclick="selectOption('album')">💿 Álbum Completo</div>
            <div id="opt-playlist" class="option-box" onclick="selectOption('playlist')">📝 Playlist</div>
        </div>

        <input type="text" id="url" placeholder="Pega el enlace de KKBOX aquí...">
        <button id="btn-procesar" onclick="iniciarDescarga()">Procesar en Servidor</button>
        
        <h3>Registro del Servidor:</h3>
        <pre id="output">Consola lista. Selecciona una opción, introduce la URL y presiona Procesar...</pre>
        
        <div id="download-container" class="download-zone">
            <a id="download-link" href="#" target="_blank">📥 DESCARGAR ARCHIVO PROCESADO (.ZIP / MP3 / FLAC)</a>
        </div>

        <div class="footer">Desarrollado por: <span>adrianmejiam</span></div>
    </div>

    <script>
        let tipoSeleccionado = 'track';

        function selectOption(tipo) {
            tipoSeleccionado = tipo;
            document.querySelectorAll('.option-box').forEach(el => el.classList.remove('active'));
            if(tipo === 'track') document.getElementById('opt-track').classList.add('active');
            if(tipo === 'album') document.getElementById('opt-album').classList.add('active');
            if(tipo === 'playlist') document.getElementById('opt-playlist').classList.add('active');
        }

        async function iniciarDescarga() {
            const urlInput = document.getElementById('url').value.trim();
            const outputBox = document.getElementById('output');
            const btn = document.getElementById('btn-procesar');
            const dlContainer = document.getElementById('download-container');
            
            if(!urlInput) {
                alert('Por favor, ingresa una URL válida de KKBOX.');
                return;
            }
            
            btn.disabled = true;
            btn.innerText = "Procesando...";
            dlContainer.style.display = "none";
            outputBox.innerText = `[INFO] Modo de descarga: \${tipoSeleccionado.toUpperCase()}\\n[INFO] Conectando con OrpheusDL backend...\\n[INFO] Descargando flujos multimedia directamente de KKBOX...\\n`;
            
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: urlInput, mode: tipoSeleccionado })
                });
                const data = await response.json();
                
                outputBox.innerText += `\\n[LOGS FINALES]:\\n\${data.output}`;
                
                if (data.status === "success" && data.file_url) {
                    document.getElementById('download-link').href = data.file_url;
                    dlContainer.style.display = "block";
                    outputBox.innerText += "\\n\\n[ÉXITO] Tu descarga está empaquetada y lista para guardarse en tu dispositivo.";
                } else {
                    outputBox.innerText += "\\n\\n[ERROR] No se pudo recuperar ningún archivo multimedia final.";
                }
            } catch (err) {
                outputBox.innerText += `\\n\\n[ERROR CRÍTICO]: Pérdida de comunicación con el backend de Render.`;
            } finally {
                btn.disabled = false;
                btn.innerText = "Procesar en Servidor";
            }
        }
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
    mode = data.get('mode', 'track')
    
    if not url:
        return jsonify({"status": "error", "output": "URL no válida."}), 400
        
    try:
        # 1. Registrar el estado del directorio antes de la descarga
        archivos_antes = set(glob.glob(os.path.join(DOWNLOAD_DIR, '**/*', '*.*'), recursive=True))
        
        # 2. Entrar a la raíz de orpheusdl y ejecutar el binario CLI
        os.chdir('orpheusdl')
        result = subprocess.run(
            ['python', 'orpheus.py', url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        os.chdir('..') # Volver a la raíz principal
        
        # 3. Detectar qué archivos nuevos se generaron
        archivos_despues = set(glob.glob(os.path.join(DOWNLOAD_DIR, '**/*', '*.*'), recursive=True))
        nuevos_archivos = list(archivos_despues - archivos_antes)
        
        if nuevos_archivos and result.returncode == 0:
            # Si el usuario bajó un álbum o playlist y hay múltiples archivos, creamos un archivo comprimido .ZIP
            if len(nuevos_archivos) > 1 or mode in ['album', 'playlist']:
                ruta_zip = os.path.join(DOWNLOAD_DIR, "pack_descarga_kkbox.zip")
                
                # Eliminar ZIP viejo si existe
                if os.path.exists(ruta_zip):
                    os.remove(ruta_zip)
                    
                with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for archivo in nuevos_archivos:
                        # Evitar meter el propio archivo ZIP dentro del ZIP
                        if archivo != ruta_zip:
                            zipf.write(archivo, os.path.basename(archivo))
                            
                return jsonify({
                    "status": "success",
                    "output": result.stdout + f"\n\n[PROCESO] Se empaquetaron {len(nuevos_archivos)} pistas en un archivo único .ZIP",
                    "file_url": "/fetch-file/pack_descarga_kkbox.zip"
                })
            else:
                # Si es una sola pista, se entrega el archivo multimedia directamente
                ruta_absoluta = max(nuevos_archivos, key=os.path.getmtime)
                ruta_relativa = os.path.relpath(ruta_absoluta, DOWNLOAD_DIR)
                return jsonify({
                    "status": "success",
                    "output": result.stdout,
                    "file_url": f"/fetch-file/{ruta_relativa}"
                })
        else:
            return jsonify({
                "status": "failed",
                "output": result.stdout + "\n[ALERTA] El proceso terminó pero no se guardó ningún archivo nuevo en el disco."
            })
            
    except Exception as e:
        return jsonify({"status": "error", "output": str(e)}), 500

@app.route('/fetch-file/<path:filename>', methods=['GET'])
def fetch_file(filename):
    """Permite la descarga directa de archivos binarios al navegador"""
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

