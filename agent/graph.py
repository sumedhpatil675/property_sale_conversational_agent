import json
import os
import logging
from typing import TypedDict, Annotated, List, Union, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from agent.vanna_setup import get_vanna_instance
from agent.models import VisitBooking, Lead
# from langchain_community.tools import DuckDuckGoSearchRun
from django.core.exceptions import ObjectDoesNotExist
import re

logger = logging.getLogger(__name__)

# Import prompts
from agent.prompts.router import ROUTER_PROMPT
from agent.prompts.generator import GENERATOR_PROMPT_TEMPLATE
from agent.prompts.book import BOOK_PROMPT
from agent.prompts.recommend import RECOMMEND_SYSTEM_PROMPT
# details and search prompts are available but logic is simple enough here for now

# Initialize Vanna
vn = get_vanna_instance()

class AgentState(TypedDict):
    messages: List[BaseMessage]
    conversation_id: Optional[str]
    intent: str
    sql_query: Optional[str]
    sql_result: Optional[str]
    search_result: Optional[str]
    final_response: str
    booking_status: Optional[str]

# Set Tavily API Key
os.environ["TAVILY_API_KEY"] = "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"

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
search_tool = TavilySearchResults(max_results=3)

def rewrite_query(query: str, messages: List[BaseMessage]) -> str:
    """Rewrites the query to include context from history."""
    if len(messages) <= 1:
        return query
        
    history = "\n".join([f"{m.type}: {m.content}" for m in messages[-4:-1]])
    if not history:
        return query
        
    prompt = f"""Based on the conversation history, rewrite the user's latest query to include necessary context (like location, property name, or project) if missing from the query itself.
    
    IMPORTANT GUIDELINES:
    1. Do NOT add the agency name (e.g., "Silver Land Properties") to the query.
    2. Do NOT add "from <Company Name>" unless the user explicitly mentioned a specific developer (e.g., Emaar, Damac).
    3. Keep the query focused on property attributes (location, price, type, bedrooms).
    4. If the query is already complete, return it as is.
    
    History:
    {history}
    
    Latest Query: {query}
    
    Rewritten Query:"""
    
    try:
        response = llm.invoke(prompt)
        rewritten = response.content.strip()
        logger.info(f"Rewrote query: '{query}' -> '{rewritten}'")
        return rewritten
    except Exception as e:
        logger.error(f"Error rewriting query: {e}")
        return query

def router_node(state: AgentState):
    messages = state['messages']
    last_message = messages[-1].content
    
    # Get last AI message for context if available
    context = ""
    if len(messages) > 1:
        last_ai_message = messages[-2].content if isinstance(messages[-2], AIMessage) else ""
        context = f"Previous AI Message: {last_ai_message}"

    # Use imported ROUTER_PROMPT
    chain = ROUTER_PROMPT | llm
    response = chain.invoke({"query": last_message, "context": context})
    intent = response.content.strip().lower()
    
    logger.info(f"ROUTER: Detected intent '{intent}' for query: '{last_message}'")
    
    valid_intents = ["recommend", "details", "book", "chat", "search"]
    if intent not in valid_intents:
        # Default fallback
        intent = "chat"
        
    return {"intent": intent}

def recommend_node(state: AgentState):
    messages = state['messages']
    query = messages[-1].content
    
    # Contextualize query
    rewritten_query = rewrite_query(query, messages)
    
    try:
        # Vanna works better with clear instructions in the query or simple questions
        # enhanced_query = f"Find properties: {rewritten_query}. Return name, city, price, bedrooms."
        # Let's try passing the rewritten query directly, but asking for specific columns via Vanna training or prompt instructions
        # Vanna's generate_sql takes the question.
        
        # We append a hint to ensure columns are selected
        enhanced_query = f"{rewritten_query}. Include name, city, price, bedrooms in the result."
        
        logger.info(f"RECOMMEND: Generating SQL for query: '{enhanced_query}'")
        sql = vn.generate_sql(enhanced_query)
        logger.info(f"RECOMMEND: Generated SQL: {sql}")
        
        if "agent_property" not in sql:
             pass
             
        df = vn.run_sql(sql)
        
        if df is not None and not df.empty:
            logger.info(f"RECOMMEND: Found {len(df)} properties")
            result_str = df.to_markdown(index=False)
        else:
            logger.info("RECOMMEND: No properties found in DB")
            result_str = "No properties found matching criteria."
            
        return {"sql_query": sql, "sql_result": result_str}
    except Exception as e:
        return {"sql_result": f"Error searching properties: {str(e)}"}

def details_node(state: AgentState):
    messages = state['messages']
    query = messages[-1].content
    
    # Contextualize query
    rewritten_query = rewrite_query(query, messages)
    
    try:
        sql = vn.generate_sql(rewritten_query)
        df = vn.run_sql(sql)
        
        if df is not None and not df.empty:
            result_str = df.to_markdown(index=False)
        else:
            result_str = "No specific details found in database."
            
        return {"sql_query": sql, "sql_result": result_str}
    except Exception as e:
        return {"sql_result": f"Error fetching details: {str(e)}"}

def search_node(state: AgentState):
    messages = state['messages']
    query = messages[-1].content
    
    # Contextualize query
    rewritten_query = rewrite_query(query, messages)
    
    logger.info(f"SEARCH: Performing Tavily search for: '{rewritten_query}'")
    
    try:
        # Tavily search
        results = search_tool.invoke(rewritten_query)
        
        # Format results if they are a list
        if isinstance(results, list):
            formatted_results = "\n".join([
                f"- {r.get('content', '')} (Source: {r.get('url', '')})" 
                for r in results
            ])
            result = formatted_results
        else:
            result = str(results)
            
        return {"search_result": result}
    except Exception as e:
        return {"search_result": f"Search failed: {str(e)}"}

def book_node(state: AgentState):
    messages = state['messages']
    last_message = messages[-1].content
    
    # Extract history for context-aware booking
    history = "\n".join([f"{m.type}: {m.content}" for m in messages[-6:]])
    
    # Use imported BOOK_PROMPT
    chain = BOOK_PROMPT | llm
    response = chain.invoke({"text": last_message, "history": history})
    
    booking_status = "pending_info"
    
    try:
        content = response.content.strip()
        # Clean up json block if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        name = data.get("name")
        email = data.get("email")
        project = data.get("project")
        city = data.get("city")
        
        # Save Lead if email present
        if email:
            lead, created = Lead.objects.get_or_create(
                email=email, 
                defaults={'first_name': name or 'Unknown', 'last_name': '', 'preferences': last_message}
            )
            if name and lead.first_name == 'Unknown':
                lead.first_name = name
                lead.save()

        if name and email and project:
            # Create Booking
            VisitBooking.objects.create(
                lead_name=name,
                lead_email=email,
                project_name=project,
                city=city or ""
            )
            booking_status = "confirmed"
        else:
            booking_status = "missing_info"
            
    except Exception as e:
        logger.error(f"Error in book_node: {e}", exc_info=True)
        booking_status = "error"
        
    return {"booking_status": booking_status}

def generator_node(state: AgentState):
    intent = state['intent']
    messages = state['messages']
    last_message = messages[-1].content
    sql_result = state.get('sql_result', '')
    search_result = state.get('search_result', '')
    booking_status = state.get('booking_status', '')
    
    # Construct history string
    history = "\n".join([f"{m.type}: {m.content}" for m in messages[-4:]])
    
    # Use imported GENERATOR_PROMPT_TEMPLATE
    prompt = ChatPromptTemplate.from_template(GENERATOR_PROMPT_TEMPLATE)
    
    chain = prompt | llm
    response = chain.invoke({
        "intent": intent,
        "last_message": last_message,
        "sql_result": sql_result,
        "search_result": search_result,
        "booking_status": booking_status,
        "history": history
    })
    
    return {"final_response": response.content}

# Workflow
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("recommender", recommend_node)
workflow.add_node("detailer", details_node)
workflow.add_node("searcher", search_node)
workflow.add_node("booker", book_node)
workflow.add_node("generator", generator_node)

workflow.set_entry_point("router")

def route_decision(state):
    return state['intent']

workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "recommend": "recommender",
        "details": "detailer",
        "search": "searcher",
        "book": "booker",
        "chat": "generator"
    }
)

workflow.add_edge("recommender", "generator")
workflow.add_edge("detailer", "generator")
workflow.add_edge("searcher", "generator")
workflow.add_edge("booker", "generator")
workflow.add_edge("generator", END)

app = workflow.compile()
