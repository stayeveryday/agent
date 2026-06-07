from enterprise_rag_agent.agent import build_agent
from enterprise_rag_agent.config import AgentSettings


def main() -> None:
    settings = AgentSettings()
    agent = build_agent(settings)

    session_id = "demo-session"
    print("Enterprise RAG Agent 已启动，输入 quit 退出。")

    while True:
        query = input("\nUser> ").strip()
        if not query or query.lower() in {"quit", "exit"}:
            break

        result = agent.invoke(
            {
                "session_id": session_id,
                "user_query": query,
            }
        )
        print(f"\nAssistant> {result['final_answer']}")
        print(f"Intent: {result['intent']}")
        print(f"Reflection: {result['reflection']['confidence']} / {result['reflection']['needs_follow_up']}")


if __name__ == "__main__":
    main()

