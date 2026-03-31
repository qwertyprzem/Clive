import os

from clive.core.connectors.base import BaseConnector


class EnvConnector(BaseConnector):
    """Resolves parameter values from environment variables.

    Reference format:
        @env.<VARIABLE_NAME>

    Example parameter value:
        @env.MY_SECRET
    """

    prefix = "env"

    def resolve(self, reference: str) -> str:
        value = os.environ.get(reference)
        if value is None:
            raise ValueError(f"Environment variable '{reference}' is not set")
        return value
