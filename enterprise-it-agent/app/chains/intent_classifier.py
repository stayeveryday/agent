from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.chains.chat_model import build_chat_model
from app.schemas.intent import IntentResult


parser = PydanticOutputParser(pydantic_object=IntentResult)


intent_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an intent classifier for an enterprise IT service desk. "
            "Classify the user's request into exactly one intent. "
            "Use knowledge_question for troubleshooting or knowledge requests. "
            "Use ticket_query for checking ticket status or progress. "
            "Use ticket_create for creating a new ticket, incident, or support request. "
            "Use asset_query for device, account, or asset lookup requests. "
            "Use smalltalk for greetings, thanks, or casual conversation. "
            "Return valid JSON only. "
            "{format_instructions}",
        ),
        ("user", "{question}"),
    ]
)


def classify_intent(question: str) -> IntentResult:
    model = build_chat_model()
    chain = intent_prompt | model | parser
    return chain.invoke(
        {
            "question": question,
            "format_instructions": parser.get_format_instructions(),
        }
    )
