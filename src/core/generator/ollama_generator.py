import ollama
from src.core.generator.base import BaseGenerator
from src.config.schemas.app import LLMConfig
from src.core.schemas import Chunk


class OllamaGenerator(BaseGenerator):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = ollama.Client(host=config.base_url)

    def generate(self, question: str, context_chunks: list[Chunk]) -> str:
        context = "\n\n---\n\n".join([chunk.content for chunk in context_chunks])
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer: "

        response = self.client.chat(
            model=self.config.model,
            messages=[
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            options={
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        )
        return response["message"]["content"].strip()
