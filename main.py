import os
from dotenv import load_dotenv

# Cargar variables de entorno antes que nada
load_dotenv()

from flask import Flask, request, jsonify
from process_video import ProcessVideo

app = Flask(__name__)
video_processor = ProcessVideo()  # Inyección de dependencia

@app.route("/process", methods=["POST"])
def process_video_route():
    data = request.get_json(silent=True)
    if not data or "url" not in data:
        return jsonify({"error": "Debes enviar un JSON con {\"url\": \"<video_url>\"}"}), 400

    url = data["url"]

    try:
        result = video_processor.process(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8080))
    mode = "VERTEX AI" if video_processor.use_vertex else "LOCAL"
    print(f"🚀 Iniciando servicio en modo {mode} en puerto {port}")
    app.run(host="0.0.0.0", port=port)
