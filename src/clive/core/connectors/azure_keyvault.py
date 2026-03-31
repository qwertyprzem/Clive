import subprocess

from loguru import logger as log

from clive.core.connectors.base import BaseConnector


class AzureKeyVaultConnector(BaseConnector):
    """Resolves parameter values from Azure Key Vault using the az CLI.

    Reference format:
        @az.kv.<vault_name>.<secret_name>

    Example parameter value:
        @az.kv.my-vault.my-secret

    Requirements:
        - Azure CLI installed and available on PATH
        - Authenticated via `az login` or a service-principal environment
    """

    prefix = "az.kv"

    def resolve(self, reference: str) -> str:
        parts = reference.split(".", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid Key Vault reference '{reference}'. "
                "Expected format: @az.kv.<vault_name>.<secret_name>"
            )

        vault_name, secret_name = parts
        log.debug(f"Fetching secret '{secret_name}' from vault '{vault_name}'...")

        try:
            result = subprocess.run(
                [
                    "az",
                    "keyvault",
                    "secret",
                    "show",
                    "--vault-name",
                    vault_name,
                    "--name",
                    secret_name,
                    "--query",
                    "value",
                    "-o",
                    "tsv",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise ValueError(
                f"Failed to retrieve secret '{secret_name}' from vault '{vault_name}': "
                f"{e.stderr.strip()}"
            ) from e
