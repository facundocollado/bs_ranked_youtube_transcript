import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from llm_helpers import prompts
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.callbacks.manager import OpenAICallbackHandler
from .schemas import TranscriptAnalysisResult
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class LlmHelper:
    def __init__(self):
        # Carga la API key y parámetros desde .env
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "512"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

        if not self.api_key:
            raise ValueError("Falta la variable OPENAI_API_KEY en .env")

        # Inicializa el cliente de langchain
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
        )

        # Configura el LLM para usar salida estructurada
        # Esto permite que el LLM devuelva un objeto TranscriptAnalysisResult en lugar de un string
        self.structured_llm = self.llm.with_structured_output(TranscriptAnalysisResult)


    def load_prompt_template(self, prompt_name: str, **kwargs) -> PromptTemplate:
        """
        Loads a prompt template by variable name from prompts.py.
    
        - Scans for all placeholders inside `{}`.
        - Builds a PromptTemplate dynamically.
        - If kwargs are provided, fills the placeholders.
        
        Example:
        _load_prompt("YOUTUBE_VIDEO_BRIEF", transcript="...", title="...")

        """
        if not hasattr(prompts, prompt_name):
            raise ValueError(f"Prompt variable '{prompt_name}' not found in prompts folder")

        template_str = getattr(prompts, prompt_name)

        chat_prompt_template = ChatPromptTemplate.from_messages([
            ("system", template_str)
        ])

        # Si pasan kwargs, valida y embebe con partial()
        if kwargs:
            # Detect placeholders inside the template (anything inside { })
            placeholders = [v.strip() for v in re.findall(r"{(.*?)}", template_str)]
            missing = [v for v in placeholders if v not in kwargs]
            if missing:
                raise ValueError(f"Missing placeholders: {missing}")
            chat_prompt_template = chat_prompt_template.partial(**kwargs)

        return chat_prompt_template.format_messages()


    def run(self, prompt: str) -> tuple[str, OpenAICallbackHandler]:
        """
        Ejecuta el prompt con nombre 'prompt_name', llenando placeholders
        con los kwargs enviados. Devuelve la respuesta de OpenAI.
        """

        with get_openai_callback() as cb:
            llmn_response = self.structured_llm.invoke(prompt)
        return llmn_response, cb

