"""Command-line interface."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import click
from ruamel.yaml import YAML
from safir.asyncio import run_with_asyncio
from xdg import XDG_CONFIG_HOME

from neophile.config import Configuration
from neophile.factory import Factory
from neophile.inventory.github import GitHubInventory

if TYPE_CHECKING:
    from typing import Any

__all__ = ["main"]


def print_yaml(results: Any) -> None:
    """Print some results to stdout as YAML."""
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(results, sys.stdout)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-c",
    "--config-path",
    type=click.Path(path_type=Path),
    metavar="PATH",
    default=str(XDG_CONFIG_HOME / "neophile.yaml"),
    envvar="NEOPHILE_CONFIG",
    help="Path to configuration",
)
@click.version_option(message="%(version)s")
@click.pass_context
def main(ctx: click.Context, config_path: Path) -> None:
    """Command-line interface for neophile."""
    ctx.ensure_object(dict)
    if config_path.exists():
        ctx.obj["config"] = Configuration.from_file(config_path)
    else:
        ctx.obj["config"] = Configuration()


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
@click.option(
    "--allow-expressions/--no-allow-expressions",
    default=False,
    help="Allow version match expressions",
)
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Path to analyze",
)
@click.option(
    "--pr/--no-pr", default=False, help="Generate a pull request of changes"
)
@click.option(
    "--update/--no-update",
    default=False,
    help="Update out-of-date dependencies",
)
@click.pass_context
@run_with_asyncio
async def analyze(
    ctx: click.Context,
    *,
    allow_expressions: bool,
    path: Path,
    pr: bool,
    update: bool,
) -> None:
    """Analyze the current directory for pending upgrades."""
    config = ctx.obj["config"]
    config.allow_expressions = allow_expressions

    async with aiohttp.ClientSession() as session:
        factory = Factory(config, session)
        processor = factory.create_processor()
        if pr:
            await processor.process_checkout(path)
        elif update:
            await processor.update_checkout(path)
        else:
            results = await processor.analyze_checkout(path)
            print_yaml(
                {k: [u.to_dict() for u in v] for k, v in results.items()}
            )


@main.command()
@click.argument("owner", required=True)
@click.argument("repo", required=True)
@click.pass_context
@run_with_asyncio
async def github_inventory(ctx: click.Context, owner: str, repo: str) -> None:
    """Inventory available GitHub tags."""
    config = ctx.obj["config"]

    async with aiohttp.ClientSession() as session:
        inventory = GitHubInventory(config, session)
        result = await inventory.inventory(owner, repo)
        if result:
            sys.stdout.write(result + "\n")
        else:
            sys.stderr.write(f"No versions found in {owner}/{repo}")


@main.command()
@click.argument("repository", required=True)
@click.pass_context
@run_with_asyncio
async def helm_inventory(ctx: click.Context, repository: str) -> None:
    """Inventory available Helm chart versions."""
    config = ctx.obj["config"]

    async with aiohttp.ClientSession() as session:
        factory = Factory(config, session)
        inventory = factory.create_helm_inventory()
        print_yaml(await inventory.inventory(repository))


@main.command()
@click.pass_context
@run_with_asyncio
async def process(ctx: click.Context) -> None:
    """Process all configured repositories."""
    config = ctx.obj["config"]
    async with aiohttp.ClientSession() as session:
        factory = Factory(config, session)
        processor = factory.create_processor()
        await processor.process()


@main.command()
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Path to scan",
)
@click.pass_context
@run_with_asyncio
async def scan(ctx: click.Context, path: Path) -> None:
    """Scan a path for versions."""
    config = ctx.obj["config"]
    async with aiohttp.ClientSession() as session:
        factory = Factory(config, session)
        scanners = factory.create_all_scanners(path)
        results = {s.name: s.scan() for s in scanners}
        print_yaml({k: [u.to_dict() for u in v] for k, v in results.items()})
