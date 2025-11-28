#!/usr/bin/env python3
"""Test script to verify session router is registered"""

import sys
sys.path.insert(0, '/app')

from app.main import app

print("=" * 70)
print("Checking Session Router Registration")
print("=" * 70)
print()

# Get all routes
all_routes = [r for r in app.routes if hasattr(r, 'path')]
print(f"Total routes: {len(all_routes)}")
print()

# Find session routes
session_routes = [r for r in all_routes if 'session' in r.path]
print(f"Session routes found: {len(session_routes)}")
for route in session_routes:
    methods = list(route.methods) if hasattr(route, 'methods') else []
    print(f"  - {route.path} {methods}")
print()

# Check if enforce-single exists
enforce_route = [r for r in session_routes if 'enforce-single' in r.path]
if enforce_route:
    print("✅ enforce-single route found!")
    print(f"   Path: {enforce_route[0].path}")
    print(f"   Methods: {list(enforce_route[0].methods) if hasattr(enforce_route[0], 'methods') else 'N/A'}")
else:
    print("❌ enforce-single route NOT found!")
print()

# List all /api routes for comparison
api_routes = [r for r in all_routes if r.path.startswith('/api')]
print(f"Total /api routes: {len(api_routes)}")
print("Sample /api routes:")
for route in api_routes[:10]:
    methods = list(route.methods) if hasattr(route, 'methods') else []
    print(f"  - {route.path} {methods}")


