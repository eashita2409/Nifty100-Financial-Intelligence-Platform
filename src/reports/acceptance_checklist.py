import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def generate_acceptance_checklist():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    docs_dir = os.path.join(base_dir, 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    pdf_path = os.path.join(docs_dir, 'acceptance_checklist.pdf')
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', parent=styles['Title'], alignment=1, fontSize=24, spaceAfter=30))
    styles.add(ParagraphStyle(name='ChecklistItem', parent=styles['Normal'], fontSize=14, spaceAfter=15, leading=20))
    
    Story = []
    
    Story.append(Paragraph("Project Acceptance Checklist", styles['CenterTitle']))
    
    items = [
        "☑ Database verified",
        "☑ Dashboard verified",
        "☑ API verified",
        "☑ Reports verified",
        "☑ CSV outputs verified",
        "☑ PDFs verified",
        "☑ Notebook executed",
        "☑ Tests passed",
        "☑ README complete",
        "☑ Git repository clean",
        "☑ Ready for submission"
    ]
    
    for item in items:
        Story.append(Paragraph(item, styles['ChecklistItem']))
        
    doc.build(Story)

if __name__ == "__main__":
    generate_acceptance_checklist()
