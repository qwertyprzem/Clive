import re
import shlex

from jinja2 import Environment, StrictUndefined, TemplateError

from clive.core.models.data.command import Command
from clive.main import log


class CommandsService:
    def render_command(self, command: Command, parameter_values: dict[str, str]) -> str:
        """Renders the command shell template using provided and default parameter values."""
        context = self._build_template_context(command, parameter_values)
        env = Environment(undefined=StrictUndefined, autoescape=False)
        # | quote filter shell-escapes a value with shlex.quote.
        # Use it in templates when a connector-resolved value is a shell argument:
        # e.g.  some_cmd --password {{ secret | quote }}
        env.filters["quote"] = shlex.quote  # type: ignore[index]
        try:
            return env.from_string(command.shell_command).render(**context)
        except TemplateError as e:
            raise ValueError(f"Failed to render command '{command.id}': {e}") from e

    def execute_command(
        self, command: Command, parameter_values: dict[str, str]
    ) -> str:
        """Builds the shell command by rendering its template with parameter values."""
        rendered_command = self.render_command(command, parameter_values)
        import subprocess

        try:
            result = subprocess.run(
                rendered_command, shell=True, check=True, capture_output=True, text=True
            )
            print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            log.error(f"Command failed with error: {e.stderr.strip()}")
        return rendered_command

    def _build_template_context(
        self, command: Command, parameter_values: dict[str, str]
    ) -> dict[str, str]:
        """Merges explicit parameter values with defaults and validates required inputs."""
        context: dict[str, str] = {}
        missing_required_parameters: list[str] = []

        for parameter in command.parameters:
            if parameter.id in parameter_values:
                context[parameter.id] = parameter_values[parameter.id]
            elif parameter.default is not None:
                context[parameter.id] = parameter.default
            else:
                missing_required_parameters.append(parameter.id)

        if missing_required_parameters:
            missing = ", ".join(sorted(missing_required_parameters))
            raise ValueError(
                f"Missing required parameters for command '{command.id}': {missing}"
            )

        self._validate_parameter_formats(command, context)

        # Keep extra values available in the template for advanced use cases.
        context.update(parameter_values)
        return context

    @staticmethod
    def _validate_parameter_formats(command: Command, context: dict[str, str]) -> None:
        """Validates parameter values against their regex patterns."""
        invalid: list[str] = []
        for parameter in command.parameters:
            if parameter.regex and parameter.id in context:
                value = context[parameter.id]
                if not re.fullmatch(parameter.regex, value):
                    invalid.append(
                        f"  - {parameter.id}: '{value}' does not match pattern '{parameter.regex}'"
                    )
        if invalid:
            raise ValueError(
                f"Parameter validation failed for command '{command.id}':\n"
                + "\n".join(invalid)
            )
