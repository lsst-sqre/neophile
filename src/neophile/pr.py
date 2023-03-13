"""Construct a GitHub PR for a set of changes."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlencode, urlparse

from gidgethub import QueryError
from gidgethub.aiohttp import GitHubAPI
from git import Actor, PushInfo, Remote, Repo

from neophile.config import GitHubRepository
from neophile.exceptions import PushError

if TYPE_CHECKING:
    from pathlib import Path
    from typing import ClassVar, List, Optional, Sequence
    from urllib.parse import ParseResult

    from aiohttp import ClientSession

    from neophile.config import Configuration
    from neophile.update.base import Update

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

    changes: List[str]
    """The changes represented by this commit."""

    title: ClassVar[str] = "[neophile] Update dependencies"
    """The title of the commit message, currently fixed for all commits."""

    def __str__(self) -> str:
        return f"{self.title}\n\n{self.body}"

    @property
    def body(self) -> str:
        """The body of the commit message."""
        return "- " + "\n- ".join(self.changes) + "\n"


class PullRequester:
    """Create GitHub pull requests.

    Parameters
    ----------
    path : `pathlib.Path`
        Path to the Git repository.
    config : `neophile.config.Configuration`
        neophile configuration.
    session : `aiohttp.ClientSession`
        The client session to use for requests.
    """

    def __init__(
        self, path: Path, config: Configuration, session: ClientSession
    ) -> None:
        self._config = config
        self._github = GitHubAPI(
            session,
            config.github_user,
            oauth_token=config.github_token.get_secret_value(),
        )
        self._repo = Repo(str(path))

    async def make_pull_request(self, changes: Sequence[Update]) -> None:
        """Create or update a pull request for a list of changes.

        Parameters
        ----------
        changes : Sequence[`neophile.update.base.Update`]
            The changes.

        Raises
        ------
        neophile.exceptions.PushError
            Pushing the branch to GitHub failed.
        """
        github_repo = self._get_github_repo()
        default_branch = await self._get_github_default_branch(github_repo)
        pr_number = await self._get_pr(github_repo, default_branch)

        message = await self._commit_changes(changes)
        self._push_branch()
        if pr_number is not None:
            await self._update_pr(github_repo, pr_number, message)
        else:
            await self._create_pr(github_repo, default_branch, message)

    def _build_commit_message(
        self, changes: Sequence[Update]
    ) -> CommitMessage:
        """Build a commit message from a list of changes.

        Parameters
        ----------
        changes : Sequence[`neophile.update.base.Update`]
            The changes.

        Returns
        -------
        message : `CommitMessage`
            The corresponding commit message.
        """
        descriptions = [change.description() for change in changes]
        return CommitMessage(changes=descriptions)

    async def _commit_changes(
        self, changes: Sequence[Update]
    ) -> CommitMessage:
        """Commit a set of changes to the repository.

        The changes will be committed on the current branch.

        Parameters
        ----------
        changes : Sequence[`neophile.update.base.Update`]
            The changes to apply and commit.

        Returns
        -------
        message : `CommitMessage`
            The commit message of the commit.
        """
        actor = await self._get_github_actor()
        for change in changes:
            self._repo.index.add(str(change.path))
        message = self._build_commit_message(changes)
        self._repo.index.commit(str(message), author=actor, committer=actor)
        return message

    async def _create_pr(
        self,
        github_repo: GitHubRepository,
        base_branch: str,
        message: CommitMessage,
    ) -> None:
        """Create a new PR for the current branch.

        Parameters
        ----------
        github_repo : `neophile.config.GitHubRepository`
            GitHub repository in which to create the pull request.
        base_branch : `str`
            The branch of the repository to use as the base for the PR.
        message : `CommitMessage`
            The commit message to use for the pull request.
        """
        branch = self._repo.head.ref.name
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

        Parameters
        ----------
        github_repo : `neophile.config.GitHubRepository`
            GitHub repository in which to create the pull request.
        pr_number : `str`
            The number of the PR in that repository to enable auto-merge for.
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
                f"{github_repo.repo}#{pr_number}: {str(e)}"
            )
            logging.warning(msg)

    def _get_authenticated_remote(self) -> str:
        """Get the URL with authentication credentials of the origin remote.

        Supports an ssh URL, an https URL, or the SSH syntax that Git
        understands (user@host:path).

        Returns
        -------
        url : `str`
            A URL suitable for an authenticated push of a new branch.
        """
        url = self._get_remote_url()
        token = self._config.github_token.get_secret_value()
        auth = f"{self._config.github_user}:{token}"
        host = url.netloc.rsplit("@", 1)[-1]
        url = url._replace(scheme="https", netloc=f"{auth}@{host}")
        return url.geturl()

    async def _get_github_actor(self) -> Actor:
        """Get authorship information for commits.

        Using the GitHub API, retrieve the name and email address of the user
        for which we have a GitHub token.  Use that to construct the Author
        information for a GitHub commit.

        Returns
        -------
        author : `git.objects.util.Actor`
            The actor to use for commits.
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
        github_repo : `neophile.config.GitHubRepository`
            GitHub repository in which to create the pull request.

        Returns
        -------
        branch : `str`
            The name of the main branch.
        """
        repo = await self._github.getitem(
            "/repos{/owner}{/repo}",
            url_vars={"owner": github_repo.owner, "repo": github_repo.repo},
        )
        return repo.get("default_branch", "main")

    def _get_github_repo(self) -> GitHubRepository:
        """Get the GitHub repository.

        Done by parsing the URL of the origin remote.

        Returns
        -------
        repo : `neophile.config.GitHubRepository`
            GitHub repository information.
        """
        url = self._get_remote_url()
        _, owner, repo = url.path.split("/")
        if repo.endswith(".git"):
            repo = repo[: -len(".git")]
        return GitHubRepository(owner=owner, repo=repo)

    async def _get_pr(
        self, github_repo: GitHubRepository, base_branch: str
    ) -> Optional[str]:
        """Get the pull request number of an existing neophile PR.

        Parameters
        ----------
        github_repo : `neophile.config.GitHubRepository`
            GitHub repository in which to search for a pull request.
        bsae_branch : `str`
            The base repository branch used to limit the search.

        Returns
        -------
        pr_number : `str` or `None`
            The PR number or `None` if there is no open pull request from
            neophile.

        Notes
        -----
        The pull request is found by searching for all PRs in the open state
        whose branch is u/neophile.
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

    def _get_remote_url(self) -> ParseResult:
        """Get the parsed URL of the origin remote.

        The URL will be converted to https form.  https, ssh, and the SSH
        remote syntax used by Git are supported.

        Returns
        -------
        url : `str`
            The results of `~urllib.parse.urlparse` on the origin remote URL.
        """
        url = next(self._repo.remotes.origin.urls)
        if "//" in url:
            return urlparse(url)
        else:
            path = url.rsplit(":", 1)[-1]
            return urlparse(f"https://github.com/{path}")

    def _push_branch(self) -> None:
        """Push the u/neophile branch to GitHub.

        Raises
        ------
        neophile.exceptions.PushError
            Pushing the branch to GitHub failed.
        """
        branch = self._repo.head.ref.name
        remote_url = self._get_authenticated_remote()
        remote = Remote.add(self._repo, "tmp-neophile", remote_url)
        try:
            push_info = remote.push(f"{branch}:{branch}", force=True)
            for result in push_info:
                if result.flags & PushInfo.ERROR:
                    msg = f"Pushing {branch} failed: {result.summary}"
                    raise PushError(msg)
        finally:
            Remote.remove(self._repo, "tmp-neophile")

    async def _update_pr(
        self,
        github_repo: GitHubRepository,
        pr_number: str,
        message: CommitMessage,
    ) -> None:
        """Update an existing PR with a new commit message.

        Parameters
        ----------
        github_repo : `neophile.config.GitHubRepository`
            GitHub repository in which to create the pull request.
        pr_number : `str`
            The number of the pull request to update.
        message : `CommitMessage`
            The commit message to use for the pull request.
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
