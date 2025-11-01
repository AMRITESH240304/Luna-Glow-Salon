# models/help_request.py

from dataclasses import dataclass, asdict
from datetime import datetime
import firebase_admin
from firebase_admin import firestore,credentials

cred = credentials.Certificate("/Users/amriteshkumar/Developer/frontdeskAssign/backend/firebase.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@dataclass
class HelpRequest:
    query: str
    user_id: str
    user_name: str | None = None
    status: str = "pending"
    assigned_to: str = "supervisor_1"
    source: str = "LiveKitCall"
    timestamp: str = datetime.utcnow().isoformat()

    def save(self):
        """Save this HelpRequest to Firestore."""
        db.collection("help_requests").add(asdict(self))
        
