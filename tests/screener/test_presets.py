import pytest
import pandas as pd
from pathlib import Path
from src.screener.engine import ScreenerEngine

@pytest.fixture
def db_path():
    project_root = Path(__file__).resolve().parent.parent.parent
    return project_root / "data" / "db" / "nifty100.db"

@pytest.fixture
def config_path():
    project_root = Path(__file__).resolve().parent.parent.parent
    return project_root / "config" / "screener_config.yaml"

def test_load_presets(config_path):
    engine = ScreenerEngine(str(config_path))
    assert hasattr(engine, 'presets')
    assert len(engine.presets) == 6
    assert "Quality Compounder" in engine.presets
    assert "Value Pick" in engine.presets
    assert "Growth Accelerator" in engine.presets
    assert "Dividend Champion" in engine.presets
    assert "Debt-Free Blue Chip" in engine.presets
    assert "Turnaround Watch" in engine.presets

def test_invalid_preset_raises_error(db_path, config_path):
    engine = ScreenerEngine(str(config_path))
    with pytest.raises(ValueError) as exc_info:
        engine.run_preset("Invalid Preset", str(db_path))
    assert "Preset 'Invalid Preset' not found" in str(exc_info.value)

@pytest.mark.parametrize("preset_name", [
    "Quality Compounder",
    "Value Pick",
    "Growth Accelerator",
    "Dividend Champion",
    "Debt-Free Blue Chip",
    "Turnaround Watch"
])
def test_preset_company_count_limits(preset_name, db_path, config_path):
    engine = ScreenerEngine(str(config_path))
    res = engine.run_preset(preset_name, str(db_path))
    
    # Assert result is a DataFrame
    assert isinstance(res, pd.DataFrame)
    
    # Assert company count is between 5 and 50 (inclusive)
    count = len(res)
    assert 5 <= count <= 50, f"Preset '{preset_name}' returned {count} companies, which is not between 5 and 50."
    
    # Assert results are sorted by composite_quality_score descending
    if 'composite_quality_score' in res.columns and count > 1:
        scores = res['composite_quality_score'].values
        assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1)), f"Preset '{preset_name}' is not sorted correctly."
