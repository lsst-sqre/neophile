"""Construct a GitHub PR for a set of changes."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from urllib.parse import ParseResult, urlencode, urlparse

from gidgethub import QueryError
from gidgethub.httpx import GitHubAPI
from git import PushInfo, Remote
from git.repo import Repo
from git.util import Actor
from httpx import AsyncClient

from .config import Config, GitHubRepository
from .exceptions import PushError
from .update.base import Update

__all__ = [
    "CommitMessage",
    "PullRequester",
]

_GRAPHQL_PR_ID = """
query FindPrId($owner:String!, $repo:String!, $pr_number:Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr_number) {
      id
    }
  }
}
"""

_GRAPHQL_ENABLE_AUTO_MERGE = """
mutation EnableAutoMerge($pr_id:ID!) {
  enablePullRequestAutoMerge(input: {pullRequestId: $pr_id}) {
    actor {
      login
    }
  }
}
"""


@dataclass(frozen=True)
class CommitMessage:
    """A Git commit message."""

    changes: list[str]
    """Changes represented by this commit."""

    title: ClassVar[str] = "[neophile] Update dependencies"
    """Title of the commit message, currently fixed for all commits."""

    def __str__(self) -> str:
        return f"{self.title}\n\n{self.body}"

    @property
    def body(self) -> str:
        """Body of the commit message."""
        return "- " + "\n- ".join(self.changes) + "\n"


class PullRequester:
    """Create GitHub pull requests.

    Parameters
    ----------
    config
        neophile configuration.
    http_client
        HTTP client to use for requests.
    """

    def __init__(self, config: Config, http_client: AsyncClient) -> None:
        self._config = config
        self._github = GitHubAPI(
            http_client,
            config.github_user,
            oauth_token=config.github_token.get_secret_value(),
        )

    async def make_pull_request(
        self, path: Path, changes: Sequence[Update]
    ) -> None:
        """Create or update a pull request for a list of changes.

        Parameters
        ----------
        path
            Path to the Git repository.
        changes
            The changes.

        Raises
        ------
        PushError
            Raised if pushing the branch to GitHub failed.
        """
        repo = Repo(str(path))
        github_repo = self._get_github_repo(repo)
        default_branch = await self._get_github_default_branch(github_repo)
        pr_number = await self._get_pr(github_repo, default_branch)

        message = await self._commit_changes(repo, changes)
        self._push_branch(repo)
        if pr_number is not None:
            await self._update_pr(github_repo, pr_number, message)
        else:
            await self._create_pr(
                repo=repo,
                github_repo=github_repo,
                base_branch=default_branch,
                message=message,
            )

    def _build_commit_message(
        self, changes: Sequence[Update]
    ) -> CommitMessage:
        """Build a commit message from a list of changes.

        Parameters
        ----------
        changes
            The changes.

        Returns
        -------
        CommitMessage
            Corresponding commit message.
        """
        descriptions = [change.description() for change in changes]
        return CommitMessage(changes=descriptions)

    async def _commit_changes(
        self, repo: Repo, changes: Sequence[Update]
    ) -> CommitMessage:
        """Commit a set of changes to the repository.

        The changes will be committed on the current branch.

        Parameters
        ----------
        repo
            Local Git repository.
        changes
            Changes to apply and commit.

        Returns
        -------
        CommitMessage
            Commit message of the commit.
        """
        actor = await self._get_github_actor()
        for change in changes:
            repo.index.add(str(change.path))
        message = self._build_commit_message(changes)
        repo.index.commit(str(message), author=actor, committer=actor)
        return message

    async def _create_pr(
        self,
        *,
        repo: Repo,
        github_repo: GitHubRepository,
        base_branch: str,
        message: CommitMessage,
    ) -> None:
        """Create a new PR for the current branch.

        Parameters
        ----------
        repo
            Local Git repository.
        github_repo
            GitHub repository in which to create the pull request.
        base_branch
            Branch of the repository to use as the base for the PR.
        message
            Commit message to use for the pull request.
        """
        branch = repo.head.ref.name
        data = {
            "title": message.title,
            "body": message.body,
            "head": branch,
            "base": base_branch,
            "maintainer_can_modify": True,
            "draft": False,
        }
        response = await self._github.post(
            "/repos{/owner}{/repo}/pulls",
            url_vars={"owner": github_repo.owner, "repo": github_repo.repo},
            data=data,
        )
        await self._enable_auto_merge(github_repo, str(response["number"]))

    async def _enable_auto_merge(
        self, github_repo: GitHubRepository, pr_number: str
    ) -> None:
        """Enable automerge for a PR.

        Failures are logged but do not raise an exception.

        Parameters
        ----------
        github_repo
            GitHub repository in which to create the pull request.
        pr_number
            Number of the PR in that repository to enable auto-merge for.
        """
        # Enabling auto-merge is only available via the GraphQL API with a
        # mutation.  To use that, we have to retrieve the GraphQL ID of the PR
        # we just created, and then send the mutation.
        try:
            response = await self._github.graphql(
                _GRAPHQL_PR_ID,
                owner=github_repo.owner,
                repo=github_repo.repo,
                pr_number=int(pr_number),
            )
            pr_id = response["repository"]["pullRequest"]["id"]
            response = await self._github.graphql(
                _GRAPHQL_ENABLE_AUTO_MERGE, pr_id=pr_id
            )
        except QueryError as e:
            msg = (
                f"cannot enable automerge for {github_repo.owner}/"
                f"{github_repo.repo}#{pr_number}: {e!s}"
            )
            logging.exception(msg)

    async def _get_github_actor(self) -> Actor:
        """Get authorship information for commits.

        Using the GitHub API, retrieve the name and email address of the user
        for which we have a GitHub token.  Use that to construct the Author
        information for a GitHub commit.

        Returns
        -------
        author
            Actor to use for commits.
        """
        response = await self._github.getitem("/user")
        if self._config.github_email:
            return Actor(response["name"], self._config.github_email)
        else:
            return Actor(response["name"], response["email"])

    async def _get_github_default_branch(
        self, github_repo: GitHubRepository
    ) -> str:
        """Get the main branch of the repository.

        Uses the default branch name if it exists, else ``main``.

        Parameters
        ----------
        github_repo
            GitHub repository in which to create the pull request.

        Returns
        -------
        str
            Name of the main branch.
        """
        repo = await self._github.getitem(
            "/repos{/owner}{/repo}",
            url_vars={"owner": github_repo.owner, "repo": github_repo.repo},
        )
        return repo.get("default_branch", "main")

    def _get_github_repo(self, repo: Repo) -> GitHubRepository:
        """Get the GitHub repository.

        Done by parsing the URL of the origin remote.

        Returns
        -------
        GitHubRepository
            GitHub repository information.
        """
        url = next(repo.remotes.origin.urls)
        if "//" in url:
            parsed_url = urlparse(url)
        else:
            path = url.rsplit(":", 1)[-1]
            parsed_url = urlparse(f"https://github.com/{path}")
        owner, github_repo = parsed_url.path.lstrip("/").split("/")
        if github_repo.endswith(".git"):
            github_repo = github_repo[: -len(".git")]
        return GitHubRepository(owner=owner, repo=github_repo)

    async def _get_pr(
        self, github_repo: GitHubRepository, base_branch: str
    ) -> str | None:
        """Get the pull request number of an existing neophile PR.

        Parameters
        ----------
        github_repo
            GitHub repository in which to search for a pull request.
        base_branch
            Base repository branch used to limit the search.

        Returns
        -------
        str or None
            PR number, or `None` if there is no open pull request from
            neophile.

        Notes
        -----
        The pull request is found by searching for all PRs in the open state
        whose branch is ``u/neophile``.
        """
        query = {
            "state": "open",
            "head": f"{github_repo.owner}:u/neophile",
            "base": base_branch,
        }

        prs = self._github.getiter(
            f"/repos{{/owner}}{{/repo}}/pulls?{urlencode(query)}",
            url_vars={"owner": github_repo.owner, "repo": github_repo.repo},
        )
        async for pr in prs:
            return str(pr["number"])
        return None

    def _get_remote_url(self, repo: Repo) -> ParseResult:
        """Get the parsed URL of the origin remote.

        The URL will be converted to https form.  https, ssh, and the SSH
        remote syntax used by Git are supported.

        Parameters
        ----------
        repo
            Local Git repository.

        Returns
        -------
        url
            Results of `~urllib.parse.urlparse` on the origin remote URL.
        """
        url = next(repo.remotes.origin.urls)
        if "//" in url:
            return urlparse(url)
        else:
            path = url.rsplit(":", 1)[-1]
            return urlparse(f"https://github.com/{path}")

    def _push_branch(self, repo: Repo) -> None:
        """Push the ``u/neophile`` branch to GitHub.

        Parameters
        ----------
        repo
            Local Git repository.

        Raises
        ------
        PushError
            Raised if pushing the branch to GitHub failed.
        """
        branch = repo.head.ref.name
        remote_url = next(repo.remotes.origin.urls)
        remote = Remote.add(repo, "tmp-neophile", remote_url)
        try:
            push_info = remote.push(f"{branch}:{branch}", force=True)
            for result in push_info:
                if result.flags & PushInfo.ERROR:
                    msg = f"Pushing {branch} failed: {result.summary}"
                    raise PushError(msg)
        finally:
            Remote.remove(repo, "tmp-neophile")

    async def _update_pr(
        self,
        github_repo: GitHubRepository,
        pr_number: str,
        message: CommitMessage,
    ) -> None:
        """Update an existing PR with a new commit message.

        Parameters
        ----------
        github_repo
            GitHub repository in which to create the pull request.
        pr_number
            Number of the pull request to update.
        message
            Commit message to use for the pull request.
        """
        data = {
            "title": message.title,
            "body": message.body,
        }
        await self._github.patch(
            "/repos{/owner}{/repo}/pulls{/pull_number}",
            url_vars={
                "owner": github_repo.owner,
                "repo": github_repo.repo,
                "pull_number": pr_number,
            },
            data=data,
        )
        await self._enable_auto_merge(github_repo, pr_number)
