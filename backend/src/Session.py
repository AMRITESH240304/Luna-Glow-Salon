from dataclasses import dataclass

@dataclass
class SalonSessionInfo:
    user_name: str | None = None
    last_query: str | None = None
    participant_sid: str | None = None
    escalated: bool = False
    vector_Results: list | None = None
    vector_Questions: list | None = None