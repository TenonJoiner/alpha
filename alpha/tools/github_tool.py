"""
GitHub Tool - Integration with Alpha's tool system

Provides seamless access to GitHub operations through Alpha's tool framework.
"""

import os
import logging
from typing import Dict, Any, Optional, List

from alpha.tools.registry import Tool, ToolResult
from alpha.integrations.github import GitHubClient
from alpha.integrations.github.exceptions import (
    GitHubError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubNotFoundError,
)

logger = logging.getLogger(__name__)


class GitHubTool(Tool):
    """
    GitHub integration tool for repository, issue, and PR management.

    Supported operations:
    - list_repos: List user repositories
    - get_repo: Get repository information
    - create_repo: Create new repository
    - update_repo: Update repository settings
    - delete_repo: Delete repository (permanent)
    - archive_repo: Archive repository (safer alternative)
    - transfer_repo: Transfer repository to new owner
    - update_topics: Update repository topics
    - list_issues: List repository issues
    - get_issue: Get issue details
    - create_issue: Create new issue
    - update_issue: Update existing issue (title, body, state, labels, assignees)
    - add_comment: Add comment to issue
    - list_prs: List pull requests
    - get_pr: Get pull request details
    - create_pr: Create new pull request
    - update_pr: Update existing pull request (title, body, state, base)
    - merge_pr: Merge pull request (merge, squash, or rebase)
    - create_review: Create review on pull request (APPROVE, REQUEST_CHANGES, COMMENT)
    - list_reviews: List reviews on pull request
    - list_commits: List repository commits
    - get_commit: Get commit details
    - list_branches: List repository branches
    - get_branch: Get branch details
    - rate_limit: Check API rate limit status
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub tool.

        Args:
            token: GitHub personal access token (reads from GITHUB_TOKEN env if not provided)
        """
        super().__init__(
            name="github",
            description="Interact with GitHub repositories, issues, PRs, and commits",
        )

        self.token = token or os.getenv("GITHUB_TOKEN")
        self.client = None
        self._initialized = False

    def _ensure_client(self):
        """Ensure GitHub client is initialized."""
        if not self._initialized:
            if not self.token:
                raise GitHubAuthenticationError(
                    "GitHub token not configured. Set GITHUB_TOKEN environment variable."
                )
            self.client = GitHubClient(token=self.token)
            self._initialized = True

    async def execute(
        self,
        operation: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        number: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute GitHub operation.

        Args:
            operation: Operation to perform
            owner: Repository owner (for repo-specific operations)
            repo: Repository name (for repo-specific operations)
            number: Issue/PR number (for item-specific operations)
            **kwargs: Additional operation-specific parameters

        Returns:
            ToolResult with operation outcome

        Examples:
            # List repositories
            await execute(operation="list_repos")

            # Get repository info
            await execute(operation="get_repo", owner="torvalds", repo="linux")

            # List issues
            await execute(operation="list_issues", owner="facebook", repo="react", state="open")

            # Create issue
            await execute(operation="create_issue", owner="me", repo="myrepo",
                         title="Bug report", body="Description", labels=["bug"])

            # Get PR details
            await execute(operation="get_pr", owner="microsoft", repo="vscode", number=12345)
        """
        try:
            self._ensure_client()

            # ===== Repository Operations =====
            if operation == "list_repos":
                username = kwargs.get("username")
                type_filter = kwargs.get("type", "all")
                sort = kwargs.get("sort", "updated")
                max_pages = kwargs.get("max_pages", 5)

                repos = self.client.list_repositories(
                    username=username, type_filter=type_filter, sort=sort, max_pages=max_pages
                )

                return ToolResult(
                    success=True,
                    output={
                        "count": len(repos),
                        "repositories": [
                            {
                                "name": r.full_name,
                                "description": r.description,
                                "stars": r.stargazers_count,
                                "forks": r.forks_count,
                                "language": r.language,
                                "url": r.html_url,
                                "private": r.private,
                                "updated_at": r.updated_at.isoformat(),
                            }
                            for r in repos
                        ],
                    },
                    metadata={"operation": "list_repos", "username": username},
                )

            elif operation == "get_repo":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                repository = self.client.get_repository(owner, repo)

                return ToolResult(
                    success=True,
                    output={
                        "name": repository.full_name,
                        "description": repository.description,
                        "stars": repository.stargazers_count,
                        "forks": repository.forks_count,
                        "watchers": repository.watchers_count,
                        "open_issues": repository.open_issues_count,
                        "language": repository.language,
                        "default_branch": repository.default_branch,
                        "topics": repository.topics,
                        "clone_url": repository.clone_url,
                        "ssh_url": repository.ssh_url,
                        "created_at": repository.created_at.isoformat(),
                        "updated_at": repository.updated_at.isoformat(),
                        "pushed_at": repository.pushed_at.isoformat(),
                        "url": repository.html_url,
                        "private": repository.private,
                        "archived": repository.archived,
                    },
                    metadata={"operation": "get_repo", "repository": f"{owner}/{repo}"},
                )

            # ===== Repository Management Operations =====
            elif operation == "create_repo":
                name = kwargs.get("name")
                if not name:
                    return ToolResult(
                        success=False, output=None, error="name parameter required"
                    )

                private = kwargs.get("private", False)
                description = kwargs.get("description")
                homepage = kwargs.get("homepage")
                auto_init = kwargs.get("auto_init", False)
                gitignore_template = kwargs.get("gitignore_template")
                license_template = kwargs.get("license_template")
                organization = kwargs.get("organization")

                repository = self.client.create_repository(
                    name=name,
                    private=private,
                    description=description,
                    homepage=homepage,
                    auto_init=auto_init,
                    gitignore_template=gitignore_template,
                    license_template=license_template,
                    organization=organization,
                )

                return ToolResult(
                    success=True,
                    output={
                        "name": repository.full_name,
                        "url": repository.html_url,
                        "clone_url": repository.clone_url,
                        "private": repository.private,
                        "description": repository.description,
                    },
                    metadata={"operation": "create_repo", "repository": repository.full_name},
                )

            elif operation == "update_repo":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                # Extract update parameters
                name = kwargs.get("name")
                description = kwargs.get("description")
                homepage = kwargs.get("homepage")
                private = kwargs.get("private")
                has_issues = kwargs.get("has_issues")
                has_wiki = kwargs.get("has_wiki")
                has_projects = kwargs.get("has_projects")
                default_branch = kwargs.get("default_branch")
                archived = kwargs.get("archived")

                repository = self.client.update_repository(
                    owner=owner,
                    repo=repo,
                    name=name,
                    description=description,
                    homepage=homepage,
                    private=private,
                    has_issues=has_issues,
                    has_wiki=has_wiki,
                    has_projects=has_projects,
                    default_branch=default_branch,
                    archived=archived,
                )

                return ToolResult(
                    success=True,
                    output={
                        "name": repository.full_name,
                        "description": repository.description,
                        "homepage": repository.homepage,
                        "private": repository.private,
                        "archived": repository.archived,
                        "url": repository.html_url,
                    },
                    metadata={
                        "operation": "update_repo",
                        "repository": f"{owner}/{repo}",
                        "updated_fields": [
                            k for k, v in {
                                "name": name,
                                "description": description,
                                "homepage": homepage,
                                "private": private,
                                "has_issues": has_issues,
                                "has_wiki": has_wiki,
                                "has_projects": has_projects,
                                "default_branch": default_branch,
                                "archived": archived,
                            }.items() if v is not None
                        ],
                    },
                )

            elif operation == "delete_repo":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                success = self.client.delete_repository(owner, repo)

                return ToolResult(
                    success=success,
                    output={"deleted": success, "repository": f"{owner}/{repo}"},
                    metadata={"operation": "delete_repo", "repository": f"{owner}/{repo}"},
                )

            elif operation == "archive_repo":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                repository = self.client.archive_repository(owner, repo)

                return ToolResult(
                    success=True,
                    output={
                        "name": repository.full_name,
                        "archived": repository.archived,
                        "url": repository.html_url,
                    },
                    metadata={"operation": "archive_repo", "repository": f"{owner}/{repo}"},
                )

            elif operation == "transfer_repo":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                new_owner = kwargs.get("new_owner")
                if not new_owner:
                    return ToolResult(
                        success=False, output=None, error="new_owner parameter required"
                    )

                repository = self.client.transfer_repository(owner, repo, new_owner)

                return ToolResult(
                    success=True,
                    output={
                        "name": repository.full_name,
                        "old_owner": owner,
                        "new_owner": repository.owner.login,
                        "url": repository.html_url,
                    },
                    metadata={
                        "operation": "transfer_repo",
                        "repository": f"{owner}/{repo}",
                        "new_owner": new_owner,
                    },
                )

            elif operation == "update_topics":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                topics = kwargs.get("topics", [])
                if not isinstance(topics, list):
                    return ToolResult(
                        success=False,
                        output=None,
                        error="topics parameter must be a list",
                    )

                updated_topics = self.client.update_topics(owner, repo, topics)

                return ToolResult(
                    success=True,
                    output={"topics": updated_topics, "count": len(updated_topics)},
                    metadata={
                        "operation": "update_topics",
                        "repository": f"{owner}/{repo}",
                    },
                )

            # ===== Issue Operations =====
            elif operation == "list_issues":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                state = kwargs.get("state", "open")
                labels = kwargs.get("labels")
                sort = kwargs.get("sort", "created")
                direction = kwargs.get("direction", "desc")
                max_pages = kwargs.get("max_pages", 5)

                issues = self.client.list_issues(
                    owner,
                    repo,
                    state=state,
                    labels=labels,
                    sort=sort,
                    direction=direction,
                    max_pages=max_pages,
                )

                return ToolResult(
                    success=True,
                    output={
                        "count": len(issues),
                        "issues": [
                            {
                                "number": i.number,
                                "title": i.title,
                                "state": i.state,
                                "author": i.user.login,
                                "labels": [l.name for l in i.labels],
                                "comments": i.comments,
                                "created_at": i.created_at.isoformat(),
                                "updated_at": i.updated_at.isoformat(),
                                "url": i.html_url,
                            }
                            for i in issues
                        ],
                    },
                    metadata={
                        "operation": "list_issues",
                        "repository": f"{owner}/{repo}",
                        "state": state,
                    },
                )

            elif operation == "get_issue":
                if not owner or not repo or number is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner, repo, and number parameters required",
                    )

                issue = self.client.get_issue(owner, repo, number)

                return ToolResult(
                    success=True,
                    output={
                        "number": issue.number,
                        "title": issue.title,
                        "body": issue.body,
                        "state": issue.state,
                        "author": issue.user.login,
                        "labels": [l.name for l in issue.labels],
                        "assignees": [a.login for a in issue.assignees],
                        "milestone": issue.milestone.title if issue.milestone else None,
                        "comments": issue.comments,
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat(),
                        "closed_at": issue.closed_at.isoformat()
                        if issue.closed_at
                        else None,
                        "url": issue.html_url,
                    },
                    metadata={
                        "operation": "get_issue",
                        "repository": f"{owner}/{repo}",
                        "issue_number": number,
                    },
                )

            elif operation == "create_issue":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                title = kwargs.get("title")
                if not title:
                    return ToolResult(
                        success=False, output=None, error="title parameter required"
                    )

                body = kwargs.get("body")
                labels = kwargs.get("labels")
                assignees = kwargs.get("assignees")

                issue = self.client.create_issue(
                    owner, repo, title, body=body, labels=labels, assignees=assignees
                )

                return ToolResult(
                    success=True,
                    output={
                        "number": issue.number,
                        "title": issue.title,
                        "url": issue.html_url,
                        "state": issue.state,
                    },
                    metadata={
                        "operation": "create_issue",
                        "repository": f"{owner}/{repo}",
                    },
                )

            elif operation == "add_comment":
                if not owner or not repo or number is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner, repo, and number parameters required",
                    )

                body = kwargs.get("body")
                if not body:
                    return ToolResult(
                        success=False, output=None, error="body parameter required"
                    )

                comment = self.client.add_issue_comment(owner, repo, number, body)

                return ToolResult(
                    success=True,
                    output={
                        "id": comment.id,
                        "body": comment.body,
                        "author": comment.user.login,
                        "created_at": comment.created_at.isoformat(),
                        "url": comment.html_url,
                    },
                    metadata={
                        "operation": "add_comment",
                        "repository": f"{owner}/{repo}",
                        "issue_number": number,
                    },
                )

            elif operation == "update_issue":
                if not owner or not repo or number is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner, repo, and number parameters required",
                    )

                # Extract update parameters
                title = kwargs.get("title")
                body = kwargs.get("body")
                state = kwargs.get("state")
                labels = kwargs.get("labels")
                assignees = kwargs.get("assignees")

                # Validate that at least one parameter is provided
                if not any([title, body, state, labels, assignees]):
                    return ToolResult(
                        success=False,
                        output=None,
                        error="At least one of title, body, state, labels, or assignees must be provided",
                    )

                # Validate state parameter
                if state and state not in ["open", "closed"]:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Invalid state '{state}'. Must be 'open' or 'closed'",
                    )

                issue = self.client.update_issue(
                    owner=owner,
                    repo=repo,
                    issue_number=number,
                    title=title,
                    body=body,
                    state=state,
                    labels=labels,
                    assignees=assignees,
                )

                return ToolResult(
                    success=True,
                    output={
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "body": issue.body,
                        "labels": [label.name for label in issue.labels],
                        "assignees": [assignee.login for assignee in issue.assignees],
                        "author": issue.user.login,
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                        "url": issue.html_url,
                    },
                    metadata={
                        "operation": "update_issue",
                        "repository": f"{owner}/{repo}",
                        "issue_number": number,
                        "updated_fields": [
                            k for k, v in {
                                "title": title,
                                "body": body,
                                "state": state,
                                "labels": labels,
                                "assignees": assignees
                            }.items() if v is not None
                        ],
                    },
                )

            # ===== Pull Request Operations =====
            elif operation == "list_prs":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                state = kwargs.get("state", "open")
                sort = kwargs.get("sort", "created")
                direction = kwargs.get("direction", "desc")
                max_pages = kwargs.get("max_pages", 5)

                prs = self.client.list_pull_requests(
                    owner, repo, state=state, sort=sort, direction=direction, max_pages=max_pages
                )

                return ToolResult(
                    success=True,
                    output={
                        "count": len(prs),
                        "pull_requests": [
                            {
                                "number": pr.number,
                                "title": pr.title,
                                "state": pr.state,
                                "author": pr.user.login,
                                "head_ref": pr.head_ref,
                                "base_ref": pr.base_ref,
                                "draft": pr.draft,
                                "merged": pr.merged,
                                "mergeable": pr.mergeable,
                                "labels": [l.name for l in pr.labels],
                                "created_at": pr.created_at.isoformat(),
                                "updated_at": pr.updated_at.isoformat(),
                                "url": pr.html_url,
                            }
                            for pr in prs
                        ],
                    },
                    metadata={
                        "operation": "list_prs",
                        "repository": f"{owner}/{repo}",
                        "state": state,
                    },
                )

            elif operation == "get_pr":
                if not owner or not repo or number is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner, repo, and number parameters required",
                    )

                pr = self.client.get_pull_request(owner, repo, number)

                return ToolResult(
                    success=True,
                    output={
                        "number": pr.number,
                        "title": pr.title,
                        "body": pr.body,
                        "state": pr.state,
                        "author": pr.user.login,
                        "head_ref": pr.head_ref,
                        "base_ref": pr.base_ref,
                        "draft": pr.draft,
                        "merged": pr.merged,
                        "mergeable": pr.mergeable,
                        "mergeable_state": pr.mergeable_state,
                        "labels": [l.name for l in pr.labels],
                        "assignees": [a.login for a in pr.assignees],
                        "commits": pr.commits,
                        "additions": pr.additions,
                        "deletions": pr.deletions,
                        "changed_files": pr.changed_files,
                        "created_at": pr.created_at.isoformat(),
                        "updated_at": pr.updated_at.isoformat(),
                        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                        "url": pr.html_url,
                    },
                    metadata={
                        "operation": "get_pr",
                        "repository": f"{owner}/{repo}",
                        "pr_number": number,
                    },
                )

            elif operation == "create_pr":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                title = kwargs.get("title")
                if not title:
                    return ToolResult(
                        success=False, output=None, error="title parameter required"
                    )

                head = kwargs.get("head")
                if not head:
                    return ToolResult(
                        success=False, output=None, error="head parameter required (source branch)"
                    )

                base = kwargs.get("base")
                if not base:
                    return ToolResult(
                        success=False, output=None, error="base parameter required (target branch)"
                    )

                body = kwargs.get("body")
                draft = kwargs.get("draft", False)
                maintainer_can_modify = kwargs.get("maintainer_can_modify", True)

                pr = self.client.create_pull_request(
                    owner,
                    repo,
                    title,
                    head,
                    base,
                    body=body,
                    draft=draft,
                    maintainer_can_modify=maintainer_can_modify,
                )

                return ToolResult(
                    success=True,
                    output={
                        "number": pr.number,
                        "title": pr.title,
                        "url": pr.html_url,
                        "state": pr.state,
                        "head_ref": pr.head_ref,
                        "base_ref": pr.base_ref,
                        "draft": pr.draft,
                    },
                    metadata={
                        "operation": "create_pr",
                        "repository": f"{owner}/{repo}",
                    },
                )

            elif operation == "update_pr":
                if not owner or not repo or number is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner, repo, and number parameters required",
                    )

                # Extract update parameters
                title = kwargs.get("title")
                body = kwargs.get("body")
                state = kwargs.get("state")
                base = kwargs.get("base")

                # Validate that at least one parameter is provided
                if not any([title, body, state, base]):
                    return ToolResult(
                        success=False,
                        output=None,
                        error="At least one of title, body, state, or base must be provided",
                    )

                # Validate state parameter
                if state and state not in ["open", "closed"]:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Invalid state '{state}'. Must be 'open' or 'closed'",
                    )

                pr = self.client.update_pull_request(
                    owner=owner,
                    repo=repo,
                    pr_number=number,
                    title=title,
                    body=body,
                    state=state,
                    base=base,
                )

                return ToolResult(
                    success=True,
                    output={
                        "number": pr.number,
                        "title": pr.title,
                        "state": pr.state,
                        "body": pr.body,
                        "head_ref": pr.head_ref,
                        "base_ref": pr.base_ref,
                        "draft": pr.draft,
                        "merged": pr.merged,
                        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                        "url": pr.html_url,
                    },
                    metadata={
                        "operation": "update_pr",
                        "repository": f"{owner}/{repo}",
                        "pr_number": number,
                        "updated_fields": [
                            k for k, v in {
                                "title": title,
                                "body": body,
                                "state": state,
                                "base": base
                            }.items() if v is not None
                        ],
                    },
                )

            elif operation == "merge_pr":
                if not owner or not repo or number is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner, repo, and number parameters required",
                    )

                commit_title = kwargs.get("commit_title")
                commit_message = kwargs.get("commit_message")
                merge_method = kwargs.get("merge_method", "merge")

                # Validate merge method
                valid_methods = ["merge", "squash", "rebase"]
                if merge_method not in valid_methods:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Invalid merge_method '{merge_method}'. Must be one of: {', '.join(valid_methods)}",
                    )

                result = self.client.merge_pull_request(
                    owner=owner,
                    repo=repo,
                    pr_number=number,
                    commit_title=commit_title,
                    commit_message=commit_message,
                    merge_method=merge_method,
                )

                return ToolResult(
                    success=result.get("merged", False),
                    output={
                        "sha": result.get("sha"),
                        "merged": result.get("merged", False),
                        "message": result.get("message", ""),
                        "merge_method": merge_method,
                    },
                    metadata={
                        "operation": "merge_pr",
                        "repository": f"{owner}/{repo}",
                        "pr_number": number,
                    },
                )

            elif operation == "create_review":
                if not owner or not repo or number is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner, repo, and number parameters required",
                    )

                event = kwargs.get("event")
                if not event:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="event parameter required (APPROVE, REQUEST_CHANGES, or COMMENT)",
                    )

                # Validate event type
                valid_events = ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
                if event not in valid_events:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Invalid event '{event}'. Must be one of: {', '.join(valid_events)}",
                    )

                body = kwargs.get("body")
                comments = kwargs.get("comments")

                # Body is required for APPROVE and REQUEST_CHANGES
                if event in ["APPROVE", "REQUEST_CHANGES"] and not body:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"'body' is required when event is '{event}'",
                    )

                review = self.client.create_review(
                    owner=owner,
                    repo=repo,
                    pr_number=number,
                    event=event,
                    body=body,
                    comments=comments,
                )

                return ToolResult(
                    success=True,
                    output={
                        "id": review.get("id"),
                        "state": review.get("state"),
                        "body": review.get("body"),
                        "user": review.get("user", {}).get("login"),
                        "submitted_at": review.get("submitted_at"),
                        "html_url": review.get("html_url"),
                    },
                    metadata={
                        "operation": "create_review",
                        "repository": f"{owner}/{repo}",
                        "pr_number": number,
                        "event": event,
                    },
                )

            elif operation == "list_reviews":
                if not owner or not repo or number is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner, repo, and number parameters required",
                    )

                max_pages = kwargs.get("max_pages", 3)

                reviews = self.client.list_reviews(
                    owner=owner,
                    repo=repo,
                    pr_number=number,
                    max_pages=max_pages,
                )

                return ToolResult(
                    success=True,
                    output={
                        "count": len(reviews),
                        "reviews": [
                            {
                                "id": r.get("id"),
                                "state": r.get("state"),
                                "body": r.get("body"),
                                "user": r.get("user", {}).get("login"),
                                "submitted_at": r.get("submitted_at"),
                                "html_url": r.get("html_url"),
                            }
                            for r in reviews
                        ],
                    },
                    metadata={
                        "operation": "list_reviews",
                        "repository": f"{owner}/{repo}",
                        "pr_number": number,
                    },
                )

            # ===== Commit Operations =====
            elif operation == "list_commits":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                sha = kwargs.get("sha")
                max_pages = kwargs.get("max_pages", 3)

                commits = self.client.list_commits(owner, repo, sha=sha, max_pages=max_pages)

                return ToolResult(
                    success=True,
                    output={
                        "count": len(commits),
                        "commits": [
                            {
                                "sha": c.sha[:8],
                                "message": c.message.split("\n")[0],
                                "author": c.author_name,
                                "date": c.author_date.isoformat(),
                                "url": c.html_url,
                            }
                            for c in commits
                        ],
                    },
                    metadata={
                        "operation": "list_commits",
                        "repository": f"{owner}/{repo}",
                        "branch": sha or "default",
                    },
                )

            elif operation == "get_commit":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                sha = kwargs.get("sha")
                if not sha:
                    return ToolResult(
                        success=False, output=None, error="sha parameter required"
                    )

                commit = self.client.get_commit(owner, repo, sha)

                return ToolResult(
                    success=True,
                    output={
                        "sha": commit.sha,
                        "message": commit.message,
                        "author": {
                            "name": commit.author_name,
                            "email": commit.author_email,
                            "date": commit.author_date.isoformat(),
                        },
                        "committer": {
                            "name": commit.committer_name,
                            "email": commit.committer_email,
                            "date": commit.committer_date.isoformat(),
                        },
                        "parents": commit.parents,
                        "url": commit.html_url,
                    },
                    metadata={
                        "operation": "get_commit",
                        "repository": f"{owner}/{repo}",
                        "sha": sha,
                    },
                )

            # ===== Branch Operations =====
            elif operation == "list_branches":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                max_pages = kwargs.get("max_pages", 5)

                branches = self.client.list_branches(owner, repo, max_pages=max_pages)

                return ToolResult(
                    success=True,
                    output={
                        "count": len(branches),
                        "branches": [
                            {
                                "name": b.name,
                                "commit_sha": b.commit_sha[:8],
                                "protected": b.protected,
                                "commit_url": b.commit_url,
                            }
                            for b in branches
                        ],
                    },
                    metadata={
                        "operation": "list_branches",
                        "repository": f"{owner}/{repo}",
                    },
                )

            elif operation == "get_branch":
                if not owner or not repo:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="owner and repo parameters required",
                    )

                branch = kwargs.get("branch")
                if not branch:
                    return ToolResult(
                        success=False, output=None, error="branch parameter required"
                    )

                branch_obj = self.client.get_branch(owner, repo, branch)

                return ToolResult(
                    success=True,
                    output={
                        "name": branch_obj.name,
                        "commit_sha": branch_obj.commit_sha,
                        "commit_url": branch_obj.commit_url,
                        "protected": branch_obj.protected,
                    },
                    metadata={
                        "operation": "get_branch",
                        "repository": f"{owner}/{repo}",
                        "branch": branch,
                    },
                )

            # ===== Utility Operations =====
            elif operation == "rate_limit":
                rate_limit = self.client.get_rate_limit()

                return ToolResult(
                    success=True,
                    output={
                        "limit": rate_limit.get("limit"),
                        "remaining": rate_limit.get("remaining"),
                        "reset": rate_limit.get("reset"),
                        "used": rate_limit.get("used"),
                    },
                    metadata={"operation": "rate_limit"},
                )

            else:
                return ToolResult(
                    success=False, output=None, error=f"Unknown operation: {operation}"
                )

        except GitHubAuthenticationError as e:
            logger.error(f"GitHub authentication error: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Authentication failed: {str(e)}",
            )

        except GitHubRateLimitError as e:
            logger.warning(f"GitHub rate limit exceeded: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Rate limit exceeded: {str(e)}",
            )

        except GitHubNotFoundError as e:
            logger.warning(f"GitHub resource not found: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Resource not found: {str(e)}",
            )

        except GitHubError as e:
            logger.error(f"GitHub API error: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=f"GitHub API error: {str(e)}",
            )

        except Exception as e:
            logger.error(f"Unexpected error in GitHub tool: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=f"Unexpected error: {str(e)}",
            )

    def __del__(self):
        """Cleanup on deletion."""
        if self.client:
            self.client.close()
