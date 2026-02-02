"""
GitHub API Client

Core client for interacting with GitHub REST API v3.

Features:
- Token-based authentication
- Automatic rate limit handling
- Request retry logic with exponential backoff
- Pagination support
- Comprehensive error handling
- Response caching

Usage:
    client = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
    repos = await client.list_repositories()
    issues = await client.list_issues("owner/repo")
"""

import os
import time
import asyncio
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from alpha.integrations.github.exceptions import (
    GitHubError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubPermissionError,
    GitHubValidationError,
    GitHubNetworkError,
)
from alpha.integrations.github.models import (
    Repository,
    Issue,
    PullRequest,
    Comment,
    Commit,
    GitHubUser,
)


class GitHubClient:
    """
    GitHub REST API client with comprehensive error handling and rate limiting.

    Attributes:
        token (str): GitHub personal access token
        base_url (str): GitHub API base URL (default: https://api.github.com)
        timeout (int): Request timeout in seconds (default: 30)
        max_retries (int): Maximum number of retry attempts (default: 3)
        rate_limit_buffer (int): Reserve API calls for critical operations (default: 100)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_buffer: int = 100,
    ):
        """
        Initialize GitHub API client.

        Args:
            token: GitHub personal access token (reads from GITHUB_TOKEN env if not provided)
            base_url: GitHub API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            rate_limit_buffer: Number of API calls to reserve
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise GitHubAuthenticationError(
                "GitHub token not provided. Set GITHUB_TOKEN environment variable or pass token parameter."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_buffer = rate_limit_buffer

        # Initialize session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Set headers
        self.session.headers.update(
            {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Alpha-GitHub-Integration/1.0",
            }
        )

        # Rate limit tracking
        self._rate_limit_remaining = None
        self._rate_limit_reset = None
        self._cache: Dict[str, tuple] = {}  # (response, expiry_time)
        self._cache_ttl = 300  # 5 minutes default

    def _get_url(self, endpoint: str) -> str:
        """Construct full API URL from endpoint."""
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _check_rate_limit(self):
        """Check if rate limit allows new requests."""
        if self._rate_limit_remaining is not None:
            if self._rate_limit_remaining <= self.rate_limit_buffer:
                if self._rate_limit_reset:
                    reset_time = datetime.fromtimestamp(self._rate_limit_reset)
                    wait_seconds = (reset_time - datetime.now()).total_seconds()
                    if wait_seconds > 0:
                        raise GitHubRateLimitError(
                            f"GitHub API rate limit exceeded. Resets in {int(wait_seconds)}s",
                            reset_time=self._rate_limit_reset,
                        )

    def _update_rate_limit(self, response: requests.Response):
        """Update rate limit information from response headers."""
        self._rate_limit_remaining = int(
            response.headers.get("X-RateLimit-Remaining", 5000)
        )
        reset_time = response.headers.get("X-RateLimit-Reset")
        if reset_time:
            self._rate_limit_reset = int(reset_time)

    def _handle_error_response(self, response: requests.Response):
        """Handle error responses from GitHub API."""
        try:
            error_data = response.json()
            message = error_data.get("message", "Unknown error")
        except Exception:
            message = response.text or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise GitHubAuthenticationError(
                f"Authentication failed: {message}", status_code=401, response=error_data if 'error_data' in locals() else None
            )
        elif response.status_code == 403:
            # Check if it's rate limit or permission error
            if "rate limit" in message.lower():
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                raise GitHubRateLimitError(message, reset_time=reset_time, status_code=403)
            else:
                raise GitHubPermissionError(message, status_code=403)
        elif response.status_code == 404:
            raise GitHubNotFoundError(message, status_code=404)
        elif response.status_code == 422:
            raise GitHubValidationError(message, status_code=422, response=error_data if 'error_data' in locals() else None)
        else:
            raise GitHubError(message, status_code=response.status_code, response=error_data if 'error_data' in locals() else None)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        use_cache: bool = True,
    ) -> Dict:
        """
        Make HTTP request to GitHub API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON request body
            use_cache: Whether to use cached responses (GET only)

        Returns:
            Response data as dictionary

        Raises:
            GitHubError: On API errors
            GitHubRateLimitError: When rate limit exceeded
            GitHubNetworkError: On network failures
        """
        url = self._get_url(endpoint)
        cache_key = f"{method}:{url}:{str(params)}"

        # Check cache for GET requests
        if method == "GET" and use_cache and cache_key in self._cache:
            cached_response, expiry = self._cache[cache_key]
            if datetime.now() < expiry:
                return cached_response

        # Check rate limit before making request
        self._check_rate_limit()

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
            )

            # Update rate limit info
            self._update_rate_limit(response)

            # Handle errors
            if not response.ok:
                self._handle_error_response(response)

            # Parse response
            if response.status_code == 204:  # No content
                return {}

            data = response.json()

            # Cache GET responses
            if method == "GET" and use_cache:
                expiry = datetime.now() + timedelta(seconds=self._cache_ttl)
                self._cache[cache_key] = (data, expiry)

            return data

        except requests.exceptions.Timeout:
            raise GitHubNetworkError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise GitHubNetworkError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise GitHubNetworkError(f"Request failed: {str(e)}")

    def _paginate(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        max_pages: int = 10,
    ) -> List[Dict]:
        """
        Handle paginated API responses.

        Args:
            endpoint: API endpoint
            params: Query parameters
            max_pages: Maximum number of pages to fetch

        Returns:
            List of all items across pages
        """
        if params is None:
            params = {}

        params.setdefault("per_page", 100)  # Max items per page
        params.setdefault("page", 1)

        all_items = []
        page = 1

        while page <= max_pages:
            params["page"] = page
            data = self._make_request("GET", endpoint, params=params)

            if not data:
                break

            # Handle both list and dict responses
            if isinstance(data, list):
                all_items.extend(data)
                if len(data) < params["per_page"]:
                    break  # Last page
            else:
                # Some endpoints return {items: [...], total_count: ...}
                items = data.get("items", [])
                all_items.extend(items)
                if len(items) < params["per_page"]:
                    break

            page += 1

        return all_items

    # ===== Repository Operations =====

    def list_repositories(
        self,
        username: Optional[str] = None,
        type_filter: str = "all",
        sort: str = "updated",
        max_pages: int = 5,
    ) -> List[Repository]:
        """
        List repositories for authenticated user or specified username.

        Args:
            username: GitHub username (None for authenticated user)
            type_filter: Repository type (all, owner, public, private, member)
            sort: Sort order (created, updated, pushed, full_name)
            max_pages: Maximum pages to fetch

        Returns:
            List of Repository objects
        """
        if username:
            endpoint = f"users/{username}/repos"
            params = {"type": type_filter, "sort": sort}
        else:
            endpoint = "user/repos"
            params = {"affiliation": "owner,collaborator", "sort": sort}

        repos_data = self._paginate(endpoint, params=params, max_pages=max_pages)
        return [Repository.from_dict(r) for r in repos_data]

    def get_repository(self, owner: str, repo: str) -> Repository:
        """
        Get detailed information about a repository.

        Args:
            owner: Repository owner username
            repo: Repository name

        Returns:
            Repository object
        """
        endpoint = f"repos/{owner}/{repo}"
        data = self._make_request("GET", endpoint)
        return Repository.from_dict(data)

    # ===== Issue Operations =====

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
        sort: str = "created",
        direction: str = "desc",
        max_pages: int = 5,
    ) -> List[Issue]:
        """
        List issues for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            labels: Filter by labels
            sort: Sort field (created, updated, comments)
            direction: Sort direction (asc, desc)
            max_pages: Maximum pages to fetch

        Returns:
            List of Issue objects
        """
        endpoint = f"repos/{owner}/{repo}/issues"
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
        }

        if labels:
            params["labels"] = ",".join(labels)

        issues_data = self._paginate(endpoint, params=params, max_pages=max_pages)
        # Filter out pull requests (they appear in issues endpoint)
        issues_data = [i for i in issues_data if "pull_request" not in i]
        return [Issue.from_dict(i) for i in issues_data]

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Issue:
        """
        Get detailed information about an issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Issue object
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}"
        data = self._make_request("GET", endpoint)
        return Issue.from_dict(data)

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Issue:
        """
        Create a new issue.

        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body/description
            labels: List of label names
            assignees: List of usernames to assign

        Returns:
            Created Issue object
        """
        endpoint = f"repos/{owner}/{repo}/issues"
        json_data = {"title": title}

        if body:
            json_data["body"] = body
        if labels:
            json_data["labels"] = labels
        if assignees:
            json_data["assignees"] = assignees

        data = self._make_request("POST", endpoint, json_data=json_data)
        return Issue.from_dict(data)

    def add_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> Comment:
        """
        Add a comment to an issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: Comment text

        Returns:
            Created Comment object
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = self._make_request("POST", endpoint, json_data={"body": body})
        return Comment.from_dict(data)

    def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Issue:
        """
        Update an existing issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number to update
            title: New issue title (optional)
            body: New issue body/description (optional)
            state: New issue state - 'open' or 'closed' (optional)
            labels: New list of label names (optional)
            assignees: New list of usernames to assign (optional)

        Returns:
            Updated Issue object

        Raises:
            GitHubValidationError: If invalid parameters provided
            GitHubNotFoundError: If issue not found
            GitHubPermissionError: If no permission to update

        Example:
            # Update issue title and close it
            client.update_issue("owner", "repo", 42,
                              title="New Title",
                              state="closed")

            # Add labels
            client.update_issue("owner", "repo", 42,
                              labels=["bug", "urgent"])

            # Assign to users
            client.update_issue("owner", "repo", 42,
                              assignees=["user1", "user2"])
        """
        # Validate state parameter
        if state and state not in ["open", "closed"]:
            raise GitHubValidationError(
                f"Invalid state '{state}'. Must be 'open' or 'closed'."
            )

        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}"
        json_data = {}

        # Only include provided parameters
        if title is not None:
            json_data["title"] = title
        if body is not None:
            json_data["body"] = body
        if state is not None:
            json_data["state"] = state
        if labels is not None:
            json_data["labels"] = labels
        if assignees is not None:
            json_data["assignees"] = assignees

        if not json_data:
            raise GitHubValidationError(
                "At least one parameter (title, body, state, labels, or assignees) must be provided"
            )

        data = self._make_request("PATCH", endpoint, json_data=json_data)
        return Issue.from_dict(data)

    # ===== Pull Request Operations =====

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        sort: str = "created",
        direction: str = "desc",
        max_pages: int = 5,
    ) -> List[PullRequest]:
        """
        List pull requests for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            sort: Sort field (created, updated, popularity, long-running)
            direction: Sort direction (asc, desc)
            max_pages: Maximum pages to fetch

        Returns:
            List of PullRequest objects
        """
        endpoint = f"repos/{owner}/{repo}/pulls"
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
        }

        prs_data = self._paginate(endpoint, params=params, max_pages=max_pages)
        return [PullRequest.from_dict(pr) for pr in prs_data]

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> PullRequest:
        """
        Get detailed information about a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            PullRequest object
        """
        endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}"
        data = self._make_request("GET", endpoint)
        return PullRequest.from_dict(data)

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
        maintainer_can_modify: bool = True,
    ) -> PullRequest:
        """
        Create a new pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            title: Pull request title
            head: The name of the branch where your changes are implemented (source branch)
            base: The name of the branch you want to merge changes into (target branch)
            body: Pull request description
            draft: Create as draft pull request (default: False)
            maintainer_can_modify: Allow maintainers to edit the PR (default: True)

        Returns:
            Created PullRequest object

        Raises:
            GitHubValidationError: If branch doesn't exist or validation fails
            GitHubPermissionError: If user lacks permission to create PR

        Example:
            pr = client.create_pull_request(
                owner="octocat",
                repo="hello-world",
                title="Add new feature",
                head="feature-branch",
                base="main",
                body="This PR implements a new feature",
                draft=False
            )
        """
        endpoint = f"repos/{owner}/{repo}/pulls"
        json_data = {
            "title": title,
            "head": head,
            "base": base,
            "maintainer_can_modify": maintainer_can_modify,
        }

        if body:
            json_data["body"] = body

        if draft:
            json_data["draft"] = draft

        data = self._make_request("POST", endpoint, json_data=json_data)
        return PullRequest.from_dict(data)

    def update_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        base: Optional[str] = None,
    ) -> PullRequest:
        """
        Update an existing pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            title: New PR title (optional)
            body: New PR body/description (optional)
            state: New PR state - 'open' or 'closed' (optional)
            base: New base branch (optional)

        Returns:
            Updated PullRequest object

        Raises:
            GitHubValidationError: If invalid parameters provided
            GitHubNotFoundError: If PR not found
            GitHubPermissionError: If no permission to update

        Example:
            # Update PR title and body
            client.update_pull_request("owner", "repo", 42,
                                      title="New Title",
                                      body="Updated description")

            # Close PR
            client.update_pull_request("owner", "repo", 42, state="closed")
        """
        # Validate state parameter
        if state and state not in ["open", "closed"]:
            raise GitHubValidationError(
                f"Invalid state '{state}'. Must be 'open' or 'closed'."
            )

        endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}"
        json_data = {}

        # Only include provided parameters
        if title is not None:
            json_data["title"] = title
        if body is not None:
            json_data["body"] = body
        if state is not None:
            json_data["state"] = state
        if base is not None:
            json_data["base"] = base

        if not json_data:
            raise GitHubValidationError(
                "At least one parameter (title, body, state, or base) must be provided"
            )

        data = self._make_request("PATCH", endpoint, json_data=json_data)
        return PullRequest.from_dict(data)

    def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        merge_method: str = "merge",
    ) -> Dict[str, Any]:
        """
        Merge a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            commit_title: Title for merge commit (optional, uses PR title if not provided)
            commit_message: Extra detail for merge commit (optional)
            merge_method: Merge method - 'merge', 'squash', or 'rebase' (default: 'merge')

        Returns:
            Dict with merge result containing:
                - sha: SHA of merge commit
                - merged: Boolean indicating success
                - message: Status message

        Raises:
            GitHubValidationError: If invalid merge_method or PR not mergeable
            GitHubNotFoundError: If PR not found
            GitHubPermissionError: If no permission to merge

        Example:
            result = client.merge_pull_request("owner", "repo", 42,
                                              commit_title="Merge feature X",
                                              merge_method="squash")
            if result["merged"]:
                print(f"Merged! Commit SHA: {result['sha']}")
        """
        # Validate merge method
        valid_methods = ["merge", "squash", "rebase"]
        if merge_method not in valid_methods:
            raise GitHubValidationError(
                f"Invalid merge_method '{merge_method}'. Must be one of: {', '.join(valid_methods)}"
            )

        endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}/merge"
        json_data = {"merge_method": merge_method}

        if commit_title:
            json_data["commit_title"] = commit_title
        if commit_message:
            json_data["commit_message"] = commit_message

        data = self._make_request("PUT", endpoint, json_data=json_data)
        return data

    def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        event: str,
        body: Optional[str] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a review on a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            event: Review action - 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'
            body: Review summary comment (optional for COMMENT, required for APPROVE/REQUEST_CHANGES)
            comments: List of inline code review comments (optional)
                Each comment should have:
                - path: File path
                - position: Line position (deprecated, use line)
                - line: Line number in the diff
                - side: 'LEFT' or 'RIGHT' (which side of diff)
                - body: Comment text

        Returns:
            Dict with review details

        Raises:
            GitHubValidationError: If invalid event type or missing required body
            GitHubNotFoundError: If PR not found
            GitHubPermissionError: If no permission to review

        Example:
            # Approve PR
            client.create_review("owner", "repo", 42,
                               event="APPROVE",
                               body="Looks good!")

            # Request changes with inline comments
            client.create_review("owner", "repo", 42,
                               event="REQUEST_CHANGES",
                               body="Please address these issues",
                               comments=[{
                                   "path": "src/main.py",
                                   "line": 10,
                                   "side": "RIGHT",
                                   "body": "This variable should be renamed"
                               }])
        """
        # Validate event type
        valid_events = ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
        if event not in valid_events:
            raise GitHubValidationError(
                f"Invalid event '{event}'. Must be one of: {', '.join(valid_events)}"
            )

        # Body is required for APPROVE and REQUEST_CHANGES
        if event in ["APPROVE", "REQUEST_CHANGES"] and not body:
            raise GitHubValidationError(
                f"'body' is required when event is '{event}'"
            )

        endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        json_data = {"event": event}

        if body:
            json_data["body"] = body
        if comments:
            json_data["comments"] = comments

        data = self._make_request("POST", endpoint, json_data=json_data)
        return data

    def list_reviews(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        max_pages: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        List reviews on a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            max_pages: Maximum pages to fetch

        Returns:
            List of review dictionaries

        Example:
            reviews = client.list_reviews("owner", "repo", 42)
            for review in reviews:
                print(f"{review['user']['login']}: {review['state']}")
        """
        endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        reviews_data = self._paginate(endpoint, max_pages=max_pages)
        return reviews_data

    # ===== Commit Operations =====

    def list_commits(
        self,
        owner: str,
        repo: str,
        sha: Optional[str] = None,
        max_pages: int = 3,
    ) -> List[Commit]:
        """
        List commits for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            sha: Branch/tag/commit SHA (default: default branch)
            max_pages: Maximum pages to fetch

        Returns:
            List of Commit objects
        """
        endpoint = f"repos/{owner}/{repo}/commits"
        params = {}
        if sha:
            params["sha"] = sha

        commits_data = self._paginate(endpoint, params=params, max_pages=max_pages)
        return [Commit.from_dict(c) for c in commits_data]

    def get_commit(self, owner: str, repo: str, sha: str) -> Commit:
        """
        Get detailed information about a commit.

        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA

        Returns:
            Commit object
        """
        endpoint = f"repos/{owner}/{repo}/commits/{sha}"
        data = self._make_request("GET", endpoint)
        return Commit.from_dict(data)

    # ===== Utility Methods =====

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dict with rate limit information
        """
        data = self._make_request("GET", "rate_limit", use_cache=False)
        return data.get("rate", {})

    def validate_token(self) -> bool:
        """
        Validate the GitHub token.

        Returns:
            True if token is valid, False otherwise
        """
        try:
            self._make_request("GET", "user", use_cache=False)
            return True
        except GitHubAuthenticationError:
            return False

    def get_authenticated_user(self) -> GitHubUser:
        """
        Get information about the authenticated user.

        Returns:
            GitHubUser object for authenticated user
        """
        data = self._make_request("GET", "user", use_cache=False)
        return GitHubUser.from_dict(data)

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
