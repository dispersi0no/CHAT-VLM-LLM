"""Shared pytest fixtures."""

import sys
from pathlib import Path

# Ensure project root is in sys.path for imports
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
