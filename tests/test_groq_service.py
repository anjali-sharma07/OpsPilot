from app.services.groq_service import GroqService


def test_build_messages_contains_context_and_history() -> None:
    service = GroqService(api_key="test-key")
    messages = service.build_messages(
        user_question="What is the policy?",
        retrieved_context=[{"chunk": "Policy details"}],
        conversation_history=[{"user": "Hello", "assistant": "Hi"}],
    )

    assert messages[0]["role"] == "system"
    assert "Answer ONLY using the provided context" in messages[0]["content"]
    assert "Policy details" in messages[1]["content"]
    assert "Hello" in messages[1]["content"]


def test_groq_service_can_be_initialized_without_api_key() -> None:
    service = GroqService(api_key=None)

    assert service.api_key is None
    assert service.client is None
