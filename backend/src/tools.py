from livekit.agents import function_tool, RunContext
from Session import SalonSessionInfo
import logging
import asyncio
from help_request import db,HelpRequest
from firebase_admin import firestore
from knowledge_base import KnowledgeBase
knowledge_base = KnowledgeBase()

async def _watch_timeout(request_id: str):
    """Runs 1-minute timeout check for unresolved requests."""
    try:
        await asyncio.sleep(60)  

        request_ref = db.collection("help_requests").document(request_id)
        snapshot = request_ref.get()
        if not snapshot.exists:
            return 

        data = snapshot.to_dict()
        if data.get("status") == "pending":
            print(f"[TIMEOUT] Moving {request_id} to history as unresolved")
            data["status"] = "unresolved"
            data["resolved_at"] = firestore.SERVER_TIMESTAMP
            data["response_message"] = "Supervisor did not respond in time."

            db.collection("history").document(request_id).set(data)
            request_ref.delete()
            
    except Exception as e:
        print(f"[TIMEOUT ERROR] {e}")
            
@function_tool
async def handle_unknown(context: RunContext[SalonSessionInfo], user_query: str):
    try:
        """Triggered when the AI doesn't know the answer. Escalates to a human supervisor. or any other action."""
        # logger.warning(f"Requesting help for query: {user_query}")
        print(f"[SUPERVISOR ALERT] User '{context.userdata.user_name}' needs help with: {user_query}")
        print(f"[SUPERVISOR ALERT] Participant SID: {context.userdata.participant_sid}")

        help_req = HelpRequest(query=user_query, user_id=context.userdata.participant_sid, user_name=context.userdata.user_name)

        doc_id = help_req.save()
        print(f"[SUPERVISOR ALERT] New help request: {user_query} (id={doc_id})")
        
        asyncio.create_task(_watch_timeout(doc_id))
        context.userdata.last_query = user_query
        context.userdata.escalated = True

        return "Let me check with my supervisor and get back to you."
    except Exception as e:
        print(f"[SUPERVISOR ERROR] {e}")
        return "I'm sorry, I'm having trouble reaching my supervisor right now."
    
@function_tool
async def salon_info(context: RunContext[SalonSessionInfo], question: str):
    try:
        kb_answer = await knowledge_base.find_all_answers(question)
        print(f"[KNOWLEDGE BASE] Searching for answers to: {question}")
        if kb_answer:
            return f"{kb_answer}"
    except Exception as e:
        print(f"[KNOWLEDGE BASE ERROR] {e}")
        return "I'm sorry, I'm having trouble accessing the knowledge base right now."

@function_tool
async def lookup_service_price(context: RunContext[SalonSessionInfo], service: str):
    try:
        """Check the price of a salon service."""
        print(f"User data: {context.userdata}")
        prices = {
            "haircut": "$40",
            "coloring": "$80",
            "manicure": "$25",
            "pedicure": "$35",
            "facial": "$60",
        }
        price = prices.get(service.lower())
        if price:
            return f"The price for a {service} is {price}. Luna Glow Salon is open 9am to 7pm, Monday through Saturday."
        else:
            return f"Sorry, I couldn’t find the price for {service}. Please ask the front desk."
    except Exception as e:
        print(f"[LOOKUP SERVICE PRICE ERROR] {e}")
        return "I'm sorry, I'm having trouble looking up the service price right now."