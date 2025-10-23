import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from agents.chat_agent import chat_with_gemini
from agents.sql_agent import sql_agent_node
from agents.email_agent import email_agent_node
from agents.report_agent import report_agent_node

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define state schema for LangGraph
class ChatState(TypedDict):
    """State schema for chat workflow - Phase 4 includes SQL + Email + Report support"""
    message: str
    context: list
    response: dict
    intent: str

def chat_node(state: ChatState) -> ChatState:
    """
    LangGraph node for general chat conversation.
    
    Args:
        state (ChatState): Current workflow state with message and context
        
    Returns:
        ChatState: Updated state with response from chat agent
    """
    try:
        logger.info(f"[ChatNode] Processing message: {state['message'][:50]}...")
        message = state.get('message', '')
        context = state.get('context', [])
        
        # Call chat agent
        response = chat_with_gemini(message, context)
        logger.info(f"[ChatNode] Chat agent returned status: {response.get('status')}")
        
        # Update state
        state['response'] = response
        return state
        
    except Exception as e:
        logger.error(f"[ChatNode] Error in chat node: {str(e)}")
        state['response'] = {'status': 'error', 'error': f'Chat node error: {str(e)}'}
        return state

def sql_node(state: ChatState) -> ChatState:
    """
    LangGraph node for SQL data queries.
    Phase 2: Handles text-to-SQL conversion and chart generation.
    
    Args:
        state (ChatState): Current workflow state with message and context
        
    Returns:
        ChatState: Updated state with response from SQL agent (includes data, chart, SQL)
    """
    try:
        logger.info(f"[SQLNode] Processing SQL query: {state['message'][:50]}...")
        message = state.get('message', '')
        context = state.get('context', [])
        
        # Call SQL agent
        response = sql_agent_node({'message': message, 'context': context})
        logger.info(f"[SQLNode] SQL agent returned status: {response.get('status')}")
        
        if response.get('status') == 'success':
            logger.info(f"[SQLNode] Data rows: {len(response.get('data', []))}, Chart: {response.get('chart_html') is not None}")
        
        # Update state
        state['response'] = response
        return state
        
    except Exception as e:
        logger.error(f"[SQLNode] Error in SQL node: {str(e)}")
        state['response'] = {'status': 'error', 'error': f'SQL node error: {str(e)}'}
        return state

def email_node(state: ChatState) -> ChatState:
    """
    LangGraph node for email automation.
    Phase 3: Handles email draft generation using Gemini LLM.
    
    Args:
        state (ChatState): Current workflow state with message and context
        
    Returns:
        ChatState: Updated state with response from Email agent (includes draft)
    """
    try:
        logger.info(f"[EmailNode] Processing email request: {state['message'][:50]}...")
        message = state.get('message', '')
        
        # Call email agent
        response = email_agent_node({'prompt': message})
        logger.info(f"[EmailNode] Email agent returned status: {response.get('status')}")
        
        if response.get('status') == 'success' and 'draft' in response:
            logger.info(f"[EmailNode] Draft generated - Subject: {response['draft'].get('subject', 'N/A')}")
        
        # Update state
        state['response'] = response
        return state
        
    except Exception as e:
        logger.error(f"[EmailNode] Error in email node: {str(e)}")
        state['response'] = {'status': 'error', 'error': f'Email node error: {str(e)}'}
        return state

def report_node(state: ChatState) -> ChatState:
    """
    LangGraph node for report generation.
    Phase 4: PDF report generation from SQL results.
    
    Args:
        state (ChatState): Current workflow state with message and context
        
    Returns:
        ChatState: Updated state with response from Report agent (includes preview or PDF path)
    """
    try:
        logger.info(f"[ReportNode] Processing report request: {state['message'][:50]}...")
        message = state.get('message', '')
        
        # Call report agent
        response = report_agent_node({'prompt': message})
        logger.info(f"[ReportNode] Report agent returned status: {response.get('status')}")
        
        if response.get('status') == 'success' and 'preview' in response:
            logger.info(f"[ReportNode] Preview generated - {response['preview'].get('data_count', 0)} rows")
        elif response.get('status') == 'success' and 'pdf_path' in response:
            logger.info(f"[ReportNode] PDF generated: {response['pdf_path']}")
        
        # Update state
        state['response'] = response
        return state
        
    except Exception as e:
        logger.error(f"[ReportNode] Error in report node: {str(e)}")
        state['response'] = {'status': 'error', 'error': f'Report node error: {str(e)}'}
        return state

# Build the LangGraph workflow
def build_chat_graph():
    """
    Build LangGraph workflow for Phase 4 (chat + SQL + Email + Report).
    
    Returns:
        Compiled LangGraph workflow
    """
    logger.info("[Graph] Building Phase 4 workflow graph (chat + SQL + Email + Report)")
    
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("chat", chat_node)
    workflow.add_node("sql", sql_node)
    workflow.add_node("email", email_node)
    workflow.add_node("report", report_node)
    
    # Set entry point
    workflow.set_entry_point("chat")
    
    # Add edges
    workflow.add_edge("chat", END)
    workflow.add_edge("sql", END)
    workflow.add_edge("email", END)
    workflow.add_edge("report", END)
    
    # Compile workflow
    graph = workflow.compile()
    logger.info("[Graph] Phase 4 workflow compiled successfully (chat + SQL + Email + Report nodes)")
    
    return graph

# Create graph instance for import
chat_graph = build_chat_graph()
