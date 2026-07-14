import sys
from pathlib import Path
import traceback

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

pages = [
    "src.dashboard.app",
    "src.dashboard.pages.01_home",
    "src.dashboard.pages.02_profile",
    "src.dashboard.pages.03_screener",
    "src.dashboard.pages.04_peers"
]

for page in pages:
    try:
        __import__(page)
        print(f"Successfully imported {page}")
    except Exception as e:
        print(f"Error importing {page}:")
        traceback.print_exc()

print("Import test finished.")
