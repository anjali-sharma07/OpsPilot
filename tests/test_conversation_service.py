from app.services.conversation_service import ConversationService


def test_conversation_service_persists_and_reads_history(tmp_path) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database.database import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    service = ConversationService(session_factory=SessionLocal)
    service.save_message("session-1", "Hello", "Hi there")

    history = service.get_history("session-1")

    assert history[0]["user"] == "Hello"
    assert history[0]["assistant"] == "Hi there"


def test_conversation_service_limits_recent_history(tmp_path) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database.database import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    service = ConversationService(session_factory=SessionLocal, max_history_turns=2)
    for index in range(3):
        service.save_message("session-2", f"Question {index}", f"Answer {index}")

    history = service.get_history("session-2")

    assert len(history) == 2
    assert history[0]["user"] == "Question 1"
    assert history[-1]["user"] == "Question 2"
