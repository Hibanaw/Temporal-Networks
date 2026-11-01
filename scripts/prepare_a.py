"""Materialise the canonical A dataset interface."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.io import prepare
if __name__ == "__main__":
    for name in ("PS", "CM"):
        print(prepare(name), flush=True)
