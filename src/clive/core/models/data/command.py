from dataclasses import dataclass

from clive.core.models.data.command_parameter import CommandParameter


@dataclass(frozen=True)
class Command:
    """Represents a command configuration."""

    id: str
    name: str
    description: str
    shell_command: str
    parameters: list[CommandParameter]
