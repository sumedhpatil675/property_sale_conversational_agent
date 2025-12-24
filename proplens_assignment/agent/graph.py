import json
from typing import TypedDict, Annotated, List, Union, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agent.vanna_setup import setup_vanna_training
from agent.models import Booking, Lead
# from langchain_community.tools import DuckDuckGoSearchRun
from django.core.exceptions import ObjectDoesNotExist
import re

# Initialize Vanna
vn = setup_vanna_training()

class AgentState(TypedDict):
    messages: List[BaseMessage]
    conversation_id: Optional[str]
    intent: str
    sql_query: Optional[str]
    sql_result: Optional[str]
    search_result: Optional[str]
    final_response: str
    booking_status: Optional[str]

class MockSearchTool:
    def invoke(self, query):
        # Simulate a search result for demonstration since internet access/packages are restricted
        return f"[Mock Search Result] Information found for '{query}': \n" \
               f"- Nearby Schools: Gems World Academy (2km), North London Collegiate School (3km)\n" \
               f"- Hospitals: King's College Hospital (5km)\n" \
               f"- Market Trends: Property prices in this area have risen 5% in the last quarter."

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
search_tool = MockSearchTool()

def router_node(state: AgentState):
    messages = state['messages']
    last_message = messages[-1].content
    
    # Get last AI message for context if available
    context = ""
    if len(messages) > 1:
        last_ai_message = messages[-2].content if isinstance(messages[-2], AIMessage) else ""
        context = f"Previous AI Message: {last_ai_message}"

    # Enhanced classification
    prompt = ChatPromptTemplate.from_template(
        """
        You are a Real Estate Agent Router.
        Classify the user's intent based on the last message and conversation context.
        
        Context:
        {context}

        Options:
        - "recommend": User is stating preferences (budget, location, bedrooms), asking for suggestions, or saying "yes" to a suggestion offer.
        - "details": User is asking specific questions about a project (amenities, price, completion) that should be in the database.
        - "search": User is asking for external information not likely in the DB (schools, nearby hospitals, general market trends).
        - "book": User wants to schedule a visit, book a viewing, or is providing contact info.
        - "chat": Greetings, thanks, or general conversation.
        
        User Query: {query}
        
        Return only the keyword.
        """
    )
    chain = prompt | llm
    response = chain.invoke({"query": last_message, "context": context})
    intent = response.content.strip().lower()
    
    valid_intents = ["recommend", "details", "book", "chat", "search"]
    if intent not in valid_intents:
        intent = "chat"
        
    return {"intent": intent}

def recommend_node(state: AgentState):
    messages = state['messages']
    query = messages[-1].content
    
    try:
        enhanced_query = f"Find properties: {query}. Return name, city, price, bedrooms."
        sql = vn.generate_sql(enhanced_query)
        
        if "agent_property" not in sql:
             pass
             
        df = vn.run_sql(sql)
        
        if df is not None and not df.empty:
            result_str = df.to_markdown(index=False)
        else:
            result_str = "No properties found matching criteria."
            
        return {"sql_query": sql, "sql_result": result_str}
    except Exception as e:
        return {"sql_result": f"Error searching properties: {str(e)}"}

def details_node(state: AgentState):
    messages = state['messages']
    query = messages[-1].content
    
    try:
        sql = vn.generate_sql(query)
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
    try:
        # DuckDuckGo search
        result = search_tool.invoke(query)
        return {"search_result": result}
    except Exception as e:
        return {"search_result": f"Search failed: {str(e)}"}

def book_node(state: AgentState):
    messages = state['messages']
    last_message = messages[-1].content
    
    prompt = ChatPromptTemplate.from_template("""
    Extract the following booking details from the text:
    - Lead Name (name)
    - Lead Email (email)
    - Project Name (project)
    - City (city)
    
    Text: {text}
    
    Return a valid JSON object with keys: name, email, project, city. 
    Values should be null if not found.
    """)
    
    chain = prompt | llm
    response = chain.invoke({"text": last_message})
    
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
            Booking.objects.create(
                lead_name=name,
                lead_email=email,
                project_name=project,
                city=city or ""
            )
            booking_status = "confirmed"
        else:
            booking_status = "missing_info"
            
    except Exception as e:
        print(f"Error in book_node: {e}")
        booking_status = "error"
        
    return {"booking_status": booking_status}

def generator_node(state: AgentState):
    intent = state['intent']
    messages = state['messages']
    last_message = messages[-1].content
    sql_result = state.get('sql_result')
    search_result = state.get('search_result')
    booking_status = state.get('booking_status')
    
    if intent == "recommend":
        prompt = f"""
        User asked: {last_message}
        
        Database Results:
        {sql_result}
        
        Task: Recommend 1-3 suitable projects from the results. 
        Highlight key features (Price, City, Beds). 
        Ask if they want to see more details or book a visit.
        """
    elif intent == "details":
        prompt = f"""
        User asked: {last_message}
        
        Database Information:
        {sql_result}
        
        Task: Answer the user's question accurately based on the data.
        If data is missing, admit it.
        """
    elif intent == "search":
        prompt = f"""
        User asked: {last_message}
        
        Web Search Results:
        {search_result}
        
        Task: Answer the user's question using the web search results.
        Cite the source if possible.
        """
    elif intent == "book":
        if booking_status == "confirmed":
            prompt = f"""
            User said: {last_message}
            Booking Status: Confirmed.
            
            Task: Confirm the booking to the user enthusiastically. Mention we will contact them shortly.
            """
        else:
            prompt = f"""
            User said: {last_message}
            Booking Status: Missing Information.
            
            Task: Politely ask for the missing information (Name, Email, or Project Name) to complete the booking.
            """
    else:
        # Chat intent: Include history for context-aware response
        history = "\n".join([f"{m.type}: {m.content}" for m in messages[-4:]]) # Last 4 messages
        prompt = f"""
        Conversation History:
        {history}
        
        You are a helpful Real Estate Sales Assistant for 'Silver Land Properties'.
        Respond to the user's last message naturally based on the history.
        If they are saying hello, greet them and ask about preferences (City, Budget, Bedrooms).
        If they are responding to a question, continue the flow naturally.
        If the conversation history shows you just provided information (like search results) and the user hasn't asked a new question, simply ask if they need help with anything else or if they would like to proceed with a booking.
        """
        
    response = llm.invoke(prompt)
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
