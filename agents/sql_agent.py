import os
import logging
from dotenv import load_dotenv
import pandas as pd
import plotly
import plotly.graph_objects as go
from vanna.vannadb import VannaDB_VectorStore
from vanna.google import GoogleGeminiChat
from google.generativeai import GenerativeModel, configure

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()
logger.info("Loaded .env file")

# Custom Vanna class for Gemini and MySQL
class MyVanna(VannaDB_VectorStore, GoogleGeminiChat):
    def __init__(self, config=None):
        MY_VANNA_MODEL = 'ingres_model'  # Replace with your model name from vanna.ai
        VANNA_API_KEY = os.getenv('VANNA_API_KEY')
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-lite')

        logger.info(f"VANNA_API_KEY: {'Set' if VANNA_API_KEY else 'Not set'}")
        logger.info(f"GEMINI_API_KEY: {'Set' if GEMINI_API_KEY else 'Not set'}")
        logger.info(f"GEMINI_MODEL: {GEMINI_MODEL}")

        if not VANNA_API_KEY or not GEMINI_API_KEY:
            raise ValueError("Missing VANNA_API_KEY or GEMINI_API_KEY")

        VannaDB_VectorStore.__init__(self, vanna_model=MY_VANNA_MODEL, vanna_api_key=VANNA_API_KEY, config=config)
        GoogleGeminiChat.__init__(self, config={'api_key': GEMINI_API_KEY, 'model_name': GEMINI_MODEL})

# Database credentials
def get_mysql_credentials():
    creds = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'dbname': os.getenv('MYSQL_DBNAME', 'ingres_db'),
        'user': os.getenv('MYSQL_USER', 'your_user'),
        'password': os.getenv('MYSQL_PASSWORD', 'your_password'),
        'port': int(os.getenv('MYSQL_PORT', 3306))
    }
    logger.info(f"MySQL credentials: host={creds['host']}, dbname={creds['dbname']}, user={creds['user']}, port={creds['port']}")
    return creds

# Initialize Vanna
vn = MyVanna()

# Initialize Gemini for summary generation
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
if GEMINI_API_KEY:
    configure(api_key=GEMINI_API_KEY)
    summary_model = GenerativeModel(GEMINI_MODEL)
    logger.info(f"Summary generation model initialized: {GEMINI_MODEL}")
else:
    logger.warning("GEMINI_API_KEY not found, summaries will not be generated")
    summary_model = None

# Global flag to track if Vanna is initialized
_vanna_initialized = False

def initialize_vanna():
    """
    Initialize Vanna connection and training at app startup.
    Should be called once when the app starts.
    """
    global _vanna_initialized
    if _vanna_initialized:
        logger.info("Vanna already initialized, skipping")
        return
    
    logger.info("Connecting to database and training Vanna...")
    connect_to_db()
    train_vanna()
    _vanna_initialized = True
    logger.info("Vanna initialization complete")

# Connect to MySQL
def connect_to_db():
    creds = get_mysql_credentials()
    try:
        vn.connect_to_mysql(**creds)
        logger.info("Connected to MySQL database: ingres_db")
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {str(e)}")
        raise

# Train Vanna with schema
def train_vanna():
    try:
        # Train with schema
        df_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'ingres_db'")
        plan = vn.get_training_plan_generic(df_schema)
        vn.train(plan=plan)
        logger.info("Schema training completed")
        
        # Train with DDL (fallback if documentation fails)
        try:
            vn.train(ddl="""
            CREATE TABLE states (
                state_id INT PRIMARY KEY,
                state_name VARCHAR(100)
            );
            CREATE TABLE districts (
                district_id INT PRIMARY KEY,
                district_name VARCHAR(100),
                state_id INT,
                FOREIGN KEY (state_id) REFERENCES states(state_id)
            );
            CREATE TABLE groundwater_data (
                id INT PRIMARY KEY,
                district_id INT,
                year INT,
                monsoon_recharge_rainfall DECIMAL(10,2),
                monsoon_recharge_other DECIMAL(10,2),
                nonmonsoon_recharge_rainfall DECIMAL(10,2),
                nonmonsoon_recharge_other DECIMAL(10,2),
                total_annual_recharge DECIMAL(10,2),
                total_natural_discharges DECIMAL(10,2),
                annual_extractable_resource DECIMAL(10,2),
                extraction_irrigation DECIMAL(10,2),
                extraction_industrial DECIMAL(10,2),
                extraction_domestic DECIMAL(10,2),
                extraction_total DECIMAL(10,2),
                gw_allocation_domestic_2025 DECIMAL(10,2),
                net_gw_availability_future DECIMAL(10,2),
                stage_of_extraction DECIMAL(10,2),
                FOREIGN KEY (district_id) REFERENCES districts(district_id)
            );
            """)
            logger.info("DDL training completed")
        except Exception as e:
            logger.warning(f"DDL training failed, proceeding without: {str(e)}")
            
    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        if 'No email' in str(e):
            logger.warning("Vanna training failed due to missing email. Queries may still work with pre-trained model.")
        else:
            raise

def create_fallback_chart(df: pd.DataFrame, question: str) -> go.Figure:
    """
    Create a fallback Plotly chart when Vanna's generation fails.
    Intelligently selects chart type based on data structure.
    
    Args:
        df (pd.DataFrame): Query results
        question (str): User's question for context
        
    Returns:
        go.Figure: Plotly figure or None if unsuitable
    """
    try:
        logger.info(f"[Fallback] Creating fallback chart for {len(df)} rows, {len(df.columns)} columns")
        
        # Too many columns or too few rows - skip chart
        if len(df.columns) > 10 or len(df) < 1:
            logger.info("[Fallback] Data not suitable for visualization")
            return None
        
        # Get numeric and text columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        text_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        logger.info(f"[Fallback] Numeric columns: {numeric_cols}, Text columns: {text_cols}")
        
        # Case 1: One text column + one numeric column = Bar chart
        if len(text_cols) == 1 and len(numeric_cols) == 1:
            x_col = text_cols[0]
            y_col = numeric_cols[0]
            
            # Limit to top 20 for readability
            df_plot = df.nlargest(20, y_col) if len(df) > 20 else df
            
            fig = go.Figure(data=[
                go.Bar(
                    x=df_plot[x_col],
                    y=df_plot[y_col],
                    marker=dict(color='#667eea')
                )
            ])
            
            fig.update_layout(
                title=f"{y_col} by {x_col}",
                xaxis_title=x_col,
                yaxis_title=y_col,
                showlegend=False
            )
            
            logger.info(f"[Fallback] Created bar chart: {x_col} vs {y_col}")
            return fig
        
        # Case 2: Multiple numeric columns = Line/Multi-bar chart
        elif len(numeric_cols) >= 2 and len(text_cols) >= 1:
            x_col = text_cols[0]
            
            # Limit to top 15 categories and first 3 numeric columns
            df_plot = df.head(15)
            numeric_cols_subset = numeric_cols[:3]
            
            fig = go.Figure()
            
            for col in numeric_cols_subset:
                fig.add_trace(go.Bar(
                    x=df_plot[x_col],
                    y=df_plot[col],
                    name=col
                ))
            
            fig.update_layout(
                title=f"Comparison across {x_col}",
                xaxis_title=x_col,
                yaxis_title="Values",
                barmode='group'
            )
            
            logger.info(f"[Fallback] Created grouped bar chart with {len(numeric_cols_subset)} series")
            return fig
        
        # Case 3: Single numeric column only = Simple bar with index
        elif len(numeric_cols) == 1 and len(text_cols) == 0:
            y_col = numeric_cols[0]
            df_plot = df.head(20)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=df_plot.index,
                    y=df_plot[y_col],
                    marker=dict(color='#667eea')
                )
            ])
            
            fig.update_layout(
                title=f"{y_col} Distribution",
                xaxis_title="Index",
                yaxis_title=y_col,
                showlegend=False
            )
            
            logger.info(f"[Fallback] Created indexed bar chart for {y_col}")
            return fig
        
        else:
            logger.info("[Fallback] No suitable chart pattern found")
            return None
            
    except Exception as e:
        logger.error(f"[Fallback] Error creating fallback chart: {str(e)}")
        return None

def generate_data_summary(question: str, sql: str, data: list, max_results: int = 10) -> str:
    """
    Generate a concise AI summary of the SQL query results.
    Phase 2 Enhancement: Natural language insights from data.
    
    Args:
        question (str): User's original question
        sql (str): SQL query that was executed
        data (list): Query results as list of dicts
        max_results (int): Max rows to include in summary prompt
        
    Returns:
        str: Concise natural language summary
    """
    if not summary_model or not data:
        return None
    
    try:
        logger.info(f"[Summary] Generating summary for {len(data)} results")
        
        # Prepare data sample for summary (limit to avoid token overflow)
        data_sample = data[:max_results]
        
        # Convert data to readable format
        if len(data) == 1:
            data_text = f"Single result: {data_sample[0]}"
        else:
            data_text = f"Sample of {len(data_sample)} results from {len(data)} total:\n"
            for i, row in enumerate(data_sample, 1):
                data_text += f"{i}. {row}\n"
        
        prompt = (
            "You are a data analyst. Provide a concise, insightful 2-3 sentence summary of the query results.\n\n"
            "Guidelines:\n"
            "- Focus on key insights and patterns\n"
            "- Use natural, conversational language\n"
            "- Mention specific numbers when relevant\n"
            "- Be concise but informative\n"
            "- If appropriate, note interesting trends or outliers\n\n"
            f"User Question: {question}\n\n"
            f"SQL Query: {sql}\n\n"
            f"Results ({len(data)} rows):\n{data_text}\n\n"
            "Provide your 2-3 sentence summary:"
        )
        
        response = summary_model.generate_content(prompt)
        summary = response.text.strip()
        
        logger.info(f"[Summary] Generated: {summary[:100]}...")
        return summary
        
    except Exception as e:
        logger.error(f"[Summary] Error generating summary: {str(e)}")
        return None

# SQL Agent Node for orchestrator
def sql_agent_node(input_data: dict) -> dict:
    """
    Handle SQL queries from the orchestrator.
    Phase 2: Text-to-SQL with Vanna.ai + Plotly chart generation + AI summary.
    
    Args:
        input_data (dict): {'message': str, 'context': list}
        
    Returns:
        dict: {'status': 'success'/'error', 'text': str, 'sql': str, 'data': list, 'chart_html': str, 'summary': str}
    """
    try:
        message = input_data.get('message', '')
        logger.info(f"[SQLAgent] Phase 2 - Processing query: {message[:50]}...")
        
        # Initialize Vanna if not already done (fallback if app.py didn't initialize)
        global _vanna_initialized
        if not _vanna_initialized:
            logger.info("[SQLAgent] Vanna not initialized, initializing now...")
            try:
                initialize_vanna()
            except Exception as e:
                logger.warning(f"[SQLAgent] DB connection/training issue: {str(e)}. Proceeding anyway.")
        
        # Call the text-to-sql function
        logger.info("[SQLAgent] Calling text_to_sql_agent with visualization enabled")
        result = text_to_sql_agent(message, visualize=True)
        
        if 'error' in result:
            logger.error(f"[SQLAgent] Error from text_to_sql_agent: {result['error']}")
            return {'status': 'error', 'error': result['error']}
        
        # Format response
        sql = result.get('sql', 'N/A')
        data = result.get('result', [])
        chart_html = result.get('chart_html')
        
        logger.info(f"[SQLAgent] 📦 Building response - data rows: {len(data)}, chart_html present: {chart_html is not None}")
        
        # Generate AI summary of results
        summary = None
        if data:
            summary = generate_data_summary(message, sql, data)
        
        # Build text response with summary
        text_response = f"✅ Query executed successfully!\n\n"
        
        if summary:
            text_response += f"📝 **Summary:**\n{summary}\n\n"
        
        text_response += f"📊 **SQL Query:**\n{sql}\n\n"
        
        if data:
            text_response += f"Found {len(data)} result(s)."
        else:
            text_response += "No results found."
        
        response = {
            'status': 'success',
            'text': text_response,
            'sql': sql,
            'data': data,
            'show_table': len(data) > 0,  # Flag to show table in frontend
            'summary': summary  # Add summary to response
        }
        
        # Add chart HTML and data if available (Plotly interactive chart)
        if chart_html:
            response['chart_html'] = chart_html
            logger.info(f"[SQLAgent] ✅ Added chart_html to response ({len(chart_html)} chars)")
            # Phase 5: Add chart data for dashboard pinning
            if result.get('chart_data'):
                response['chart_data'] = result['chart_data']
                logger.info(f"[SQLAgent] ✅ Added chart_data to response for pinning")
        else:
            logger.warning("[SQLAgent] ⚠️ No chart_html in result - chart will not display")
        
        logger.info(f"[SQLAgent] Final response keys: {list(response.keys())}")
        logger.info(f"[SQLAgent] Returning {len(data)} rows and {'chart' if chart_html else 'no chart'}")
        
        # Phase 4: Store response for potential report generation
        if response['status'] == 'success' and response.get('data'):
            try:
                from agents.report_agent import store_sql_response
                
                # Save chart as image file for PDF if chart_html exists
                chart_path = None
                if chart_html:
                    try:
                        # Re-generate figure from Plotly code to save as image
                        logger.info("[SQLAgent] 💾 Converting chart to image for PDF report...")
                        import pandas as pd
                        result_df = pd.DataFrame(data)
                        plotly_code = vn.generate_plotly_code(
                            question=message,
                            sql=sql,
                            df_metadata=f"Running df.dtypes gives:\n{result_df.dtypes}"
                        )
                        fig = vn.get_plotly_figure(plotly_code=plotly_code, df=result_df, dark_mode=False)
                        
                        if fig:
                            # Ensure charts directory exists
                            os.makedirs('charts', exist_ok=True)
                            
                            # Generate unique filename
                            from datetime import datetime
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            chart_path = f"charts/chart_{timestamp}.png"
                            
                            # Save as PNG using kaleido (Plotly's static image export)
                            fig.write_image(chart_path, width=1200, height=600, scale=2)
                            logger.info(f"[SQLAgent] ✅ Chart saved to {chart_path}")
                        else:
                            logger.warning("[SQLAgent] ⚠️ Could not regenerate figure for image export")
                    except Exception as img_error:
                        logger.warning(f"[SQLAgent] ⚠️ Failed to save chart as image: {str(img_error)}")
                        logger.warning("[SQLAgent] ℹ️ Install kaleido for chart export: pip install kaleido")
                
                store_sql_response({
                    'title': f"Query Results - {message[:50]}",
                    'summary': summary,
                    'data': data,
                    'sql': sql,
                    'chart_html': chart_html,
                    'chart_path': chart_path
                })
                logger.info(f"[SQLAgent] ✅ Stored SQL response for report generation (chart_path: {chart_path})")
            except Exception as e:
                logger.warning(f"[SQLAgent] Failed to store SQL response for reports: {str(e)}")
        
        return response
        
    except Exception as e:
        logger.error(f"[SQLAgent] Error: {str(e)}")
        return {'status': 'error', 'error': f"SQL Agent error: {str(e)}"}

# Text-to-SQL Agent (internal function)
def text_to_sql_agent(question: str, visualize: bool = True):
    try:
        logger.info(f"Processing question: {question}")
        # Generate SQL
        sql = vn.generate_sql(question=question)
        if not sql:
            logger.error("Failed to generate SQL")
            return {"error": "Failed to generate SQL"}

        logger.info(f"Generated SQL: {sql}")
        # Execute SQL
        result_df = vn.run_sql(sql)
        if result_df.empty:
            logger.info("Query returned no results")
            return {"sql": sql, "result": [], "chart_path": None, "chart_html": None}

        # Visualize using Vanna's built-in Plotly chart generation
        chart_html = None
        chart_data = None  # Phase 5: Store chart data for pinning
        if visualize and len(result_df) > 0:
            try:
                logger.info(f"🎨 Generating Plotly chart for question: {question}")
                logger.info(f"DataFrame shape: {result_df.shape}, columns: {result_df.columns.tolist()}")
                
                # Use Vanna's built-in chart generation
                # First, generate Plotly code
                logger.info("Step 1: Generating Plotly code via Vanna...")
                plotly_code = vn.generate_plotly_code(
                    question=question,
                    sql=sql,
                    df_metadata=f"Running df.dtypes gives:\n{result_df.dtypes}"
                )
                logger.info(f"✓ Generated Plotly code (first 300 chars): {plotly_code[:300]}...")
                
                # Get the Plotly figure
                logger.info("Step 2: Creating Plotly figure...")
                fig = vn.get_plotly_figure(plotly_code=plotly_code, df=result_df, dark_mode=False)
                
                # Check if Vanna returned a valid figure
                if fig is None:
                    logger.warning("⚠️ Vanna returned None figure, using fallback chart generation")
                    fig = create_fallback_chart(result_df, question)
                
                if fig is None:
                    logger.error("❌ Failed to create any chart")
                    chart_html = None
                    chart_data = None
                else:
                    logger.info(f"✓ Figure created: {type(fig)}, data traces: {len(fig.data)}")
                    
                    # Ensure figure has proper layout with dimensions
                    fig.update_layout(
                        height=500,
                        autosize=True,
                        margin=dict(l=60, r=40, t=80, b=60),
                        showlegend=True
                    )
                    logger.info(f"✓ Updated figure layout with height=500, traces: {len(fig.data)}")
                    
                    # Extract chart data for pinning (Phase 5)
                    import json
                    chart_data = {
                        'data': json.loads(fig.to_json())['data'],
                        'layout': json.loads(fig.to_json())['layout']
                    }
                    logger.info(f"✓ Extracted chart data with {len(chart_data['data'])} traces")
                    
                    # Convert to HTML for embedding (only div, no full page)
                    # Use unique div ID to avoid conflicts with multiple charts
                    import time
                    unique_id = f"plotly-chart-{int(time.time() * 1000)}"
                    logger.info(f"Step 3: Converting to HTML with unique ID: {unique_id}")
                    chart_html = fig.to_html(
                        include_plotlyjs=False,  # Don't include Plotly.js (already in head)
                        div_id=unique_id,
                        full_html=False,  # Only return the div, not full HTML document
                        config={'responsive': True, 'displayModeBar': True}
                    )
                    logger.info(f"✓ Chart HTML generated, length: {len(chart_html)} chars")
                    logger.info(f"Chart HTML preview (first 500 chars): {chart_html[:500]}")
                
            except Exception as e:
                logger.error(f"❌ Plotly visualization error: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                chart_html = None

        return {
            'sql': sql,
            'result': result_df.to_dict(orient='records'),
            'chart_html': chart_html,
            'chart_data': chart_data if chart_html else None  # Phase 5: Include chart data for pinning
        }
    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        return {"error": f"Query execution error: {str(e)}"}

# Main function for testing
def main():
    # Connect and train
    connect_to_db()
    train_vanna()

    # Test query
    test_question = "What is the total annual recharge by district in 2024?"
    result = text_to_sql_agent(test_question)
    
    # Print results
    logger.info("\nTest Query Results:")
    logger.info(f"Question: {test_question}")
    logger.info(f"SQL: {result.get('sql', 'N/A')}")
    logger.info(f"Result: {result.get('result', result.get('error', 'No results'))}")
    logger.info(f"Chart Path: {result.get('chart_path', 'No chart generated')}")

if __name__ == "__main__":
    main()