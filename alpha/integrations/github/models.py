"""
GitHub Data Models

Data classes representing GitHub entities (Repository, Issue, PullRequest, etc.)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class GitHubUser:
    """Represents a GitHub user."""

    login: str
    id: int
    avatar_url: str
    html_url: str
    type: str = "User"  # User or Organization
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "GitHubUser":
        """Create GitHubUser from API response."""
        return cls(
            login=data.get("login"),
            id=data.get("id"),
            avatar_url=data.get("avatar_url"),
            html_url=data.get("html_url"),
            type=data.get("type", "User"),
            name=data.get("name"),
            email=data.get("email"),
            bio=data.get("bio"),
        )


@dataclass
class Repository:
    """Represents a GitHub repository."""

    name: str
    full_name: str
    owner: GitHubUser
    html_url: str
    description: Optional[str]
    private: bool
    fork: bool
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    size: int
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    default_branch: str
    language: Optional[str] = None
    homepage: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    clone_url: str = ""
    ssh_url: str = ""
    archived: bool = False
    disabled: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Repository":
        """Create Repository from API response."""
        return cls(
            name=data.get("name"),
            full_name=data.get("full_name"),
            owner=GitHubUser.from_dict(data.get("owner", {})),
            html_url=data.get("html_url"),
            description=data.get("description"),
            private=data.get("private", False),
            fork=data.get("fork", False),
            created_at=datetime.fromisoformat(
                data.get("created_at", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data.get("updated_at", "").replace("Z", "+00:00")
            ),
            pushed_at=datetime.fromisoformat(
                data.get("pushed_at", "").replace("Z", "+00:00")
            ),
            size=data.get("size", 0),
            stargazers_count=data.get("stargazers_count", 0),
            watchers_count=data.get("watchers_count", 0),
            forks_count=data.get("forks_count", 0),
            open_issues_count=data.get("open_issues_count", 0),
            default_branch=data.get("default_branch", "main"),
            language=data.get("language"),
            homepage=data.get("homepage"),
            topics=data.get("topics", []),
            clone_url=data.get("clone_url", ""),
            ssh_url=data.get("ssh_url", ""),
            archived=data.get("archived", False),
            disabled=data.get("disabled", False),
        )


@dataclass
class Label:
    """Represents a GitHub label."""

    id: int
    name: str
    color: str
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Label":
        """Create Label from API response."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            color=data.get("color"),
            description=data.get("description"),
        )


@dataclass
class Milestone:
    """Represents a GitHub milestone."""

    id: int
    number: int
    title: str
    description: Optional[str]
    state: str
    open_issues: int
    closed_issues: int
    created_at: datetime
    due_on: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Milestone":
        """Create Milestone from API response."""
        due_on = data.get("due_on")
        if due_on:
            due_on = datetime.fromisoformat(due_on.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            number=data.get("number"),
            title=data.get("title"),
            description=data.get("description"),
            state=data.get("state"),
            open_issues=data.get("open_issues", 0),
            closed_issues=data.get("closed_issues", 0),
            created_at=datetime.fromisoformat(
                data.get("created_at", "").replace("Z", "+00:00")
            ),
            due_on=due_on,
        )


@dataclass
class Issue:
    """Represents a GitHub issue."""

    id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    user: GitHubUser
    labels: List[Label]
    assignees: List[GitHubUser]
    milestone: Optional[Milestone]
    comments: int
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    html_url: str
    repository_url: str

    @classmethod
    def from_dict(cls, data: dict) -> "Issue":
        """Create Issue from API response."""
        closed_at = data.get("closed_at")
        if closed_at:
            closed_at = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))

        milestone_data = data.get("milestone")
        milestone = Milestone.from_dict(milestone_data) if milestone_data else None

        return cls(
            id=data.get("id"),
            number=data.get("number"),
            title=data.get("title"),
            body=data.get("body"),
            state=data.get("state"),
            user=GitHubUser.from_dict(data.get("user", {})),
            labels=[Label.from_dict(l) for l in data.get("labels", [])],
            assignees=[GitHubUser.from_dict(a) for a in data.get("assignees", [])],
            milestone=milestone,
            comments=data.get("comments", 0),
            created_at=datetime.fromisoformat(
                data.get("created_at", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data.get("updated_at", "").replace("Z", "+00:00")
            ),
            closed_at=closed_at,
            html_url=data.get("html_url"),
            repository_url=data.get("repository_url", ""),
        )


@dataclass
class PullRequest:
    """Represents a GitHub pull request."""

    id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    user: GitHubUser
    head_ref: str
    base_ref: str
    draft: bool
    merged: bool
    mergeable: Optional[bool]
    mergeable_state: str
    labels: List[Label]
    assignees: List[GitHubUser]
    milestone: Optional[Milestone]
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime]
    closed_at: Optional[datetime]
    html_url: str
    commits: int = 0
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "PullRequest":
        """Create PullRequest from API response."""
        merged_at = data.get("merged_at")
        if merged_at:
            merged_at = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))

        closed_at = data.get("closed_at")
        if closed_at:
            closed_at = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))

        milestone_data = data.get("milestone")
        milestone = Milestone.from_dict(milestone_data) if milestone_data else None

        head = data.get("head", {})
        base = data.get("base", {})

        return cls(
            id=data.get("id"),
            number=data.get("number"),
            title=data.get("title"),
            body=data.get("body"),
            state=data.get("state"),
            user=GitHubUser.from_dict(data.get("user", {})),
            head_ref=head.get("ref", ""),
            base_ref=base.get("ref", ""),
            draft=data.get("draft", False),
            merged=data.get("merged", False),
            mergeable=data.get("mergeable"),
            mergeable_state=data.get("mergeable_state", "unknown"),
            labels=[Label.from_dict(l) for l in data.get("labels", [])],
            assignees=[GitHubUser.from_dict(a) for a in data.get("assignees", [])],
            milestone=milestone,
            created_at=datetime.fromisoformat(
                data.get("created_at", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data.get("updated_at", "").replace("Z", "+00:00")
            ),
            merged_at=merged_at,
            closed_at=closed_at,
            html_url=data.get("html_url"),
            commits=data.get("commits", 0),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            changed_files=data.get("changed_files", 0),
        )


@dataclass
class Comment:
    """Represents a GitHub comment (issue or PR)."""

    id: int
    body: str
    user: GitHubUser
    created_at: datetime
    updated_at: datetime
    html_url: str

    @classmethod
    def from_dict(cls, data: dict) -> "Comment":
        """Create Comment from API response."""
        return cls(
            id=data.get("id"),
            body=data.get("body"),
            user=GitHubUser.from_dict(data.get("user", {})),
            created_at=datetime.fromisoformat(
                data.get("created_at", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data.get("updated_at", "").replace("Z", "+00:00")
            ),
            html_url=data.get("html_url"),
        )


@dataclass
class Commit:
    """Represents a GitHub commit."""

    sha: str
    message: str
    author_name: str
    author_email: str
    author_date: datetime
    committer_name: str
    committer_email: str
    committer_date: datetime
    html_url: str
    parents: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Commit":
        """Create Commit from API response."""
        commit_data = data.get("commit", {})
        author = commit_data.get("author", {})
        committer = commit_data.get("committer", {})

        return cls(
            sha=data.get("sha"),
            message=commit_data.get("message", ""),
            author_name=author.get("name", ""),
            author_email=author.get("email", ""),
            author_date=datetime.fromisoformat(
                author.get("date", "").replace("Z", "+00:00")
            ),
            committer_name=committer.get("name", ""),
            committer_email=committer.get("email", ""),
            committer_date=datetime.fromisoformat(
                committer.get("date", "").replace("Z", "+00:00")
            ),
            html_url=data.get("html_url", ""),
            parents=[p.get("sha") for p in data.get("parents", [])],
        )


@dataclass
class Branch:
    """Represents a GitHub branch."""

    name: str
    commit_sha: str
    commit_url: str
    protected: bool

    @classmethod
    def from_dict(cls, data: dict) -> "Branch":
        """Create Branch from API response."""
        commit = data.get("commit", {})

        return cls(
            name=data.get("name"),
            commit_sha=commit.get("sha", ""),
            commit_url=commit.get("url", ""),
            protected=data.get("protected", False),
        )
