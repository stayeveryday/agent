from langchain_core.prompts import ChatPromptTemplate


def get_it_support_prompt(style: str = "default") -> ChatPromptTemplate:
    system_prompts = {
        "default": (
            "You are an enterprise IT service desk assistant. "
            "Reply in the user's language. Keep answers clear, concise, and actionable."
        ),
        "brief": (
            "You are an enterprise IT service desk assistant. "
            "Reply in the user's language. Keep answers short, practical, and direct."
        ),
        "guided": (
            "You are an enterprise IT service desk assistant. "
            "Reply in the user's language. Ask at most one clarifying question if needed, "
            "then provide step-by-step guidance."
        ),
    }

    system_prompt = system_prompts.get(style, system_prompts["default"])

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{question}"),
        ]
    )
