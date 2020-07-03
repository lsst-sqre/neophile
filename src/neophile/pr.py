"""Construct a GitHub PR for a set of changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import ParseResult, urlparse

from gidgethub.aiohttp import GitHubAPI
from git import Actor, PushInfo, Remote, Repo

from neophile.exceptions import PushError

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from neophile.config import Configuration
    from neophile.update.base import Update
    from typing import List, Sequence

__all__ = ["PullRequester"]


@dataclass(frozen=True)
class CommitMessage:
    """A Git commit message."""

    title: str
    """The title of the message."""

    changes: List[str]
    """The changes represented by this commit."""

    def __str__(self) -> str:
        return f"{self.title}\n\n{self.body}"

    @property
    def body(self) -> str:
        """The body of the commit message."""
        return "- " + "\n- ".join(self.changes) + "\n"


@dataclass(frozen=True)
class GitHubRepo:
    """Path information for a GitHub repository."""

    owner: str
    """The owner of the repository."""

    repo: str
    """The name of the repository."""


class PullRequester:
    """Create GitHub pull requests.

    Parameters
    ----------
    path : `str`
        Path to the Git repository.
    config : `neophile.config.Configuration`
        neophile configuration.
    session : `aiohttp.ClientSession`
        The client session to use for requests.
    """

    def __init__(
        self, path: str, config: Configuration, session: ClientSession
    ) -> None:
        self._config = config
        self._github = GitHubAPI(
            session,
            config.github_user,
            oauth_token=config.github_token.get_secret_value(),
        )
        self._repo = Repo(path)

    async def make_pull_request(self, changes: Sequence[Update]) -> None:
        """Create a pull request for a list of changes.

        Parameters
        ----------
        changes : Sequence[`neophile.update.base.Update`]
            The changes.

        Raises
        ------
        neophile.exceptions.PushError
            Pushing the branch to GitHub failed.
        """
        message = await self._commit_changes(changes)
        await self._create_pr(message)

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
        return CommitMessage(title="Update dependencies", changes=descriptions)

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
        message = self._build_commit_message(changes)
        actor = await self._get_github_actor()
        self._repo.index.commit(str(message), author=actor, committer=actor)
        return message

    async def _create_pr(self, message: CommitMessage) -> None:
        """Create a new PR for the current branch.

        Parameters
        ----------
        title : `str`
            The title of the pull request message.
        body : `str`
            The body of the pull request message.

        Raises
        ------
        neophile.exceptions.PushError
            Pushing the branch to GitHub failed.
        """
        remote_url = self._get_authenticated_remote()
        github_repo = self._get_github_repo()
        branch = self._repo.head.ref.name

        remote = Remote.add(self._repo, "tmp-neophile", remote_url)
        try:
            push_info = remote.push(f"{branch}:{branch}")
            for result in push_info:
                if result.flags & PushInfo.ERROR:
                    msg = f"Pushing {branch} failed: {result.summary}"
                    raise PushError(msg)
        finally:
            Remote.remove(self._repo, "tmp-neophile")

        data = {
            "title": message.title,
            "body": message.body,
            "head": branch,
            "base": "master",
            "maintainer_can_modify": True,
            "draft": False,
        }
        await self._github.post(
            "/repos{/owner}{/repo}/pulls",
            url_vars={"owner": github_repo.owner, "repo": github_repo.repo},
            data=data,
        )

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
        return Actor(response["name"], response["email"])

    def _get_github_repo(self) -> GitHubRepo:
        """Get the GitHub repository.

        Done by parsing the URL of the origin remote.

        Returns
        -------
        repo : `GitHubRepo`
            GitHub repository information.
        """
        url = self._get_remote_url()
        _, owner, repo = url.path.split("/")
        if repo.endswith(".git"):
            repo = repo[: -len(".git")]
        return GitHubRepo(owner=owner, repo=repo)

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
