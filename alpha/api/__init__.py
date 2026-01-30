"""
Alpha REST API Server

Provides HTTP API for interacting with Alpha daemon.
"""

__version__ = "1.0.0"

from .server import create_app, start_server

__all__ = ["create_app", "start_server"]
