from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliSubCommand,
    SettingsConfigDict,
)

from .config import KnowledgeSettings
from .knowledge import KnowledgeBase


class Ingest(KnowledgeSettings):
    """Sync the source folder into the knowledge base."""

    def cli_cmd(self) -> None:
        """Open the knowledge base and sync the folder."""
        KnowledgeBase(self).sync()


class Runner(BaseSettings):
    """Command-line entry point of the customer support service."""

    model_config = SettingsConfigDict(
        cli_kebab_case=True,
    )

    ingest: CliSubCommand[Ingest]

    def cli_cmd(self) -> None:
        """Dispatch to the selected subcommand."""
        CliApp.run_subcommand(self)


def main(args: list[str] | None = None) -> None:
    """Parse the command line, or `args` when given, and run it.

    Run it with `python -m customer_support <subcommand>`.

    Args:
        args (list[str] | None):
            Arguments to parse instead of `sys.argv`.
    """
    CliApp.run(Runner, cli_args=args)


if __name__ == "__main__":
    main()
