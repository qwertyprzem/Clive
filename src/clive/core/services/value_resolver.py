from clive.core.connectors.base import BaseConnector


class ValueResolverService:
    """Resolves parameter values through a list of registered connectors.

    Each connector declares a prefix (e.g. "az.kv"). When a parameter value
    starts with "<prefix>.", it is routed to the matching connector which
    returns the real value. Plain values with no matching prefix pass through
    unchanged.

    To register a new connector, add its instance to the list passed to
    __init__. The first connector whose prefix matches is used.
    """

    def __init__(self, connectors: list[BaseConnector]) -> None:
        self._connectors = connectors

    def resolve(self, value: str, parameter_name: str | None = None) -> str:
        """Resolve a single parameter value.

        Returns the connector-resolved value if a prefix matches,
        otherwise returns the original value unchanged.

        Raises:
            ValueError: When a matching connector fails to resolve the value.
        """
        for connector in self._connectors:
            if connector.matches(value):
                reference = connector.extract_reference(value)
                try:
                    return connector.resolve(reference)
                except ValueError:
                    raise
                except Exception as e:
                    param_hint = (
                        f" (parameter '{parameter_name}')" if parameter_name else ""
                    )
                    raise ValueError(
                        f"Connector '{connector.prefix}' failed to resolve '{value}'{param_hint}: {e}"
                    ) from e
        return value

    def resolve_all(self, parameter_values: dict[str, str]) -> dict[str, str]:
        """Resolve every value in a parameter dict.

        Raises:
            ValueError: When any connector reference cannot be resolved.
        """
        resolved: dict[str, str] = {}
        errors: list[str] = []
        for key, value in parameter_values.items():
            try:
                resolved[key] = self.resolve(value, parameter_name=key)
            except ValueError as e:
                errors.append(f"  - {key}: {e}")
        if errors:
            raise ValueError(
                "Could not resolve the following parameter(s):\n" + "\n".join(errors)
            )
        return resolved
