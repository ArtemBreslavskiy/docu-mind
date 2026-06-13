import ollama
from src.core.models.base import BaseLLMModel
from src.config.schemas.app import ModelConfig
from src.core.schemas import Chunk


class OllamaModel(BaseLLMModel):
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = ollama.Client(host=config.base_url)

    def generate(self, question: str, context_chunks: list[Chunk]) -> str:
        context = "\n\n---\n\n".join([chunk.content for chunk in context_chunks])
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer: "

        response = self.client.chat(
            model=self.config.name,
            messages=[
                {"role": "system", "content": self.config.prompts.generate},
                {"role": "user", "content": user_prompt}
            ],
            options={
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        )
        return response["message"]["content"].strip()

    def summarize(self, text: str, max_length: int = 200) -> str:
        prompt = self.config.prompts.summarize.format(max_length=max_length, text=text)
        response = self.client.chat(
            model=self.config.name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        )
        return response["message"]["content"].strip()
