"""
Test Runner Shortcut for SafeKerala / DisasterSafe
Allows running the full pytest suite directly via `python test_chatbot.py`.
"""
import sys
import pytest

if __name__ == "__main__":
    exit_code = pytest.main(["-v", "tests/"])
    sys.exit(exit_code)
