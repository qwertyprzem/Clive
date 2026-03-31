import re
import subprocess

import pytest

from clive.core.models.data.command import Command
from clive.core.models.data.command_parameter import CommandParameter
from clive.core.services.commands import CommandsService


def test_render_command_combines_parameters_and_quote_filter():
    command = Command(
        id="echo",
        name="Echo",
        description="Echo text",
        shell_command="echo {{ text }} {{ secret | quote }}",
        parameters=[
            CommandParameter(id="text", description="Text to echo"),
            CommandParameter(id="secret", description="Secret", default="a b"),
        ],
    )
    svc = CommandsService()

    rendered = svc.render_command(command, {"text": "hello", "secret": "a b"})

    assert re.fullmatch(r"echo hello 'a b'", rendered)


def test_build_template_context_raises_on_missing_required_parameter():
    command = Command(
        id="cmd",
        name="Cmd",
        description="Cmd",
        shell_command="echo {{ required }}",
        parameters=[CommandParameter(id="required", description="Required")],
    )
    svc = CommandsService()

    with pytest.raises(ValueError, match="Missing required parameters"):
        svc._build_template_context(command, {})


def test_build_template_context_raises_on_regex_mismatch():
    command = Command(
        id="cmd",
        name="Cmd",
        description="Cmd",
        shell_command="echo {{ number }}",
        parameters=[
            CommandParameter(id="number", description="Number", regex=r"^\\d+$"),
        ],
    )
    svc = CommandsService()

    with pytest.raises(ValueError, match="Parameter validation failed"):
        svc._build_template_context(command, {"number": "abc"})


def test_execute_command_returns_rendered_command_and_prints(monkeypatch, capsys):
    command = Command(
        id="cmd",
        name="Cmd",
        description="Cmd",
        shell_command="echo test",
        parameters=[],
    )
    svc = CommandsService()

    class FakeCompleted:
        stdout = "fake-output\n"

    def fake_run(*args, **kwargs):
        return FakeCompleted()

    monkeypatch.setattr(subprocess, "run", fake_run)
    rendered = svc.execute_command(command, {})
    captured = capsys.readouterr()

    assert rendered == "echo test"
    assert captured.out.strip() == "fake-output"
