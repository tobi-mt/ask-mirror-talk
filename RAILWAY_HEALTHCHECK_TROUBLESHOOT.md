# Railway Healthcheck Troubleshooting

## Issues Fixed

### 1. Invalid Railway Configuration
**Problem:** `railway.toml` contained `restartPolicyType = "always"` which is not a supported Railway configuration option.

**Fix:** Removed the unsupported option. Railway only supports these keys in the `[deploy]` section:
- `startCommand`
- `healthcheckPath`
- `healthcheckTimeout`

### 2. Docker CMD Format
**Problem:** Using shell form (`CMD command`) in Dockerfile can sometimes cause issues with signal handling and process management.

**Fix:** Changed to exec form with sh -c wrapper:
```dockerfile
CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 75"]
```

This ensures proper:
- Environment variable expansion (`$PORT`)
- Signal handling (SIGTERM for graceful shutdown)
- Process management

## Current Configuration

### railway.toml
```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn app.api.main:app --host 0.0.0.0 --port $PORT --workers 1"
healthcheckPath = "/health"
healthcheckTimeout = 100
```

### Health Endpoint
The `/health` endpoint in `app/api/main.py` is designed to:
- Always return 200 OK status
- Not depend on database connectivity
- Return quickly (no heavy operations)

```python
@app.get("/health")
def health():
    """Health check endpoint - returns OK even if database is not ready."""
    return {"status": "ok"}
```

## Testing After Deployment

Once Railway redeploys, test:

```bash
# Check health endpoint
curl https://your-app.up.railway.app/health

# Check status endpoint (requires DB)
curl https://your-app.up.railway.app/status
```

## Common Healthcheck Failure Causes

1. **App not starting:** Check Railway logs for Python errors
2. **Port mismatch:** Ensure app listens on Railway's `$PORT`
3. **Timeout:** App takes too long to start (>100s)
4. **Wrong path:** Healthcheck path doesn't exist or returns error
5. **Heavy startup:** Database migrations or data loading blocks startup

## Our Solutions

✅ Lightweight health endpoint (no DB dependency)
✅ Non-blocking startup (DB errors logged but don't crash app)
✅ Proper port binding (uses `$PORT` from Railway)
✅ Fast startup (minimal dependencies, no ML models)
✅ Proper process management (exec form CMD)

## Next Steps

1. Commit and push these changes
2. Wait for Railway to redeploy
3. Monitor deployment logs
4. Test health endpoint
5. If still failing, check Railway logs for specific errors
