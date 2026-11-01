"""Compatibility interface; all D/E loading delegates to A's shared src.io."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.io import (Dataset, RAW, PS_DIR, CM_DIR, load, load_primaryschool, load_collegemsg)
