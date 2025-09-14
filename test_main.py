#!/usr/bin/env python3
"""
Test script to verify main.py can be imported and started with uvicorn
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test import
    import main
    print("✅ main.py imported successfully")
    
    # Test app creation
    app = main.app
    print(f"✅ FastAPI app created: {app.title} v{app.version}")
    
    # Test endpoints
    print("📋 Available endpoints:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  - {route.methods} {route.path}")
    
    print("\n🚀 main.py is ready for uvicorn")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()