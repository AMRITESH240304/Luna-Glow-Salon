from dataclasses import dataclass

@dataclass
class SalonSessionInfo:
    user_name: str | None = None
    last_query: str | None = None
    escalated: bool = False