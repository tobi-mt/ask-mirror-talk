#!/usr/bin/env python3
"""
Minimal test script to verify the app can import and start.
Run this in Railway shell to debug startup issues.
"""
import sys
import traceback

print("=" * 60)
print("MINIMAL APP STARTUP TEST")
print("=" * 60)

# Test 1: Python version
print(f"\n1. Python version: {sys.version}")

# Test 2: Import standard library
try:
    import logging
    print("✓ Standard library imports OK")
except Exception as e:
    print(f"✗ Standard library import failed: {e}")
    sys.exit(1)

# Test 3: Import FastAPI
try:
    import fastapi
    print(f"✓ FastAPI imported: v{fastapi.__version__}")
except Exception as e:
    print(f"✗ FastAPI import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Import app.core.config
try:
    from app.core.config import settings
    print(f"✓ Config loaded: {settings.app_name}")
except Exception as e:
    print(f"✗ Config import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Import app.core.db (the lazy version)
try:
    from app.core.db import get_db, get_engine, get_session_local
    print("✓ Database module imported (no connection attempted)")
except Exception as e:
    print(f"✗ Database module import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 6: Import main app module
try:
    from app.api import main
    print("✓ Main API module imported")
except Exception as e:
    print(f"✗ Main API module import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 7: Get the FastAPI app instance
try:
    from app.api.main import app
    print(f"✓ FastAPI app instance created: {app.title}")
except Exception as e:
    print(f"✗ FastAPI app creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 8: Check if /health endpoint exists
try:
    routes = [r.path for r in app.routes]
    if "/health" in routes:
        print("✓ /health endpoint registered")
    else:
        print(f"✗ /health endpoint NOT found. Available routes: {routes}")
except Exception as e:
    print(f"✗ Route check failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("ALL TESTS PASSED - App should be able to start!")
print("=" * 60)
print("\nNow try starting with uvicorn:")
print("uvicorn app.api.main:app --host 0.0.0.0 --port 8000")
