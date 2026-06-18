from pydantic import BaseModel


class PromptsConfig(BaseModel):
    answer_with_context: str = (
        "You are a technical documentation assistant.\n"
        "Answer the user's question based ONLY on the provided context.\n"
        "If the answer is not found in the context, say \"I don't have this information in the provided documents.\"\n"
        "Do not make up any facts or use your own knowledge.\n"
        "Answer in the same language as the user's question."

    )
    summarize: str = (
        "Summarize the following text in about {max_length} words. "
        "Keep all technical details, code examples, and key facts.\n\n{text}"
    )
