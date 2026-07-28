"""Make `pytest` work regardless of cwd by putting the package root on sys.path."""
import pathlib
import sys

_PKG_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
