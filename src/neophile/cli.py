"""Command-line interface."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click
from httpx import AsyncClient
from ruamel.yaml import YAML
from safir.asyncio import run_with_asyncio

from .factory import Factory
from .inventory.github import GitHubInventory

__all__ = [
    "analyze",
    "check",
    "github_inventory",
    "help",
    "main",
    "scan",
    "update",
]


def print_yaml(results: Any) -> None:
    """Print some results to stdout as YAML."""
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(results, sys.stdout)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(message="%(version)s")
def main() -> None:
    """Command-line interface for neophile."""


@main.command()
@click.argument("topic", default=None, required=False, nargs=1)
@click.pass_context
def help(ctx: click.Context, topic: str | None) -> None:
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
        if not ctx.parent:
            raise RuntimeError("help called without topic or parent")
        click.echo(ctx.parent.get_help())


@main.command()
@click.argument("types", type=click.Choice(["pre-commit", "python"]), nargs=-1)
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Path to analyze (default: current directory).",
)
@run_with_asyncio
async def analyze(types: list[str], *, path: Path) -> None:
    """Analyze a path for pending upgrades."""
    async with AsyncClient() as client:
        factory = Factory(client)
        processor = factory.create_processor(types=types if types else None)
        results = await processor.analyze_checkout(path)
        if results:
            data = {k: [u.to_dict() for u in v] for k, v in results.items()}
            print_yaml(data)


@main.command()
@click.argument("types", type=click.Choice(["pre-commit", "python"]), nargs=-1)
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Path to analyze (default: current directory).",
)
@run_with_asyncio
async def check(types: list[str], *, path: Path) -> None:
    """Check whether dependencies are up-to-date."""
    async with AsyncClient() as client:
        factory = Factory(client)
        processor = factory.create_processor(types=types if types else None)
        results = await processor.analyze_checkout(path)
        for dependency in results:
            sys.stderr.write(f"{dependency} dependencies out of date\n")
        if results:
            sys.exit(1)


@main.command()
@click.argument("owner", required=True)
@click.argument("repo", required=True)
@run_with_asyncio
async def github_inventory(owner: str, repo: str) -> None:
    """Inventory available GitHub tags."""
    async with AsyncClient() as client:
        inventory = GitHubInventory(client)
        result = await inventory.inventory(owner, repo)
        if result:
            sys.stdout.write(result + "\n")
        else:
            sys.stderr.write(f"No versions found in {owner}/{repo}")


@main.command()
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Path to scan (default: current directory).",
)
@run_with_asyncio
async def scan(path: Path) -> None:
    """Scan a path for versions."""
    async with AsyncClient() as client:
        factory = Factory(client)
        scanners = factory.create_all_scanners()
        results = {s.name: s.scan(path) for s in scanners}
        print_yaml({k: [u.to_dict() for u in v] for k, v in results.items()})


@main.command()
@click.argument("types", type=click.Choice(["pre-commit", "python"]), nargs=-1)
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Path to analyze (default: current directory).",
)
@click.option(
    "--pr/--no-pr", default=False, help="Generate a pull request of changes."
)
@run_with_asyncio
async def update(types: list[str], *, path: Path, pr: bool) -> None:
    """Update dependencies."""
    async with AsyncClient() as client:
        factory = Factory(client)
        processor = factory.create_processor(types=types if types else None)
        if pr:
            await processor.process_checkout(path)
        else:
            await processor.update_checkout(path)
