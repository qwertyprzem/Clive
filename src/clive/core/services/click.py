import click

from clive.core.models.data.command import Command


class ClickService:
    def parse_extra_args(self, extra_args: list[str]) -> dict[str, str]:
        """Parses extra arguments passed to the Click command."""
        parsed_args: dict[str, str] = {}
        it = iter(extra_args)
        for item in it:
            # Only process flags that start with '--'; skip bare positional args.
            if item.startswith("--"):
                key = item.lstrip("-")
                try:
                    # The item immediately following the flag is its value.
                    value = next(it)
                    parsed_args[key] = value
                except StopIteration:
                    # Flag with no following value is treated as a boolean True.
                    parsed_args[key] = "True"
        return parsed_args

    def is_help_requested(self, args: list[str]) -> bool:
        """Checks whether the user requested custom help output."""
        return any(arg in {"--help", "-h", "help"} for arg in args)

    def print_general_help(self, commands: list[Command], config_path: str) -> None:
        """Prints the top-level CLI help."""
        click.echo("Usage: clive [OPTIONS] COMMAND [COMMAND OPTIONS]")
        click.echo("")
        click.echo("Options:")
        click.echo(
            f"  -c, --config PATH  Commands configuration file. Default: {config_path}"
        )
        click.echo("  -h, --help         Show this help message")
        click.echo("")
        click.echo("Commands:")
        for command in commands:
            click.echo(f"  {command.id:<20} {command.description}")

    def print_command_help(self, command: Command) -> None:
        """Prints help for a single configured command."""
        click.echo(f"Usage: clive {command.id} [PARAMETERS]")
        click.echo("")
        click.echo(f"{command.name}: {command.description}")
        click.echo("")
        click.echo("Parameters:")
        if not command.parameters:
            click.echo("  This command does not define any parameters.")
            return

        for parameter in command.parameters:
            # Append the default value hint only when a default is defined.
            default_suffix = (
                f" [default: {parameter.default}]"
                if parameter.default is not None
                else ""
            )
            regex_suffix = (
                f" [pattern: {parameter.regex}]" if parameter.regex is not None else ""
            )
            click.echo(
                f"  --{parameter.id:<18} {parameter.description}{default_suffix}{regex_suffix}"
            )
