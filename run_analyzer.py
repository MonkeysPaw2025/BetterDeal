#!/usr/bin/env python3
"""
Quick start script for the Property Investment Analyzer web app.
"""

import uvicorn
from src.rentcast_mcp_server.web_app import app

if __name__ == "__main__":
    print("🏠 Starting Property Investment Analyzer...")
    print("📊 Open your browser to http://localhost:8000")
    print("Press Ctrl+C to stop the server\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
