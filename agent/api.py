from ninja_extra import NinjaExtraAPI, api_controller, route, ControllerBase
from ninja import Schema
from typing import List, Optional, Dict
from django.shortcuts import get_object_or_404
from .models import Property, VisitBooking, Message
from .graph import app as agent_app
from langchain_core.messages import HumanMessage, AIMessage
import uuid
from ninja.security import HttpBearer
from datetime import datetime

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        if token == "supersecret":
            return token
        return None

api = NinjaExtraAPI(auth=AuthBearer())

class ChatRequest(Schema):
    message: str
    conversation_id: str

class ChatResponse(Schema):
    response: str
    shortlisted_projects: Optional[List[str]] = None

class BookingSchema(Schema):
    lead_name: str
    lead_email: str
    project_name: str
    city: Optional[str] = None
    booking_date: datetime

class ConversationResponse(Schema):
    conversation_id: str

@api_controller("/agents", tags=["Agents"])
class AgentController(ControllerBase):
    @route.post("/chat", response=ChatResponse)
    def chat_agent(self, payload: ChatRequest):
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

@api_controller("", tags=["General"])
class GeneralController(ControllerBase):
    @route.post("/conversations", response=ConversationResponse)
    def create_conversation(self):
        """
        Creates a new conversation session.
        """
        cid = str(uuid.uuid4())
        return {"conversation_id": cid}

    @route.get("/bookings", response=List[BookingSchema])
    def list_bookings(self):
        """
        List all confirmed bookings.
        """
        bookings = VisitBooking.objects.all()
        return bookings

api.register_controllers(AgentController, GeneralController)
