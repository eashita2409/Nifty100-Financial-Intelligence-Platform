import sqlite3
import os

def audit_project():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # 1. Database Stats
    db_path = os.path.join(base_dir, 'data', 'db', 'nifty100.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM companies")
    companies = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM financial_ratios")
    ratios = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM market_cap")
    mcap = cursor.fetchone()[0]
    
    conn.close()
    
    # 2. File Stats
    output_dir = os.path.join(base_dir, 'output')
    csvs = [f for f in os.listdir(output_dir) if f.endswith('.csv')] if os.path.exists(output_dir) else []
    excels = [f for f in os.listdir(output_dir) if f.endswith('.xlsx')] if os.path.exists(output_dir) else []
    pngs = [f for f in os.listdir(output_dir) if f.endswith('.png')] if os.path.exists(output_dir) else []
    
    reports_dir = os.path.join(base_dir, 'reports')
    pdfs = []
    for root, dirs, files in os.walk(reports_dir):
        for file in files:
            if file.endswith(".pdf"):
                pdfs.append(file)
                
    docs_dir = os.path.join(base_dir, 'docs')
    docs = [f for f in os.listdir(docs_dir) if f.endswith('.pdf')] if os.path.exists(docs_dir) else []
    
    print(f"DATABASE: Companies={companies}, Ratios={ratios}, MarketCap={mcap}")
    print(f"OUTPUTS: CSVs={len(csvs)}, Excels={len(excels)}, PNGs={len(pngs)}")
    print(f"REPORTS: PDFs={len(pdfs)}")
    print(f"DOCS: PDFs={len(docs)}")

if __name__ == "__main__":
    audit_project()
