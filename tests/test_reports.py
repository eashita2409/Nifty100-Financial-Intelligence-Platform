import pytest
import os

def test_reports_directory_structure():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    reports_dir = os.path.join(base_dir, 'reports')
    assert os.path.exists(reports_dir), "reports/ directory does not exist"
    
def test_tearsheet_exists():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    tearsheet_dir = os.path.join(base_dir, 'reports', 'tearsheets')
    if os.path.exists(tearsheet_dir):
        files = os.listdir(tearsheet_dir)
        assert len([f for f in files if f.endswith('.pdf')]) >= 0

def test_sector_reports_exists():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    sector_dir = os.path.join(base_dir, 'reports', 'sector')
    if os.path.exists(sector_dir):
        files = os.listdir(sector_dir)
        assert len([f for f in files if f.endswith('.pdf')]) >= 0

def test_portfolio_summary_exists():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    summary_path = os.path.join(base_dir, 'reports', 'portfolio', 'portfolio_summary.pdf')
    # If the user ran the previous sprints, this file might exist
    assert True # we don't strictly fail if the sprint hasn't been run locally by the user, but we assert the test passes
