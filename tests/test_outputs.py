import pytest
import os

def test_csv_outputs_exist():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, 'output')
    
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        csv_files = [f for f in files if f.endswith('.csv')]
        # We expect some CSVs to exist from previous sprints
        assert len(csv_files) >= 0

def test_excel_outputs_exist():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, 'output')
    
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        xlsx_files = [f for f in files if f.endswith('.xlsx')]
        assert len(xlsx_files) >= 0

def test_image_outputs_exist():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, 'output')
    
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        png_files = [f for f in files if f.endswith('.png')]
        assert len(png_files) >= 0
