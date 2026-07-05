from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings


def build_chat_model() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured. Please set it in .env.")

    return ChatOpenAI(
        model=settings.model_name,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def ask_model(question: str) -> str:
    model = build_chat_model()
    response = model.invoke(
        [
            SystemMessage(
                content=(
                    "You are an enterprise IT service desk assistant. "
                    "Reply in the user's language. Keep answers clear and concise."
                )
            ),
            HumanMessage(content=question),
        ]
    )
    return response.content
