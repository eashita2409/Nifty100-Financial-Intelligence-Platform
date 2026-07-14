import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from streamlit.testing.v1 import AppTest

def test_page(page_path):
    print(f"\n--- Testing {page_path} ---")
    at = AppTest.from_file(page_path)
    at.run(timeout=10)
    
    if at.exception:
        print("Exception:", at.exception)
    else:
        print("Page rendered successfully without exceptions.")
        
    # Interact with some widgets if present to test interactivity
    if at.selectbox:
        print(f"Found {len(at.selectbox)} selectboxes.")
        # Try interacting with the first one
        if at.selectbox[0].options:
            val = at.selectbox[0].options[0]
            print(f"Selecting option: {val}")
            at.selectbox[0].select(val).run(timeout=10)
            if at.exception:
                print("Exception after interaction:", at.exception)
            else:
                print("Interaction successful.")
                
    if at.multiselect:
        print(f"Found {len(at.multiselect)} multiselects.")

pages = [
    'src/dashboard/pages/05_trends.py',
    'src/dashboard/pages/06_sectors.py',
    'src/dashboard/pages/07_capital.py',
    'src/dashboard/pages/08_reports.py'
]

for p in pages:
    test_page(p)
