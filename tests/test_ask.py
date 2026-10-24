"""質問スクリプトのテスト（Gemini APIは呼び出さない）。"""

import builtins
import sys
from types import SimpleNamespace

from app import ask as ask_module


def _mock_client(monkeypatch):
    captured = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            usage = SimpleNamespace(
                prompt_token_count=12, candidates_token_count=7
            )
            return SimpleNamespace(usage_metadata=usage, text="response")

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "test-key"
            self.models = FakeModels()

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    return captured


def test_ask_passes_temperature_to_generation_config(monkeypatch):
    captured = _mock_client(monkeypatch)

    assert ask_module.ask("question", temperature=0.2) == "response"
    assert captured["config"].temperature == 0.2


def test_ask_uses_model_default_when_temperature_is_omitted(monkeypatch):
    captured = _mock_client(monkeypatch)

    assert ask_module.ask("question") == "response"
    assert captured["config"] is None


def test_ask_reports_elapsed_time_and_token_counts(monkeypatch, capsys):
    _mock_client(monkeypatch)
    timestamps = iter([10.0, 10.375])
    monkeypatch.setattr(ask_module, "perf_counter", lambda: next(timestamps))

    assert ask_module.ask("question") == "response"

    output = capsys.readouterr().out
    assert "応答時間=0.38秒" in output
    assert "入力トークン=12" in output
    assert "出力トークン=7" in output


def test_compare_runs_every_model_and_question(monkeypatch, capsys):
    calls = []

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            calls.append((model, contents, config))
            usage = SimpleNamespace(
                prompt_token_count=10, candidates_token_count=5
            )
            return SimpleNamespace(
                usage_metadata=usage,
                text=f"{model} answer to {contents}",
            )

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "test-key"
            self.models = FakeModels()

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "perf_counter", lambda: 1.0)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.ask",
            "--compare-models",
            "model-a",
            "model-b",
            "--question",
            "first question",
            "--question",
            "follow-up",
        ],
    )

    ask_module.main()

    assert calls == [
        ("model-a", "first question", None),
        ("model-b", "first question", None),
        ("model-a", "follow-up", None),
        ("model-b", "follow-up", None),
    ]
    output = capsys.readouterr().out
    assert "model | question | elapsed (s) | input tokens | output tokens" in output
    assert "0.00 | 10 | 5" in output
    assert "model-b answer to follow-up" in output


def test_chat_mode_keeps_history_between_questions(monkeypatch, capsys):
    sent_messages = []
    created_chats = []

    class FakeChat:
        def __init__(self):
            self.history = []

        def send_message(self, message):
            self.history.append(message)
            sent_messages.append(message)
            return SimpleNamespace(
                usage_metadata=None, text=f"reply to {message}"
            )

    class FakeChats:
        def create(self, *, model, config):
            chat = FakeChat()
            created_chats.append((model, config, chat))
            return chat

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "test-key"
            self.chats = FakeChats()

    questions = iter(["first question", "follow-up", "exit"])
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(builtins, "input", lambda _: next(questions))
    monkeypatch.setattr(sys, "argv", ["app.ask", "--chat", "--temperature", "0.5"])

    ask_module.main()

    assert sent_messages == ["first question", "follow-up"]
    assert len(created_chats) == 1
    model, config, chat = created_chats[0]
    assert model == ask_module.MODEL
    assert config.temperature == 0.5
    assert chat.history == sent_messages
    assert "reply to first question" in capsys.readouterr().out
