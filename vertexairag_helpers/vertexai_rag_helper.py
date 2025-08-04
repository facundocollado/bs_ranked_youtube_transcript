import os
from dotenv import load_dotenv
import vertexai
from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from google.cloud import aiplatform
from google.api_core import operation_async
from vertexai.generative_models import GenerationResponse
from langfuse import Langfuse, observe, get_client


# Cargar variables desde .env
load_dotenv()

class VertexAIRagHelper:
    """
    Helper class for Vertex AI RAG (Retrieval-Augmented Generation) operations.
    This class provides methods to create and manage RAG storage, including
    embedding models and corpus management.
    """

    project_id = os.getenv("PROJECT_ID", "bs-ranked")
    location = os.getenv("VERTEX_REGION", "us-central1")
    embed_model = os.getenv("EMBED_MODEL_NAME", "text-embedding-005")
    model_name = os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-lite")
    temperature = float(os.getenv("VERTEX_TEMPERATURE", "0.0"))
    max_output_tokens = int(os.getenv("VERTEX_MAX_OUTPUT_TOKENS", "256"))

    def __init__(self, project_id: str = None) -> None:
        vertexai.init(project=project_id, location=self.location)
        aiplatform.init(project="bs-ranked")
        
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            environment=os.getenv("LANGFUSE_TRACING_ENVIRONMENT"),
        )

        
    def list_files(self, corpus_name: str) -> list | None:
        """
        List all files in a RAG corpus.

        Args:
            corpus_name (str): The display name of the RAG corpus.

        Returns:
            list: A list of file names in the RAG corpus.
        """
        return rag.list_files(corpus_name=corpus_name)        


    def list_rag_corpora(self) -> list  | None:
        """
        List all RAG corpora in the specified project and location.

        Returns:
            list: A list of RAG corpus names.
        """
        return rag.list_corpora()


    def get_rag_corpus(self, name: str) -> rag.RagCorpus | None:
        """
        Get an existing RAG corpus by name.

        Args:
            name (str): The name of the RAG corpus.

        Returns:
            rag.RagCorpus: The RAG corpus object if found, otherwise None.
        """
        return rag.get_corpus(name=name)
    
    def get_rag_corpus_display_name(self, display_name: str) -> rag.RagCorpus | None:
        """
        Get a RAG corpus by its display name.

        Args:
            display_name (str): The display name of the RAG corpus.

        Returns:
            rag.RagCorpus: The RAG corpus object if found, otherwise None.
        """
        corpora = self.list_rag_corpora()
        for corpus in corpora:
            if corpus.display_name == display_name:
                return self.get_rag_corpus(name=corpus.name)
        return None

    def create_rag_storage_corpus(self, name: str, embed_model: str) -> rag.RagCorpus:
        """
        Create a RAG storage with the specified name and configuration.

        Args:
            name (str): The name of the RAG storage.
            embed_model (str): The embedding model to use for the RAG storage.
        """
        cfg = rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                publisher_model=f"publishers/google/models/{embed_model}"
            )
        )
        return rag.create_corpus(
            display_name=name,
            backend_config=rag.RagVectorDbConfig(
                rag_embedding_model_config=cfg
            )
        )

    async def import_files_async(self, corpus_name: str, gcs_path: str) -> operation_async.AsyncOperation:
        """ Import chunks into a RAG corpus from a GCS path.
        Args:
            corpus_name (str): The display name of the RAG corpus.
            gcs_path (str): The GCS path where the chunks are stored.

        Returns:
            operation_async.AsyncOperation: The import operation is asynchronous, 
            so it returns an AsyncOperation object.
        """
        return await rag.import_files_async(
            corpus_name=corpus_name,
            paths=[gcs_path],
            transformation_config=rag.TransformationConfig(
                rag.ChunkingConfig(chunk_size=0, chunk_overlap=0)
            ),
            max_embedding_requests_per_min=900
        )


    @observe(as_type="generation")
    def query_rag_corpus(self, corpus_display_name: str, query: str) -> GenerationResponse:
        """
        Query the RAG corpus with a text query.

        Args:
            corpus_display_name (str): The display name of the RAG corpus.
            query (str): The text query to search in the RAG corpus.
        
        Returns:
            str: The response from the RAG corpus.
        """

        # Get the RAG corpus by display name
        rag_corpus = self.get_rag_corpus_display_name(corpus_display_name)
        if rag_corpus is None:
            raise ValueError("RAG corpus not found.")
        # Create a RagResource for the corpus
        rag_resource = rag.RagResource(
            rag_corpus=rag_corpus.name,
        )
        # Create a retrieval tool from the RagResource
        rag_retrieval_tool = Tool.from_retrieval(
            retrieval=rag.Retrieval(
                source=rag.VertexRagStore(
                    # Currently only 1 corpus is allowed.
                    rag_resources=[rag_resource],
                ),
            )
        )
        # Create a GenerativeModel with the retrieval tool
        generative_model = GenerativeModel(
            model_name=self.model_name,
            tools=[rag_retrieval_tool]
        )
        # Generate content using the GenerativeModel with the query and retrieval tool
        # The response will include the retrieved context from the RAG corpus
        # and the generated response based on that context.
        response = generative_model.generate_content(
            query,
            tools=[rag_retrieval_tool],
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens
            }
        )

        self.langfuse.flush()

        return response