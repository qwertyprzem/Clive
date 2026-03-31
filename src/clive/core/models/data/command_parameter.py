from dataclasses import dataclass


@dataclass(frozen=True)
class CommandParameter:
    """Represents a command parameter configuration."""

    id: str
    description: str
    default: str | None = None
    regex: str | None = None
