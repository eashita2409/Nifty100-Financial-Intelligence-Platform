from streamlit.testing.v1 import AppTest
import sys
from pathlib import Path
import traceback

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

pages = [
    "src/dashboard/app.py",
    "src/dashboard/pages/01_home.py",
    "src/dashboard/pages/02_profile.py",
    "src/dashboard/pages/03_screener.py",
    "src/dashboard/pages/04_peers.py",
    "src/dashboard/pages/05_trends.py",
    "src/dashboard/pages/06_sectors.py",
    "src/dashboard/pages/07_capital.py",
    "src/dashboard/pages/08_reports.py"
]

all_passed = True
issues = []

for page_path in pages:
    print(f"\nTesting {page_path}...")
    try:
        at = AppTest.from_file(page_path)
        at.run(timeout=10)
        
        if at.exception:
            print(f"[FAIL] Exception in {page_path}:")
            for e in at.exception:
                print(e)
            issues.append(f"Exception in {page_path}: {at.exception[0]}")
            all_passed = False
            continue
            
        print(f"[PASS] {page_path} loaded successfully without exceptions.")
        
        # Test basic UI elements
        if "01_home" in page_path:
            # Check sidebar selector
            if at.selectbox:
                # change year
                at.selectbox[0].set_value(2023).run(timeout=10)
                if at.exception:
                    issues.append(f"Exception changing year in 01_home: {at.exception[0]}")
                    all_passed = False
                    
        elif "02_profile" in page_path:
            # test selecting a company
            if at.selectbox:
                options = at.selectbox[0].options
                if options:
                    at.selectbox[0].set_value(options[-1]).run(timeout=10)
                    if at.exception:
                        issues.append(f"Exception selecting company in 02_profile: {at.exception[0]}")
                        all_passed = False
                        
        elif "03_screener" in page_path:
            # test buttons and sliders
            if at.button:
                at.button[0].click().run(timeout=10)
                if at.exception:
                    issues.append(f"Exception clicking Quality button in 03_screener: {at.exception[0]}")
                    all_passed = False
                    
        elif "04_peers" in page_path:
            if at.selectbox:
                # select peer group
                groups = at.selectbox[0].options
                if groups:
                    at.selectbox[0].set_value(groups[0]).run(timeout=10)
                    if at.exception:
                        issues.append(f"Exception selecting peer group in 04_peers: {at.exception[0]}")
                        all_passed = False
                        
    except Exception as e:
        print(f"[ERROR] Error testing {page_path}: {str(e)}")
        issues.append(f"Error testing {page_path}: {str(e)}")
        traceback.print_exc()
        all_passed = False

if all_passed:
    print("\nALL TESTS PASSED!")
else:
    print("\nSOME TESTS FAILED.")
    for issue in issues:
        print(f"  - {issue}")
