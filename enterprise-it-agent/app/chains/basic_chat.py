from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import ChatPromptValue
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.prompts.it_support import get_it_support_prompt


def _build_model() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured. Please set it in .env.")

    return ChatOpenAI(
        model=settings.model_name,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def ask(question: str, style: str = "default") -> str:
    prompt = get_it_support_prompt(style=style)
    chain = prompt | _build_model() | StrOutputParser()
    return chain.invoke({"question": question})


def inspect_chain(question: str, style: str = "default") -> dict[str, object]:
    prompt = get_it_support_prompt(style=style)
    model = _build_model()
    parser = StrOutputParser()

    prompt_value: ChatPromptValue = prompt.invoke({"question": question})
    model_response = model.invoke(prompt_value)
    parsed_output = parser.invoke(model_response)

    return {
        "prompt_messages": [
            {"type": message.type, "content": str(message.content)}
            for message in prompt_value.messages
        ],
        "model_response_type": model_response.__class__.__name__,
        "model_response_content": str(model_response.content),
        "parsed_output": parsed_output,
    }
