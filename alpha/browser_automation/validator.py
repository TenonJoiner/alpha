"""
Alpha - Page Validator

Security validation for browser navigation and actions.
"""

import logging
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation check."""
    valid: bool
    reason: Optional[str] = None
    severity: str = "info"  # info, warning, error
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PageValidator:
    """
    Validates browser navigation and actions for security.

    Features:
    - URL validation and whitelisting/blacklisting
    - Protocol validation (http/https only)
    - Local network blocking
    - Dangerous operation detection
    - Content policy enforcement
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize page validator.

        Args:
            config: Browser automation configuration
        """
        self.config = config or {}
        self.security_config = self.config.get("security", {})

        # Load blacklist
        self.url_blacklist = self.security_config.get("url_blacklist", [
            "*.onion",
            "localhost",
            "127.0.0.1",
            "0.0.0.0"
        ])

        # Convert glob patterns to regex
        self.blacklist_patterns = [
            self._glob_to_regex(pattern) for pattern in self.url_blacklist
        ]

        logger.info(f"PageValidator initialized with {len(self.url_blacklist)} blacklist rules")

    def _glob_to_regex(self, pattern: str) -> re.Pattern:
        """Convert glob pattern to regex."""
        # Escape special chars except *
        escaped = pattern.replace(".", r"\.")
        # Convert * to regex
        regex_pattern = escaped.replace("*", ".*")
        return re.compile(f"^{regex_pattern}$", re.IGNORECASE)

    def validate_url(self, url: str) -> ValidationResult:
        """
        Validate a URL for safety.

        Args:
            url: URL to validate

        Returns:
            ValidationResult
        """
        # Check if validation is enabled
        if not self.security_config.get("validate_urls", True):
            return ValidationResult(valid=True, reason="Validation disabled")

        try:
            parsed = urlparse(url)
        except Exception as e:
            return ValidationResult(
                valid=False,
                reason=f"Invalid URL format: {e}",
                severity="error"
            )

        # Check protocol
        if parsed.scheme not in ["http", "https"]:
            # Check if file:// is allowed
            if parsed.scheme == "file":
                if not self.security_config.get("allow_file_access", False):
                    return ValidationResult(
                        valid=False,
                        reason="file:// URLs not allowed",
                        severity="error"
                    )
            else:
                return ValidationResult(
                    valid=False,
                    reason=f"Unsupported protocol: {parsed.scheme}",
                    severity="error"
                )

        # Check for local networks
        if not self.security_config.get("allow_local_networks", False):
            hostname = parsed.hostname or ""
            if self._is_local_address(hostname):
                return ValidationResult(
                    valid=False,
                    reason=f"Local network access not allowed: {hostname}",
                    severity="error"
                )

        # Check blacklist
        full_url = url.lower()
        hostname = (parsed.hostname or "").lower()

        for pattern in self.blacklist_patterns:
            if pattern.match(hostname) or pattern.match(full_url):
                return ValidationResult(
                    valid=False,
                    reason=f"URL matches blacklist pattern",
                    severity="error",
                    metadata={"hostname": hostname}
                )

        return ValidationResult(
            valid=True,
            reason="URL validation passed",
            metadata={"hostname": hostname, "scheme": parsed.scheme}
        )

    def _is_local_address(self, hostname: str) -> bool:
        """Check if hostname is a local address."""
        local_patterns = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
        ]

        hostname_lower = hostname.lower()

        # Check exact matches
        if hostname_lower in local_patterns:
            return True

        # Check 127.x.x.x range
        if hostname_lower.startswith("127."):
            return True

        # Check 10.x.x.x (private network)
        if hostname_lower.startswith("10."):
            return True

        # Check 192.168.x.x (private network)
        if hostname_lower.startswith("192.168."):
            return True

        # Check 172.16.x.x - 172.31.x.x (private network)
        if hostname_lower.startswith("172."):
            try:
                second_octet = int(hostname.split(".")[1])
                if 16 <= second_octet <= 31:
                    return True
            except (ValueError, IndexError):
                pass

        return False

    def validate_action(
        self,
        action: str,
        parameters: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Validate a browser action for safety.

        Args:
            action: Action name (navigate, click, fill_form, etc.)
            parameters: Action parameters

        Returns:
            ValidationResult
        """
        parameters = parameters or {}

        # Validate based on action type
        if action == "navigate":
            url = parameters.get("url")
            if not url:
                return ValidationResult(
                    valid=False,
                    reason="Missing URL parameter",
                    severity="error"
                )
            return self.validate_url(url)

        elif action == "execute_script":
            # Script execution requires extra validation
            script = parameters.get("script", "")

            # Check for dangerous operations
            dangerous_patterns = [
                r"eval\s*\(",
                r"Function\s*\(",
                r"setTimeout\s*\(",
                r"setInterval\s*\(",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, script, re.IGNORECASE):
                    return ValidationResult(
                        valid=False,
                        reason=f"Potentially dangerous script pattern detected",
                        severity="warning",
                        metadata={"pattern": pattern}
                    )

        elif action == "click":
            # Click validation
            selector = parameters.get("selector")
            if not selector:
                return ValidationResult(
                    valid=False,
                    reason="Missing selector parameter",
                    severity="error"
                )

        elif action == "fill_form":
            # Form fill validation
            data = parameters.get("data")
            if not data or not isinstance(data, dict):
                return ValidationResult(
                    valid=False,
                    reason="Invalid form data",
                    severity="error"
                )

        # Default: allow action
        return ValidationResult(
            valid=True,
            reason=f"Action '{action}' validation passed"
        )

    def validate_selector(self, selector: str) -> ValidationResult:
        """
        Validate a CSS selector.

        Args:
            selector: CSS selector string

        Returns:
            ValidationResult
        """
        if not selector or not selector.strip():
            return ValidationResult(
                valid=False,
                reason="Empty selector",
                severity="error"
            )

        # Check for dangerous selectors
        # (This is a basic check; Playwright has its own validation)
        if len(selector) > 1000:
            return ValidationResult(
                valid=False,
                reason="Selector too long",
                severity="error"
            )

        return ValidationResult(valid=True, reason="Selector validation passed")

    def should_require_approval(self, action: str, parameters: Optional[Dict] = None) -> bool:
        """
        Check if action requires user approval.

        Args:
            action: Action name
            parameters: Action parameters

        Returns:
            True if approval required
        """
        # Check global setting
        if not self.security_config.get("require_approval", True):
            return False

        # High-risk actions always require approval
        high_risk_actions = ["execute_script", "fill_form"]
        if action in high_risk_actions:
            return True

        # Navigation to external URLs requires approval
        if action == "navigate":
            parameters = parameters or {}
            url = parameters.get("url", "")
            parsed = urlparse(url)
            # Require approval for non-https
            if parsed.scheme != "https":
                return True

        return False
