"""Alpha AI Assistant - Main Entry Point"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from alpha.core.engine import AlphaEngine
from alpha.utils.config import load_config
from alpha.daemon import PIDManager, SignalHandler, daemonize
from alpha.api.server import start_server


def setup_logging(daemon_mode: bool = False):
    """
    Setup logging configuration.

    Args:
        daemon_mode: If True, only log to file (no console output)
    """
    Path('logs').mkdir(exist_ok=True)

    handlers = []

    if not daemon_mode:
        # Interactive mode - log to console and file
        handlers.append(logging.StreamHandler(sys.stdout))

    # Always log to file
    handlers.append(logging.FileHandler('logs/alpha.log'))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Alpha AI Assistant - Personal Super AI Assistant'
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon process in background'
    )

    parser.add_argument(
        '--pid-file',
        type=str,
        default='/var/run/alpha/alpha.pid',
        help='PID file location (default: /var/run/alpha/alpha.pid)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )

    parser.add_argument(
        '--api-host',
        type=str,
        default='0.0.0.0',
        help='API server host (default: 0.0.0.0)'
    )

    parser.add_argument(
        '--api-port',
        type=int,
        default=8080,
        help='API server port (default: 8080)'
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(daemon_mode=args.daemon)
    logger = logging.getLogger(__name__)

    # Daemonize if requested
    if args.daemon:
        logger.info("Starting Alpha in daemon mode...")

        # Daemonize the process
        daemonize(
            working_directory=str(Path.cwd()),
            stdin='/dev/null',
            stdout='logs/alpha.stdout.log',
            stderr='logs/alpha.stderr.log'
        )

        # Re-setup logging after daemonizing (file handles may have changed)
        setup_logging(daemon_mode=True)
        logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Alpha AI Assistant Starting...")
    if args.daemon:
        logger.info("Running in daemon mode with API server")
        logger.info(f"API will be available at http://{args.api_host}:{args.api_port}")
    logger.info("=" * 60)

    # Setup PID file and signal handlers for daemon mode
    pid_manager = None
    signal_handler = None

    try:
        # Create PID file if in daemon mode
        if args.daemon:
            pid_manager = PIDManager(args.pid_file)
            if not pid_manager.write():
                logger.error("Failed to create PID file - daemon may already be running")
                sys.exit(1)
            logger.info(f"PID file created: {args.pid_file}")

        # Load configuration
        config = load_config(args.config)
        logger.info(f"Loaded configuration: {config.name} v{config.version}")

        # Setup signal handlers
        signal_handler = SignalHandler()

        shutdown_event = asyncio.Event()

        async def shutdown():
            """Shutdown handler."""
            logger.info("Shutting down Alpha...")
            shutdown_event.set()

        async def reload_config():
            """Reload configuration handler."""
            logger.info("Reloading configuration...")
            try:
                new_config = load_config(args.config)
                logger.info("Configuration reloaded successfully")
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")

        signal_handler.setup(
            shutdown_callback=shutdown,
            reload_callback=reload_config
        )

        # Run API server (includes engine initialization)
        logger.info(f"Starting API server on {args.api_host}:{args.api_port}")
        server_task = asyncio.create_task(
            start_server(
                host=args.api_host,
                port=args.api_port,
                reload=False
            )
        )

        # Wait for shutdown signal
        await shutdown_event.wait()

        # Cancel server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            logger.info("Server stopped")

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if pid_manager:
            pid_manager.remove()

        logger.info("Alpha stopped")


if __name__ == "__main__":
    asyncio.run(main())
