from uuid import UUID

import pytest
from pydantic import ValidationError

from bible_study_ai.api.schemas import ChatRequest, ChatResponse


def test_chat_request_accepts_valid_data():
    conversation_id = UUID("12345678-1234-5678-1234-567812345678")

    request = ChatRequest(
        question="What does John 3:16 mean?",
        conversation_id=str(conversation_id),
    )

    assert request.question == "What does John 3:16 mean?"
    assert request.conversation_id == conversation_id


def test_chat_request_allows_new_conversation():
    request = ChatRequest(question="Explain Psalm 23")

    assert request.conversation_id is None


def test_chat_request_rejects_invalid_uuid():
    with pytest.raises(ValidationError):
        ChatRequest(
            question="Explain Psalm 23",
            conversation_id="not-a-uuid",
        )


def test_chat_response_accepts_valid_data():
    conversation_id = UUID("12345678-1234-5678-1234-567812345678")

    response = ChatResponse(
        conversation_id=conversation_id,
        answer="God's love is expressed through the gift of his Son.",
        sources=["John 3:16"],
    )

    assert response.conversation_id == conversation_id
    assert response.sources == ["John 3:16"]