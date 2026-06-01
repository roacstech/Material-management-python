#!/usr/bin/env python
import os
import sys
import uvicorn
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

if __name__ == "__main__":
    app_env = os.getenv("APP_ENV", "development")
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = app_env == "development"

   # run.py
if app_env == "production":
    print("Starting production server with gunicorn...")
    os.system("gunicorn -c gunicorn_config.py main:app")

    
    else:
        print(f"Starting development server on {host}:{port}")
        uvicorn.run(
            "main:app",   # <-- was "app.main:app"
            host=host,
            port=port,
            reload=debug,
            reload_dirs=[os.path.dirname(os.path.abspath(__file__))],
            log_level="info" if not debug else "debug"
        )