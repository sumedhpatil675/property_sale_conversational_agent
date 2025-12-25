import json
from django.test import TestCase, Client
from agent.models import VisitBooking, Lead, Message
from unittest.mock import patch, MagicMock

class AgentFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.headers = {"HTTP_AUTHORIZATION": "Bearer supersecret"}

    def test_conversation_flow(self):
        # 1. Create Conversation
        response = self.client.post(
            "/api/conversations", 
            content_type="application/json",
            **self.headers
        )
        self.assertEqual(response.status_code, 201)
        conv_id = response.json().get("conversation_id")
        self.assertTrue(conv_id)

        # 2. Chat - Greeting
        payload = {"conversation_id": conv_id, "message": "Hi"}
        with patch("agent.graph.app.invoke") as mock_invoke:
            mock_invoke.return_value = {"final_response": "Hello! How can I help?"}
            response = self.client.post(
                "/api/agents/chat",
                data=payload,
                content_type="application/json",
                **self.headers
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["response"], "Hello! How can I help?")

        # 3. Check Message Persistence
        self.assertEqual(Message.objects.count(), 2) # User + Assistant

    def test_booking_retrieval(self):
        VisitBooking.objects.create(
            lead_name="Test User",
            lead_email="test@example.com",
            project_name="Test Project",
            city="Dubai"
        )
        response = self.client.get("/api/bookings", **self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["lead_name"], "Test User")

    def test_unauthorized_access(self):
        response = self.client.get("/api/bookings") # No header
        self.assertEqual(response.status_code, 401)
