import os
import logging
from typing import Dict, Any
from utils.report_utils import generate_pdf_report

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Store last SQL response for report generation
last_sql_response = {}

def store_sql_response(response: Dict[str, Any]):
    """
    Store the last SQL response for potential report generation.
    Phase 4: Capture SQL results for PDF reports.
    """
    global last_sql_response
    last_sql_response = response
    logger.info(f"[ReportAgent] Stored SQL response for report generation: {len(response.get('data', []))} rows")

def report_agent_node(input_data: dict) -> dict:
    """
    Generate report preview or final PDF.
    Phase 4: Report generation from previous SQL results.
    
    Args:
        input_data (dict): {'prompt': str, 'confirm': bool (optional)}
        
    Returns:
        dict: {'status': 'success', 'preview': dict} or {'status': 'success', 'pdf_path': str}
    """
    try:
        prompt = input_data.get('prompt', '')
        confirm = input_data.get('confirm', False)
        
        logger.info(f"[ReportAgent] Phase 4 - Report request: {prompt[:50]}... (confirm={confirm})")
        
        # Check if we have previous SQL data
        if not last_sql_response or not last_sql_response.get('data'):
            logger.warning("[ReportAgent] No SQL data available for report")
            return {
                'status': 'error',
                'error': 'No data available to generate report. Please run a query first.',
                'text': '❌ No data available for report generation.\n\nPlease run a SQL query first, then request a report.'
            }
        
        # If not confirmed, return preview
        if not confirm:
            logger.info("[ReportAgent] Returning report preview")
            
            preview = {
                'title': last_sql_response.get('title', 'Data Report'),
                'summary': last_sql_response.get('summary', ''),
                'sql': last_sql_response.get('sql', ''),
                'data_count': len(last_sql_response.get('data', [])),
                'has_chart': last_sql_response.get('chart_html') is not None
            }
            
            logger.info(f"[ReportAgent] Preview: {preview['data_count']} rows, chart={preview['has_chart']}")
            
            return {
                'status': 'success',
                'preview': preview,
                'text': '📄 **Report Preview**\n\nI\'ve prepared a report with the data from your last query. Review the contents below and click "Generate PDF" to download.'
            }
        
        # Generate PDF
        else:
            logger.info("[ReportAgent] Generating PDF report")
            
            # Extract data from last response
            title = last_sql_response.get('title', 'Data Report')
            summary = last_sql_response.get('summary')
            data = last_sql_response.get('data')
            sql = last_sql_response.get('sql')
            chart_path = last_sql_response.get('chart_path')
            
            logger.info(f"[ReportAgent] PDF inputs - title: {title[:30]}..., summary: {bool(summary)}, data: {len(data)} rows, chart: {bool(chart_path)}")
            
            # Generate PDF
            pdf_path = generate_pdf_report(
                title=title,
                summary=summary,
                data=data,
                chart_path=chart_path,
                sql=sql
            )
            
            if pdf_path:
                logger.info(f"[ReportAgent] ✅ PDF generated successfully: {pdf_path}")
                return {
                    'status': 'success',
                    'pdf_path': pdf_path,
                    'text': '✅ Report generated successfully! Your PDF download should begin automatically.'
                }
            else:
                logger.error("[ReportAgent] PDF generation failed")
                return {
                    'status': 'error',
                    'error': 'Failed to generate PDF',
                    'text': '❌ Failed to generate PDF report. Please try again.'
                }
                
    except Exception as e:
        logger.error(f"[ReportAgent] Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'status': 'error',
            'error': str(e),
            'text': f'❌ Error generating report: {str(e)}'
        }

# For testing
if __name__ == '__main__':
    logger.info("[ReportAgent] Running test")
    
    # Simulate SQL response
    test_response = {
        'title': 'Test Report - Districts by Recharge',
        'summary': 'This report shows the top districts by total annual recharge.',
        'data': [
            {'district_name': 'District A', 'total_annual_recharge': 45000.0},
            {'district_name': 'District B', 'total_annual_recharge': 38000.0}
        ],
        'sql': 'SELECT district_name, total_annual_recharge FROM groundwater_data',
        'chart_html': '<div>Chart placeholder</div>',
        'chart_path': None
    }
    
    store_sql_response(test_response)
    
    # Test preview
    preview_result = report_agent_node({'prompt': 'generate report', 'confirm': False})
    logger.info(f"Preview result: {preview_result}")
    
    # Test PDF generation
    pdf_result = report_agent_node({'prompt': 'generate report', 'confirm': True})
    logger.info(f"PDF result: {pdf_result}")
