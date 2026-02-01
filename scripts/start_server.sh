#!/bin/bash
#
# Alpha Server Startup Script
#
# Ensures proper environment activation before starting server
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Alpha Server Startup${NC}"
echo "Project: $PROJECT_ROOT"
echo

# Check virtual environment
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}Error: Virtual environment not found!${NC}"
    echo "Please create it first:"
    echo "  cd $PROJECT_ROOT"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if server is already running
PID_FILE="$PROJECT_ROOT/data/alpha.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "${YELLOW}Alpha server is already running (PID: $PID)${NC}"
        echo "Use 'alpha stop' to stop it first"
        exit 0
    else
        echo -e "${YELLOW}Removing stale PID file${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Activate virtual environment and start server
cd "$PROJECT_ROOT"
source venv/bin/activate

# Activate virtual environment and start server
cd "$PROJECT_ROOT"
source venv/bin/activate

echo "Starting Alpha server..."

# Start server in background using uvicorn directly
nohup python3 -m uvicorn alpha.api.server:create_app \
    --factory \
    --host "${1:-0.0.0.0}" \
    --port "${2:-8080}" \
    > logs/alpha-api.log 2>&1 &
SERVER_PID=$!

# Save PID
echo $SERVER_PID > data/alpha.pid

# Wait a moment and check if still running
sleep 3
if kill -0 $SERVER_PID 2>/dev/null; then
    echo
    echo -e "${GREEN}✓ Alpha server started (PID: $SERVER_PID)${NC}"
    echo "  API: http://${1:-0.0.0.0}:${2:-8080}"
    echo "  WebSocket: ws://${1:-0.0.0.0}:${2:-8080}/api/v1/ws/chat"
    echo
    echo "Connect with: $SCRIPT_DIR/alpha chat"
    echo
    echo "Logs: tail -f $PROJECT_ROOT/logs/alpha-api.log"
else
    echo -e "${RED}Failed to start server${NC}"
    echo "Check logs: tail -f $PROJECT_ROOT/logs/alpha-api.log"
    rm -f data/alpha.pid
    exit 1
fi
