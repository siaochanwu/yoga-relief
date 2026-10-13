"""薄入口：uv run python scripts/build_advice.py [--force]"""

import sys

from yoga_relief.build_advice import main

if __name__ == "__main__":
    sys.exit(main())
