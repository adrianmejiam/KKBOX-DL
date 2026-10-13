from flask import Flask, request, jsonify, render_template_string
import subprocess
import os

app = Flask(__name__)

# Interfaz web HTML minimalista incorporada
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>KKBOX Downloader - Cloud</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; background: #f4f4f9; }
        input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; width: 100%; }
        pre { background: #222; color: #fff; padding: 15px; overflow-x: auto; border-radius: 5px; min-height: 100px; }
    </style>
</head>
<body>
    <h2>Descargador de KKBOX en la Nube</h2>
    <p>Introduce el enlace de la canción o álbum:</p>
    <input type="text" id="url" placeholder="https://kkbox.fm...">
    <button onclick="enviarDescarga()">Procesar Descarga</button>
    <h3>Consola del Servidor:</h3>
    <pre id="output">Esperando acciones...</pre>

    <script>
        async function enviarDescarga() {
            const urlInput = document.getElementById('url').value;
            const outputBox = document.getElementById('output');
            if(!urlInput) return alert('Por favor ingresa una URL');
            
            outputBox.innerText = "Ejecutando proceso de descarga en el servidor Render...\\n";
            
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: urlInput })
                });
                const data = await response.json();
                outputBox.innerText += `\\n[LOGS DEL SERVIDOR]:\\n${data.output}`;
            } catch (err) {
                outputBox.innerText += `\\n[ERROR]: No se pudo conectar con el backend.`;
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
    
    if not url:
        return jsonify({"status": "error", "output": "URL no válida"}), 400
        
    # Cambiar al directorio donde está instalado orpheusdl para ejecutarlo
    try:
        os.chdir('orpheusdl')
        # Ejecutar el script original simulando la consola
        result = subprocess.run(
            ['python', 'orpheus.py', url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        os.chdir('..') # Regresar a la raíz
        
        return jsonify({
            "status": "success" if result.returncode == 0 else "failed",
            "output": result.stdout
        })
    except Exception as e:
        return jsonify({"status": "error", "output": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
  
