"""Command-line interface."""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import asdict
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
from neophile.scanner.helm import HelmScanner
from neophile.scanner.kustomize import KustomizeScanner
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
        analyzers = factory.create_all_analyzers(
            path, allow_expressions=allow_expressions
        )

        if pr:
            repo = factory.create_repository(Path(path))
            repo.switch_branch()
            all_updates = []
            for analyzer in analyzers:
                updates = await analyzer.update()
                all_updates.extend(updates)
            pull_requester = factory.create_pull_requester(path)
            await pull_requester.make_pull_request(all_updates)
            repo.restore_branch()
        elif update:
            for analyzer in analyzers:
                await analyzer.update()
        else:
            results = {a.name(): await a.analyze() for a in analyzers}
            print_yaml({k: [asdict(u) for u in v] for k, v in results.items()})


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
@click.option("--path", default=os.getcwd(), type=str, help="Path to scan.")
def scan(path: str) -> None:
    """Scan a path for versions."""
    helm_scanner = HelmScanner(root=path)
    helm_results = helm_scanner.scan()
    kustomize_scanner = KustomizeScanner(root=path)
    kustomize_results = kustomize_scanner.scan()
    pre_commit_scanner = PreCommitScanner(root=path)
    pre_commit_results = pre_commit_scanner.scan()

    results = {
        "helm": [asdict(d) for d in helm_results],
        "pre-commit": [asdict(d) for d in pre_commit_results],
        "kustomize": [asdict(d) for d in kustomize_results],
    }
    print_yaml(results)
