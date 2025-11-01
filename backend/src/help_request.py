# models/help_request.py

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
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
    timeout_at: str = (datetime.utcnow() + timedelta(minutes=1)).isoformat()

    def save(self):
        """Save this HelpRequest to Firestore."""
        doc_ref = db.collection("help_requests").add(asdict(self))
        return doc_ref[1].id
