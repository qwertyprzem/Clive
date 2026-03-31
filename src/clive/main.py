import os
import sys
from pathlib import Path

import click
from loguru import logger as log

from clive.core.connectors.azure_keyvault import AzureKeyVaultConnector
from clive.core.connectors.env import EnvConnector
from clive.core.models.data.command import Command
from clive.core.services.click import ClickService
from clive.core.services.commands import CommandsService
from clive.core.services.commands_config import CommandsConfigService
from clive.core.services.value_resolver import ValueResolverService

CONTEXT_SETTINGS: dict[str, bool] = {
    "ignore_unknown_options": True,
    "allow_extra_args": True,
}

log.remove()
log.add(sys.stderr, level=os.environ.get("CLIVE_LOG_LEVEL", "INFO"))


@log.catch
@click.command(context_settings=CONTEXT_SETTINGS, add_help_option=False)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False),
    default=Path("clive_cfg.yml"),
    envvar="CLIVE_CONFIG",
    help="Path to the commands configuration YAML file.",
)
@click.pass_context
def main(ctx: click.Context, config: Path):
    log.debug("Starting clive...")
    commands_config_service = CommandsConfigService()
    click_service = ClickService()

    # Load all commands from the YAML config file.
    try:
        commands: list[Command] = commands_config_service.parse_commands_config(config)
    except ValueError as e:
        log.error(f"Failed to parse commands configuration: {e}")
        return

    log.debug(f"Parsed {len(commands)} commands from configuration")

    # Show general help when no command is given or the first arg is a help flag.
    if not ctx.args or click_service.is_help_requested([ctx.args[0]]):
        click_service.print_general_help(commands, str(config))
        return

    # ctx.args[0] is the command ID; everything after it are the command's own args.
    command_id: str = ctx.args[0] if ctx.args else ""
    command = next((cmd for cmd in commands if cmd.id == command_id), None)
    if not command:
        log.error(f"Command '{command_id}' not found in configuration")
        # Fall back to general help so the user can see available commands.
        click_service.print_general_help(commands, str(config))
        return

    # Show command-specific help when --help/-h appears after the command ID.
    if click_service.is_help_requested(ctx.args[1:]):
        click_service.print_command_help(command)
        return

    # Parse --key value pairs that follow the command ID into a dict.
    given_parameters: dict[str, str] = click_service.parse_extra_args(ctx.args[1:])

    # Resolve connector references (e.g. az.kv.<vault>.<secret>) before rendering.
    # To add a new connector, import it and append an instance to this list.
    resolver = ValueResolverService(
        [
            AzureKeyVaultConnector(),
            EnvConnector(),
        ]
    )
    try:
        given_parameters = resolver.resolve_all(given_parameters)
    except ValueError as e:
        log.error(str(e))
        return

    commands_service = CommandsService()
    log.info(f"Executing command: {command.name}")
    try:
        commands_service.execute_command(command, given_parameters)
    except ValueError as e:
        log.error(str(e))
        return

    log.debug("Clive finished successfully.")
