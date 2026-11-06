"""
Pytest configuration and environment fixtures for SafeKerala test suite.
Ensures project root is always included in sys.path.
"""
import sys
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

