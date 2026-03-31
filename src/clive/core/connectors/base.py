from abc import ABC, abstractmethod

# All connector references must start with this sigil.
# It unambiguously distinguishes a reference from a plain value, e.g.:
#   @az.kv.my-vault.my-secret  → connector reference
#   az.kv.some-tool-name       → treated as a plain string, never routed
CONNECTOR_SIGIL = "@"


class BaseConnector(ABC):
    """Base class for parameter value connectors.

    A connector intercepts a parameter value that matches the pattern
    @<prefix>.<reference> and resolves it to the actual value.

    The leading '@' sigil is mandatory and prevents accidental matching of
    plain values that happen to start with the same characters as a prefix.

    """

    # Each subclass must declare its own prefix, e.g. "az.kv" or "env".
    prefix: str

    def matches(self, value: str) -> bool:
        """Returns True when this connector should handle the given value."""
        return value.startswith(f"{CONNECTOR_SIGIL}{self.prefix}.")

    def extract_reference(self, value: str) -> str:
        """Strips the sigil and connector prefix, returning the bare reference."""
        # Strip '@<prefix>.' — e.g. '@az.kv.' → '' leaving 'my-vault.my-secret'
        return value[len(CONNECTOR_SIGIL) + len(self.prefix) + 1 :]

    @abstractmethod
    def resolve(self, reference: str) -> str:
        """Resolve the reference to its actual value.

        Args:
            reference: The part of the value after the connector prefix,
                       e.g. "my-vault.my-secret" for an az.kv connector.

        Returns:
            The resolved plain-text value.

        Raises:
            ValueError: When the reference is invalid or resolution fails.
        """
        ...
