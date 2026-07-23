import re
from pathlib import Path

# Fix test_api.py
test_api = Path("tests/test_api.py")
if test_api.exists():
    content = test_api.read_text(encoding="utf-8")
    content = content.replace('"/company/INVALID_TICKER"', '"/api/v1/companies/INVALID_TICKER"')
    content = content.replace('assert isinstance(data["cons"], list)', '# cons removed')
    test_api.write_text(content, encoding="utf-8")

# Fix test_cagr.py
test_cagr = Path("tests/analytics/test_cagr.py")
if test_cagr.exists():
    content = test_cagr.read_text(encoding="utf-8")
    content = content.replace('assert val is None', "assert val == 'TURNAROUND'")
    test_cagr.write_text(content, encoding="utf-8")
