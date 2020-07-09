"""Command-line interface."""

from __future__ import annotations

import asyncio
import os
import sys
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import click
from ruamel.yaml import YAML
from xdg import XDG_CONFIG_HOME

from neophile.config import Configuration
from neophile.factory import Factory
from neophile.inventory.github import GitHubInventory
from neophile.inventory.helm import CachedHelmInventory

if TYPE_CHECKING:
    from typing import Any, Awaitable, Callable, Optional, TypeVar

    T = TypeVar("T")

__all__ = ["main"]


def coroutine(f: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def print_yaml(results: Any) -> None:
    """Print some results to stdout as YAML."""
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(results, sys.stdout)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-c",
    "--config-path",
    type=str,
    metavar="PATH",
    default=str(XDG_CONFIG_HOME / "neophile.yaml"),
    envvar="NEOPHILE_CONFIG",
    help="Path to configuration.",
)
@click.version_option(message="%(version)s")
@click.pass_context
def main(ctx: click.Context, config_path: str) -> None:
    """Command-line interface for neophile."""
    ctx.ensure_object(dict)
    if os.path.exists(config_path):
        ctx.obj["config"] = Configuration.from_file(config_path)
    else:
        ctx.obj["config"] = Configuration()


@main.command()
@click.argument("topic", default=None, required=False, nargs=1)
@click.pass_context
def help(ctx: click.Context, topic: Optional[str]) -> None:
    """Show help for any command."""
    # The help command implementation is taken from
    # https://www.burgundywall.com/post/having-click-help-subcommand
    if topic:
        if topic in main.commands:
            ctx.info_name = topic
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
    help="Allow version match expressions.",
)
@click.option("--path", default=os.getcwd(), type=str, help="Path to analyze.")
@click.option(
    "--pr/--no-pr", default=False, help="Generate a pull request of changes."
)
@click.option(
    "--update/--no-update",
    default=False,
    help="Update out-of-date dependencies",
)
@click.pass_context
async def analyze(
    ctx: click.Context,
    allow_expressions: bool,
    path: str,
    pr: bool,
    update: bool,
) -> None:
    """Analyze the current directory for pending upgrades."""
    config = ctx.obj["config"]

    async with aiohttp.ClientSession() as session:
        factory = Factory(config, session)
        processor = factory.create_processor()
        if pr:
            await processor.process_checkout(Path(path))
        elif update:
            await processor.update_checkout(Path(path))
        else:
            results = await processor.analyze_checkout(Path(path))
            print_yaml(
                {k: [u.to_dict() for u in v] for k, v in results.items()}
            )


@main.command()
@coroutine
@click.argument("owner", required=True)
@click.argument("repo", required=True)
@click.pass_context
async def github_inventory(ctx: click.Context, owner: str, repo: str) -> None:
    """Inventory available GitHub tags."""
    config = ctx.obj["config"]

    async with aiohttp.ClientSession() as session:
        inventory = GitHubInventory(config, session)
        result = await inventory.inventory(owner, repo)
    print(result)


@main.command()
@coroutine
@click.argument("repository", required=True)
@click.pass_context
async def helm_inventory(ctx: click.Context, repository: str) -> None:
    """Inventory available Helm chart versions."""
    async with aiohttp.ClientSession() as session:
        inventory = CachedHelmInventory(session)
        results = await inventory.inventory(repository)
    print_yaml(results)


@main.command()
@coroutine
@click.pass_context
async def process(ctx: click.Context) -> None:
    """Process all configured repositories."""
    config = ctx.obj["config"]
    async with aiohttp.ClientSession() as session:
        factory = Factory(config, session)
        processor = factory.create_processor()
        await processor.process()


@main.command()
@coroutine
@click.option("--path", default=os.getcwd(), type=str, help="Path to scan.")
@click.pass_context
async def scan(ctx: click.Context, path: str) -> None:
    """Scan a path for versions."""
    config = ctx.obj["config"]
    async with aiohttp.ClientSession() as session:
        factory = Factory(config, session)
        scanners = factory.create_all_scanners(Path(path))
        results = {s.name(): s.scan() for s in scanners}
        print_yaml({k: [u.to_dict() for u in v] for k, v in results.items()})
