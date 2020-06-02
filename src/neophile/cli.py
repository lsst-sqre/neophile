"""Command-line interface."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import click
import yaml

from neophile.scanner import Scanner

if TYPE_CHECKING:
    from typing import Union

__all__ = ["main", "help", "scan"]


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
def help(ctx: click.Context, topic: Union[None, str]) -> None:
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
def scan() -> None:
    """Scan the current directory for versions."""
    scanner = Scanner(root=os.getcwd())
    results = scanner.scan()
    print(yaml.dump(results))
