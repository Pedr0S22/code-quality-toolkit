import sys
from pathlib import Path

# Add src/ for toolkit imports
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Add project root for web imports
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
