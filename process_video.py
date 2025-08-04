import os
from dotenv import load_dotenv
from google.cloud import aiplatform
from youtube_helpers.youtube_helper import YouTubeHelper as yt
import utils

# Cargar variables desde .env
load_dotenv()

# Solo importamos Vertex AI si se habilita
USE_VERTEX = os.getenv("USE_VERTEX", "false").lower() == "true"
if USE_VERTEX:
    import vertexai
    from vertexai import rag
    from vertexai.generative_models import GenerativeModel

    vertexai.init(
        project=os.getenv("PROJECT_ID"),
        location=os.getenv("VERTEX_REGION", "us-central1")
    )

creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if creds_path and os.path.exists(creds_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
    print(f"✅ Usando credenciales: {creds_path}")
else:
    print("⚠️ No se encontró GOOGLE_APPLICATION_CREDENTIALS o el archivo no existe")



class ProcessVideo:
    """
    Clase que encapsula toda la lógica de:
    - Extracción de video_id
    - Transcripción del video
    - Procesamiento opcional con Vertex AI (resumen + RAG)
    """

    def __init__(self):
        self.use_vertex = USE_VERTEX
        self.vertex_region = os.getenv("VERTEX_REGION", "us-central1")
        self.project_id = os.getenv("PROJECT_ID")

        # Solo inicializamos RAG si está activo
        self.corpus = None
        if self.use_vertex:
            self.corpus = self._get_or_create_corpus("youtube_videos")

    # --- SRP 1: Obtener video_id y transcripción ---
    def transcribe_video(self, url: str):
        yt_helper = yt(url)
        vid = yt_helper.extract_video_id()
        text, segments = yt_helper.get_transcript()
        return vid, text, segments

    # --- SRP 2: Resumir texto usando Gemini ---
    def summarize_text(self, text: str, max_tokens: int = 2000) -> str:
        if not self.use_vertex:
            return None
        model = GenerativeModel(model_name=os.getenv("VERTEX_MODEL_NAME", "gemini-1.5-flash-002"))
        response = model.generate_content(
            f"Resume este texto de un video de YouTube en español:\n\n{text[:max_tokens]}"
        )
        return response.text

    # --- SRP 3: Guardar texto e indexar en RAG ---
    def index_in_rag(self, vid: str, text: str):
        if not self.use_vertex:
            return None

        # Guardamos temporalmente
        fname = f"/tmp/{vid}.txt"
        with open(fname, "w") as f:
            f.write(text)

        # Importamos en RAG Engine
        rag.import_files(
            self.corpus.name,
            [fname],
            transformation_config=rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(
                    chunk_size=512,
                    chunk_overlap=100
                )
            )
        )
        return True

    # --- Método público para procesar todo ---
    def process(self, url: str):
        """
        Procesa un video de YouTube:
        - Obtiene transcripción
        - Opcionalmente resume e indexa en RAG
        """
        vid, text, segments = self.transcribe_video(url)

        # Si solo queremos test local
        if not self.use_vertex:
            return {
                "video_id": vid,
                "mode": "local",
                "transcript_preview": text[:500] + ("..." if len(text) > 500 else ""),
                "segments_count": len(segments)
            }

        # Modo Vertex: resumen + RAG
        summary = self.summarize_text(text)
        self.index_in_rag(vid, text)

        return {
            "video_id": vid,
            "mode": "vertex",
            "summary": summary,
            "segments_count": len(segments)
        }

    # --- Helpers privados ---
    def _get_or_create_corpus(self, name: str):
        EMBED_MODEL = os.getenv("EMBED_MODEL_NAME", "text-embedding-005")
        try:
            return rag.get_corpus(name=name)
        except:
            cfg = rag.RagEmbeddingModelConfig(
                vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                    publisher_model="publishers/google/models/{EMBED_MODEL}"
                )
            )
            return rag.create_corpus(
                display_name=name,
                backend_config=rag.RagVectorDbConfig(
                    rag_embedding_model_config=cfg
                )
            )
