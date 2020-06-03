"""Command-line interface."""

from __future__ import annotations

import asyncio
import os
from functools import wraps
from typing import TYPE_CHECKING

import aiohttp
import click
import yaml

from neophile.inventory import HelmInventory
from neophile.scanner import Scanner

if TYPE_CHECKING:
    from typing import Any, Awaitable, Callable, Optional, TypeVar

    T = TypeVar("T")

__all__ = ["main"]


def coroutine(f: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(message="%(version)s")
def main() -> None:
    """neophile main.

    Administrative command-line interface for neophile.
    """
    pass


@main.command()
@click.argument("topic", default=None, required=False, nargs=1)
@click.pass_context
def help(ctx: click.Context, topic: Optional[str]) -> None:
    """Show help for any command."""
    # The help command implementation is taken from
    # https://www.burgundywall.com/post/having-click-help-subcommand
    if topic:
        if topic in main.commands:
            click.echo(main.commands[topic].get_help(ctx))
        else:
            raise click.UsageError(f"Unknown help topic {topic}", ctx)
    else:
        assert ctx.parent
        click.echo(ctx.parent.get_help())


@main.command()
@coroutine
@click.argument("repository", required=True)
async def inventory(repository: str) -> None:
    """Inventory available versions."""
    async with aiohttp.ClientSession() as session:
        inventory = HelmInventory(session)
        results = await inventory.inventory(repository)
    print(yaml.dump(dict(results)))


@main.command()
def scan() -> None:
    """Scan the current directory for versions."""
    scanner = Scanner(root=os.getcwd())
    results = scanner.scan()
    print(yaml.dump(results))
