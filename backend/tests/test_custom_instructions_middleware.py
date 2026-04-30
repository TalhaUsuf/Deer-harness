"""Tests for CustomInstructionsMiddleware."""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from deerflow.agents.middlewares.custom_instructions_middleware import (
    CustomInstructionsMiddleware,
)


def _runtime(custom_instructions: str | None = None, thread_id: str = "thread-xyz") -> Runtime:
    ctx: dict = {"thread_id": thread_id}
    if custom_instructions is not None:
        ctx["custom_instructions"] = custom_instructions
    return Runtime(context=ctx)


class TestFirstTurn:
    def test_injects_system_message_when_instructions_present(self):
        mw = CustomInstructionsMiddleware()
        state = {"messages": [HumanMessage(content="Hello")]}
        runtime = _runtime("Always answer in pirate dialect.")

        result = mw.before_agent(state=state, runtime=runtime)

        assert result is not None
        msgs = result["messages"]
        assert len(msgs) == 2
        assert isinstance(msgs[0], SystemMessage)
        assert "<custom_instructions>" in msgs[0].content
        assert "</custom_instructions>" in msgs[0].content
        assert "Always answer in pirate dialect." in msgs[0].content
        assert isinstance(msgs[1], HumanMessage)
        assert msgs[1].content == "Hello"

    def test_returns_none_when_no_instructions(self):
        mw = CustomInstructionsMiddleware()
        state = {"messages": [HumanMessage(content="Hello")]}
        runtime = _runtime(custom_instructions=None)

        assert mw.before_agent(state=state, runtime=runtime) is None

    def test_returns_none_when_instructions_blank(self):
        mw = CustomInstructionsMiddleware()
        state = {"messages": [HumanMessage(content="Hello")]}
        runtime = _runtime("   \n  ")

        assert mw.before_agent(state=state, runtime=runtime) is None

    def test_strips_whitespace_from_instructions(self):
        mw = CustomInstructionsMiddleware()
        state = {"messages": [HumanMessage(content="Hi")]}
        runtime = _runtime("\n  Be terse.  \n")

        result = mw.before_agent(state=state, runtime=runtime)

        assert result is not None
        sys_msg = result["messages"][0]
        assert sys_msg.content == "<custom_instructions>\nBe terse.\n</custom_instructions>"

    def test_works_with_empty_messages_list(self):
        mw = CustomInstructionsMiddleware()
        state: dict = {"messages": []}
        runtime = _runtime("Be helpful.")

        result = mw.before_agent(state=state, runtime=runtime)

        assert result is not None
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], SystemMessage)


class TestContinuingThread:
    def test_ignores_instructions_when_ai_message_already_present(self, caplog):
        mw = CustomInstructionsMiddleware()
        state = {
            "messages": [
                HumanMessage(content="What is 2+2?"),
                AIMessage(content="4"),
                HumanMessage(content="And 3+3?"),
            ]
        }
        runtime = _runtime("Switch to robot mode.")

        with caplog.at_level(logging.WARNING, logger="deerflow.agents.middlewares.custom_instructions_middleware"):
            result = mw.before_agent(state=state, runtime=runtime)

        assert result is None
        assert any("custom_instructions ignored on existing thread" in r.message for r in caplog.records)

    def test_returns_none_silently_on_continuing_thread_without_instructions(self, caplog):
        mw = CustomInstructionsMiddleware()
        state = {
            "messages": [
                HumanMessage(content="Hi"),
                AIMessage(content="Hello!"),
                HumanMessage(content="How are you?"),
            ]
        }
        runtime = _runtime(custom_instructions=None)

        with caplog.at_level(logging.WARNING, logger="deerflow.agents.middlewares.custom_instructions_middleware"):
            result = mw.before_agent(state=state, runtime=runtime)

        assert result is None
        assert not any("custom_instructions" in r.message for r in caplog.records)


class TestFallbackToConfigurable:
    def test_reads_from_configurable_when_context_is_none(self, monkeypatch):
        mw = CustomInstructionsMiddleware()
        state = {"messages": [HumanMessage(content="Hi")]}
        runtime = Runtime(context=None)
        monkeypatch.setattr(
            "langgraph.config.get_config",
            lambda: {"configurable": {"custom_instructions": "Be brief.", "thread_id": "t1"}},
        )

        result = mw.before_agent(state=state, runtime=runtime)

        assert result is not None
        assert "Be brief." in result["messages"][0].content

    def test_reads_from_configurable_when_context_lacks_field(self, monkeypatch):
        mw = CustomInstructionsMiddleware()
        state = {"messages": [HumanMessage(content="Hi")]}
        runtime = Runtime(context={"thread_id": "t1"})
        monkeypatch.setattr(
            "langgraph.config.get_config",
            lambda: {"configurable": {"custom_instructions": "Use bullet points.", "thread_id": "t1"}},
        )

        result = mw.before_agent(state=state, runtime=runtime)

        assert result is not None
        assert "Use bullet points." in result["messages"][0].content

    def test_context_takes_precedence_over_configurable(self, monkeypatch):
        mw = CustomInstructionsMiddleware()
        state = {"messages": [HumanMessage(content="Hi")]}
        runtime = _runtime("From context")
        monkeypatch.setattr(
            "langgraph.config.get_config",
            lambda: {"configurable": {"custom_instructions": "From configurable"}},
        )

        result = mw.before_agent(state=state, runtime=runtime)

        assert result is not None
        assert "From context" in result["messages"][0].content
        assert "From configurable" not in result["messages"][0].content


class TestRegistration:
    def test_included_in_lead_runtime_middlewares(self):
        from deerflow.agents.middlewares.tool_error_handling_middleware import (
            build_lead_runtime_middlewares,
        )

        middlewares = build_lead_runtime_middlewares(lazy_init=True)
        assert any(isinstance(mw, CustomInstructionsMiddleware) for mw in middlewares), (
            "CustomInstructionsMiddleware must be wired into the lead runtime middleware list"
        )

    def test_not_included_in_subagent_runtime_middlewares(self):
        from deerflow.agents.middlewares.tool_error_handling_middleware import (
            build_subagent_runtime_middlewares,
        )

        middlewares = build_subagent_runtime_middlewares(lazy_init=True)
        assert not any(isinstance(mw, CustomInstructionsMiddleware) for mw in middlewares), (
            "Subagents should not receive thread-level custom_instructions"
        )
