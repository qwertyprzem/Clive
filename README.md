# Clive

> A lightweight CLI that turns a YAML file into your personal multi-tool.

Clive lets you define parameterised shell commands in a single YAML config and run them by name — with full parameter validation, secret resolution, and built-in auto-generated help — all without writing a single line of shell script boilerplate.

### Why it exists

Shell one-liners are powerful but hard to share, document, and maintain. Clive solves that by acting as a thin, opinionated wrapper:

- **One config file = one multi-tool.** Keep all your project or team commands in one place, version-controlled and readable.
- **CI/CD friendly.** The exact same command you run locally in your pipeline works identically on your machine — no more "it works in CI but not here" debugging. Parameters make pipelines self-documenting.
- **Secrets without copy-pasting.** Pull parameter values from Azure Key Vault (or any connector you add) at runtime, so credentials never touch your shell history or `.env` files.
- **Designed to grow.** The connector system is intentionally simple to extend. Adding a new secret source (env vars, files, AWS SSM, HashiCorp Vault…) is a matter of one class and one line of registration.

Even though the tool is intentionally small, it executes commands through the real shell, so piping (`|`), redirection (`>`, `>>`), and all other shell features work exactly as expected.

## Features

| Feature | Detail |
|---|---|
| **YAML-defined commands** | Declare any shell command in a config file — name, description, shell template, parameters |
| **Jinja2 templates** | Use `{{ param }}` placeholders in shell strings; rendered on every run |
| **Parameter validation** | Required parameters must be provided; optional `regex` pattern validates format before execution |
| **Parameter defaults** | Optional parameters fall back to a configured default value |
| **Connector system** | Parameter values can be resolved from external sources at runtime (see [Connectors](#connectors)) |
| **Azure Key Vault** | Built-in connector: prefix any value with `@az.kv.<vault>.<secret>` to pull it from Key Vault |
| **Environment Variables** | Built-in connector: prefix any value with `@env.<VARIABLE>` to read it from the environment |
| **Shell-injection protection** | Use the `\| quote` Jinja filter to safely shell-escape resolved secrets |
| **Custom help** | `--help` / `-h` / `help` at any position prints context-aware, config-driven help |
| **Full shell support** | Commands run via the real shell — piping (`\|`), redirection (`>`, `>>`), and all operators work |

---

## Requirements

- Python **3.10+**
- [`uv`](https://docs.astral.sh/uv/) (recommended) **or** `pip`
- Linux / macOS / Windows

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/<your-username>/Clive.git
cd Clive

# 2. Install dependencies (uv recommended)
uv sync

# 3. See what commands the example config provides
uv run clive -c example_cfg.yml --help

# 4. Run your first command
uv run clive -c example_cfg.yml greet_user --user_name Alice
```

---

## Installation

### Recommended: uv

[uv](https://docs.astral.sh/uv/) is a fast Python package and project manager. It handles the virtual environment and dependency installation in a single command.

```bash
# Install uv (once, globally)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync

# Run the CLI
uv run clive --help
```

### Alternative: pip + venv

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e .

clive --help
```

---

## Configuration

Clive reads commands from a YAML file. By default it looks for `clive_cfg.yml` in the current directory. Use `-c` / `--config` to point to any file, or set the `CLIVE_CONFIG` environment variable:

```bash
export CLIVE_CONFIG=example_cfg.yml
uv run clive greet_user
```

The precedence is: `--config` flag > `CLIVE_CONFIG` env var > default (`clive_cfg.yml`).

### Command schema

```yaml
<command_id>:
  name: Human-readable name
  description: What the command does
  shell: the-shell-command --flag {{ param_name }}
  parameters:
    param_name:
      description: What this parameter does
      default: optional_default_value   # omit to make the parameter required
      regex: "^\\d+$"                  # optional — validate value format before execution
```

### Example config ([example_cfg.yml](example_cfg.yml))

```yaml
greet_user:
  name: Greet user
  description: Prints a personalised greeting
  shell: echo "Hello, {{ user_name }}!"
  parameters:
    user_name:
      description: Name displayed in the greeting
      default: world

list_directory:
  name: List directory
  description: Lists files in a directory
  shell: ls -la {{ directory }}
  parameters:
    directory:
      description: Directory to list
      default: .
      regex: "^[\\w./_-]+$"

show_file_head:
  name: Show file head
  description: Prints the first N lines of a file
  shell: head -n {{ lines }} {{ file_path }}
  parameters:
    file_path:
      description: Path to the file to preview
    lines:
      description: Number of lines to print
      default: "20"
      regex: "^\\d+$"
```

---

## Usage

### Help

```bash
# List all available commands
uv run clive -c example_cfg.yml --help

# Show parameters for a specific command
uv run clive -c example_cfg.yml show_file_head --help
```

### Running commands

```bash
# Use default parameter value
uv run clive -c example_cfg.yml greet_user

# Override the default
uv run clive -c example_cfg.yml greet_user --user_name Alice

# Required parameter (no default)
uv run clive -c example_cfg.yml show_file_head --file_path README.md

# Override multiple parameters
uv run clive -c example_cfg.yml show_file_head \
  --file_path README.md \
  --lines 5

# Shell output flow works as-is — the template runs through the real shell
uv run clive -c example_cfg.yml list_directory --directory /tmp | grep ".log" >> logs.txt
```

---

## Connectors

Connectors let you pull parameter values from external sources at runtime instead of passing them on the command line. This is the main security feature of Clive — secrets are fetched just-in-time and never stored in shell history.

Any parameter value prefixed with `@<connector>.<reference>` is intercepted and resolved before the command template is rendered.

### Azure Key Vault

Requires the [Azure CLI](https://learn.microsoft.com/cli/azure/) installed and an active `az login` session.

```bash
uv run clive -c my_cfg.yml deploy \
  --password @az.kv.my-vault.db-password
```

Format: `@az.kv.<vault_name>.<secret_name>`

### Environment Variables

Resolves parameter values from environment variables. No external dependencies required.

```bash
export DB_PASSWORD="s3cret"
uv run clive -c my_cfg.yml deploy \
  --password @env.DB_PASSWORD
```

Format: `@env.<VARIABLE_NAME>`

### Shell-injection protection for secrets

When a resolved secret is used as a shell argument, wrap it with the `| quote` Jinja filter to safely escape any special characters:

```yaml
deploy_db:
  shell: psql --password {{ db_password | quote }} --host {{ host }}
```

### Adding a new connector

1. Create a file in `src/clive/core/connectors/`.
2. Subclass `BaseConnector`, set a unique `prefix`, and implement `resolve(reference) -> str`.
3. Register an instance in `main.py` by appending it to the `ValueResolverService` list.

```python
# Example: environment variable connector  →  @env.MY_VAR
class EnvConnector(BaseConnector):
    prefix = "env"

    def resolve(self, reference: str) -> str:
        value = os.environ.get(reference)
        if value is None:
            raise ValueError(f"Environment variable '{reference}' is not set")
        return value
```


## Troubleshooting

**`File 'clive_cfg.yml' does not exist`**
Pass the config path explicitly:
```bash
uv run clive -c example_cfg.yml --help
```

**`Missing required parameters`**
The command requires a parameter that was not provided and has no default. Run `--help` on the command to see what is needed.

**`Parameter validation failed`**
A parameter value does not match the `regex` pattern defined in the config. Check the expected format with `--help` — the pattern is shown next to the parameter.

**`Failed to retrieve secret … from vault`**
Make sure you are authenticated: `az login`. Verify the vault name and secret name are correct.

**No output**
Some commands produce no stdout. Errors always go to stderr. Enable debug logs to trace execution:
```bash
CLIVE_LOG_LEVEL=DEBUG uv run clive -c example_cfg.yml <command>
```

