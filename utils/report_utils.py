import os
import logging
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()
logger.info("[ReportUtils] Loaded .env file for report utils")

def generate_pdf_report(title: str, summary: str = None, data: list = None, 
                        chart_path: str = None, sql: str = None) -> str:
    """
    Generate a comprehensive PDF report with summary, chart, and data table.
    Phase 4: Report generation with ReportLab.
    
    Args:
        title (str): Report title
        summary (str): AI-generated summary (optional)
        data (list): List of dictionaries with query results
        chart_path (str): Path to chart image file (optional)
        sql (str): SQL query that was executed (optional)
        
    Returns:
        str: Path to generated PDF file, or None if failed
    """
    try:
        logger.info(f"[ReportUtils] Generating PDF report: {title}")
        
        # Create reports directory if it doesn't exist
        reports_dir = 'reports'
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = title.replace(' ', '_').replace('/', '_')[:50]
        pdf_filename = f"{safe_title}_{timestamp}.pdf"
        pdf_path = os.path.join(reports_dir, pdf_filename)
        
        logger.info(f"[ReportUtils] PDF path: {pdf_path}")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Custom heading style
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Body text style
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=14,
            spaceAfter=12
        )
        
        # Add title
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add generation date
        date_text = f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        elements.append(Paragraph(date_text, body_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Add AI Summary section if provided
        if summary:
            logger.info("[ReportUtils] Adding summary section")
            elements.append(Paragraph("📝 Executive Summary", heading_style))
            elements.append(Paragraph(summary, body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Add SQL Query section if provided
        if sql:
            logger.info("[ReportUtils] Adding SQL query section")
            elements.append(Paragraph("📊 SQL Query", heading_style))
            sql_style = ParagraphStyle(
                'SQLCode',
                parent=styles['Code'],
                fontSize=9,
                fontName='Courier',
                textColor=colors.HexColor('#333333'),
                backColor=colors.HexColor('#f5f5f5'),
                leftIndent=20,
                rightIndent=20,
                spaceAfter=12
            )
            elements.append(Paragraph(f"<pre>{sql}</pre>", sql_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Add chart if provided
        if chart_path and os.path.exists(chart_path):
            logger.info(f"[ReportUtils] Adding chart: {chart_path}")
            elements.append(Paragraph("📈 Visualization", heading_style))
            try:
                # Add chart image with proper sizing
                img = Image(chart_path)
                img.drawHeight = 4*inch
                img.drawWidth = 6*inch
                elements.append(img)
                elements.append(Spacer(1, 0.3*inch))
            except Exception as e:
                logger.error(f"[ReportUtils] Error adding chart: {str(e)}")
        else:
            logger.warning(f"[ReportUtils] Chart not found: {chart_path}")
        
        # Add data table if provided
        if data and len(data) > 0:
            logger.info(f"[ReportUtils] Adding data table with {len(data)} rows")
            elements.append(Paragraph("📋 Data Table", heading_style))
            
            # Get column names from first row
            columns = list(data[0].keys())
            
            # Limit columns if too many (max 6 for readability)
            if len(columns) > 6:
                columns = columns[:6]
                logger.info(f"[ReportUtils] Limited table to first 6 columns")
            
            # Create table data
            table_data = [[col.replace('_', ' ').title() for col in columns]]
            
            # Add rows (limit to 50 for PDF size)
            max_rows = min(len(data), 50)
            for i in range(max_rows):
                row = data[i]
                table_data.append([str(row.get(col, 'N/A')) for col in columns])
            
            if len(data) > max_rows:
                table_data.append(['...' for _ in columns])
                logger.info(f"[ReportUtils] Limited table to {max_rows} rows")
            
            # Calculate column widths
            col_width = 6.5*inch / len(columns)
            
            # Create table
            table = Table(table_data, colWidths=[col_width] * len(columns))
            
            # Style table
            table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Body
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
            ]))
            
            elements.append(table)
            
            # Add note if data was truncated
            if len(data) > max_rows:
                elements.append(Spacer(1, 0.1*inch))
                note_style = ParagraphStyle(
                    'Note',
                    parent=styles['Italic'],
                    fontSize=9,
                    textColor=colors.grey
                )
                elements.append(Paragraph(
                    f"Note: Showing {max_rows} of {len(data)} total rows in report.",
                    note_style
                ))
        
        # Add footer with page numbers
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 9)
            page_num = canvas.getPageNumber()
            text = f"Page {page_num}"
            canvas.drawRightString(7.5*inch, 0.5*inch, text)
            canvas.restoreState()
        
        # Build PDF
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        
        logger.info(f"[ReportUtils] ✅ PDF report generated successfully: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logger.error(f"[ReportUtils] ❌ Failed to generate PDF report: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def save_chart_from_base64(chart_base64: str, filename: str) -> str:
    """
    Save a base64-encoded chart image to file.
    
    Args:
        chart_base64 (str): Base64-encoded image data
        filename (str): Desired filename
        
    Returns:
        str: Path to saved chart file
    """
    try:
        charts_dir = 'charts'
        os.makedirs(charts_dir, exist_ok=True)
        
        filepath = os.path.join(charts_dir, filename)
        
        # Decode and save
        img_data = base64.b64decode(chart_base64)
        with open(filepath, 'wb') as f:
            f.write(img_data)
        
        logger.info(f"[ReportUtils] Chart saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"[ReportUtils] Error saving chart: {str(e)}")
        return None

if __name__ == '__main__':
    # Test report generation
    logger.info("[ReportUtils] Running test report generation")
    
    test_title = "Sample Groundwater Report"
    test_summary = "This report shows the total annual recharge for various districts. The data indicates significant variation across regions, with some districts showing much higher recharge rates than others."
    test_data = [
        {'district_name': 'District A', 'total_annual_recharge': 43617.1, 'year': 2024},
        {'district_name': 'District B', 'total_annual_recharge': 52341.8, 'year': 2024},
        {'district_name': 'District C', 'total_annual_recharge': 38920.5, 'year': 2024}
    ]
    test_sql = "SELECT district_name, total_annual_recharge, year FROM groundwater_data WHERE year = 2024"
    
    pdf_path = generate_pdf_report(
        title=test_title,
        summary=test_summary,
        data=test_data,
        sql=test_sql
    )
    
    if pdf_path:
        logger.info(f"[ReportUtils] ✅ Test report generated: {pdf_path}")
    else:
        logger.error("[ReportUtils] ❌ Test report generation failed")
