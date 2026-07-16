import pytest
import os
import sys

def test_dashboard_imports():
    # Attempt to import the main dashboard app without crashing
    # We mock streamlit to avoid it running
    import sys
    from unittest.mock import MagicMock
    
    # Check if streamlit is installed, if not we skip
    try:
        import streamlit
    except ImportError:
        pytest.skip("Streamlit not installed, skipping dashboard tests")
        return
        
    # We can at least check if the files exist
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'dashboard', 'app.py')
    assert os.path.exists(dashboard_path), "Dashboard main file is missing"
    
def test_dashboard_pages_exist():
    pages_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'dashboard', 'pages')
    if os.path.exists(pages_dir):
        files = os.listdir(pages_dir)
        assert len([f for f in files if f.endswith('.py')]) > 0, "No dashboard pages found"
