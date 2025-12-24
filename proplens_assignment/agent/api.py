from ninja import NinjaAPI, File, UploadedFile, Schema
from typing import List, Optional, Dict
from django.shortcuts import get_object_or_404
from .models import Property, Booking, Message
# from .rag_utils import ingest_brochure # Disabling old RAG for now
from .graph import app as agent_app
from langchain_core.messages import HumanMessage, AIMessage
import os
import uuid
import tempfile
from ninja.security import HttpBearer

api = NinjaAPI()

class ChatRequest(Schema):
    message: str
    conversation_id: str

class ChatResponse(Schema):
    response: str
    shortlisted_projects: Optional[List[str]] = None

@api.post("/agents/chat", response=ChatResponse)
def chat_agent(request, payload: ChatRequest):
    """
    Main chat endpoint.
    """
    cid = payload.conversation_id
    
    # Store user message
    Message.objects.create(
        conversation_id=cid,
        role='user',
        content=payload.message
    )
    
    # Retrieve history from DB
    db_messages = Message.objects.filter(conversation_id=cid).order_by('created_at')
    
    # Convert to LangChain format
    messages = []
    for msg in db_messages:
        if msg.role == 'user':
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
            
    initial_state = {
        "messages": messages,
        "conversation_id": cid
    }
    
    result = agent_app.invoke(initial_state)
    final_response = result.get("final_response", "I'm not sure how to respond to that.")
    
    # Store AI response
    Message.objects.create(
        conversation_id=cid,
        role='assistant',
        content=final_response
    )
    
    return {
        "response": final_response,
        "shortlisted_projects": [] # To be filled if available
    }

@api.post("/conversations")
def create_conversation(request):
    """
    Creates a new conversation session.
    """
    cid = str(uuid.uuid4())
    return {"conversation_id": cid}
