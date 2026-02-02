# GitHub Integration Guide

**Version**: 1.0
**Last Updated**: 2026-02-03
**Phase**: 11.1 - Real-World Integrations

---

## Overview

Alpha's GitHub integration enables seamless interaction with GitHub repositories, issues, pull requests, commits, and branches directly from the command line. This integration eliminates context switching and enables powerful automation workflows.

### Key Features

- **Repository Management**: List, view, and clone repositories
- **Issue Tracking**: Create, update, search, and comment on issues
- **Pull Request Operations**: List, view, create, update, merge, and review PRs
- **Commit History**: Browse commits and view detailed commit information
- **Branch Management**: List and inspect branches with protection status
- **Rate Limit Management**: Automatic rate limiting with intelligent caching
- **Proactive Notifications**: Smart suggestions for GitHub operations (coming in Phase 11.3)

---

## Setup

### 1. Generate GitHub Personal Access Token

1. Visit [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click **Generate new token** → **Generate new token (classic)**
3. Set token name (e.g., "Alpha Assistant")
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:user` (Read user profile data)
   - ✅ `read:org` (Read organization membership)
5. Click **Generate token**
6. **Copy the token immediately** (you won't be able to see it again)

### 2. Configure Environment Variable

**Linux/macOS**:
```bash
export GITHUB_TOKEN="ghp_your_token_here"

# Make it permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (Command Prompt)**:
```cmd
setx GITHUB_TOKEN "ghp_your_token_here"
```

**Windows (PowerShell)**:
```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"

# Make it permanent
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'ghp_your_token_here', 'User')
```

### 3. Verify Configuration

```bash
# Start Alpha
alpha

# Check rate limit status (verifies token is valid)
You> github rate_limit
```

Expected output:
```
Rate Limit Status:
- Limit: 5000
- Remaining: 4998
- Reset: 2026-02-03 12:30:00
```

---

## Configuration

Edit `config.yaml` to customize GitHub integration behavior:

```yaml
integrations:
  github:
    enabled: true
    token_env_var: "GITHUB_TOKEN"
    default_org: null  # Optional: set default organization

    api:
      timeout: 30
      max_retries: 3
      rate_limit_buffer: 100

    cache:
      ttl: 300  # 5 minutes
      enabled: true

    pagination:
      repositories: 5
      issues: 5
      pull_requests: 5
      commits: 3
      branches: 5
```

---

## Usage

### Repository Operations

#### List Repositories

```bash
# List your repositories
You> github list_repos

# List another user's public repositories
You> github list_repos username=torvalds

# Filter by type (all, owner, public, private, member)
You> github list_repos type=owner

# Sort by (created, updated, pushed, full_name)
You> github list_repos sort=updated
```

#### Get Repository Information

```bash
# View repository details
You> github get_repo owner=facebook repo=react

# Natural language
You> Show me info about the React repository
```

**Output**:
- Repository name and description
- Stars, forks, watchers count
- Primary language
- Created/updated dates
- Default branch
- Clone URLs

#### Create Repository

```bash
# Create a personal repository
You> github create_repo name="my-project" private=true description="My awesome project"

# Create with templates
You> github create_repo name="python-app" auto_init=true gitignore_template="Python" license_template="mit"

# Create organization repository
You> github create_repo name="team-project" organization="myorg" private=false

# Natural language
You> Create a new private repository called "backend-api" with MIT license
```

**Parameters**:
- `name` (required): Repository name
- `private` (optional): Public (false) or private (true), default: false
- `description` (optional): Repository description
- `homepage` (optional): Project homepage URL
- `auto_init` (optional): Initialize with README, default: false
- `gitignore_template` (optional): Language name (e.g., "Python", "Node")
- `license_template` (optional): License identifier (e.g., "mit", "apache-2.0")
- `organization` (optional): Create under organization instead of user

#### Update Repository Settings

```bash
# Update description and homepage
You> github update_repo owner=me repo=myrepo description="Updated description" homepage="https://example.com"

# Change visibility to private
You> github update_repo owner=me repo=myrepo private=true

# Enable/disable features
You> github update_repo owner=me repo=myrepo has_issues=true has_wiki=false

# Change default branch
You> github update_repo owner=me repo=myrepo default_branch="main"

# Natural language
You> Make my repository "backend-api" private and add description "REST API backend"
```

**Parameters**:
- `name` (optional): Rename repository
- `description` (optional): Update description
- `homepage` (optional): Update homepage URL
- `private` (optional): Change visibility
- `has_issues` (optional): Enable/disable issues
- `has_wiki` (optional): Enable/disable wiki
- `has_projects` (optional): Enable/disable projects
- `default_branch` (optional): Change default branch
- `archived` (optional): Archive repository

#### Archive Repository

```bash
# Archive repository (safer than deleting)
You> github archive_repo owner=me repo=old-project

# Natural language
You> Archive my old-project repository
```

**Note**: Archived repositories become read-only. This is the recommended alternative to deletion for preserving history.

#### Delete Repository

```bash
# Delete repository permanently
You> github delete_repo owner=me repo=temporary-test

# Natural language
You> Delete my temporary-test repository
```

**⚠️ WARNING**: Deletion is permanent and cannot be undone. Consider archiving instead.

#### Transfer Repository

```bash
# Transfer to another user
You> github transfer_repo owner=me repo=project new_owner="newuser"

# Transfer to organization
You> github transfer_repo owner=me repo=project new_owner="myorg"

# Natural language
You> Transfer my project repository to organization "myorg"
```

**Requirements**:
- You must have admin permissions on the repository
- Target user/organization must accept the transfer
- Repository collaborators and teams will be updated automatically

#### Update Repository Topics

```bash
# Set repository topics
You> github update_topics owner=me repo=myrepo topics=["python", "api", "rest"]

# Clear all topics
You> github update_topics owner=me repo=myrepo topics=[]

# Natural language
You> Add topics "machine-learning" and "tensorflow" to my project
```

**Topic Rules**:
- Maximum 20 topics per repository
- Topics must be lowercase, alphanumeric (hyphens and underscores allowed)
- Each topic max 50 characters

---

### Issue Management

#### List Issues

```bash
# List open issues
You> github list_issues owner=microsoft repo=vscode

# Filter by state (open, closed, all)
You> github list_issues owner=facebook repo=react state=all

# Natural language
You> Show me all open bugs in the React repo
```

#### View Issue Details

```bash
# Get issue by number
You> github get_issue owner=facebook repo=react number=12345

# Natural language
You> What's issue #12345 about in React?
```

#### Create Issue

```bash
# Basic issue creation
You> github create_issue owner=me repo=myrepo title="Bug report" body="Description here"

# With labels and assignees
You> github create_issue owner=me repo=myrepo title="Feature request" body="Add dark mode" labels=["enhancement"] assignees=["username"]

# Natural language
You> Create an issue in my repo: "Fix authentication bug - users can't log in after password reset"
```

#### Update Issue

```bash
# Close an issue
You> github update_issue owner=me repo=myrepo number=42 state=closed

# Update title and body
You> github update_issue owner=me repo=myrepo number=42 title="New title" body="Updated description"

# Add labels
You> github update_issue owner=me repo=myrepo number=42 labels=["bug", "high-priority"]

# Add assignees
You> github update_issue owner=me repo=myrepo number=42 assignees=["developer1", "developer2"]
```

#### Add Comment

```bash
# Comment on an issue
You> github add_comment owner=me repo=myrepo number=42 body="Working on this now"

# Natural language
You> Add comment to issue #42: "Fixed in PR #43"
```

---

### Pull Request Operations

#### List Pull Requests

```bash
# List open PRs
You> github list_prs owner=facebook repo=react

# Filter by state (open, closed, all)
You> github list_prs owner=facebook repo=react state=merged

# Natural language
You> Show me open pull requests in React
```

#### View PR Details

```bash
# Get PR information
You> github get_pr owner=facebook repo=react number=12345

# Natural language
You> What's PR #12345 about?
```

**Output**:
- Title, body, author
- Source and target branches
- Merge status (mergeable, conflicts, checks passing)
- Review status
- Commits and file changes count

#### Create Pull Request

```bash
# Basic PR creation
You> github create_pr owner=me repo=myrepo title="Add feature" head=feature-branch base=main body="Implements feature XYZ"

# Draft PR
You> github create_pr owner=me repo=myrepo title="WIP: New feature" head=feature base=main draft=true

# Natural language
You> Create a PR from my feature-branch to main: "Add user authentication"
```

#### Update Pull Request

```bash
# Update PR title/body
You> github update_pr owner=me repo=myrepo number=42 title="New title" body="Updated description"

# Change base branch
You> github update_pr owner=me repo=myrepo number=42 base=develop

# Close PR
You> github update_pr owner=me repo=myrepo number=42 state=closed
```

#### Merge Pull Request

```bash
# Merge PR (standard merge commit)
You> github merge_pr owner=me repo=myrepo number=42

# Squash and merge
You> github merge_pr owner=me repo=myrepo number=42 merge_method=squash

# Rebase and merge
You> github merge_pr owner=me repo=myrepo number=42 merge_method=rebase

# With custom commit message
You> github merge_pr owner=me repo=myrepo number=42 commit_title="Feature: Add authentication" commit_message="Implements OAuth 2.0 authentication"
```

**Merge Methods**:
- `merge`: Creates a merge commit (default)
- `squash`: Squashes all commits into one
- `rebase`: Rebases and merges

#### Create Review

```bash
# Approve PR
You> github create_review owner=me repo=myrepo number=42 event=APPROVE body="Looks good!"

# Request changes
You> github create_review owner=me repo=myrepo number=42 event=REQUEST_CHANGES body="Please fix the tests"

# Comment without approval
You> github create_review owner=me repo=myrepo number=42 event=COMMENT body="Nice work!"

# With inline comments
You> github create_review owner=me repo=myrepo number=42 event=APPROVE body="LGTM" comments=[{"path": "src/auth.py", "line": 42, "body": "Consider adding error handling here"}]
```

**Review Events**:
- `APPROVE`: Approve the PR
- `REQUEST_CHANGES`: Request changes before merge
- `COMMENT`: Comment without approval/rejection

#### List Reviews

```bash
# Get all reviews on a PR
You> github list_reviews owner=me repo=myrepo number=42

# Natural language
You> Show me all reviews on PR #42
```

---

### Commit Operations

#### List Commits

```bash
# List recent commits
You> github list_commits owner=torvalds repo=linux

# List commits on specific branch
You> github list_commits owner=facebook repo=react sha=develop

# Natural language
You> Show me recent commits in the Linux kernel
```

#### Get Commit Details

```bash
# View commit information
You> github get_commit owner=torvalds repo=linux sha=abc123def

# Natural language
You> What's in commit abc123?
```

**Output**:
- Commit SHA and message
- Author and committer information
- Timestamp
- Parent commits
- Link to GitHub

---

### Branch Operations

#### List Branches

```bash
# List all branches
You> github list_branches owner=facebook repo=react

# Natural language
You> Show me all branches in React
```

**Output**:
- Branch name
- Latest commit SHA
- Protection status
- Commit URL

#### Get Branch Information

```bash
# View branch details
You> github get_branch owner=facebook repo=react branch=main

# Natural language
You> Is the main branch protected?
```

**Output**:
- Branch name
- Latest commit SHA and URL
- Protection status (true/false)

---

### Utility Operations

#### Check Rate Limit

```bash
You> github rate_limit
```

**Output**:
- API rate limit (5000 requests/hour for authenticated users)
- Remaining requests
- Reset time

**Tip**: Alpha automatically manages rate limits with a 100-request buffer for critical operations.

---

## Advanced Usage

### Batch Operations

```bash
# Check multiple PRs in sequence
You> List all open PRs in React, then show me details of PR #12345

# Workflow automation
You> Create an issue for bug XYZ, then create a branch feature/fix-xyz
```

### Natural Language Commands

Alpha understands natural language for GitHub operations:

```bash
You> Show me all my repositories
You> Create an issue in myrepo: "Fix login bug"
You> What's the status of PR #42 in React?
You> Merge PR #123 with squash method
You> Who reviewed PR #456?
You> Is the main branch protected in Linux kernel?
```

### Proactive Suggestions (Coming in Phase 11.3)

Alpha will soon proactively suggest GitHub operations based on your workflow:

- **Issue from error logs**: "I detected an error. Should I create a GitHub issue?"
- **Stale PR notifications**: "PR #42 has been open for 7 days without review"
- **CI/CD failure alerts**: "Tests failed on PR #123. View details?"
- **Review reminders**: "You have 3 PRs awaiting your review"

---

## Troubleshooting

### Authentication Errors

**Problem**: "GitHub token not configured" or "Authentication failed"

**Solution**:
1. Verify `GITHUB_TOKEN` environment variable is set:
   ```bash
   echo $GITHUB_TOKEN  # Linux/macOS
   echo %GITHUB_TOKEN%  # Windows CMD
   $env:GITHUB_TOKEN    # Windows PowerShell
   ```
2. Check token is valid on [GitHub Settings](https://github.com/settings/tokens)
3. Ensure token has required scopes (repo, read:user, read:org)
4. Restart Alpha after setting environment variable

### Rate Limit Exceeded

**Problem**: "Rate limit exceeded: 0 remaining"

**Solution**:
- Wait for rate limit reset (check with `github rate_limit`)
- GitHub allows 5000 requests/hour for authenticated users
- Alpha automatically caches responses for 5 minutes
- Increase `cache.ttl` in config.yaml for longer caching

### Resource Not Found

**Problem**: "Resource not found: repository/issue/PR doesn't exist"

**Solution**:
- Verify repository name format: `owner/repo` (e.g., `facebook/react`)
- Check you have permission to access the repository
- For private repos, ensure token has `repo` scope
- Verify issue/PR number is correct

### Network Timeouts

**Problem**: "Request timeout" or "Network error"

**Solution**:
- Check internet connection
- Verify GitHub is accessible: https://www.githubstatus.com/
- Increase timeout in config.yaml:
  ```yaml
  integrations:
    github:
      api:
        timeout: 60  # Increase from default 30s
  ```

---

## Best Practices

### Security

1. **Never commit tokens to Git**:
   - Use environment variables only
   - Add `.env` files to `.gitignore`
   - Rotate tokens regularly (every 90 days recommended)

2. **Use fine-grained tokens**:
   - Grant minimal required scopes
   - Set token expiration date
   - Limit token to specific repositories if possible

3. **Monitor token usage**:
   ```bash
   # Check rate limit frequently
   You> github rate_limit
   ```

### Performance Optimization

1. **Use caching effectively**:
   - Default 5-minute cache balances freshness and API usage
   - Increase `cache.ttl` for relatively static data (repos, branches)
   - Disable cache for real-time data (issue states, PR status)

2. **Limit pagination**:
   ```yaml
   pagination:
     repositories: 5  # Fetch only 5 pages (100 repos)
     issues: 3         # Fetch only 3 pages (90 issues)
   ```

3. **Batch related operations**:
   ```bash
   # Instead of: get_pr, then list_reviews, then list_commits
   # Use: get_pr (includes review count and commit count)
   ```

### Workflow Efficiency

1. **Set default organization**:
   ```yaml
   integrations:
     github:
       default_org: "mycompany"
   ```
   Now commands can omit organization: `github repos` lists mycompany repos

2. **Use natural language**:
   - Faster than memorizing exact command syntax
   - Alpha translates to optimal API calls
   - Example: "Show me failed CI runs on PR #42"

3. **Combine with other Alpha features**:
   - **Code Execution**: Analyze PR diffs with custom scripts
   - **Browser Automation**: Screenshot PR pages
   - **Workflows**: Automate PR review → merge → deploy pipeline

---

## Examples

### Example 1: Create Issue from Error

```bash
You> I'm getting "TypeError: Cannot read property 'name' of undefined" in auth.js line 42. Create a GitHub issue for this.

Alpha> I'll create an issue in your repository with the error details.

[Creates issue with stack trace, file location, and reproduction steps]

Alpha> Issue #127 created: "TypeError in auth.js line 42"
       View at: https://github.com/you/yourrepo/issues/127
```

### Example 2: Review and Merge PR Workflow

```bash
You> Show me details of PR #42

Alpha> PR #42: "Add user authentication"
       - Branch: feature/auth → main
       - Status: ✅ Checks passing, 2 approvals
       - Files: 8 changed (+342, -12)
       - Reviews: 2 approved, 0 changes requested

You> Looks good. Merge it with squash.

Alpha> Merging PR #42 with squash method...
       ✅ PR #42 merged successfully!
       Commit SHA: abc123def456
```

### Example 3: Monitor Repository Activity

```bash
You> What's new in the React repo?

Alpha> Recent activity in facebook/react:

       **Open Pull Requests** (3 new):
       - #12345: "Fix concurrent rendering bug" (2 hours ago)
       - #12346: "Improve error messages" (5 hours ago)
       - #12347: "Update documentation" (1 day ago)

       **Closed Issues** (5 today):
       - #10001: "Memory leak in useEffect" ✅ Fixed
       - #10002: "TypeScript types incorrect" ✅ Fixed
       ...

       **Latest Commits** (10 today):
       - abc123: "chore: update dependencies"
       - def456: "fix: resolve edge case in hooks"
       ...
```

---

## FAQ

**Q: Does Alpha support GitHub Enterprise?**
A: Yes. Set `integrations.github.api.base_url` to your enterprise URL in config.yaml.

**Q: Can I use multiple GitHub accounts?**
A: Currently, Alpha uses one token (GITHUB_TOKEN). Support for multiple accounts is planned for Phase 11.2.

**Q: Is my token stored securely?**
A: Yes. Alpha reads GITHUB_TOKEN from environment variables only, never stores it in files or logs.

**Q: Can Alpha create repositories?**
A: Not yet. Repository creation, deletion, and settings management are planned for Phase 11.2.

**Q: Does Alpha support GitHub Actions?**
A: GitHub Actions integration (trigger workflows, view logs) is planned for Phase 11.2.

**Q: Can I use Alpha to review code automatically?**
A: Basic PR review is supported. Advanced code review with LLM analysis is planned for Phase 11.3.

**Q: How much does GitHub API usage cost?**
A: GitHub API is free for personal use. You get 5000 requests/hour for authenticated users.

---

## Next Steps

- **Phase 11.2**: Advanced GitHub features (Actions, webhooks, repository management)
- **Phase 11.3**: Proactive GitHub intelligence (automated code review, CI/CD integration)
- **Phase 11.4**: Multi-account support and organization management

---

## Support

- **Documentation**: `/help github` in Alpha CLI
- **Issues**: Report bugs at [GitHub Issues](https://github.com/yourusername/alpha/issues)
- **Discussions**: Join community at [GitHub Discussions](https://github.com/yourusername/alpha/discussions)

---

**Version**: 1.0
**Status**: Production Ready ✅
**Last Updated**: 2026-02-03
