import os
import sys
import django
import json
import uuid

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from agent.api import api, chat_agent, create_conversation, ChatRequest
from agent.models import Lead, Booking
from langchain_core.messages import HumanMessage, AIMessage

def test_flow():
    # 1. Create Conversation
    print("--- 1. Creating Conversation ---")
    conv_id = str(uuid.uuid4())
    print(f"Conversation ID: {conv_id}")

    # 2. Greet
    print("\n--- 2. User says 'Hi' ---")
    req = ChatRequest(message="Hi", conversation_id=conv_id)
    resp = chat_agent(None, req)
    print(f"Agent: {resp['response']}")

    # 3. Preferences
    print("\n--- 3. User provides preferences ---")
    req = ChatRequest(message="I'm looking for a 2 bedroom apartment in Dubai under 1 million USD.", conversation_id=conv_id)
    resp = chat_agent(None, req)
    print(f"Agent: {resp['response']}")
    
    # 4. Specific Details (DB)
    print("\n--- 4. User asks for details ---")
    # Pick a project name from previous response if possible, or just ask generic
    req = ChatRequest(message="Tell me more about Chelsea Residences by Damac.", conversation_id=conv_id)
    resp = chat_agent(None, req)
    print(f"Agent: {resp['response']}")

    # 5. External Info (Search)
    print("\n--- 5. User asks for external info ---")
    req = ChatRequest(message="What are the best schools near Downtown Dubai?", conversation_id=conv_id)
    resp = chat_agent(None, req)
    print(f"Agent: {resp['response']}")

    # 6. Booking
    print("\n--- 6. User wants to book ---")
    req = ChatRequest(message="I'd like to book a viewing for Chelsea Residences. My name is Jane Doe and email is jane@example.com", conversation_id=conv_id)
    resp = chat_agent(None, req)
    print(f"Agent: {resp['response']}")
    
    # 7. Verify DB
    print("\n--- 7. Verifying DB ---")
    lead = Lead.objects.filter(email="jane@example.com").first()
    if lead:
        print(f"Lead Found: {lead.first_name} {lead.last_name}")
    else:
        print("Lead NOT Found!")

    booking = Booking.objects.filter(lead_email="jane@example.com").first()
    if booking:
        print(f"Booking Found: {booking.project_name}")
    else:
        print("Booking NOT Found!")

if __name__ == "__main__":
    test_flow()

