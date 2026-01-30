# Alpha REST API Server

**Status**: ✅ Phase 3.1 - Week 1 Implementation Complete
**Version**: 1.0.0
**Protocol**: HTTP/REST
**Format**: JSON

---

## Overview

The Alpha REST API Server provides HTTP endpoints for interacting with Alpha daemon, enabling:
- Task submission and monitoring
- System status queries
- Integration with third-party applications
- Remote control and automation

---

## Quick Start

### 1. Start API Server

```bash
# Start on default port (8080)
python scripts/start_api_server.py

# Custom host and port
python scripts/start_api_server.py --host 0.0.0.0 --port 9000

# Development mode with auto-reload
python scripts/start_api_server.py --reload
```

### 2. Access API Documentation

Once started, visit:
- **Interactive Docs**: http://localhost:8080/api/docs
- **ReDoc**: http://localhost:8080/api/redoc
- **OpenAPI JSON**: http://localhost:8080/api/openapi.json

---

## API Endpoints

### Health & Status

#### `GET /api/health`
Health check for monitoring.

**Response**:
```json
{
  "healthy": true,
  "timestamp": "2026-01-30T16:50:00Z",
  "checks": {
    "api": true,
    "engine": true,
    "database": true,
    "llm": true
  }
}
```

#### `GET /api/v1/status`
Get system status and statistics.

**Response**:
```json
{
  "status": "operational",
  "uptime": 3600.5,
  "version": "1.0.0",
  "tasks_total": 42,
  "tasks_running": 2,
  "tasks_completed": 38,
  "tasks_failed": 2,
  "memory_usage_mb": 256.4,
  "cpu_percent": 12.3
}
```

---

### Task Management

#### `POST /api/v1/tasks`
Create and submit a new task.

**Request**:
```json
{
  "prompt": "Search for latest AI news and summarize",
  "priority": 7,
  "context": {
    "sources": ["TechCrunch", "VentureBeat"]
  },
  "timeout": 300
}
```

**Response** (201 Created):
```json
{
  "task_id": "task_abc123",
  "status": "pending",
  "created_at": "2026-01-30T16:50:00Z",
  "metadata": {
    "priority": 7
  }
}
```

#### `GET /api/v1/tasks/{task_id}`
Get task status and result.

**Response**:
```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "created_at": "2026-01-30T16:50:00Z",
  "started_at": "2026-01-30T16:50:01Z",
  "completed_at": "2026-01-30T16:50:45Z",
  "result": {
    "summary": "Latest AI news summary...",
    "sources": 5
  },
  "error": null
}
```

#### `GET /api/v1/tasks`
List all tasks with filtering.

**Query Parameters**:
- `status`: Filter by status (pending, running, completed, failed)
- `limit`: Maximum results (default: 50, max: 100)
- `offset`: Pagination offset (default: 0)

**Example**:
```bash
curl "http://localhost:8080/api/v1/tasks?status=completed&limit=10"
```

**Response**:
```json
{
  "tasks": [...],
  "total": 10,
  "page": 0,
  "page_size": 10
}
```

#### `DELETE /api/v1/tasks/{task_id}`
Cancel a running task.

**Response**: 204 No Content

---

## Usage Examples

### Using curl

```bash
# Health check
curl http://localhost:8080/api/health

# Get status
curl http://localhost:8080/api/v1/status

# Submit task
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the weather in Beijing?",
    "priority": 5
  }'

# Get task result
curl http://localhost:8080/api/v1/tasks/task_abc123

# List completed tasks
curl "http://localhost:8080/api/v1/tasks?status=completed"
```

### Using Python

```python
import requests

# Submit task
response = requests.post(
    "http://localhost:8080/api/v1/tasks",
    json={
        "prompt": "Search for Python tutorials",
        "priority": 5
    }
)
task = response.json()
task_id = task["task_id"]

# Poll for completion
import time
while True:
    response = requests.get(f"http://localhost:8080/api/v1/tasks/{task_id}")
    task = response.json()

    if task["status"] in ["completed", "failed"]:
        break

    time.sleep(1)

# Get result
if task["status"] == "completed":
    print(f"Result: {task['result']}")
else:
    print(f"Failed: {task['error']}")
```

### Using JavaScript/Node.js

```javascript
// Submit task
const response = await fetch('http://localhost:8080/api/v1/tasks', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'Translate this to Chinese',
    priority: 5
  })
});

const task = await response.json();
console.log(`Task created: ${task.task_id}`);

// Get result
const result = await fetch(`http://localhost:8080/api/v1/tasks/${task.task_id}`);
const taskInfo = await result.json();
console.log(taskInfo);
```

---

## Integration with Daemon Mode

When Alpha runs as a daemon (systemd service), you can interact with it via the REST API:

```bash
# Start Alpha daemon
sudo systemctl start alpha

# In another terminal, start API server
python scripts/start_api_server.py

# Now you can send tasks to the running daemon
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Check system disk usage"}'
```

---

## Error Handling

All errors return JSON with error details:

```json
{
  "error": "Task not found",
  "detail": "No task with ID task_xyz exists",
  "code": "TASK_NOT_FOUND"
}
```

**HTTP Status Codes**:
- `200 OK`: Successful request
- `201 Created`: Task created successfully
- `204 No Content`: Task cancelled successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Security Considerations

**Current Implementation** (v1.0.0):
- ⚠️ No authentication required (localhost only)
- ⚠️ No rate limiting
- ⚠️ CORS enabled for all origins

**Recommended for Production**:
1. Enable API key authentication
2. Implement rate limiting
3. Configure CORS whitelist
4. Use HTTPS with SSL/TLS
5. Run behind reverse proxy (nginx/Caddy)

---

## Performance

**Expected Response Times**:
- Health check: <10ms
- Status query: <50ms
- Task submission: <100ms
- Task query: <50ms

**Concurrent Requests**: Supports 100+ concurrent connections

---

## Troubleshooting

### Server won't start

**Error**: `Address already in use`
```bash
# Find process using port 8080
lsof -i :8080
# Kill it or use different port
python scripts/start_api_server.py --port 9000
```

### Task submission fails

**Error**: `Alpha engine not initialized`
- Ensure Alpha daemon is running
- Check logs: `journalctl -u alpha -f`

### Slow responses

- Check system resource usage
- Review Alpha logs for errors
- Consider increasing worker count

---

## Future Enhancements (Phase 3.2+)

**Planned Features**:
- [ ] API key authentication
- [ ] Rate limiting per client
- [ ] WebSocket support for real-time updates
- [ ] Task scheduling via API
- [ ] Configuration management endpoints
- [ ] File upload for document processing
- [ ] Webhook notifications

---

## See Also

- [Alpha Documentation](../../docs/README.md)
- [Daemon Mode Guide](../../docs/manual/en/daemon_mode.md)
- [Phase 3 Requirements](../internal/phase3_requirements_analysis.md)

---

**Version**: 1.0.0
**Last Updated**: 2026-01-30
**Status**: ✅ Functional (Basic Implementation)
