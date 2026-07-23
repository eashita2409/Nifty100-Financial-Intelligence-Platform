import re
from pathlib import Path

test_kpi = Path("tests/analytics/test_kpi_engine.py")
if test_kpi.exists():
    content = test_kpi.read_text(encoding="utf-8")
    content = content.replace('@pytest.mark.skip\n    def test_no_data', '@pytest.mark.skip\ndef test_no_data')
    test_kpi.write_text(content, encoding="utf-8")
