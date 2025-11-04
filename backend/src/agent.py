from datetime import datetime
import logging
from unittest import result
from knowledge_base import KnowledgeBase

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
from livekit.agents import function_tool, RunContext, ChatContext, ChatMessage
from Session import SalonSessionInfo
from firebase_admin import firestore
from prompts import INSTRUCTIONS
from tools import handle_unknown, salon_info, lookup_service_price

import threading
import asyncio
from help_request import db
from queue import Queue

logger = logging.getLogger("agent")
logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
kb = KnowledgeBase()

load_dotenv(".env")


class Assistant(Agent):
    def __init__(self, chat_ctx: ChatContext) -> None:
        super().__init__(
            chat_ctx=chat_ctx,
            instructions=INSTRUCTIONS,
        )

    tools = [lookup_service_price, salon_info, handle_unknown]

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    
def listen_for_supervisor_responses(session: AgentSession, message_queue: Queue):
    """Firestore watcher that pushes messages into a thread-safe queue."""
    def on_snapshot(col_snapshot, changes, read_time):
        try: 
            for change in changes:
                if change.type.name == "ADDED":
                    doc = change.document.to_dict()
                    user_id = doc.get("user_id")
                    message = doc.get("response_message")
                    question = doc.get("query")

                    if user_id == session.userdata.participant_sid and message and question:
                        print(f"[SUPERVISOR RESPONSE] {message}")
                        asyncio.run(kb.add_entry(question, message))
                        message_queue.put(message)
        except Exception as e:
            print(f"[SUPERVISOR LISTENER ERROR] {e}")
            message_queue.put(None)

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
    initial_ctx = ChatContext()
    
    initial_ctx.add_message(role="assistant", content=f"The user's name is Ankur.")
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=Assistant(chat_ctx=initial_ctx),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    await session.generate_reply(
        instructions="Greet the user as a salon receptionist named Amritesh and also user name ask how you can assist them with their beauty appointment."
    )

    await ctx.connect()
    participant = await ctx.wait_for_participant()
    
    session.userdata.user_name = participant.identity
    session.userdata.participant_sid = participant.sid
    
    message_queue = Queue()

    async def supervisor_message_consumer():
        try:
            while True:
                message = await asyncio.get_event_loop().run_in_executor(None, message_queue.get)
                if message:
                    await session.generate_reply(
                        instructions=f"Say this supervisor response yes this reponse you dont have to introduce again: '{message}'"
                    )
        except asyncio.CancelledError:
            print("[SUPERVISOR CONSUMER] Shutting down supervisor message consumer.")
            message_queue.put(None)
    
    threading.Thread(
        target=listen_for_supervisor_responses,
        args=(session,message_queue),
        daemon=True
    ).start()

    asyncio.create_task(supervisor_message_consumer())

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
