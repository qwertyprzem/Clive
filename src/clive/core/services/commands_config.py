from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from clive.core.models.data.command import Command
from clive.core.models.data.command_parameter import CommandParameter
from clive.main import log


class CommandsConfigService:
    def parse_commands_config(self, config_path: Path) -> list[Command]:
        """Parses the commands configuration from a YAML file."""
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        commands: list[Command] = []
        for command_id, command_data in config_data.items():
            try:
                self._validate_command_data(command_data)
                command = Command(
                    id=command_id,
                    name=command_data.get("name", ""),
                    description=command_data.get("description", ""),
                    shell_command=command_data.get("shell", ""),
                    parameters=self._create_command_parameters(
                        command_data.get("parameters", [])
                    ),
                )
            except ValueError as e:
                log.error(f"Error in command '{command_id}': {e}")
                raise ValueError(
                    f"Invalid command configuration for '{command_id}'"
                ) from e
            commands.append(command)
        return commands

    def execute_command(
        self, command: Command, parameter_values: dict[str, str]
    ) -> None:
        """Executes the given command with the provided parameter values."""
        # This is a placeholder for command execution logic.
        # You would need to implement the actual execution based on your requirements.
        log.info(
            f"Executing command '{command.name}' with parameters: {parameter_values}"
        )
        # Example: You could use subprocess to execute the shell command.
        # import subprocess
        # subprocess.run(command.shell_command, shell=True, check=True)

    def _validate_command_data(self, command_data: Mapping[str, Any]) -> bool:
        """Validates the command data structure."""
        required_fields = ["name", "description", "shell"]
        for field in required_fields:
            if field not in command_data:
                raise ValueError(
                    f"Missing required field '{field}' in command configuration"
                )
        return True

    def _create_command_parameters(
        self, parameters_data: dict[str, Mapping[str, Any]]
    ) -> list[CommandParameter]:
        """Creates command parameters from the parameters data."""
        parameters: list[CommandParameter] = []
        for param_id, param_data in parameters_data.items():
            if "description" not in param_data:
                raise ValueError("Each parameter must have 'description'.")
            parameter = CommandParameter(
                id=param_id,
                description=param_data["description"],
                default=param_data.get("default"),
                regex=param_data.get("regex"),
            )
            parameters.append(parameter)
        return parameters
