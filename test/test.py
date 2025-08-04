import os
import pytest
from process_video import ProcessVideo as pv
from llm_helpers.llm_helper import LlmHelper
from llm_helpers.brawlers_data import get_brawlers_list
import json
from youtube_helpers.youtube_helper import YouTubeHelper as yt
from vertexairag_helpers.vertexai_rag_helper import VertexAIRagHelper, rag
from gcs_helpers.gcs_helper import GCSHelper
import utils
import asyncio

@pytest.fixture(scope="module")
def video_url():
    return "https://www.youtube.com/watch?v=4H9i-VC1adM"

@pytest.fixture(scope="module")
def youtube_helper(video_url: str):
    return yt(video_url)

# pytest test/test.py -k test_extract_video_title
def test_extract_video_title(youtube_helper: yt):
    """ Test to extract video title from YouTube URL. """
    title = youtube_helper.get_title()
    assert title == "Jae_Yong_Ranks_ALL_93_Brawlers_From_Worst_To_Best_Tier_List_YouTube"

# pytest test/test.py -k test_extract_video_publish_date
def test_extract_video_publish_date(youtube_helper: yt):
    """ Test to extract video publish date from YouTube URL. """
    publish_date = youtube_helper.get_publish_date()
    assert publish_date == "2025-07-10"

# pytest test/test.py -k test_transcribe_video_and_save
def test_transcribe_video_and_save(youtube_helper: yt):
    result = youtube_helper.get_transcript()
    transcript_text, segments = result

    # Verifica que el resultado sea una tupla con tres elementos
    assert isinstance(result, tuple)
    assert len(result) == 2
    # Verifica los tipos de cada elemento
    assert isinstance(transcript_text, str)
    assert isinstance(segments, list)

    # Guarda el texto en un archivo para otros tests
    os.makedirs("test", exist_ok=True)
    with open("test/transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)


@pytest.fixture(scope="module")
def transcribed_video():
    # Lee el transcript guardado por el test anterior
    with open("test/transcript.txt", "r", encoding="utf-8") as f:
        transcript_text = f.read()
    # Simula la tupla (id, texto, segmentos) si solo necesitas el texto
    return ("dummy_id", transcript_text, [])

@pytest.fixture(scope="module")
def llm_helper():
    return LlmHelper()

# pytest test/test.py -k test_llm_response
def test_llm_response(transcribed_video: tuple, llm_helper: LlmHelper):
    prompt = llm_helper.load_prompt_template(
        prompt_name="YOUTUBE_VIDEO_BRIEF",
        transcript=transcribed_video[1],
        brawlers_list=get_brawlers_list()
    )
    llm_response, cb = llm_helper.run(prompt)
    filtered_response = utils.filter_brawlers(llm_response)

    # Guardar el resultado filtrado
    with open("test/llm_response.txt", "w", encoding="utf-8") as f:
        import json
        json.dump(filtered_response, f, indent=4)
    
    # Guarda métricas de uso en un archivo de log
    with open("test/llm_usage_metrics.log", "a", encoding="utf-8") as logf:
        logf.write(
            f"Prompt tokens: {cb.prompt_tokens}, "
            f"Completion tokens: {cb.completion_tokens}, "
            f"Total tokens: {cb.total_tokens}, "
            f"Cost: ${cb.total_cost:.6f}\n"
        )

    assert isinstance(llm_response, dict)
    assert len(filtered_response["brawlers_mentioned"]) <= len(llm_response["brawlers_mentioned"])

@pytest.fixture(scope="module")
def embed_model():
    return os.getenv("EMBED_MODEL_NAME", "text-embedding-005")

@pytest.fixture(scope="module")
def project_id():
    return os.getenv("PROJECT_ID", "bs-ranked")

@pytest.fixture(scope="module")
def bucket_id(project_id):
    return f"{project_id}-bucket"

@pytest.fixture(scope="module")
def corpus_display_name():
    return os.getenv("CORPUS_DISPLAY_NAME", "test_corpus")

@pytest.fixture(scope="module")
def vertexairag_helpers(project_id):
    # Initialize the VertexAIRagHelper
    return VertexAIRagHelper(project_id)

@pytest.fixture(scope="module")
def rag_vector_db():
    # Define the RAG retrieval strategy
    return rag.RagManagedDb()

# pytest test/test.py -k test_create_rag_storage_corpus
def test_create_rag_storage_corpus(vertexairag_helpers: VertexAIRagHelper, embed_model: str, corpus_display_name: str):
    """ Test to create a RAG storage if it does not exist. """
     
    new_corpus = vertexairag_helpers.create_rag_storage_corpus(
        name=corpus_display_name,
        embed_model=embed_model
    )

    assert new_corpus is not None, "Failed to create RAG storage corpus."
    assert isinstance(new_corpus, rag.RagCorpus)

# pytest test/test.py -k test_rag_get_corpus
def test_rag_get_corpus(
        vertexairag_helpers: VertexAIRagHelper,
        corpus_display_name: str):
    """ Test to get or create a RAG corpus. """
    # Try to get an existing RAG corpus
    rag_corpus = vertexairag_helpers.get_rag_corpus_display_name(corpus_display_name)
    assert rag_corpus is not None, "Failed to retrieve existing RAG corpus."
    assert isinstance(rag_corpus, rag.RagCorpus)

@pytest.fixture(scope="module")
def gcs_helper():
    """ Fixture to initialize GCSHelper. """
    return GCSHelper()

# pytest test/test.py -k test_get_or_create_corpus
def test_get_or_create_corpus(gcs_helper: GCSHelper):
    """ Test to get or create a GCS bucket. """
    assert gcs_helper.bucket is not None, "Failed to get or create GCS bucket."

# pytest test/test.py -k test_process_video_dict
def test_process_video_dict(
        video_url: str,
        corpus_display_name: str,
        youtube_helper: yt,
        vertexairag_helpers: VertexAIRagHelper,
        gcs_helper: GCSHelper
):
    """ Test end-to-end processing of a video URL. """
    video_id = youtube_helper.extract_video_id(video_url)
    title = youtube_helper.get_title()
    publish_date = youtube_helper.get_publish_date()
    corpus_name = f"{video_id}_{title}"

    # Leer dict con datos del video
    with open("test/llm_response.txt", "r", encoding="utf-8") as f:
        raw = f.read()
    d = json.loads(raw)
    
    chunks = utils.process_video_dict(d, file_id=corpus_name, publish_date=publish_date)

    # Guardar local JSONL (sin embeddings, se generan en el corpus)
    fname = "test/upload_chunks.jsonl"
    utils.save_chunks_to_jsonl(chunks, file_name=fname)
    
    # Subir a GCS
    gcs_path = gcs_helper.upload_file(fname, f"rag_upload/{fname}")

    corpus = vertexairag_helpers.get_rag_corpus_display_name(corpus_display_name)
    # Importar al corpus (async)
    asyncio.run(vertexairag_helpers.import_files_async(
        corpus_name=corpus.name,
        gcs_path=gcs_path
    ))

    # Check the files just imported. It may take a few seconds to process the imported files.
    assert list(vertexairag_helpers.list_files(corpus_name=corpus.name)) != [], "No files found in the RAG corpus after import."


def test_query_rag_corpus(
        vertexairag_helpers: VertexAIRagHelper,
        corpus_display_name: str,
):
    """ Query the RAG corpus with a text query. """
    
    response = vertexairag_helpers.query_rag_corpus(
        corpus_display_name=corpus_display_name,
        query="Is Grom strong in the current meta?"
    )

    assert isinstance(response.text, str), "Response from RAG corpus should be a string."
    assert len(response.text) > 0, "Response from RAG corpus should not be empty."



# RagManagedDb 



# TODO (facundo): Configuración de pipeline optimizada para batching de múltiples videos o manejo incremental