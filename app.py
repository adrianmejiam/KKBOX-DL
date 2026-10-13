import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_music():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "No se proporcionó ninguna URL de KKBOX"}), 400

    try:
        # Aquí puedes integrar la lógica o llamada al script de KKBOX-DL
        # Ejemplo simulado de procesamiento:
        # os.system(f"python3 main.py {url}")
        
        return jsonify({
            "success": True, 
            "message": f"Proceso iniciado correctamente para la URL: {url}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
