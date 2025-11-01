from datetime import datetime
import logging

from help_request import HelpRequest
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    inference,
    metrics,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import function_tool, RunContext
from Session import SalonSessionInfo
from firebase_admin import firestore

import threading
import asyncio
from help_request import db
from queue import Queue

logger = logging.getLogger("agent")

load_dotenv(".env")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions = """
                You are Amritesh, a friendly, professional AI receptionist for Luna Glow Salon.
                You speak naturally and warmly, like a real front desk assistant.

                Your main goals:
                1. Greet clients and help them with bookings, service details, and pricing.
                2. Answer questions about salon hours, stylists, treatments, and appointments.
                3. If someone requests to speak to the owner, say you’ll note their message and pass it to the owner.
                4. If a question is outside your knowledge (e.g., “?”), politely say you'll check with the front desk, then call the `handle_unknown()` tool.
                5. Always stay friendly and positive — even if the client is frustrated or unclear.
                6. Avoid technical talk. Keep responses short and natural, since users are speaking aloud.
                7. If a user gives a name, service, or time preference, acknowledge it politely and confirm details.

                Example style:
                - “Hi! This is Amritesh at Luna Glow Salon. How can I make your day a little brighter?”
                - “Let me double-check that with the front desk, one moment please.”
                - “I’ll pass your request to the owner and make sure they get back to you soon.”

                Never mention being an AI or a virtual system — just act like the salon’s receptionist.
                """

        )

    async def handle_unknown(self, context: RunContext[SalonSessionInfo], user_query: str):
        """Triggered when the AI doesn't know the answer. Escalates to a human supervisor. or any other action."""
        logger.warning(f"Requesting help for query: {user_query}")
        print(f"[SUPERVISOR ALERT] User '{context.userdata.user_name}' needs help with: {user_query}")
        print(f"[SUPERVISOR ALERT] Participant SID: {context.userdata.participant_sid}")

        help_req = HelpRequest(query=user_query, user_id=context.userdata.participant_sid, user_name=context.userdata.user_name)

        doc_id = help_req.save()
        print(f"[SUPERVISOR ALERT] New help request: {user_query} (id={doc_id})")
        
        asyncio.create_task(self._watch_timeout(doc_id))
        context.userdata.last_query = user_query
        context.userdata.escalated = True

        return "Let me check with my supervisor and get back to you."
    
    @function_tool
    async def salon_info(self, context: RunContext, question: str):
        known_topics = ["hours", "price", "services", "location", "booking"]
        if any(word in question.lower() for word in known_topics):
            return "Luna Glow Salon is open 9am to 7pm, Monday through Saturday."
        else:
            return await self.handle_unknown(context, question)

    
    @function_tool
    async def lookup_service_price(self, context: RunContext[SalonSessionInfo], service: str):
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
            return f"The price for a {service} is {price}."
        else:
            return f"Sorry, I couldn’t find the price for {service}. Please ask the front desk."

    @function_tool
    async def lookup_weather(self, context: RunContext, location: str):
        """Use this tool to look up current weather information in the given location.
    
        If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    
        Args:
            location: The location to look up weather information for (e.g. city name)
        """
    
        logger.info(f"Looking up weather for {location}")
    
        return "sunny with a temperature of 70 degrees."
    
    async def _watch_timeout(self, request_id: str):
        """Runs 1-minute timeout check for unresolved requests."""
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


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    
def listen_for_supervisor_responses(session: AgentSession, message_queue: Queue):
    """Firestore watcher that pushes messages into a thread-safe queue."""
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == "ADDED":
                doc = change.document.to_dict()
                user_id = doc.get("user_id")
                message = doc.get("response_message")

                if user_id == session.userdata.participant_sid and message:
                    print(f"[SUPERVISOR RESPONSE] {message}")
                    message_queue.put(message)

    query = (
        db.collection("history")
        .where("user_id", "==", session.userdata.participant_sid)
    )

    query.on_snapshot(on_snapshot)

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession[SalonSessionInfo](
        userdata=SalonSessionInfo(),
        stt=inference.STT(model="assemblyai/universal-streaming", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    await session.generate_reply(
        instructions="Greet the user as a salon receptionist named Amritesh and ask how you can assist them with their beauty appointment."
    )

    await ctx.connect()
    participant = await ctx.wait_for_participant()
    
    session.userdata.user_name = participant.identity
    session.userdata.participant_sid = participant.sid
    
    message_queue = Queue()

    async def supervisor_message_consumer():
        while True:
            # wait for message from thread
            message = await asyncio.get_event_loop().run_in_executor(None, message_queue.get)
            if message:
                await session.generate_reply(
                    instructions=f"Say this supervisor response naturally: '{message}'"
                )
    
    threading.Thread(
        target=listen_for_supervisor_responses,
        args=(session,message_queue),
        daemon=True
    ).start()

    asyncio.create_task(supervisor_message_consumer())

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
