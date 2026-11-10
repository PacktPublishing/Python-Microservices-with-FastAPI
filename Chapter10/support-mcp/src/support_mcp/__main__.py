from fastmcp import FastMCP
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliSubCommand,
    SettingsConfigDict,
)

from .config import AuthSettings, Settings
from .generated import build_generated_server, fetch_spec
from .identity import (
    ForwardedIdentity,
    build_verifier,
    create_token,
)
from .server import build_server
from .support import SupportService, support_client


class Stdio(Settings):
    """Serve the curated tools to a local host over stdio."""

    local_user: str = Field(
        min_length=1,
        description="Local user identity; not authentication.",
    )

    async def cli_cmd(self) -> None:
        """Serve until the host closes standard input."""
        async with support_client(self.support) as client:
            server = build_server(
                SupportService(client),
                local_user=self.local_user,
            )
            await server.run_async(
                transport="stdio", show_banner=False
            )


class Http(Settings):
    """Serve the curated tools over Streamable HTTP."""

    auth: AuthSettings = Field(default_factory=AuthSettings)

    async def cli_cmd(self) -> None:
        """Serve authenticated clients until interrupted."""
        async with support_client(self.support) as client:
            server = build_server(
                SupportService(client),
                auth=build_verifier(self.auth),
            )
            await self.serve(server)

    async def serve(self, server: FastMCP) -> None:
        """Serve `server` over HTTP on the configured address.

        Args:
            server (FastMCP):
                The server to serve until interrupted.
        """
        await server.run_async(
            transport="http",
            host=str(self.server.host),
            port=self.server.port,
        )


class Token(BaseSettings):
    """Print a development access token for a user."""

    subject: str = Field(
        min_length=1, description="User the token identifies."
    )
    auth: AuthSettings = Field(default_factory=AuthSettings)

    def cli_cmd(self) -> None:
        """Sign the token with the shared secret and print it."""
        print(create_token(self.auth, self.subject))


class Generated(Http):
    """Serve tools generated from the support service's OpenAPI."""

    async def cli_cmd(self) -> None:
        """Download the OpenAPI document, then serve its routes."""
        async with support_client(
            self.support, auth=ForwardedIdentity()
        ) as client:
            server = build_generated_server(
                await fetch_spec(client),
                client,
                auth=build_verifier(self.auth),
            )
            await self.serve(server)


class Runner(BaseSettings):
    """Command-line entry point of the support MCP server."""

    model_config = SettingsConfigDict(
        cli_kebab_case=True,
        cli_enforce_required=True,
    )

    stdio: CliSubCommand[Stdio]
    http: CliSubCommand[Http]
    token: CliSubCommand[Token]
    generated: CliSubCommand[Generated]

    def cli_cmd(self) -> None:
        """Dispatch to the selected subcommand."""
        CliApp.run_subcommand(self)


def main(args: list[str] | None = None) -> None:
    """Parse the command line, or `args` when given, and run it.

    Run it with `python -m support_mcp <subcommand>`.

    Args:
        args (list[str] | None):
            Arguments to parse instead of `sys.argv`.
    """
    CliApp.run(Runner, cli_args=args)


if __name__ == "__main__":
    main()
