from unittest.mock import Mock

import pytest
from pydantic_ai.messages import ModelRequest, ToolReturnPart
from pydantic_ai.models.test import TestModel
from pydantic_ai.usage import UsageLimits

from customer_support.agent import build_agent, build_model
from customer_support.config import LLMSettings
from customer_support.knowledge import Chunk


def test_local_model(llm_settings: LLMSettings) -> None:
    """Build the configured local model without a provider request."""
    model = build_model(llm_settings)
    assert not isinstance(model, str), (
        "Local models need an explicit provider URL."
    )
    assert model.model_name == llm_settings.model, (
        "Use the configured local model."
    )
    assert str(llm_settings.port) in str(model.base_url), (
        "Use the configured Ollama port."
    )


def test_hosted_model(
    hosted_settings: LLMSettings,
    inferred_model: Mock,
    test_model: TestModel,
) -> None:
    """Return the resolved hosted Model rather than its name."""
    model = build_model(hosted_settings)
    inferred_model.assert_called_once_with(
        f"{hosted_settings.provider}:{hosted_settings.model}"
    )
    assert model is test_model, (
        "Return the Model instance produced by infer_model."
    )


async def test_tool_returns_traceable_chunks(
    llm_settings: LLMSettings,
    search_stub: Mock,
    test_model: TestModel,
    retrieved_chunks: list[Chunk],
    reply_text: str,
    retrieval_query: str,
) -> None:
    """Run a real tool with an offline model and inspect its messages."""
    agent = build_agent(llm_settings)
    with agent.override(model=test_model):
        result = await agent.run(
            retrieval_query, deps=search_stub
        )
    assert result.output == reply_text, (
        "Return the model answer unchanged."
    )
    assert (
        search_stub.search.call_args.kwargs["limit"]
        == llm_settings.retrieval_limit
    ), "Retrieval must respect settings."
    returns = [
        part
        for message in result.new_messages()
        if isinstance(message, ModelRequest)
        for part in message.parts
        if isinstance(part, ToolReturnPart)
    ]
    assert returns[0].content == retrieved_chunks, (
        "Keep text and sources in the message audit trail."
    )


async def test_agent_can_stream(
    llm_settings: LLMSettings,
    search_stub: Mock,
    test_model: TestModel,
    reply_text: str,
    retrieval_query: str,
) -> None:
    """Use the same agent in PydanticAI's streaming context manager."""
    agent = build_agent(llm_settings)
    with agent.override(model=test_model):
        async with agent.run_stream(
            retrieval_query,
            deps=search_stub,
            usage_limits=UsageLimits(
                request_limit=llm_settings.request_limit
            ),
        ) as result:
            pieces = [
                piece
                async for piece in result.stream_text(delta=True)
            ]
            assert "".join(pieces) == reply_text, (
                "Streaming must deliver the same complete answer."
            )
            assert result.new_messages(), (
                "Completed streams must expose persistable messages."
            )


def test_ipv6_model(ipv6_settings: LLMSettings) -> None:
    """Bracket IPv6 addresses in the local OpenAI-compatible URL."""
    model = build_model(ipv6_settings)
    assert not isinstance(model, str), (
        "Local models need an explicit provider."
    )
    assert f"[{ipv6_settings.host}]" in str(model.base_url), (
        "IPv6 hosts must be bracketed in URLs."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
