from flask import Flask, request, jsonify
import os
import vertexai
from vertexai import rag
from shared.utils import extract_video_id, get_transcript
from vertexai.generative_models import GenerativeModel, Tool

app = Flask(__name__)
vertexai.init(project=os.getenv("PROJECT_ID"), location="us-central1")

# 1. Crear o recuperar corpus
EMBED_MODEL = "publishers/google/models/text-embedding-005"
def get_or_create_corpus(name):
    try:
        return rag.get_corpus(name=name)
    except:
        cfg = rag.RagEmbeddingModelConfig(vertex_prediction_endpoint=rag.VertexPredictionEndpoint(publisher_model=EMBED_MODEL))
        return rag.create_corpus(display_name=name, backend_config=rag.RagVectorDbConfig(rag_embedding_model_config=cfg))

corpus = get_or_create_corpus("youtube_videos")

@app.route("/process", methods=["POST"])
def process():
    url = request.json.get("url")
    vid = extract_video_id(url)
    text, segments = get_transcript(vid)

    # 2. Resumir con LLM
    model = GenerativeModel(model_name="gemini-2.0-flash-001")
    summary = model.generate_content(f"Resume esto:\n\n{text[:2000]}").text

    # 3. Guardar texto y metadata en un archivo JSONL
    fname = f"/tmp/{vid}.txt"
    with open(fname, "w") as f:
        f.write(text)

    rag.import_files(
        corpus.name,
        [fname],
        transformation_config=rag.TransformationConfig(chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100))
    )

    return jsonify({"video_id": vid, "summary": summary})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
