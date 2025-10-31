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

logger = logging.getLogger("agent")

load_dotenv(".env")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions = """
                You are Mia, a friendly, professional AI receptionist for Luna Glow Salon.
                You speak naturally and warmly, like a real front desk assistant.

                Your main goals:
                1. Greet clients and help them with bookings, service details, and pricing.
                2. Answer questions about salon hours, stylists, treatments, and appointments.
                3. If someone requests to speak to the owner, say you’ll note their message and pass it to the owner.
                4. If a question is outside your knowledge (e.g., “Do you offer laser hair removal?”), politely say you'll check with the front desk, then call the `handle_unknown()` tool.
                5. Always stay friendly and positive — even if the client is frustrated or unclear.
                6. Avoid technical talk. Keep responses short and natural, since users are speaking aloud.
                7. If a user gives a name, service, or time preference, acknowledge it politely and confirm details.

                Example style:
                - “Hi! This is Mia at Luna Glow Salon. How can I make your day a little brighter?”
                - “Let me double-check that with the front desk, one moment please.”
                - “I’ll pass your request to the owner and make sure they get back to you soon.”

                Never mention being an AI or a virtual system — just act like the salon’s receptionist.
                """

        )
        
    async def handle_unknown(self, context: RunContext, user_query: str):
        """Triggered when the AI doesn't know the answer."""
        logger.warning(f"Requesting help for query: {user_query}")
        
        help_req = HelpRequest(query=user_query)
        help_req.save()

        print(f"[SUPERVISOR ALERT] New help request: {user_query}")
        
        context.userdata.last_query = user_query
        context.userdata.escalated = True

        return "Let me check with my supervisor and get back to you."

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    
    @function_tool
    async def salon_info(self, context: RunContext, question: str):
        known_topics = ["hours", "price", "services", "location", "booking"]
        if any(word in question.lower() for word in known_topics):
            return "Luna Glow Salon is open 9am to 7pm, Monday through Saturday."
        else:
            return await self.handle_unknown(context, question)

    
    @function_tool
    async def lookup_service_price(self, context: RunContext, service: str):
        """Check the price of a salon service."""
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


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession[SalonSessionInfo](
        userdata=SalonSessionInfo(),
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=inference.STT(model="assemblyai/universal-streaming", language="en"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user as a salon receptionist named Mia and ask how you can assist them with their beauty appointment."
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
