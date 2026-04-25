import sys
import pathlib

# Make the coordination-service package importable from the tests/ subdirectory.
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
