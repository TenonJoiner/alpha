"""
Alpha - Screenshot Manager

Manages browser screenshots and image storage.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class ScreenshotManager:
    """
    Manages screenshot capture and storage.

    Features:
    - Full page and element screenshots
    - Multiple image formats (PNG, JPEG)
    - Automatic storage management
    - Retention policy enforcement
    - Screenshot metadata tracking
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize screenshot manager.

        Args:
            config: Browser automation configuration
        """
        self.config = config or {}
        self.screenshot_config = self.config.get("screenshots", {})

        # Storage path
        storage_path = self.screenshot_config.get("storage_path", "data/screenshots")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Settings
        self.format = self.screenshot_config.get("format", "png")
        self.quality = self.screenshot_config.get("quality", 80)
        self.max_storage_mb = self.screenshot_config.get("max_storage_mb", 100)
        self.retention_days = self.screenshot_config.get("retention_days", 7)

        logger.info(f"ScreenshotManager initialized (storage: {self.storage_path})")

    async def capture_screenshot(
        self,
        page,
        full_page: bool = False,
        selector: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Capture a screenshot.

        Args:
            page: Playwright Page instance
            full_page: Capture full scrollable page
            selector: Capture specific element by selector
            filename: Custom filename (without extension)

        Returns:
            Dictionary with screenshot information
        """
        if not self.screenshot_config.get("enabled", True):
            return {
                "success": False,
                "error": "Screenshots disabled in configuration"
            }

        try:
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                url_hash = hashlib.md5(page.url.encode()).hexdigest()[:8]
                filename = f"screenshot_{timestamp}_{url_hash}"

            # Add extension
            file_ext = "png" if self.format == "png" else "jpg"
            filepath = self.storage_path / f"{filename}.{file_ext}"

            # Screenshot options
            options = {
                "path": str(filepath),
                "type": self.format,
                "full_page": full_page
            }

            # Add quality for JPEG
            if self.format == "jpeg":
                options["quality"] = self.quality

            # Capture screenshot
            if selector:
                # Element screenshot
                element = await page.query_selector(selector)
                if not element:
                    return {
                        "success": False,
                        "error": f"Element not found: {selector}"
                    }
                await element.screenshot(**options)
            else:
                # Page screenshot
                await page.screenshot(**options)

            # Get file info
            file_size = filepath.stat().st_size

            logger.info(f"Screenshot captured: {filepath} ({file_size} bytes)")

            # Check storage limits
            await self._enforce_storage_limits()

            return {
                "success": True,
                "path": str(filepath),
                "filename": filepath.name,
                "size_bytes": file_size,
                "format": self.format,
                "full_page": full_page,
                "selector": selector,
                "url": page.url,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _enforce_storage_limits(self):
        """Enforce storage limits and retention policy."""
        try:
            # Calculate total storage
            total_size = sum(
                f.stat().st_size for f in self.storage_path.glob("*")
                if f.is_file()
            )
            total_mb = total_size / (1024 * 1024)

            # Check size limit
            if total_mb > self.max_storage_mb:
                logger.warning(
                    f"Screenshot storage exceeds limit: {total_mb:.2f}MB > {self.max_storage_mb}MB"
                )
                await self._cleanup_old_screenshots(target_mb=self.max_storage_mb * 0.8)

            # Enforce retention policy
            await self._cleanup_expired_screenshots()

        except Exception as e:
            logger.error(f"Error enforcing storage limits: {e}")

    async def _cleanup_old_screenshots(self, target_mb: float):
        """
        Clean up old screenshots to reach target size.

        Args:
            target_mb: Target storage size in MB
        """
        try:
            # Get all screenshots sorted by modification time
            screenshots = sorted(
                self.storage_path.glob("*"),
                key=lambda f: f.stat().st_mtime
            )

            total_size = sum(f.stat().st_size for f in screenshots)
            target_bytes = target_mb * 1024 * 1024

            # Delete oldest screenshots until under target
            for screenshot in screenshots:
                if total_size <= target_bytes:
                    break

                size = screenshot.stat().st_size
                screenshot.unlink()
                total_size -= size
                logger.info(f"Deleted old screenshot: {screenshot.name}")

        except Exception as e:
            logger.error(f"Error cleaning up old screenshots: {e}")

    async def _cleanup_expired_screenshots(self):
        """Clean up screenshots older than retention period."""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.retention_days)
            cutoff_timestamp = cutoff_time.timestamp()

            for screenshot in self.storage_path.glob("*"):
                if screenshot.is_file():
                    mtime = screenshot.stat().st_mtime
                    if mtime < cutoff_timestamp:
                        screenshot.unlink()
                        logger.info(f"Deleted expired screenshot: {screenshot.name}")

        except Exception as e:
            logger.error(f"Error cleaning up expired screenshots: {e}")

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get storage information.

        Returns:
            Dictionary with storage statistics
        """
        try:
            screenshots = list(self.storage_path.glob("*"))
            total_size = sum(f.stat().st_size for f in screenshots if f.is_file())
            total_mb = total_size / (1024 * 1024)

            return {
                "total_screenshots": len(screenshots),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_mb, 2),
                "max_storage_mb": self.max_storage_mb,
                "usage_percent": round((total_mb / self.max_storage_mb) * 100, 2),
                "retention_days": self.retention_days,
                "storage_path": str(self.storage_path)
            }
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return {"error": str(e)}

    def get_screenshot_path(self, filename: str) -> Optional[Path]:
        """
        Get path to a screenshot by filename.

        Args:
            filename: Screenshot filename

        Returns:
            Path object or None if not found
        """
        filepath = self.storage_path / filename
        if filepath.exists():
            return filepath
        return None

    async def delete_screenshot(self, filename: str) -> bool:
        """
        Delete a specific screenshot.

        Args:
            filename: Screenshot filename

        Returns:
            True if deleted successfully
        """
        try:
            filepath = self.storage_path / filename
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Screenshot deleted: {filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting screenshot {filename}: {e}")
            return False
