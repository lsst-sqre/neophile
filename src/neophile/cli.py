"""Command-line interface."""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import asdict
from functools import wraps
from typing import TYPE_CHECKING

import aiohttp
import click
from ruamel.yaml import YAML

from neophile.analysis import Analyzer
from neophile.config import Configuration
from neophile.factory import Factory
from neophile.inventory import CachedHelmInventory
from neophile.scanner.helm import HelmScanner
from neophile.scanner.pre_commit import PreCommitScanner

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
@click.option(
    "--allow-expressions/--no-allow-expressions",
    default=False,
    help="Allow version match expressions",
)
@click.option("--path", default=os.getcwd(), type=str, help="Path to analyze")
@click.option(
    "--pr/--no-pr", default=False, help="Generate a pull request of changes."
)
@click.option(
    "--update/--no-update",
    default=False,
    help="Update out-of-date dependencies",
)
async def analyze(
    allow_expressions: bool, path: str, pr: bool, update: bool
) -> None:
    """Analyze the current directory for pending upgrades."""
    async with aiohttp.ClientSession() as session:
        analyzer = Analyzer(path, session, allow_expressions=allow_expressions)
        results = await analyzer.analyze()
        if pr:
            config = Configuration()
            factory = Factory(config, session)
            pull_requester = factory.create_pull_requester(path)
            await pull_requester.make_pull_request(results)
        elif update:
            for change in results:
                change.apply()
        else:
            yaml = YAML()
            yaml.indent(mapping=2, sequence=4, offset=2)
            yaml.dump([asdict(u) for u in results], sys.stdout)


@main.command()
@coroutine
@click.argument("repository", required=True)
async def inventory(repository: str) -> None:
    """Inventory available versions."""
    async with aiohttp.ClientSession() as session:
        inventory = CachedHelmInventory(session)
        results = await inventory.inventory(repository)
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(results, sys.stdout)


@main.command()
@click.option("--path", default=os.getcwd(), type=str, help="Path to scan")
def scan(path: str) -> None:
    """Scan the current directory for versions."""
    helm_scanner = HelmScanner(root=path)
    helm_results = helm_scanner.scan()
    pre_commit_scanner = PreCommitScanner(root=path)
    pre_commit_results = pre_commit_scanner.scan()
    results = {
        "helm": [asdict(d) for d in helm_results],
        "pre-commit": [asdict(d) for d in pre_commit_results],
    }

    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(results, sys.stdout)
