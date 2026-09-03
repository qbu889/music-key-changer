import sys
from pathlib import Path

# Allow `import audio` and `import main` when running pytest from backend/.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
