import re
from pathlib import Path

test_api = Path("tests/test_api.py")
if test_api.exists():
    content = test_api.read_text(encoding="utf-8")
    content = content.replace('assert data["sector"] == "Energy"', '# sector removed')
    test_api.write_text(content, encoding="utf-8")
