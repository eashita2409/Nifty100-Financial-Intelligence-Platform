import pytest
import sqlite3
import pandas as pd
from pathlib import Path
import os
import numpy as np

from src.analytics.cashflow_kpis import (
    compute_cfo_quality,
    compute_capex_intensity,
    compute_fcf_conversion,
    compute_distress_signal,
    compute_deleveraging_flag,
    _classify_capital
)

def test_compute_cfo_quality():
    assert compute_cfo_quality(150, 100) == 1.5
    assert np.isnan(compute_cfo_quality(150, 0))
    assert compute_cfo_quality(0, 100) == 0.0

def test_compute_capex_intensity():
    assert compute_capex_intensity(50, 500) == 0.1
    assert compute_capex_intensity(-50, 500) == 0.1
    assert np.isnan(compute_capex_intensity(50, 0))

def test_compute_fcf_conversion():
    assert compute_fcf_conversion(60, 100) == 0.6
    assert np.isnan(compute_fcf_conversion(60, 0))

def test_compute_distress_signal():
    assert compute_distress_signal(-10, -20) == 1
    assert compute_distress_signal(10, -20) == 0
    assert compute_distress_signal(-10, 20) == 0

def test_compute_deleveraging_flag():
    assert compute_deleveraging_flag(-10, 50, 100) == 1
    assert compute_deleveraging_flag(10, 50, 100) == 0
    assert compute_deleveraging_flag(-10, 100, 50) == 0

def test_classify_capital():
    assert _classify_capital(-10, 5, -15, 0) == "Cash Burn"
    assert _classify_capital(50, 60, -10, 0) == "Aggressive Expansion"
    assert _classify_capital(100, 20, 80, -50) == "Cash Cow / Returner"
    assert _classify_capital(100, 20, 80, 50) == "Stable / Moderate Reinvestment"
